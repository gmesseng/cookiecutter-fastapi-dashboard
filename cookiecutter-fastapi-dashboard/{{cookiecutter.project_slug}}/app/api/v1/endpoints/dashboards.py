"""
Dashboards — un handler par cadran d'écran (routes déclarées dans app/api/v1/router.py).

Logique et requêtes : app/services/dashboard_service.py.

`date_start`/`date_end` sont optionnels ; sans borne, le comportement est
"cumulé jusqu'à aujourd'hui" (cf. app/schemas/filters.py::build_where).
"""
from fastapi import Depends

from app.api.deps import require_permission
from app.core.constants import Perm
from app.schemas import responses
from app.schemas.filters import DashboardFilters, parse_filters
from app.services import dashboard_service


async def get_kpi_exemple(
    filters: DashboardFilters = Depends(parse_filters),
    _u: dict = Depends(require_permission(Perm.DASHBOARD_READ)),
) -> responses.ExampleKPIResponse:
    """
    Cadran KPI d'exemple, à remplacer par les cadrans du projet.

        - valeur : nombre de lignes de la table de faits sur la période.
        - montant_total : somme de la colonne `amount` sur la période.
    """
    return await dashboard_service.kpi_exemple(filters.to_params())
