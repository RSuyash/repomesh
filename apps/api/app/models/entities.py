from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin


class Repo(Base):
    __tablename__ = 'repos'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(200), unique=True)
    root_path: Mapped[str] = mapped_column(String(500))
    default_branch: Mapped[str] = mapped_column(String(100), default='main')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class Agent(Base, TimestampMixin):
    __tablename__ = 'agents'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    repo_id: Mapped[str | None] = mapped_column(String(36), ForeignKey('repos.id'), nullable=True)
    name: Mapped[str] = mapped_column(String(200))
    type: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(50), default='active')
    capabilities: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    last_heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AgentSession(Base):
    __tablename__ = 'agent_sessions'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id: Mapped[str] = mapped_column(String(36), ForeignKey('agents.id'))
    status: Mapped[str] = mapped_column(String(50), default='active')
    current_task_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    last_heartbeat_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Task(Base, TimestampMixin):
    __tablename__ = 'tasks'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    repo_id: Mapped[str | None] = mapped_column(String(36), ForeignKey('repos.id'), nullable=True)
    goal: Mapped[str] = mapped_column(String(500))
    description: Mapped[str] = mapped_column(Text)
    scope: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    priority: Mapped[int] = mapped_column(Integer, default=3)
    status: Mapped[str] = mapped_column(String(50), default='pending')
    acceptance_criteria: Mapped[str | None] = mapped_column(Text, nullable=True)
    assignee_agent_id: Mapped[str | None] = mapped_column(String(36), ForeignKey('agents.id'), nullable=True)
    blocked_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    progress: Mapped[int] = mapped_column(Integer, default=0)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)


class TaskClaim(Base):
    __tablename__ = 'task_claims'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id: Mapped[str] = mapped_column(String(36), ForeignKey('tasks.id'))
    agent_id: Mapped[str] = mapped_column(String(36), ForeignKey('agents.id'))
    resource_key: Mapped[str] = mapped_column(String(500))
    lease_ttl_seconds: Mapped[int] = mapped_column(Integer)
    state: Mapped[str] = mapped_column(String(50), default='active')
    claimed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ResourceLock(Base):
    __tablename__ = 'resource_locks'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    resource_key: Mapped[str] = mapped_column(String(500), index=True)
    owner_agent_id: Mapped[str] = mapped_column(String(36), ForeignKey('agents.id'))
    state: Mapped[str] = mapped_column(String(50), default='active')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Event(Base):
    __tablename__ = 'events'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    repo_id: Mapped[str | None] = mapped_column(String(36), ForeignKey('repos.id'), nullable=True)
    agent_id: Mapped[str | None] = mapped_column(String(36), ForeignKey('agents.id'), nullable=True)
    task_id: Mapped[str | None] = mapped_column(String(36), ForeignKey('tasks.id'), nullable=True)
    type: Mapped[str] = mapped_column(String(120))
    severity: Mapped[str] = mapped_column(String(30), default='info')
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class Artifact(Base):
    __tablename__ = 'artifacts'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id: Mapped[str] = mapped_column(String(36), ForeignKey('tasks.id'))
    kind: Mapped[str] = mapped_column(String(120))
    uri: Mapped[str] = mapped_column(String(500))
    metadata_json: Mapped[dict[str, Any]] = mapped_column('metadata', JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
