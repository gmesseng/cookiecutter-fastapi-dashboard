"""
Paramètres de requête réutilisés par plusieurs endpoints (pagination).
"""
from fastapi import Query

from app.core.constants import (
    DEFAULT_PAGE,
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    MIN_PAGE,
    MIN_PAGE_SIZE,
)

PAGE_QUERY = Query(DEFAULT_PAGE, ge=MIN_PAGE)
PAGE_SIZE_QUERY = Query(DEFAULT_PAGE_SIZE, ge=MIN_PAGE_SIZE, le=MAX_PAGE_SIZE)
