"""
Dépendances FastAPI réutilisables pour les filtres de requêtes.

Chaque endpoint compose les petites dépendances ci-dessous dont il a besoin
plutôt qu'un seul objet générique à colonnes fixes.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from typing import Any, Optional, Tuple
from fastapi import HTTPException, Query

from app.core.constants import ErrorMessage


@dataclass
class Pagination:
    page: int
    page_size: int

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


def parse_pagination(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
) -> Pagination:
    return Pagination(page=page, page_size=page_size)


@dataclass
class DashboardFilters:
    date_start: Optional[date] = None
    date_end: Optional[date] = None

    def to_params(self) -> dict:
        return {
            "date_start": self.date_start,
            "date_end": self.date_end,
        }


async def parse_filters(
    date_start: Optional[date] = Query(
        None, description="Date début YYYY-MM-DD. Par défaut : la donnée la plus ancienne (aucune borne basse)."
    ),
    date_end: Optional[date] = Query(
        None, description="Date fin YYYY-MM-DD. Par défaut : aujourd'hui."
    ),
) -> DashboardFilters:
    if date_start and date_end and date_start > date_end:
        raise HTTPException(
            status_code=400,
            detail=ErrorMessage.INVALID_DATE_RANGE.format(date_start=date_start, date_end=date_end),
        )
    return DashboardFilters(date_start=date_start, date_end=date_end)


def build_where(params: dict[str, Any], date_column: str) -> Tuple[list[str], dict[str, Any]]:
    """Construit la clause WHERE dynamique et les paramètres SQL pour les requêtes du Mart.

        - date_start (Optionnel) : si absente, aucune borne basse ('-infinity'::DATE).
        - date_end (Optionnel)   : si absente, la date du jour (CURRENT_DATE).
    """
    params = params.copy()
    params.setdefault("date_start", None)
    params.setdefault("date_end", None)
    where_clauses = [
        f"{date_column}::date >= COALESCE(CAST(:date_start AS DATE), '-infinity'::DATE)",
        f"{date_column}::date <= COALESCE(CAST(:date_end AS DATE), CURRENT_DATE)",
    ]
    return where_clauses, params
