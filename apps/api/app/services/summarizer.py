from __future__ import annotations

from collections import Counter
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import Event, Task
from app.services.events import EventService


class SummarizerService:
    def __init__(self, db: Session):
        self.db = db
        self.events = EventService(db)

    def run_once(self, *, max_tasks: int = 10, max_events_per_task: int = 200) -> dict[str, Any]:
        tasks = list(
            self.db.execute(
                select(Task)
                .where(Task.status == 'completed')
                .order_by(Task.updated_at.desc())
                .limit(max_tasks)
            ).scalars().all()
        )
        compressed: list[dict[str, Any]] = []
        for task in tasks:
            if self._has_summary_event(task.id):
                continue
            task_events = self.events.list(task_id=task.id, direction='asc', limit=max_events_per_task)
            if not task_events:
                continue
            summary_payload = self._summarize_task(task=task, task_events=task_events)
            summary_event = self.events.log(
                event_type='summary.task',
                payload=summary_payload,
                severity='info',
                task_id=task.id,
                agent_id=None,
                repo_id=task.repo_id,
                recipient_id=None,
                parent_message_id=None,
                channel='summary',
            )
            compressed.append({'task_id': task.id, 'summary_event_id': summary_event.id, 'event_count': len(task_events)})
        return {'compressed': compressed, 'count': len(compressed)}

    def _has_summary_event(self, task_id: str) -> bool:
        return (
            self.db.execute(select(Event.id).where(Event.task_id == task_id, Event.type == 'summary.task').limit(1))
            .scalar_one_or_none()
            is not None
        )

    @staticmethod
    def _summarize_task(*, task: Task, task_events: list[Event]) -> dict[str, Any]:
        type_counts = Counter(item.type for item in task_events)
        sev_counts = Counter(item.severity for item in task_events)
        last_events = [
            {'id': item.id, 'type': item.type, 'severity': item.severity, 'created_at': item.created_at.isoformat()}
            for item in task_events[-5:]
        ]
        return {
            'task': {'id': task.id, 'goal': task.goal, 'priority': task.priority},
            'aggregate': {
                'event_count': len(task_events),
                'type_counts': dict(type_counts),
                'severity_counts': dict(sev_counts),
            },
            'last_events': last_events,
            'summary_text': f"Task completed with {len(task_events)} events and {len(type_counts)} unique event types.",
        }
