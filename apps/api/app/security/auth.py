from __future__ import annotations

from fastapi import Header

from app.config.settings import get_settings
from app.services.errors import AppError, ERROR_UNAUTHORIZED


async def require_token(
    authorization: str | None = Header(default=None),
    x_repomesh_token: str | None = Header(default=None),
) -> None:
    settings = get_settings()
    expected = settings.local_token

    token = x_repomesh_token
    if not token and authorization and authorization.lower().startswith('bearer '):
        token = authorization[7:]

    if token != expected:
        raise AppError(
            code=ERROR_UNAUTHORIZED,
            message='Invalid API token',
            status_code=401,
        )
