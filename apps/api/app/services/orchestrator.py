from __future__ import annotations

from datetime import timedelta

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.config.settings import get_settings
from app.models.entities import Agent, Task
from app.repositories.common import utc_now
from app.services.agents import AgentService
from app.services.errors import AppError, ERROR_CONFLICT
from app.services.events import EventService
from app.services.routing import RoutingPolicyService
from app.services.tasks import TaskService


class OrchestratorEngine:
    def __init__(self, *, agent_name: str = 'repomesh-orchestrator', lease_ttl: int = 600):
        self.agent_name = agent_name
        self.lease_ttl = lease_ttl
        self.routing = RoutingPolicyService()

    def ensure_orchestrator_agent(self, db: Session) -> Agent:
        return AgentService(db).register(
            name=self.agent_name,
            agent_type='orchestrator',
            capabilities={
                'auto_claim': True,
                'event_driven': True,
                'role': 'supervisor',
            },
            repo_id=None,
            reuse_existing=True,
            takeover_if_stale=True,
        )

    def run_once(self, db: Session, *, max_assignments: int = 10) -> dict:
        agent = self.ensure_orchestrator_agent(db)
        AgentService(db).heartbeat(agent_id=agent.id, status='active', current_task=None)
        stale_sessions = AgentService(db).mark_stale_sessions()
        stale_claims = TaskService(db).expire_stale_claims()
        assignments = self._assign_pending_tasks(db, orchestrator_agent_id=agent.id, max_assignments=max_assignments)
        return {
            'orchestrator_agent_id': agent.id,
            'stale_sessions': stale_sessions,
            'stale_claims': stale_claims,
            'assignments': assignments,
        }

    def _assign_pending_tasks(self, db: Session, *, orchestrator_agent_id: str, max_assignments: int) -> list[dict]:
        workers = self._active_workers(db, exclude_agent_id=orchestrator_agent_id)
        if not workers:
            return []

        tasks = list(
            db.execute(
                select(Task)
                .where(Task.status.in_(['pending', 'stalled']))
                .order_by(desc(Task.priority), Task.created_at.asc())
                .limit(max_assignments)
            ).scalars().all()
        )
        if not tasks:
            return []

        task_service = TaskService(db)
        event_service = EventService(db)
        assignments: list[dict] = []
        worker_idx = 0

        for task in tasks:
            decision = self.routing.decide(task)
            matching = [candidate for candidate in workers if self.routing.supports(candidate, decision)]
            if matching:
                worker = matching[worker_idx % len(matching)]
            else:
                worker = workers[worker_idx % len(workers)]
            worker_idx += 1
            resource_key = self._derive_resource_key(task)
            try:
                claim = task_service.claim(
                    task_id=task.id,
                    agent_id=worker.id,
                    resource_key=resource_key,
                    lease_ttl=self.lease_ttl,
                )
            except AppError as exc:
                if exc.code == ERROR_CONFLICT:
                    continue
                raise

            task_service.update(task_id=task.id, status='in_progress', progress=0, summary=None, blocked_reason=None)
            event_service.log(
                event_type='orchestrator.assignment',
                payload={
                    'task_id': task.id,
                    'assigned_to': worker.id,
                    'assigned_to_name': worker.name,
                    'resource_key': resource_key,
                    'assigned_at': utc_now().isoformat(),
                    'route': {
                        'tier': decision.tier,
                        'adapter_profile': decision.adapter_profile,
                        'reason': decision.reason,
                    },
                },
                severity='info',
                task_id=task.id,
                agent_id=orchestrator_agent_id,
                repo_id=task.repo_id,
                recipient_id=worker.id,
                parent_message_id=None,
                channel='orchestration',
            )
            assignments.append(
                {
                    'task_id': task.id,
                    'claim_id': claim.id,
                    'agent_id': worker.id,
                    'agent_name': worker.name,
                    'resource_key': resource_key,
                    'route': {
                        'tier': decision.tier,
                        'adapter_profile': decision.adapter_profile,
                    },
                }
            )

        return assignments

    @staticmethod
    def _derive_resource_key(task: Task) -> str:
        scope = task.scope or {}
        explicit = scope.get('resource_key')
        if isinstance(explicit, str) and explicit.strip():
            return explicit

        files = scope.get('files')
        if isinstance(files, list) and files:
            first = files[0]
            if isinstance(first, str) and first.strip():
                return f'file:{first}'

        component = scope.get('component')
        if isinstance(component, str) and component.strip():
            return f'component:{component}'

        return f'task:{task.id}'

    @staticmethod
    def _active_workers(db: Session, *, exclude_agent_id: str) -> list[Agent]:
        settings = get_settings()
        now = utc_now()
        fresh_cutoff = now - timedelta(seconds=settings.session_ttl_seconds * 2)
        return list(
            db.execute(
                select(Agent)
                .where(
                    Agent.status == 'active',
                    Agent.id != exclude_agent_id,
                    Agent.type != 'orchestrator',
                    Agent.last_heartbeat_at.is_not(None),
                    Agent.last_heartbeat_at >= fresh_cutoff,
                )
                .order_by(Agent.last_heartbeat_at.desc())
            ).scalars().all()
        )
