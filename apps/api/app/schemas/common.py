from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ErrorEnvelope(BaseModel):
    error: dict[str, Any]


class RepoRef(BaseModel):
    id: str
    name: str


class AgentRegisterRequest(BaseModel):
    name: str
    type: str
    capabilities: dict[str, Any] = Field(default_factory=dict)
    repo_id: str | None = None


class AgentHeartbeatRequest(BaseModel):
    status: str
    current_task: str | None = None


class AgentResponse(BaseModel):
    id: str
    repo_id: str | None
    name: str
    type: str
    status: str
    capabilities: dict[str, Any]
    last_heartbeat_at: datetime | None


class TaskCreateRequest(BaseModel):
    goal: str
    description: str
    scope: dict[str, Any] = Field(default_factory=dict)
    priority: int = 3
    deps: list[str] = Field(default_factory=list)
    acceptance_criteria: str | None = None
    repo_id: str | None = None


class TaskClaimRequest(BaseModel):
    agent_id: str
    resource_key: str
    lease_ttl: int = 1800


class TaskUpdateRequest(BaseModel):
    status: str | None = None
    notes: str | None = None
    progress: int | None = None
    summary: str | None = None
    blocked_reason: str | None = None


class TaskResponse(BaseModel):
    id: str
    repo_id: str | None
    goal: str
    description: str
    scope: dict[str, Any]
    priority: int
    status: str
    acceptance_criteria: str | None
    assignee_agent_id: str | None
    blocked_reason: str | None
    progress: int
    summary: str | None
    created_at: datetime
    updated_at: datetime


class LockAcquireRequest(BaseModel):
    resource_key: str
    agent_id: str
    ttl: int = 1800


class LockRenewRequest(BaseModel):
    agent_id: str
    ttl: int = 1800


class LockReleaseRequest(BaseModel):
    agent_id: str


class LockResponse(BaseModel):
    id: str
    resource_key: str
    owner_agent_id: str
    state: str
    created_at: datetime
    expires_at: datetime
    released_at: datetime | None


class EventLogRequest(BaseModel):
    type: str
    payload: dict[str, Any] = Field(default_factory=dict)
    severity: str = 'info'
    task_id: str | None = None
    agent_id: str | None = None
    repo_id: str | None = None


class EventResponse(BaseModel):
    id: str
    repo_id: str | None
    agent_id: str | None
    task_id: str | None
    type: str
    severity: str
    payload: dict[str, Any]
    created_at: datetime


class ContextBundleResponse(BaseModel):
    task: dict[str, Any]
    scope_files: list[str]
    recent_events: list[dict[str, Any]]
    lock_status: list[dict[str, Any]]
    placeholders: dict[str, Any]


class MCPCallRequest(BaseModel):
    jsonrpc: str = '2.0'
    id: str | int | None = None
    method: str
    params: dict[str, Any] = Field(default_factory=dict)


class MCPCallResponse(BaseModel):
    jsonrpc: str = '2.0'
    id: str | int | None = None
    result: dict[str, Any] | None = None
    error: dict[str, Any] | None = None
