from __future__ import annotations

from datetime import timedelta

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.models.entities import ResourceLock, Task, TaskClaim
from app.repositories.common import utc_now
from app.services.errors import AppError, ERROR_CONFLICT, ERROR_NOT_FOUND, ERROR_VALIDATION
from app.services.locks import LockService

ALLOWED_STATUSES = {'pending', 'claimed', 'in_progress', 'blocked', 'completed', 'stalled'}


class TaskService:
    def __init__(self, db: Session):
        self.db = db

    def create(self, *, goal: str, description: str, scope: dict, priority: int, acceptance_criteria: str | None, repo_id: str | None) -> Task:
        task = Task(
            goal=goal,
            description=description,
            scope=scope,
            priority=priority,
            acceptance_criteria=acceptance_criteria,
            repo_id=repo_id,
            status='pending',
        )
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def list(self, *, status: str | None, scope: str | None, assignee: str | None) -> list[Task]:
        self.expire_stale_claims()
        stmt = select(Task).order_by(Task.created_at.desc())
        if status:
            stmt = stmt.where(Task.status == status)
        if assignee:
            stmt = stmt.where(Task.assignee_agent_id == assignee)
        if scope:
            stmt = stmt.where(Task.scope['component'].as_string() == scope)
        return list(self.db.execute(stmt).scalars().all())

    def claim(self, *, task_id: str, agent_id: str, resource_key: str, lease_ttl: int) -> TaskClaim:
        now = utc_now()
        task = self.db.get(Task, task_id)
        if not task:
            raise AppError(code=ERROR_NOT_FOUND, message='Task not found', status_code=404)
        if task.status == 'completed':
            raise AppError(code=ERROR_CONFLICT, message='Task already completed', status_code=409)

        lock = self.db.execute(
            select(ResourceLock).where(
                ResourceLock.resource_key == resource_key,
                ResourceLock.owner_agent_id == agent_id,
                ResourceLock.state == 'active',
                ResourceLock.expires_at >= now,
            )
        ).scalars().first()

        if not lock:
            # Auto-acquire the requested resource lock for this claim to reduce
            # claim friction while preserving single-owner lock semantics.
            lock = LockService(self.db).acquire(resource_key=resource_key, agent_id=agent_id, ttl=lease_ttl)

        self.expire_stale_claims(task_id)
        active_claim = self.db.execute(
            select(TaskClaim).where(
                TaskClaim.task_id == task_id,
                TaskClaim.state == 'active',
                TaskClaim.expires_at >= now,
            )
        ).scalars().first()
        if active_claim and active_claim.agent_id != agent_id:
            raise AppError(code=ERROR_CONFLICT, message='Task already claimed by another agent', status_code=409)

        claim = TaskClaim(
            task_id=task_id,
            agent_id=agent_id,
            resource_key=resource_key,
            lease_ttl_seconds=lease_ttl,
            state='active',
            claimed_at=now,
            expires_at=now + timedelta(seconds=lease_ttl),
        )
        task.status = 'claimed'
        task.assignee_agent_id = agent_id
        self.db.add(claim)
        self.db.commit()
        self.db.refresh(claim)
        return claim

    def update(self, *, task_id: str, status: str | None, progress: int | None, summary: str | None, blocked_reason: str | None) -> Task:
        task = self.db.get(Task, task_id)
        if not task:
            raise AppError(code=ERROR_NOT_FOUND, message='Task not found', status_code=404)

        if status:
            if status not in ALLOWED_STATUSES:
                raise AppError(code=ERROR_VALIDATION, message='Invalid task status', status_code=400)
            task.status = status

        if progress is not None:
            if progress < 0 or progress > 100:
                raise AppError(code=ERROR_VALIDATION, message='Progress must be between 0 and 100', status_code=400)
            task.progress = progress

        if summary is not None:
            task.summary = summary

        if blocked_reason is not None:
            task.blocked_reason = blocked_reason

        self.db.commit()
        self.db.refresh(task)
        return task

    def get(self, task_id: str) -> Task:
        self.expire_stale_claims(task_id=task_id)
        task = self.db.get(Task, task_id)
        if not task:
            raise AppError(code=ERROR_NOT_FOUND, message='Task not found', status_code=404)
        return task

    def expire_stale_claims(self, task_id: str | None = None) -> int:
        now = utc_now()
        stmt = select(TaskClaim).where(and_(TaskClaim.state == 'active', TaskClaim.expires_at < now))
        if task_id:
            stmt = stmt.where(TaskClaim.task_id == task_id)
        stale_claims = self.db.execute(stmt).scalars().all()
        for claim in stale_claims:
            claim.state = 'expired'
            claim.released_at = now
            task = self.db.get(Task, claim.task_id)
            if task and task.status in {'claimed', 'in_progress'}:
                task.status = 'stalled'
        if stale_claims:
            self.db.commit()
        return len(stale_claims)
