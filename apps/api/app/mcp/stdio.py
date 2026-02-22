from __future__ import annotations

import json
import sys

from app.db import SessionLocal, create_all
from app.mcp.service import MCPToolService
from app.services.errors import AppError


def _response(request_id: str | int | None, result: dict | None = None, error: dict | None = None) -> dict:
    return {
        'jsonrpc': '2.0',
        'id': request_id,
        'result': result,
        'error': error,
    }


def _initialize_result() -> dict:
    return {
        'protocolVersion': '2024-11-05',
        'capabilities': {'tools': {}},
        'serverInfo': {'name': 'repomesh-mcp', 'version': '0.1.0'},
    }


def _tool_result(result: dict) -> dict:
    text = json.dumps(result, default=str)
    return {
        'content': [{'type': 'text', 'text': text}],
        'structuredContent': result,
        'isError': False,
    }


def handle_line(raw: str) -> dict | None:
    payload = json.loads(raw)
    method = payload.get('method')
    if method == 'notifications/initialized':
        return None
    if method == 'initialize':
        return _response(payload.get('id'), result=_initialize_result())
    if method == 'tools/list':
        return _response(payload.get('id'), result={'tools': MCPToolService.definitions()})
    if method not in {'tools/call', 'tool.call'}:
        return _response(payload.get('id'), error={'code': 'INVALID_METHOD', 'message': 'Unsupported method'})

    params = payload.get('params', {})
    tool_name = params.get('name')
    args = params.get('arguments', {})

    if not tool_name:
        return _response(payload.get('id'), error={'code': 'VALIDATION_ERROR', 'message': 'params.name is required'})

    with SessionLocal() as db:
        try:
            result = MCPToolService(db).call(tool_name=tool_name, arguments=args)
            if method == 'tools/call':
                return _response(payload.get('id'), result=_tool_result(result))
            return _response(payload.get('id'), result=result)
        except AppError as exc:
            return _response(payload.get('id'), error={'code': exc.code, 'message': exc.message, 'status': exc.status_code})
        except ValueError as exc:
            return _response(payload.get('id'), error={'code': 'UNKNOWN_TOOL', 'message': str(exc)})


def _read_message() -> dict | None:
    first_line = sys.stdin.buffer.readline()
    if not first_line:
        return None

    stripped = first_line.strip()
    if stripped.startswith(b'{'):
        return json.loads(stripped.decode('utf-8'))

    headers: list[str] = [first_line.decode('utf-8').strip()]
    while True:
        line = sys.stdin.buffer.readline()
        if not line:
            return None
        if line in (b'\r\n', b'\n'):
            break
        headers.append(line.decode('utf-8').strip())

    content_length = None
    for header in headers:
        parts = header.split(':', 1)
        if len(parts) == 2 and parts[0].lower() == 'content-length':
            content_length = int(parts[1].strip())
            break

    if content_length is None:
        return None

    body = sys.stdin.buffer.read(content_length)
    if not body:
        return None

    return json.loads(body.decode('utf-8'))


def _write_message(output: dict) -> None:
    payload = json.dumps(output, default=str).encode('utf-8')
    header = f'Content-Length: {len(payload)}\r\n\r\n'.encode('utf-8')
    sys.stdout.buffer.write(header + payload)
    sys.stdout.buffer.flush()


def main() -> None:
    create_all()
    while True:
        try:
            payload = _read_message()
        except json.JSONDecodeError:
            output = _response(None, error={'code': 'INVALID_JSON', 'message': 'Malformed JSON payload'})
            _write_message(output)
            continue

        if payload is None:
            break

        try:
            output = handle_line(json.dumps(payload))
        except json.JSONDecodeError:
            output = _response(None, error={'code': 'INVALID_JSON', 'message': 'Malformed JSON payload'})

        if output is not None:
            _write_message(output)

        # Legacy line mode compatibility for local manual testing.
        if payload.get('method') == 'tool.call' and payload.get('jsonrpc') != '2.0':
            continue


if __name__ == '__main__':
    main()
