from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db_session, require_auth
from app.services.summarizer import SummarizerService
from app.services.summarizer_runtime import summarizer_runtime

router = APIRouter(prefix='/v1/summarizer', tags=['summarizer'], dependencies=[Depends(require_auth)])


@router.get('/status')
def status() -> dict:
    return summarizer_runtime.status()


@router.post('/start')
async def start() -> dict:
    return await summarizer_runtime.start()


@router.post('/stop')
async def stop() -> dict:
    return await summarizer_runtime.stop()


@router.post('/tick')
def tick(max_tasks: int = Query(default=10, ge=1, le=200), db: Session = Depends(get_db_session)) -> dict:
    return SummarizerService(db).run_once(max_tasks=max_tasks)
