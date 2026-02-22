from __future__ import annotations

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.security.auth import require_token


def get_db_session(db: Session = Depends(get_db)) -> Session:
    return db


def require_auth(_: None = Depends(require_token)) -> None:
    return None
