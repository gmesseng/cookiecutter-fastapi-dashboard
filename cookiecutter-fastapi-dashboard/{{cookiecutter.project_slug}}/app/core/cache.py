"""
Cache Redis async.
@cached(prefix="...") : décorateur transparent — lecture cache → calcul → écriture cache.
La clé est construite automatiquement à partir du prefix + arguments de la fonction.
"""
import functools
import inspect
import json
from datetime import datetime
from typing import Any, Callable
import redis.asyncio as aioredis
from pydantic_core import to_jsonable_python

from app.core.config import settings
_redis: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = await aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis


async def close_redis() -> None:
    global _redis
    if _redis:
        await _redis.aclose()
        _redis = None


def _serialize_value(v: Any) -> str:
    """Convertit n'importe quelle valeur en string stable pour la clé Redis."""
    if v is None:
        return "null"
    if isinstance(v, datetime):
        return v.strftime("%Y%m%d%H%M%S")
    if isinstance(v, dict):
        return json.dumps({k: _serialize_value(val) for k, val in sorted(v.items())})
    return str(v)


def cached(prefix: str, ttl: int | None = None) -> Callable:
    """
    Décorateur de cache Redis transparent.

    Usage :
        @cached(prefix="dashboard_kpi")
        async def get_kpi(*, query: dict) -> dict:
            ...
    """
    def decorator(func: Callable) -> Callable:
        signature = inspect.signature(func)

        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            r = await get_redis()

            # Construction de la clé à partir de TOUS les arguments (positionnels
            # compris) : les services sont appelés en positionnel, ex. f(query).
            bound = signature.bind(*args, **kwargs)
            key_parts = [settings.REDIS_KEY_PREFIX + prefix]
            for k, v in sorted(bound.arguments.items()):
                if v is not None:
                    key_parts.append(f"{k}={_serialize_value(v)}")
            cache_key = ":".join(key_parts)

            # Lecture cache — renvoie un dict, revalidé par le response_model de la route
            cached_val = await r.get(cache_key)
            if cached_val is not None:
                return json.loads(cached_val)

            # Calcul
            result = await func(*args, **kwargs)

            # Écriture cache — modèles Pydantic, dates, Decimal, UUID convertis en
            # types JSON. Pas de default=str : un type inconnu doit lever une
            # erreur plutôt que stocker sa représentation texte.
            await r.set(
                cache_key,
                json.dumps(to_jsonable_python(result)),
                ex=ttl or settings.REDIS_TTL,
            )
            return result

        return wrapper
    return decorator
