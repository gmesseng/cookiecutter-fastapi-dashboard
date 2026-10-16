"""
{{ cookiecutter.project_name }} — Bootstrap.

Production-ready :
  - JWT obligatoire sur toutes les routes
  - Rate limiting Redis-backed (60 req/min par IP)
  - Request-ID propagé + access log JSON structuré
  - Headers de sécurité (HSTS, nosniff, frame-options)
  - Erreurs JSON standardisées avec codes machine-readable
  - CORS configuré via .env
  - Probes K8s /healthz et /readyz
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_redoc_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse, JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.api.v1.router import router as api_router
from app.core.cache import close_redis, get_redis
from app.core.config import settings
from app.core.errors import install_exception_handlers
from app.core.health import check_services
from app.core.logging import log, setup_logging
from app.core.middleware import (
    AccessLogMiddleware,
    RequestIDMiddleware,
    SecurityHeadersMiddleware,
)
from app.core.rate_limit import limiter
from app.db.session import close_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    log.info("startup_begin", project=settings.PROJECT_NAME)

    # Vérification Redis
    await get_redis()
    log.info("redis_connected")

    log.info("startup_done")
    try:
        yield
    finally:
        log.info("shutdown_begin")
        await close_redis()
        await close_engine()
        log.info("shutdown_done")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=f"{settings.PROJECT_NAME} — {{ cookiecutter.description }}",
    version="{{ cookiecutter.version }}",
    docs_url="/docs",
    redoc_url=None,
    lifespan=lifespan,
    openapi_url="/api/v1/openapi.json"
)

# ── Middlewares (ordre = ordre d'exécution sur la requête entrante) ────────
app.add_middleware(RequestIDMiddleware)
app.add_middleware(AccessLogMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

if settings.cors_origins_list:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["GET"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
        expose_headers=["X-Request-ID", "X-RateLimit-Limit", "X-RateLimit-Remaining"],
    )

# ── Rate limiting ──────────────────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]

# ── Erreurs JSON structurées ───────────────────────────────────────────────
install_exception_handlers(app)

# ── Routes ─────────────────────────────────────────────────────────────────
app.include_router(api_router, prefix=settings.API_V1_STR)


# ── Swagger en lecture seule ────────────────────────────────────────────────
def custom_openapi() -> dict:
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    for path, operations in list(schema.get("paths", {}).items()):
        for method in list(operations.keys()):
            if method.lower() != "get":
                del operations[method]
        if not operations:
            del schema["paths"][path]
    app.openapi_schema = schema
    return app.openapi_schema


app.openapi = custom_openapi


@app.get("/redoc", include_in_schema=False)
async def redoc_html() -> HTMLResponse:
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - ReDoc",
        redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@2.1.5/bundles/redoc.standalone.js",
    )


# ── Probes K8s ─────────────────────────────────────────────────────────────
@app.get("/healthz", include_in_schema=False, tags=["k8s"])
async def liveness() -> dict:
    """Liveness probe — répond 200 tant que le process est vivant."""
    return {"status": "alive"}


@app.get("/readyz", include_in_schema=False, tags=["k8s"])
async def readiness() -> dict:
    """Readiness probe — vérifie que le cache et les deux bases sont joignables."""
    services = await check_services()
    issues = [f"{name}: {info['error']}" for name, info in services.items() if info["status"] == "down"]
    if issues:
        return {"status": "not_ready", "issues": issues}
    return {"status": "ready"}


@app.get(
    "/health",
    tags=["Health"],
    summary="État des services externes (app, cache, bases source/destination)",
)
async def health() -> JSONResponse:
    """
    Statut détaillé de chaque service externe dont l'API dépend pour fonctionner (recensés dans app/core/health.py, réutilisant les factories
    
        de connexion existantes — aucune nouvelle connexion créée ici) : le cache Redis, la base PostgreSQL source (OLTP) et la base PostgreSQL destination
        (analytique). Route publique, hors JWT — n'expose que des statuts up/down et un message d'erreur technique, aucune donnée métier.

        200 si tous les services sont up, 305 dès qu'un seul est down (chaque
        service en panne porte son propre message d'erreur, en plus d'un
        résumé {service: message} au niveau racine).
    """
    services = await check_services()
    errors = {name: info["error"] for name, info in services.items() if info["status"] == "down"}
    http_status = 200 if not errors else 305
    content: dict[str, object] = {"status": http_status, "services": services}
    if errors:
        content["error"] = errors
    return JSONResponse(status_code=http_status, content=content)
