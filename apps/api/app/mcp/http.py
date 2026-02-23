from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, Response
from sqlalchemy.orm import Session

from app.api.deps import get_db_session
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
def mcp_http_call(payload: dict[str, Any], db: Session = Depends(get_db_session)):
    request_id = payload.get('id')
    method = payload.get('method')
    if not isinstance(method, str):
        return _response(
            request_id,
            error={'code': 'VALIDATION_ERROR', 'message': 'method is required and must be a string'},
        )

    if request_id is None and method.startswith('notifications/'):
        return Response(status_code=204)

    if method == 'initialize':
        return _response(request_id, result=_initialize_result())

    if method == 'tools/list':
        return _response(request_id, result={'tools': MCPToolService.definitions()})

    if method == 'notifications/initialized':
        return Response(status_code=204)

    if method not in {'tool.call', 'tools/call'}:
        return _response(request_id, error={'code': 'INVALID_METHOD', 'message': 'Unsupported method'})

    params = payload.get('params')
    if params is None:
        params = {}
    if not isinstance(params, dict):
        return _response(request_id, error={'code': 'VALIDATION_ERROR', 'message': 'params must be an object'})
    tool_name = params.get('name')
    arguments = params.get('arguments') or {}
    if not isinstance(arguments, dict):
        return _response(request_id, error={'code': 'VALIDATION_ERROR', 'message': 'params.arguments must be an object'})

    if not tool_name:
        return _response(request_id, error={'code': 'VALIDATION_ERROR', 'message': 'params.name is required'})

    try:
        result = MCPToolService(db).call(tool_name=tool_name, arguments=arguments)
        if method == 'tools/call':
            result = _tool_result(result)
        return _response(request_id, result=result)
    except AppError as exc:
        return _response(
            request_id,
            error={'code': exc.code, 'message': exc.message, 'status': exc.status_code, 'details': exc.details or {}},
        )
    except ValueError as exc:
        return _response(request_id, error={'code': 'UNKNOWN_TOOL', 'message': str(exc)})
