from __future__ import annotations

from datetime import datetime

from sqlalchemy import String, cast, or_, select
from sqlalchemy.orm import Session

from app.models.entities import Event


class EventService:
    def __init__(self, db: Session):
        self.db = db

    def log(
        self,
        *,
        event_type: str,
        payload: dict,
        severity: str,
        task_id: str | None,
        agent_id: str | None,
        repo_id: str | None,
        recipient_id: str | None = None,
        parent_message_id: str | None = None,
        channel: str | None = None,
    ) -> Event:
        event = Event(
            type=event_type,
            payload=payload,
            severity=severity,
            task_id=task_id,
            agent_id=agent_id,
            repo_id=repo_id,
            recipient_id=recipient_id,
            parent_message_id=parent_message_id,
            channel=channel or 'default',
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def list(
        self,
        *,
        task_id: str | None = None,
        agent_id: str | None = None,
        event_type: str | None = None,
        recipient_id: str | None = None,
        parent_message_id: str | None = None,
        channel: str | None = None,
        payload_contains: str | None = None,
        include_broadcast: bool = False,
        since: datetime | None = None,
        before: datetime | None = None,
        direction: str = 'desc',
        limit: int = 100,
    ) -> list[Event]:
        stmt = select(Event)
        if task_id:
            stmt = stmt.where(Event.task_id == task_id)
        if agent_id:
            stmt = stmt.where(Event.agent_id == agent_id)
        if event_type:
            stmt = stmt.where(Event.type == event_type)
        if recipient_id:
            if include_broadcast:
                stmt = stmt.where(or_(Event.recipient_id == recipient_id, Event.recipient_id.is_(None)))
            else:
                stmt = stmt.where(Event.recipient_id == recipient_id)
        if parent_message_id:
            stmt = stmt.where(Event.parent_message_id == parent_message_id)
        if channel:
            stmt = stmt.where(Event.channel == channel)
        if payload_contains:
            stmt = stmt.where(cast(Event.payload, String).ilike(f'%{payload_contains}%'))
        if since:
            stmt = stmt.where(Event.created_at > since)
        if before:
            stmt = stmt.where(Event.created_at < before)

        order_field = Event.created_at.asc() if direction == 'asc' else Event.created_at.desc()
        stmt = stmt.order_by(order_field).limit(limit)
        return list(self.db.execute(stmt).scalars().all())

    def thread(self, *, message_id: str, limit: int = 200) -> list[Event]:
        root = self.db.get(Event, message_id)
        if not root:
            return []

        results: list[Event] = [root]
        seen: set[str] = {root.id}
        frontier: list[str] = [root.id]

        while frontier and len(results) < limit:
            replies = list(
                self.db.execute(
                    select(Event)
                    .where(Event.parent_message_id.in_(frontier))
                    .order_by(Event.created_at.asc())
                ).scalars().all()
            )
            frontier = []
            for reply in replies:
                if reply.id in seen:
                    continue
                seen.add(reply.id)
                results.append(reply)
                frontier.append(reply.id)
                if len(results) >= limit:
                    break

        return sorted(results, key=lambda item: item.created_at)
