from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import Event


class EventService:
    def __init__(self, db: Session):
        self.db = db

    def log(self, *, event_type: str, payload: dict, severity: str, task_id: str | None, agent_id: str | None, repo_id: str | None) -> Event:
        event = Event(
            type=event_type,
            payload=payload,
            severity=severity,
            task_id=task_id,
            agent_id=agent_id,
            repo_id=repo_id,
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def list(self, *, task_id: str | None = None, agent_id: str | None = None, event_type: str | None = None, limit: int = 100) -> list[Event]:
        stmt = select(Event).order_by(Event.created_at.desc()).limit(limit)
        if task_id:
            stmt = stmt.where(Event.task_id == task_id)
        if agent_id:
            stmt = stmt.where(Event.agent_id == agent_id)
        if event_type:
            stmt = stmt.where(Event.type == event_type)
        return list(self.db.execute(stmt).scalars().all())
