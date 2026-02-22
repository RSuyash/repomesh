from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db_session, require_auth
from app.schemas.common import ContextBundleResponse
from app.services.context import ContextService

router = APIRouter(prefix='/v1/context', tags=['context'], dependencies=[Depends(require_auth)])


@router.get('/bundle/{task_id}', response_model=ContextBundleResponse)
def get_bundle(
    task_id: str,
    mode: str = Query(default='compact'),
    include_recent: bool = Query(default=True),
    db: Session = Depends(get_db_session),
) -> ContextBundleResponse:
    bundle = ContextService(db).bundle(task_id=task_id, mode=mode, include_recent=include_recent)
    return ContextBundleResponse.model_validate(bundle)
