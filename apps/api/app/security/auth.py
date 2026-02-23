from __future__ import annotations

from fastapi import Header, Query

from app.config.settings import get_settings
from app.services.errors import AppError, ERROR_UNAUTHORIZED


async def require_token(
    authorization: str | None = Header(default=None),
    x_repomesh_token: str | None = Header(default=None),
    token: str | None = Query(default=None),
) -> None:
    settings = get_settings()
    expected = settings.local_token

    resolved = x_repomesh_token or token
    if not resolved and authorization and authorization.lower().startswith('bearer '):
        resolved = authorization[7:]

    if resolved != expected:
        raise AppError(
            code=ERROR_UNAUTHORIZED,
            message='Invalid API token',
            status_code=401,
        )
