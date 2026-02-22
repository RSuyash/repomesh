from __future__ import annotations

from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config.settings import get_settings
from app.models.entities import Agent, AgentSession
from app.repositories.common import utc_now
from app.services.errors import AppError, ERROR_NOT_FOUND


class AgentService:
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()

    def register(self, *, name: str, agent_type: str, capabilities: dict, repo_id: str | None) -> Agent:
        agent = Agent(name=name, type=agent_type, capabilities=capabilities, repo_id=repo_id, status='active')
        self.db.add(agent)
        self.db.flush()

        now = utc_now()
        session = AgentSession(
            agent_id=agent.id,
            status='active',
            current_task_id=None,
            last_heartbeat_at=now,
            expires_at=now + timedelta(seconds=self.settings.session_ttl_seconds),
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(agent)
        return agent

    def heartbeat(self, *, agent_id: str, status: str, current_task: str | None) -> Agent:
        agent = self.db.get(Agent, agent_id)
        if not agent:
            raise AppError(code=ERROR_NOT_FOUND, message='Agent not found', status_code=404)

        now = utc_now()
        agent.status = status
        agent.last_heartbeat_at = now

        session = self.db.execute(
            select(AgentSession).where(AgentSession.agent_id == agent_id).order_by(AgentSession.last_heartbeat_at.desc())
        ).scalars().first()

        if session is None:
            session = AgentSession(
                agent_id=agent.id,
                status=status,
                current_task_id=current_task,
                last_heartbeat_at=now,
                expires_at=now + timedelta(seconds=self.settings.session_ttl_seconds),
            )
            self.db.add(session)
        else:
            session.status = status
            session.current_task_id = current_task
            session.last_heartbeat_at = now
            session.expires_at = now + timedelta(seconds=self.settings.session_ttl_seconds)

        self.db.commit()
        self.db.refresh(agent)
        return agent

    def list(self, repo_id: str | None) -> list[Agent]:
        self.mark_stale_sessions()
        stmt = select(Agent).order_by(Agent.created_at.desc())
        if repo_id:
            stmt = stmt.where(Agent.repo_id == repo_id)
        return list(self.db.execute(stmt).scalars().all())

    def mark_stale_sessions(self) -> int:
        now = utc_now()
        sessions = self.db.execute(select(AgentSession).where(AgentSession.expires_at < now, AgentSession.status == 'active')).scalars().all()
        count = 0
        for session in sessions:
            session.status = 'stale'
            count += 1
        if count:
            self.db.commit()
        return count
