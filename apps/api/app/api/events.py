from __future__ import annotations

import asyncio
import json
from datetime import datetime

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db_session, require_auth
from app.config.settings import get_settings
from app.models.entities import Agent
from app.schemas.common import EventLogRequest, EventResponse
from app.services.errors import AppError, ERROR_VALIDATION
from app.services.event_stream import event_stream_broker
from app.services.events import EventService

router = APIRouter(prefix='/v1/events', tags=['events'], dependencies=[Depends(require_auth)])


def _resolve_agent_ref(db: Session, *, reference: str, repo_id: str | None) -> str:
    by_id = db.get(Agent, reference)
    if by_id:
        return by_id.id

    stmt = select(Agent).where(Agent.name == reference)
    if repo_id is not None:
        stmt = stmt.where(Agent.repo_id == repo_id)
    by_name = db.execute(stmt.order_by(Agent.created_at.desc())).scalars().first()
    if by_name:
        return by_name.id

    raise AppError(
        code=ERROR_VALIDATION,
        message='Unknown recipient reference',
        status_code=400,
        details={'reference': reference},
    )


@router.post('', response_model=EventResponse)
async def log_event(payload: EventLogRequest, db: Session = Depends(get_db_session)) -> EventResponse:
    message_payload = payload.payload or {}

    recipient_ref = payload.recipient_id or message_payload.get('recipient_id') or message_payload.get('to')
    recipient_id = _resolve_agent_ref(db, reference=recipient_ref, repo_id=payload.repo_id) if recipient_ref else None
    parent_message_id = payload.parent_message_id or message_payload.get('parent_message_id') or message_payload.get('reply_to')
    channel = payload.channel or message_payload.get('channel')

    event = EventService(db).log(
        event_type=payload.type,
        payload=message_payload,
        severity=payload.severity,
        task_id=payload.task_id,
        agent_id=payload.agent_id,
        repo_id=payload.repo_id,
        recipient_id=recipient_id,
        parent_message_id=parent_message_id,
        channel=channel,
    )
    response = EventResponse.model_validate(event, from_attributes=True)
    await event_stream_broker.publish(response.model_dump(mode='json'))
    return response


def _authorize_ws_token(*, token: str | None, authorization: str | None) -> bool:
    expected = get_settings().local_token
    resolved = token
    if not resolved and authorization and authorization.lower().startswith('bearer '):
        resolved = authorization[7:]
    return resolved == expected


@router.websocket('/ws')
async def websocket_events(
    websocket: WebSocket,
    recipient_id: str | None = Query(default=None),
    channel: str | None = Query(default=None),
    include_broadcast: bool = Query(default=True),
) -> None:
    token = websocket.query_params.get('token') or websocket.headers.get('x-repomesh-token')
    authorization = websocket.headers.get('authorization')
    if not _authorize_ws_token(token=token, authorization=authorization):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason='Invalid API token')
        return

    await websocket.accept()
    subscriber = await event_stream_broker.subscribe(
        recipient_id=recipient_id,
        channel=channel,
        include_broadcast=include_broadcast,
    )
    try:
        while True:
            item = await subscriber.queue.get()
            await websocket.send_json(item)
    except WebSocketDisconnect:
        pass
    finally:
        await event_stream_broker.unsubscribe(subscriber.id)


@router.get('/sse')
async def sse_events(
    recipient_id: str | None = Query(default=None),
    channel: str | None = Query(default=None),
    include_broadcast: bool = Query(default=True),
) -> StreamingResponse:
    async def _generator():
        subscriber = await event_stream_broker.subscribe(
            recipient_id=recipient_id,
            channel=channel,
            include_broadcast=include_broadcast,
        )
        try:
            while True:
                try:
                    item = await asyncio.wait_for(subscriber.queue.get(), timeout=15)
                    yield f"data: {json.dumps(item)}\n\n"
                except asyncio.TimeoutError:
                    yield ": keep-alive\n\n"
        finally:
            await event_stream_broker.unsubscribe(subscriber.id)

    return StreamingResponse(_generator(), media_type='text/event-stream')


@router.get('', response_model=list[EventResponse])
def list_events(
    task_id: str | None = Query(default=None),
    agent_id: str | None = Query(default=None),
    type: str | None = Query(default=None),
    recipient_id: str | None = Query(default=None),
    parent_message_id: str | None = Query(default=None),
    channel: str | None = Query(default=None),
    payload_contains: str | None = Query(default=None),
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
        payload_contains=payload_contains,
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
