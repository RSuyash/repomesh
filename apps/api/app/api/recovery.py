from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db_session, require_auth
from app.services.agents import AgentService
from app.services.tasks import TaskService

router = APIRouter(prefix='/v1/recovery', tags=['recovery'], dependencies=[Depends(require_auth)])


@router.post('/reconcile')
def reconcile(db: Session = Depends(get_db_session)) -> dict:
    stale_sessions = AgentService(db).mark_stale_sessions()
    stale_claims = TaskService(db).expire_stale_claims()
    return {'stale_sessions': stale_sessions, 'stale_claims': stale_claims}
