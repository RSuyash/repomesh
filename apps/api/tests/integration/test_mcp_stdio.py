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
    assert response['error'] is None
    assert response['result']['name'] == 'stdio-agent'
