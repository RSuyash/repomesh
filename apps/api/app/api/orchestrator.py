from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db_session, require_auth
from app.services.orchestrator import OrchestratorEngine
from app.services.orchestrator_runtime import orchestrator_runtime

router = APIRouter(prefix='/v1/orchestrator', tags=['orchestrator'], dependencies=[Depends(require_auth)])


@router.get('/status')
def status() -> dict:
    return orchestrator_runtime.status()


@router.post('/start')
async def start() -> dict:
    return await orchestrator_runtime.start()


@router.post('/stop')
async def stop() -> dict:
    return await orchestrator_runtime.stop()


@router.post('/tick')
def tick(
    max_assignments: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db_session),
) -> dict:
    return OrchestratorEngine().run_once(db, max_assignments=max_assignments)
