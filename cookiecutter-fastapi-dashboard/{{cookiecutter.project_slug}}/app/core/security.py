"""
Vérification JWT HS256.
verify_token : dependency FastAPI — injecté sur chaque endpoint protégé.
create_access_token : utilisé si l'API émet elle-même des tokens.
"""
from datetime import datetime, timedelta
from typing import Any

import jwt
from fastapi import Depends, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings
from app.core.errors import ApiError, ErrorCodes

bearer_scheme = HTTPBearer(auto_error=True)


def verify_token(
    creds: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict[str, Any]:
    """Décode et valide le JWT. Injecter via Depends() sur les endpoints."""
    token = creds.credentials
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=["HS256"],
            options={"require": ["exp", "iat"]},
        )
        return payload
    except jwt.ExpiredSignatureError as e:
        raise ApiError(
            code=ErrorCodes.AUTH_EXPIRED_TOKEN,
            message="Token expiré.",
            status=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Bearer"},
        ) from e
    except jwt.InvalidTokenError as e:
        raise ApiError(
            code=ErrorCodes.AUTH_INVALID_TOKEN,
            message="Token invalide.",
            status=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


def create_access_token(
    subject: str,
    expires_delta: timedelta | None = None,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """Crée un JWT signé HS256. extra_claims (roles, perms, email...) est fusionné dans le payload."""
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload = {
        "sub": subject,
        "exp": expire,
        "iat": datetime.utcnow(),
        **(extra_claims or {}),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
