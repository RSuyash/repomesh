from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db_session, require_auth
from app.schemas.common import EventLogRequest, EventResponse
from app.services.events import EventService

router = APIRouter(prefix='/v1/events', tags=['events'], dependencies=[Depends(require_auth)])


@router.post('', response_model=EventResponse)
def log_event(payload: EventLogRequest, db: Session = Depends(get_db_session)) -> EventResponse:
    event = EventService(db).log(
        event_type=payload.type,
        payload=payload.payload,
        severity=payload.severity,
        task_id=payload.task_id,
        agent_id=payload.agent_id,
        repo_id=payload.repo_id,
    )
    return EventResponse.model_validate(event, from_attributes=True)


@router.get('', response_model=list[EventResponse])
def list_events(
    task_id: str | None = Query(default=None),
    agent_id: str | None = Query(default=None),
    type: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db_session),
) -> list[EventResponse]:
    events = EventService(db).list(task_id=task_id, agent_id=agent_id, event_type=type, limit=limit)
    return [EventResponse.model_validate(item, from_attributes=True) for item in events]
