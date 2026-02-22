from __future__ import annotations

import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db_session, require_auth
from app.schemas.common import MCPCallRequest, MCPCallResponse
from app.services.errors import AppError
from app.mcp.service import MCPToolService

router = APIRouter(prefix='/mcp', tags=['mcp'], dependencies=[Depends(require_auth)])


@router.get('/tools')
def list_tools() -> dict:
    return {'tools': [item['name'] for item in MCPToolService.definitions()]}


def _initialize_result() -> dict:
    return {
        'protocolVersion': '2024-11-05',
        'capabilities': {'tools': {}},
        'serverInfo': {'name': 'repomesh-mcp', 'version': '0.1.0'},
    }


def _tool_result(result: dict) -> dict:
    text = json.dumps(result, default=str)
    return {'content': [{'type': 'text', 'text': text}], 'structuredContent': result, 'isError': False}


@router.post('/http', response_model=MCPCallResponse)
def mcp_http_call(payload: MCPCallRequest, db: Session = Depends(get_db_session)) -> MCPCallResponse:
    if payload.method == 'initialize':
        return MCPCallResponse(id=payload.id, result=_initialize_result())

    if payload.method == 'tools/list':
        return MCPCallResponse(id=payload.id, result={'tools': MCPToolService.definitions()})

    if payload.method == 'notifications/initialized':
        return MCPCallResponse(id=payload.id, result={})

    if payload.method not in {'tool.call', 'tools/call'}:
        return MCPCallResponse(id=payload.id, error={'code': 'INVALID_METHOD', 'message': 'Unsupported method'})

    params = payload.params or {}
    tool_name = params.get('name')
    arguments = params.get('arguments', {})

    if not tool_name:
        return MCPCallResponse(id=payload.id, error={'code': 'VALIDATION_ERROR', 'message': 'params.name is required'})

    try:
        result = MCPToolService(db).call(tool_name=tool_name, arguments=arguments)
        if payload.method == 'tools/call':
            result = _tool_result(result)
        return MCPCallResponse(id=payload.id, result=result)
    except AppError as exc:
        return MCPCallResponse(
            id=payload.id,
            error={'code': exc.code, 'message': exc.message, 'status': exc.status_code, 'details': exc.details or {}},
        )
    except ValueError as exc:
        return MCPCallResponse(id=payload.id, error={'code': 'UNKNOWN_TOOL', 'message': str(exc)})
