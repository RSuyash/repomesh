from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db_session, require_auth
from app.services.adapters import AdapterService
from app.services.adapter_runtime import adapter_runtime

router = APIRouter(prefix='/v1/adapters', tags=['adapters'], dependencies=[Depends(require_auth)])


@router.get('/status')
def status() -> dict:
    return adapter_runtime.status()


@router.post('/start')
async def start() -> dict:
    return await adapter_runtime.start()


@router.post('/stop')
async def stop() -> dict:
    return await adapter_runtime.stop()


@router.post('/execute')
def execute(
    agent_id: str = Query(...),
    task_id: str | None = Query(default=None),
    dry_run: bool = Query(default=False),
    max_tasks: int = Query(default=5, ge=1, le=50),
    db: Session = Depends(get_db_session),
) -> dict:
    return AdapterService(db).execute(
        agent_id=agent_id,
        task_id=task_id,
        dry_run=dry_run,
        max_tasks=max_tasks,
    )


@router.post('/tick')
def tick(max_tasks_per_agent: int = Query(default=2, ge=1, le=10)) -> dict:
    return adapter_runtime.run_once_sync(max_tasks_per_agent=max_tasks_per_agent)
