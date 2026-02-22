from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db_session, require_auth
from app.schemas.common import LockAcquireRequest, LockReleaseRequest, LockRenewRequest, LockResponse
from app.services.locks import LockService

router = APIRouter(prefix='/v1/locks', tags=['locks'], dependencies=[Depends(require_auth)])


@router.post('/acquire', response_model=LockResponse)
def acquire_lock(payload: LockAcquireRequest, db: Session = Depends(get_db_session)) -> LockResponse:
    lock = LockService(db).acquire(resource_key=payload.resource_key, agent_id=payload.agent_id, ttl=payload.ttl)
    return LockResponse.model_validate(lock, from_attributes=True)


@router.post('/{lock_id}/renew', response_model=LockResponse)
def renew_lock(lock_id: str, payload: LockRenewRequest, db: Session = Depends(get_db_session)) -> LockResponse:
    lock = LockService(db).renew(lock_id=lock_id, agent_id=payload.agent_id, ttl=payload.ttl)
    return LockResponse.model_validate(lock, from_attributes=True)


@router.post('/{lock_id}/release', response_model=LockResponse)
def release_lock(lock_id: str, payload: LockReleaseRequest, db: Session = Depends(get_db_session)) -> LockResponse:
    lock = LockService(db).release(lock_id=lock_id, agent_id=payload.agent_id)
    return LockResponse.model_validate(lock, from_attributes=True)
