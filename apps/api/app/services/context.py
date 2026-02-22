from __future__ import annotations

from sqlalchemy.orm import Session

from app.services.events import EventService
from app.services.locks import LockService
from app.services.tasks import TaskService


class ContextService:
    def __init__(self, db: Session):
        self.db = db
        self.tasks = TaskService(db)
        self.events = EventService(db)
        self.locks = LockService(db)

    def bundle(self, task_id: str, mode: str = 'compact', include_recent: bool = True) -> dict:
        task = self.tasks.get(task_id)
        scope_files = task.scope.get('files', []) if isinstance(task.scope, dict) else []

        recent_events = []
        if include_recent:
            for item in self.events.list(task_id=task_id, limit=20):
                recent_events.append(
                    {
                        'id': item.id,
                        'type': item.type,
                        'severity': item.severity,
                        'payload': item.payload,
                        'created_at': item.created_at.isoformat(),
                    }
                )

        lock_status = []
        if task.assignee_agent_id:
            for lock in self.locks.active_for(agent_id=task.assignee_agent_id):
                lock_status.append(
                    {
                        'id': lock.id,
                        'resource_key': lock.resource_key,
                        'owner_agent_id': lock.owner_agent_id,
                        'state': lock.state,
                        'expires_at': lock.expires_at.isoformat(),
                    }
                )

        placeholders = {
            'errors': {'latest': [], 'note': 'Error pipeline placeholder for MVP'},
            'tests': {'latest_runs': [], 'note': 'Test pipeline placeholder for MVP'},
            'mode': mode,
        }

        return {
            'task': {
                'id': task.id,
                'goal': task.goal,
                'description': task.description,
                'status': task.status,
                'priority': task.priority,
                'acceptance_criteria': task.acceptance_criteria,
                'assignee_agent_id': task.assignee_agent_id,
                'progress': task.progress,
            },
            'scope_files': sorted(scope_files),
            'recent_events': recent_events,
            'lock_status': sorted(lock_status, key=lambda x: x['resource_key']),
            'placeholders': placeholders,
        }
