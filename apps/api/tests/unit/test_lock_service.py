from __future__ import annotations

from app.models.entities import Agent
from app.services.errors import AppError
from app.services.locks import LockService


def test_lock_conflict(db_session):
    agent_a = Agent(name='a', type='cli', capabilities={})
    agent_b = Agent(name='b', type='cli', capabilities={})
    db_session.add(agent_a)
    db_session.add(agent_b)
    db_session.commit()

    locks = LockService(db_session)
    first = locks.acquire(resource_key='repo://backend/contracts/*', agent_id=agent_a.id, ttl=60)
    assert first.state == 'active'

    try:
        locks.acquire(resource_key='repo://backend/contracts/*', agent_id=agent_b.id, ttl=60)
        assert False, 'Expected conflict'
    except AppError as exc:
        assert exc.code == 'CONFLICT'
