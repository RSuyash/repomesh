from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db_session, require_auth
from app.schemas.common import AgentHeartbeatRequest, AgentRegisterRequest, AgentResponse
from app.services.agents import AgentService

router = APIRouter(prefix='/v1/agents', tags=['agents'], dependencies=[Depends(require_auth)])


@router.post('/register', response_model=AgentResponse)
def register_agent(payload: AgentRegisterRequest, db: Session = Depends(get_db_session)) -> AgentResponse:
    agent = AgentService(db).register(
        name=payload.name,
        agent_type=payload.type,
        capabilities=payload.capabilities,
        repo_id=payload.repo_id,
    )
    return AgentResponse.model_validate(agent, from_attributes=True)


@router.post('/{agent_id}/heartbeat', response_model=AgentResponse)
def heartbeat(agent_id: str, payload: AgentHeartbeatRequest, db: Session = Depends(get_db_session)) -> AgentResponse:
    agent = AgentService(db).heartbeat(agent_id=agent_id, status=payload.status, current_task=payload.current_task)
    return AgentResponse.model_validate(agent, from_attributes=True)


@router.get('', response_model=list[AgentResponse])
def list_agents(
    repo_id: str | None = Query(default=None),
    db: Session = Depends(get_db_session),
) -> list[AgentResponse]:
    agents = AgentService(db).list(repo_id=repo_id)
    return [AgentResponse.model_validate(item, from_attributes=True) for item in agents]
