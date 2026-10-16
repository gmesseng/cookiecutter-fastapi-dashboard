"""
Router v1 — déclaration centralisée de TOUTES les routes de l'API.

Chaque route est enregistrée explicitement via `router.add_api_route` :
chemin, handler (app/api/v1/endpoints/*), méthode HTTP, tag OpenAPI, résumé.
Les handlers ne portent pas de décorateur ; ils délèguent toute la logique
et le SQL aux services (app/services/*).

L'ordre de déclaration compte : à chemin égal, FastAPI résout les routes
dans l'ordre où elles sont enregistrées.
"""
from fastapi import APIRouter
from app.api.v1.endpoints import dashboards
from app.core.constants import ApiTag
from app.schemas import responses

router = APIRouter()

router.add_api_route(
    "/dashboards/kpis/exemple",
    dashboards.get_kpi_exemple,
    methods=["GET"],
    tags=[ApiTag.DASHBOARDS],
    response_model=responses.ExampleKPIResponse,
    summary="Cadran KPI — exemple (nombre de lignes et montant total)",
)
