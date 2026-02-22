from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AppError(Exception):
    code: str
    message: str
    status_code: int = 400
    details: dict | None = None


ERROR_NOT_FOUND = 'NOT_FOUND'
ERROR_CONFLICT = 'CONFLICT'
ERROR_UNAUTHORIZED = 'UNAUTHORIZED'
ERROR_VALIDATION = 'VALIDATION_ERROR'
