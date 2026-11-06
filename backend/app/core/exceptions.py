"""
Domain errors and the single HTTP handler that renders them.

Services raise these instead of `HTTPException`, so business rules do not know
they are being served over HTTP. The handler answers with the same body
FastAPI's `HTTPException` produces — `{"detail": "<message>"}` — which is what
the frontend reads (`frontend/src/shared/api/http.ts`, `errorFrom`).

Messages reach the end user: write them for a person, never with internal
detail (ids of other tenants, SQL, stack traces).
"""

from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse


class AppError(Exception):
    status_code: int = status.HTTP_400_BAD_REQUEST

    def __init__(self, message: str, *, headers: dict[str, str] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.headers = headers


class BadRequest(AppError):
    status_code = status.HTTP_400_BAD_REQUEST


class Unauthorized(AppError):
    status_code = status.HTTP_401_UNAUTHORIZED


class Forbidden(AppError):
    status_code = status.HTTP_403_FORBIDDEN


class NotFound(AppError):
    status_code = status.HTTP_404_NOT_FOUND


class Conflict(AppError):
    status_code = status.HTTP_409_CONFLICT


class TooManyRequests(AppError):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS


class ServiceUnavailable(AppError):
    """A state that resolves by itself (provisioning, migration pending): the caller may retry."""

    status_code = status.HTTP_503_SERVICE_UNAVAILABLE


async def _handle_app_error(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, AppError)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
        headers=exc.headers,
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, _handle_app_error)
