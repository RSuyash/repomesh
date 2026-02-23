from __future__ import annotations

from datetime import datetime

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
        recipient_id=payload.recipient_id,
        parent_message_id=payload.parent_message_id,
        channel=payload.channel,
    )
    return EventResponse.model_validate(event, from_attributes=True)


@router.get('', response_model=list[EventResponse])
def list_events(
    task_id: str | None = Query(default=None),
    agent_id: str | None = Query(default=None),
    type: str | None = Query(default=None),
    recipient_id: str | None = Query(default=None),
    parent_message_id: str | None = Query(default=None),
    channel: str | None = Query(default=None),
    include_broadcast: bool = Query(default=False),
    since: datetime | None = Query(default=None),
    before: datetime | None = Query(default=None),
    direction: str = Query(default='desc', pattern='^(asc|desc)$'),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db_session),
) -> list[EventResponse]:
    events = EventService(db).list(
        task_id=task_id,
        agent_id=agent_id,
        event_type=type,
        recipient_id=recipient_id,
        parent_message_id=parent_message_id,
        channel=channel,
        include_broadcast=include_broadcast,
        since=since,
        before=before,
        direction=direction,
        limit=limit,
    )
    return [EventResponse.model_validate(item, from_attributes=True) for item in events]


@router.get('/thread/{message_id}', response_model=list[EventResponse])
def get_thread(
    message_id: str,
    limit: int = Query(default=200, ge=1, le=1000),
    db: Session = Depends(get_db_session),
) -> list[EventResponse]:
    events = EventService(db).thread(message_id=message_id, limit=limit)
    return [EventResponse.model_validate(item, from_attributes=True) for item in events]
