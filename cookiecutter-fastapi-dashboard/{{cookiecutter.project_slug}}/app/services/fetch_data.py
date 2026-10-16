"""
Fonctions utilitaires génériques d'accès aux données.

fetch_all/fetch_one/fetch_scalar/execute -> base DEST (analytics).
fetch_all_source/fetch_one_source/execute_source -> base SOURCE (OLTP,
comptes/rôles, événements bruts, factures, QR codes, audit_logs...).
"""
from math import ceil
from typing import Any, Optional
from fastapi import HTTPException, status
from sqlalchemy import text
from app.db.session import get_session, get_source_session

async def fetch_all(query: str, params: dict[str, Any] | None = None, source: bool = False) -> list[dict]:
    session_context = get_source_session() if source else get_session()
    async with session_context as session:
        result = await session.execute(text(query), params or {})
        rows = result.fetchall()
        if not rows:
            return []
        keys = list(result.keys())
        return [dict(zip(keys, row)) for row in rows]

async def fetch_one(query: str, params: dict[str, Any] | None = None, source: bool = False) -> Optional[dict]:
    rows = await fetch_all(query, params, source)
    return rows[0] if rows else None


async def fetch_scalar(query: str, params: dict[str, Any] | None = None, source: bool = False) -> Any:
    row = await fetch_one(query, params, source)
    return list(row.values())[0] if row else None


def build_pagination(total_items: int, page: int, page_size: int) -> dict:
    total_pages = ceil(total_items / page_size) if page_size > 0 else 0
    return {
        "current_page": page,
        "page_size": page_size,
        "total_items": total_items,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_previous": page > 1,
    }

