from __future__ import annotations

import json

from app.db import create_all
from app.mcp.stdio import handle_line


def test_mcp_stdio_register_agent():
    create_all()

    request = {
        'jsonrpc': '2.0',
        'id': 'stdio-1',
        'method': 'tool.call',
        'params': {
            'name': 'agent.register',
            'arguments': {
                'name': 'stdio-agent',
                'type': 'cli',
                'capabilities': {'mcp': True}
            }
        }
    }

    response = handle_line(json.dumps(request))

    assert response['id'] == 'stdio-1'
    assert 'error' not in response
    assert response['result']['name'] == 'stdio-agent'


def test_mcp_stdio_initialize_and_tools_list():
    init_request = {'jsonrpc': '2.0', 'id': 'init-1', 'method': 'initialize', 'params': {}}
    init_response = handle_line(json.dumps(init_request))
    assert init_response['id'] == 'init-1'
    assert 'error' not in init_response
    assert init_response['result']['serverInfo']['name'] == 'repomesh-mcp'

    list_request = {'jsonrpc': '2.0', 'id': 'list-1', 'method': 'tools/list', 'params': {}}
    list_response = handle_line(json.dumps(list_request))
    assert list_response['id'] == 'list-1'
    assert 'error' not in list_response
    names = {tool['name'] for tool in list_response['result']['tools']}
    assert 'task.list' in names


def test_mcp_stdio_tools_call_shape():
    request = {
        'jsonrpc': '2.0',
        'id': 'call-1',
        'method': 'tools/call',
        'params': {'name': 'task.list', 'arguments': {}},
    }
    response = handle_line(json.dumps(request))
    assert response['id'] == 'call-1'
    assert 'error' not in response
    assert response['result']['isError'] is False
    assert 'structuredContent' in response['result']
    assert isinstance(response['result']['content'], list)
