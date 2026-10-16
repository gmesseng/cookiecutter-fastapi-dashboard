"""
Vérifie la disponibilité de chaque service externe dont l'application a
réellement besoin pour tourner (cf. app/main.py::lifespan et
app/db/session.py / app/core/cache.py pour les factories de connexion) :

  - cache        -> Redis, via get_redis() (app/core/cache.py)
  - source_db    -> PostgreSQL OLTP, via get_source_session() (app/db/session.py)
  - destination_db -> PostgreSQL analytique, via get_session() (app/db/session.py)

Aucune autre dépendance externe (pas de file de messages, pas de stockage
objet, pas d'API tierce) n'existe dans ce projet à ce jour — cette liste
n'est pas figée, elle reflète uniquement ce que le code importe et connecte
réellement. Les noms de clé ci-dessous désignent le RÔLE du service dans le
projet (utile s'il y avait plusieurs bases de types différents), le type
technique réel est porté par le champ "type" de chaque entrée.

Utilisé par /health (détail, JSON riche) et /readyz (probe k8s, résumé).
"""
from typing import Any
from sqlalchemy import text
from app.core.cache import get_redis
from app.db.session import get_session, get_source_session

async def check_services() -> dict[str, dict[str, Any]]:
    services: dict[str, dict[str, Any]] = {"app": {"status": "up"}}

    try:
        r = await get_redis()
        await r.ping()
        services["cache"] = {"type": "redis", "status": "up"}
    except Exception as e:
        services["cache"] = {"type": "redis", "status": "down", "error": str(e)}

    try:
        async with get_source_session() as s:
            await s.execute(text("SELECT 1"))
        services["source_db"] = {"type": "postgresql", "status": "up"}
    except Exception as e:
        services["source_db"] = {"type": "postgresql", "status": "down", "error": str(e)}

    try:
        async with get_session() as s:
            await s.execute(text("SELECT 1"))
        services["destination_db"] = {"type": "postgresql", "status": "up"}
    except Exception as e:
        services["destination_db"] = {"type": "postgresql", "status": "down", "error": str(e)}

    return services
