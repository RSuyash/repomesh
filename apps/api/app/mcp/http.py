from __future__ import annotations

import json

from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, Response
from sqlalchemy.orm import Session

from app.api.deps import get_db_session
from app.schemas.common import MCPCallRequest
from app.services.errors import AppError
from app.mcp.service import MCPToolService

router = APIRouter(prefix='/mcp', tags=['mcp'])


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


def _response(request_id: str | int | None, result: dict | None = None, error: dict | None = None) -> JSONResponse:
    body: dict = {'jsonrpc': '2.0', 'id': request_id}
    if error is not None:
        body['error'] = error
    else:
        body['result'] = result or {}
    return JSONResponse(content=jsonable_encoder(body))


@router.post('/http', response_model=None)
def mcp_http_call(payload: MCPCallRequest, db: Session = Depends(get_db_session)):
    if payload.id is None and payload.method.startswith('notifications/'):
        return Response(status_code=204)

    if payload.method == 'initialize':
        return _response(payload.id, result=_initialize_result())

    if payload.method == 'tools/list':
        return _response(payload.id, result={'tools': MCPToolService.definitions()})

    if payload.method == 'notifications/initialized':
        return Response(status_code=204)

    if payload.method not in {'tool.call', 'tools/call'}:
        return _response(payload.id, error={'code': 'INVALID_METHOD', 'message': 'Unsupported method'})

    params = payload.params or {}
    tool_name = params.get('name')
    arguments = params.get('arguments', {})

    if not tool_name:
        return _response(payload.id, error={'code': 'VALIDATION_ERROR', 'message': 'params.name is required'})

    try:
        result = MCPToolService(db).call(tool_name=tool_name, arguments=arguments)
        if payload.method == 'tools/call':
            result = _tool_result(result)
        return _response(payload.id, result=result)
    except AppError as exc:
        return _response(
            payload.id,
            error={'code': exc.code, 'message': exc.message, 'status': exc.status_code, 'details': exc.details or {}},
        )
    except ValueError as exc:
        return _response(payload.id, error={'code': 'UNKNOWN_TOOL', 'message': str(exc)})
