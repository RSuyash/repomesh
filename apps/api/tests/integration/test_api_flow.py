from __future__ import annotations

import time


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


def test_recovery_reclaims_expired_claims(client):
    register = client.post(
        '/v1/agents/register',
        headers=_headers(),
        json={'name': 'recovery-agent', 'type': 'cli', 'capabilities': {}},
    )
    assert register.status_code == 200
    agent_id = register.json()['id']

    lock = client.post(
        '/v1/locks/acquire',
        headers=_headers(),
        json={'resource_key': 'repo://db/migrations', 'agent_id': agent_id, 'ttl': 5},
    )
    assert lock.status_code == 200

    task = client.post(
        '/v1/tasks',
        headers=_headers(),
        json={
            'goal': 'Crash recovery test',
            'description': 'simulate expired lease',
            'scope': {'files': ['db/migrations/001.sql']},
        },
    )
    assert task.status_code == 200
    task_id = task.json()['id']

    claim = client.post(
        f'/v1/tasks/{task_id}/claim',
        headers=_headers(),
        json={'agent_id': agent_id, 'resource_key': 'repo://db/migrations', 'lease_ttl': 1},
    )
    assert claim.status_code == 200

    time.sleep(1.2)

    reconcile = client.post('/v1/recovery/reconcile', headers=_headers())
    assert reconcile.status_code == 200
    assert reconcile.json()['stale_claims'] >= 1

    tasks = client.get('/v1/tasks', headers=_headers())
    assert tasks.status_code == 200
    matched = [item for item in tasks.json() if item['id'] == task_id]
    assert matched
    assert matched[0]['status'] == 'stalled'


def test_agent_register_reuses_existing_identity_by_default(client):
    first = client.post(
        '/v1/agents/register',
        headers=_headers(),
        json={'name': 'shared-agent', 'type': 'cli', 'capabilities': {'source': 'first'}},
    )
    assert first.status_code == 200
    first_id = first.json()['id']

    second = client.post(
        '/v1/agents/register',
        headers=_headers(),
        json={'name': 'shared-agent', 'type': 'cli', 'capabilities': {'source': 'second'}},
    )
    assert second.status_code == 200
    assert second.json()['id'] == first_id


def test_agent_register_can_force_new_identity(client):
    first = client.post(
        '/v1/agents/register',
        headers=_headers(),
        json={'name': 'forked-agent', 'type': 'cli', 'capabilities': {}},
    )
    assert first.status_code == 200

    second = client.post(
        '/v1/agents/register',
        headers=_headers(),
        json={'name': 'forked-agent', 'type': 'cli', 'capabilities': {}, 'reuse_existing': False},
    )
    assert second.status_code == 200
    assert second.json()['id'] != first.json()['id']


def test_events_list_supports_recipient_broadcast_and_since_filters(client):
    sender = client.post(
        '/v1/agents/register',
        headers=_headers(),
        json={'name': 'sender-agent', 'type': 'cli', 'capabilities': {}},
    )
    recipient = client.post(
        '/v1/agents/register',
        headers=_headers(),
        json={'name': 'recipient-agent', 'type': 'cli', 'capabilities': {}},
    )
    other = client.post(
        '/v1/agents/register',
        headers=_headers(),
        json={'name': 'other-agent', 'type': 'cli', 'capabilities': {}},
    )
    assert sender.status_code == 200
    assert recipient.status_code == 200
    assert other.status_code == 200
    sender_id = sender.json()['id']
    recipient_id = recipient.json()['id']
    other_id = other.json()['id']

    direct = client.post(
        '/v1/events',
        headers=_headers(),
        json={
            'type': 'chat.message',
            'payload': {'content': 'direct'},
            'agent_id': sender_id,
            'recipient_id': recipient_id,
            'channel': 'work',
        },
    )
    assert direct.status_code == 200
    direct_created_at = direct.json()['created_at']

    broadcast = client.post(
        '/v1/events',
        headers=_headers(),
        json={
            'type': 'chat.message',
            'payload': {'content': 'broadcast'},
            'agent_id': sender_id,
            'channel': 'work',
        },
    )
    assert broadcast.status_code == 200

    other_target = client.post(
        '/v1/events',
        headers=_headers(),
        json={
            'type': 'chat.message',
            'payload': {'content': 'other'},
            'agent_id': sender_id,
            'recipient_id': other_id,
            'channel': 'work',
        },
    )
    assert other_target.status_code == 200

    inbox = client.get(
        '/v1/events',
        headers=_headers(),
        params={
            'recipient_id': recipient_id,
            'include_broadcast': True,
            'channel': 'work',
            'type': 'chat.message',
            'direction': 'asc',
            'limit': 20,
        },
    )
    assert inbox.status_code == 200
    items = inbox.json()
    assert len(items) == 2
    assert {item['payload']['content'] for item in items} == {'direct', 'broadcast'}

    since_poll = client.get(
        '/v1/events',
        headers=_headers(),
        params={
            'recipient_id': recipient_id,
            'include_broadcast': True,
            'channel': 'work',
            'type': 'chat.message',
            'since': direct_created_at,
            'direction': 'asc',
            'limit': 20,
        },
    )
    assert since_poll.status_code == 200
    incremental = since_poll.json()
    assert len(incremental) == 1
    assert incremental[0]['payload']['content'] == 'broadcast'


def test_mcp_event_inbox_returns_incremental_compact_results(client):
    sender = client.post(
        '/v1/agents/register',
        headers=_headers(),
        json={'name': 'mcp-sender', 'type': 'cli', 'capabilities': {}},
    )
    recipient = client.post(
        '/v1/agents/register',
        headers=_headers(),
        json={'name': 'mcp-recipient', 'type': 'cli', 'capabilities': {}},
    )
    assert sender.status_code == 200
    assert recipient.status_code == 200
    sender_id = sender.json()['id']
    recipient_id = recipient.json()['id']

    first = client.post(
        '/mcp/http',
        headers=_headers(),
        json={
            'jsonrpc': '2.0',
            'id': 'evt1',
            'method': 'tool.call',
            'params': {
                'name': 'event.log',
                'arguments': {
                    'type': 'chat.message',
                    'agent_id': sender_id,
                    'recipient_id': recipient_id,
                    'channel': 'ops',
                    'payload': {'content': 'hello'},
                },
            },
        },
    )
    assert first.status_code == 200

    inbox = client.post(
        '/mcp/http',
        headers=_headers(),
        json={
            'jsonrpc': '2.0',
            'id': 'evt2',
            'method': 'tool.call',
            'params': {
                'name': 'event.inbox',
                'arguments': {'recipient_id': recipient_id, 'channel': 'ops', 'limit': 10},
            },
        },
    )
    assert inbox.status_code == 200
    result = inbox.json()['result']
    assert result['count'] == 1
    assert result['items'][0]['channel'] == 'ops'
    assert result['items'][0]['recipient_id'] == recipient_id
    assert 'payload' not in result['items'][0]
    assert result['latest_seen_at']

    second = client.post(
        '/mcp/http',
        headers=_headers(),
        json={
            'jsonrpc': '2.0',
            'id': 'evt3',
            'method': 'tool.call',
            'params': {
                'name': 'event.log',
                'arguments': {
                    'type': 'chat.message',
                    'agent_id': sender_id,
                    'recipient_id': recipient_id,
                    'channel': 'ops',
                    'payload': {'content': 'follow-up'},
                },
            },
        },
    )
    assert second.status_code == 200

    incremental = client.post(
        '/mcp/http',
        headers=_headers(),
        json={
            'jsonrpc': '2.0',
            'id': 'evt4',
            'method': 'tool.call',
            'params': {
                'name': 'event.inbox',
                'arguments': {
                    'recipient_id': recipient_id,
                    'channel': 'ops',
                    'since': result['latest_seen_at'],
                    'direction': 'asc',
                    'limit': 10,
                },
            },
        },
    )
    assert incremental.status_code == 200
    incr_result = incremental.json()['result']
    assert incr_result['count'] == 1
    assert incr_result['items'][0]['type'] == 'chat.message'


def test_events_threading_via_rest(client):
    sender = client.post(
        '/v1/agents/register',
        headers=_headers(),
        json={'name': 'thread-sender', 'type': 'cli', 'capabilities': {}},
    )
    assert sender.status_code == 200
    sender_id = sender.json()['id']

    root = client.post(
        '/v1/events',
        headers=_headers(),
        json={
            'type': 'chat.message',
            'agent_id': sender_id,
            'channel': 'work',
            'payload': {'content': 'root'},
        },
    )
    assert root.status_code == 200
    root_id = root.json()['id']

    reply = client.post(
        '/v1/events',
        headers=_headers(),
        json={
            'type': 'chat.message',
            'agent_id': sender_id,
            'channel': 'work',
            'parent_message_id': root_id,
            'payload': {'content': 'reply'},
        },
    )
    assert reply.status_code == 200
    reply_id = reply.json()['id']

    nested = client.post(
        '/v1/events',
        headers=_headers(),
        json={
            'type': 'chat.message',
            'agent_id': sender_id,
            'channel': 'work',
            'parent_message_id': reply_id,
            'payload': {'content': 'nested'},
        },
    )
    assert nested.status_code == 200

    direct_children = client.get(
        '/v1/events',
        headers=_headers(),
        params={'parent_message_id': root_id, 'direction': 'asc', 'limit': 10},
    )
    assert direct_children.status_code == 200
    children_items = direct_children.json()
    assert len(children_items) == 1
    assert children_items[0]['payload']['content'] == 'reply'

    thread = client.get(
        f'/v1/events/thread/{root_id}',
        headers=_headers(),
        params={'limit': 20},
    )
    assert thread.status_code == 200
    thread_items = thread.json()
    assert [item['payload']['content'] for item in thread_items] == ['root', 'reply', 'nested']


def test_mcp_event_thread_returns_root_and_replies(client):
    sender = client.post(
        '/v1/agents/register',
        headers=_headers(),
        json={'name': 'thread-mcp-sender', 'type': 'cli', 'capabilities': {}},
    )
    assert sender.status_code == 200
    sender_id = sender.json()['id']

    root = client.post(
        '/mcp/http',
        headers=_headers(),
        json={
            'jsonrpc': '2.0',
            'id': 'thr1',
            'method': 'tool.call',
            'params': {
                'name': 'event.log',
                'arguments': {'type': 'chat.message', 'agent_id': sender_id, 'payload': {'content': 'mcp-root'}},
            },
        },
    )
    assert root.status_code == 200
    root_id = root.json()['result']['id']

    reply = client.post(
        '/mcp/http',
        headers=_headers(),
        json={
            'jsonrpc': '2.0',
            'id': 'thr2',
            'method': 'tool.call',
            'params': {
                'name': 'event.log',
                'arguments': {
                    'type': 'chat.message',
                    'agent_id': sender_id,
                    'parent_message_id': root_id,
                    'payload': {'content': 'mcp-reply'},
                },
            },
        },
    )
    assert reply.status_code == 200

    thread = client.post(
        '/mcp/http',
        headers=_headers(),
        json={
            'jsonrpc': '2.0',
            'id': 'thr3',
            'method': 'tool.call',
            'params': {
                'name': 'event.thread',
                'arguments': {'message_id': root_id, 'include_payload': True, 'limit': 10},
            },
        },
    )
    assert thread.status_code == 200
    items = thread.json()['result']['items']
    assert [item['payload']['content'] for item in items] == ['mcp-root', 'mcp-reply']
