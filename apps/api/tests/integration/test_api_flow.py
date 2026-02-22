from __future__ import annotations


def _headers() -> dict[str, str]:
    return {'x-repomesh-token': 'test-token'}


def test_agent_task_lock_context_flow(client):
    register = client.post(
        '/v1/agents/register',
        headers=_headers(),
        json={'name': 'agent-one', 'type': 'cli', 'capabilities': {'mcp': True}},
    )
    assert register.status_code == 200
    agent_id = register.json()['id']

    lock = client.post(
        '/v1/locks/acquire',
        headers=_headers(),
        json={'resource_key': 'repo://backend/contracts/*', 'agent_id': agent_id, 'ttl': 300},
    )
    assert lock.status_code == 200

    task = client.post(
        '/v1/tasks',
        headers=_headers(),
        json={
            'goal': 'Implement lock-safe task flow',
            'description': 'test flow',
            'scope': {'files': ['backend/contracts/task.py']},
            'priority': 2,
        },
    )
    assert task.status_code == 200
    task_id = task.json()['id']

    claim = client.post(
        f'/v1/tasks/{task_id}/claim',
        headers=_headers(),
        json={'agent_id': agent_id, 'resource_key': 'repo://backend/contracts/*', 'lease_ttl': 300},
    )
    assert claim.status_code == 200

    event = client.post(
        '/v1/events',
        headers=_headers(),
        json={'type': 'test.run', 'severity': 'info', 'payload': {'ok': True}, 'task_id': task_id, 'agent_id': agent_id},
    )
    assert event.status_code == 200

    bundle = client.get(f'/v1/context/bundle/{task_id}', headers=_headers())
    assert bundle.status_code == 200
    payload = bundle.json()
    assert payload['task']['id'] == task_id
    assert payload['scope_files'] == ['backend/contracts/task.py']
    assert len(payload['recent_events']) >= 1


def test_mcp_http_parity(client):
    register = client.post('/v1/agents/register', headers=_headers(), json={'name': 'mcp-agent', 'type': 'cli', 'capabilities': {}})
    assert register.status_code == 200
    agent_id = register.json()['id']

    lock = client.post(
        '/mcp/http',
        headers=_headers(),
        json={
            'jsonrpc': '2.0',
            'id': '1',
            'method': 'tool.call',
            'params': {
                'name': 'lock.acquire',
                'arguments': {'resource_key': 'repo://frontend/audience-tab', 'agent_id': agent_id, 'ttl': 120},
            },
        },
    )
    assert lock.status_code == 200
    assert lock.json()['result']['resource_key'] == 'repo://frontend/audience-tab'
