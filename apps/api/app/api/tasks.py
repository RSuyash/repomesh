from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db_session, require_auth
from app.schemas.common import TaskClaimRequest, TaskCreateRequest, TaskResponse, TaskUpdateRequest
from app.services.tasks import TaskService

router = APIRouter(prefix='/v1/tasks', tags=['tasks'], dependencies=[Depends(require_auth)])


@router.post('', response_model=TaskResponse)
def create_task(payload: TaskCreateRequest, db: Session = Depends(get_db_session)) -> TaskResponse:
    task = TaskService(db).create(
        goal=payload.goal,
        description=payload.description,
        scope=payload.scope,
        priority=payload.priority,
        acceptance_criteria=payload.acceptance_criteria,
        repo_id=payload.repo_id,
    )
    return TaskResponse.model_validate(task, from_attributes=True)


@router.get('', response_model=list[TaskResponse])
def list_tasks(
    status: str | None = Query(default=None),
    scope: str | None = Query(default=None),
    assignee: str | None = Query(default=None),
    db: Session = Depends(get_db_session),
) -> list[TaskResponse]:
    tasks = TaskService(db).list(status=status, scope=scope, assignee=assignee)
    return [TaskResponse.model_validate(item, from_attributes=True) for item in tasks]


@router.post('/{task_id}/claim')
def claim_task(task_id: str, payload: TaskClaimRequest, db: Session = Depends(get_db_session)) -> dict:
    claim = TaskService(db).claim(
        task_id=task_id,
        agent_id=payload.agent_id,
        resource_key=payload.resource_key,
        lease_ttl=payload.lease_ttl,
    )
    return {
        'id': claim.id,
        'task_id': claim.task_id,
        'agent_id': claim.agent_id,
        'resource_key': claim.resource_key,
        'state': claim.state,
        'expires_at': claim.expires_at,
    }


@router.patch('/{task_id}', response_model=TaskResponse)
def update_task(task_id: str, payload: TaskUpdateRequest, db: Session = Depends(get_db_session)) -> TaskResponse:
    task = TaskService(db).update(
        task_id=task_id,
        status=payload.status,
        progress=payload.progress,
        summary=payload.summary,
        blocked_reason=payload.blocked_reason,
    )
    return TaskResponse.model_validate(task, from_attributes=True)
