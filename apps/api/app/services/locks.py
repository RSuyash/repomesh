from __future__ import annotations

from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import ResourceLock
from app.repositories.common import utc_now
from app.services.errors import AppError, ERROR_CONFLICT, ERROR_NOT_FOUND


class LockService:
    def __init__(self, db: Session):
        self.db = db

    def _expire_stale(self, resource_key: str | None = None) -> None:
        now = utc_now()
        stmt = select(ResourceLock).where(ResourceLock.state == 'active', ResourceLock.expires_at < now)
        if resource_key:
            stmt = stmt.where(ResourceLock.resource_key == resource_key)
        stale = self.db.execute(stmt).scalars().all()
        for lock in stale:
            lock.state = 'expired'

    def acquire(self, *, resource_key: str, agent_id: str, ttl: int) -> ResourceLock:
        self._expire_stale(resource_key)
        now = utc_now()
        active = self.db.execute(
            select(ResourceLock).where(
                ResourceLock.resource_key == resource_key,
                ResourceLock.state == 'active',
                ResourceLock.expires_at >= now,
            )
        ).scalars().all()

        for lock in active:
            if lock.owner_agent_id != agent_id:
                raise AppError(code=ERROR_CONFLICT, message='Resource already locked', status_code=409)

        if active:
            lock = active[0]
            lock.expires_at = now + timedelta(seconds=ttl)
            self.db.commit()
            self.db.refresh(lock)
            return lock

        lock = ResourceLock(
            resource_key=resource_key,
            owner_agent_id=agent_id,
            state='active',
            created_at=now,
            expires_at=now + timedelta(seconds=ttl),
        )
        self.db.add(lock)
        self.db.commit()
        self.db.refresh(lock)
        return lock

    def renew(self, *, lock_id: str, agent_id: str, ttl: int) -> ResourceLock:
        lock = self.db.get(ResourceLock, lock_id)
        if not lock:
            raise AppError(code=ERROR_NOT_FOUND, message='Lock not found', status_code=404)
        if lock.owner_agent_id != agent_id:
            raise AppError(code=ERROR_CONFLICT, message='Lock owner mismatch', status_code=409)
        if lock.state != 'active':
            raise AppError(code=ERROR_CONFLICT, message='Lock is not active', status_code=409)

        lock.expires_at = utc_now() + timedelta(seconds=ttl)
        self.db.commit()
        self.db.refresh(lock)
        return lock

    def release(self, *, lock_id: str, agent_id: str) -> ResourceLock:
        lock = self.db.get(ResourceLock, lock_id)
        if not lock:
            raise AppError(code=ERROR_NOT_FOUND, message='Lock not found', status_code=404)
        if lock.owner_agent_id != agent_id:
            raise AppError(code=ERROR_CONFLICT, message='Lock owner mismatch', status_code=409)

        lock.state = 'released'
        lock.released_at = utc_now()
        self.db.commit()
        self.db.refresh(lock)
        return lock

    def active_for(self, *, agent_id: str | None = None, resource_key: str | None = None) -> list[ResourceLock]:
        self._expire_stale(resource_key)
        stmt = select(ResourceLock).where(ResourceLock.state == 'active').order_by(ResourceLock.created_at.desc())
        if agent_id:
            stmt = stmt.where(ResourceLock.owner_agent_id == agent_id)
        if resource_key:
            stmt = stmt.where(ResourceLock.resource_key == resource_key)
        return list(self.db.execute(stmt).scalars().all())
