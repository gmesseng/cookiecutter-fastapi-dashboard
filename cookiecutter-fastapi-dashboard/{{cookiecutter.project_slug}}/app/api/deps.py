"""
Dépendances FastAPI réutilisables.
"""
from typing import Any

from fastapi import Depends

from app.core.constants import MISSING_PERMISSION_MESSAGE, Perm
from app.core.errors import ApiError, ErrorCodes
from app.core.security import verify_token  # noqa: F401 — re-export


def require_permission(permission: str):
    """
    Vérifie que le JWT porte la permission demandée (embarquée dans la claim
    "perms" au moment du login).

    Les restrictions de rôle s'appliquent au niveau des données et des
    actions, pas seulement de l'affichage — donc côté API, pas côté front.
    """

    def _checker(claims: dict[str, Any] = Depends(verify_token)) -> dict[str, Any]:
        perms = set(claims.get("perms", []))
        if Perm.WILDCARD not in perms and permission not in perms:
            raise ApiError(
                code=ErrorCodes.AUTH_MISSING_SCOPE,
                message=MISSING_PERMISSION_MESSAGE.format(permission=permission),
                status=403,
            )
        return claims

    return _checker
