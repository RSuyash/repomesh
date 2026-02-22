from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db_session, require_auth
from app.schemas.common import MCPCallRequest, MCPCallResponse
from app.services.errors import AppError
from app.mcp.service import MCPToolService

router = APIRouter(prefix='/mcp', tags=['mcp'], dependencies=[Depends(require_auth)])


@router.get('/tools')
def list_tools() -> dict:
    return {
        'tools': [
            'agent.register',
            'agent.heartbeat',
            'agent.list',
            'task.create',
            'task.list',
            'task.claim',
            'task.update',
            'lock.acquire',
            'lock.renew',
            'lock.release',
            'event.log',
            'event.list',
            'context.bundle',
        ]
    }


@router.post('/http', response_model=MCPCallResponse)
def mcp_http_call(payload: MCPCallRequest, db: Session = Depends(get_db_session)) -> MCPCallResponse:
    if payload.method != 'tool.call':
        return MCPCallResponse(id=payload.id, error={'code': 'INVALID_METHOD', 'message': 'Only tool.call is supported'})

    params = payload.params or {}
    tool_name = params.get('name')
    arguments = params.get('arguments', {})

    if not tool_name:
        return MCPCallResponse(id=payload.id, error={'code': 'VALIDATION_ERROR', 'message': 'params.name is required'})

    try:
        result = MCPToolService(db).call(tool_name=tool_name, arguments=arguments)
        return MCPCallResponse(id=payload.id, result=result)
    except AppError as exc:
        return MCPCallResponse(
            id=payload.id,
            error={'code': exc.code, 'message': exc.message, 'status': exc.status_code, 'details': exc.details or {}},
        )
    except ValueError as exc:
        return MCPCallResponse(id=payload.id, error={'code': 'UNKNOWN_TOOL', 'message': str(exc)})
