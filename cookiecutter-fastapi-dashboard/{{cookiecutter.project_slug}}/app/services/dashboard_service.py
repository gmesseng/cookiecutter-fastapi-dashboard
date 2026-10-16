"""
Dashboards — calcul des cadrans (routes déclarées dans app/api/v1/router.py).

Lecture du mart analytique uniquement (base DEST). Chaque cadran est mis en
cache Redis via @cached : la clé inclut tous les paramètres de la requête.
"""
from typing import Any, Dict

from app.core.cache import cached
from app.core.config import settings
from app.schemas.filters import build_where
from app.schemas.responses import ExampleKPIResponse, ExampleKPIValue
from app.services.fetch_data import fetch_one


@cached(prefix="kpi_exemple")
async def kpi_exemple(query: Dict[str, Any]) -> ExampleKPIResponse:
    where_clauses, params = build_where(query, date_column="f.created_at")
    sql = f"""
        SELECT
            COUNT(*)                    AS valeur,
            COALESCE(SUM(f.amount), 0)  AS montant_total
        FROM {settings.T_FACT_EXAMPLE} f
        WHERE {" AND ".join(where_clauses)}
    """
    record = await fetch_one(sql, params) or {}
    return ExampleKPIResponse(data=ExampleKPIValue(
        valeur=int(record.get("valeur") or 0),
        montant_total=float(record.get("montant_total") or 0),
    ))
