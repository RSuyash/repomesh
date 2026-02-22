from __future__ import annotations

import json
import sys

from app.db import SessionLocal
from app.mcp.service import MCPToolService
from app.services.errors import AppError


def _response(request_id: str | int | None, result: dict | None = None, error: dict | None = None) -> dict:
    return {
        'jsonrpc': '2.0',
        'id': request_id,
        'result': result,
        'error': error,
    }


def handle_line(raw: str) -> dict:
    payload = json.loads(raw)
    if payload.get('method') != 'tool.call':
        return _response(payload.get('id'), error={'code': 'INVALID_METHOD', 'message': 'Only tool.call is supported'})

    params = payload.get('params', {})
    tool_name = params.get('name')
    args = params.get('arguments', {})

    if not tool_name:
        return _response(payload.get('id'), error={'code': 'VALIDATION_ERROR', 'message': 'params.name is required'})

    with SessionLocal() as db:
        try:
            result = MCPToolService(db).call(tool_name=tool_name, arguments=args)
            return _response(payload.get('id'), result=result)
        except AppError as exc:
            return _response(payload.get('id'), error={'code': exc.code, 'message': exc.message, 'status': exc.status_code})
        except ValueError as exc:
            return _response(payload.get('id'), error={'code': 'UNKNOWN_TOOL', 'message': str(exc)})


def main() -> None:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            output = handle_line(line)
        except json.JSONDecodeError:
            output = _response(None, error={'code': 'INVALID_JSON', 'message': 'Malformed JSON payload'})
        sys.stdout.write(json.dumps(output) + '\n')
        sys.stdout.flush()


if __name__ == '__main__':
    main()
