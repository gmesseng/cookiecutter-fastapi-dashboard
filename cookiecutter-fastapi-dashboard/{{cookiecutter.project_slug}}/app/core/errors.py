"""
Erreurs JSON structurées avec codes machine-readable.
Chaque erreur retourne : { "code": "...", "message": "...", "request_id": "..." }
"""
from typing import Any, Optional

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse


class ErrorCodes:
    AUTH_INVALID_TOKEN  = "auth/invalid-token"
    AUTH_EXPIRED_TOKEN  = "auth/expired-token"
    AUTH_MISSING_SCOPE  = "auth/missing-scope"
    NOT_FOUND           = "resource/not-found"
    VALIDATION_ERROR    = "validation/error"
    INTERNAL_ERROR      = "internal/error"
    DB_UNAVAILABLE      = "db/unavailable"


class ApiError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status: int = 400,
        headers: Optional[dict] = None,
    ):
        self.code    = code
        self.message = message
        self.status  = status
        self.headers = headers or {}
        super().__init__(message)


def _error_response(request: Request, code: str, message: str, status_code: int, headers: dict = None) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "code":       code,
            "message":    message,
            "request_id": request.headers.get("X-Request-ID", ""),
        },
        headers=headers or {},
    )


def install_exception_handlers(app: FastAPI) -> None:
    from fastapi.exceptions import RequestValidationError
    from starlette.exceptions import HTTPException as StarletteHTTPException

    @app.exception_handler(ApiError)
    async def api_error_handler(request: Request, exc: ApiError) -> JSONResponse:
        return _error_response(request, exc.code, exc.message, exc.status, exc.headers)

    @app.exception_handler(StarletteHTTPException)
    async def http_error_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        return _error_response(request, "http/error", str(exc.detail), exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        return _error_response(
            request,
            ErrorCodes.VALIDATION_ERROR,
            str(exc.errors()),
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
        return _error_response(
            request,
            ErrorCodes.INTERNAL_ERROR,
            "Une erreur interne est survenue.",
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
