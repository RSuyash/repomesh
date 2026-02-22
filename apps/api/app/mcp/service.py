from __future__ import annotations

from sqlalchemy.orm import Session

from app.services.agents import AgentService
from app.services.context import ContextService
from app.services.events import EventService
from app.services.locks import LockService
from app.services.tasks import TaskService

TOOL_DEFINITIONS = [
    {
        'name': 'agent.register',
        'description': 'Register an agent instance in RepoMesh.',
        'inputSchema': {
            'type': 'object',
            'required': ['name', 'type'],
            'properties': {
                'name': {'type': 'string'},
                'type': {'type': 'string'},
                'capabilities': {'type': 'object'},
                'repo_id': {'type': ['string', 'null']},
            },
        },
    },
    {
        'name': 'agent.heartbeat',
        'description': 'Update agent heartbeat and status.',
        'inputSchema': {
            'type': 'object',
            'required': ['agent_id', 'status'],
            'properties': {
                'agent_id': {'type': 'string'},
                'status': {'type': 'string'},
                'current_task': {'type': ['string', 'null']},
            },
        },
    },
    {'name': 'agent.list', 'description': 'List agents.', 'inputSchema': {'type': 'object', 'properties': {'repo_id': {'type': ['string', 'null']}}}},
    {
        'name': 'task.create',
        'description': 'Create a task.',
        'inputSchema': {
            'type': 'object',
            'required': ['goal'],
            'properties': {
                'goal': {'type': 'string'},
                'description': {'type': 'string'},
                'scope': {'type': 'object'},
                'priority': {'type': 'integer'},
                'acceptance_criteria': {'type': ['string', 'null']},
                'repo_id': {'type': ['string', 'null']},
            },
        },
    },
    {'name': 'task.list', 'description': 'List tasks.', 'inputSchema': {'type': 'object', 'properties': {'status': {'type': 'string'}, 'scope': {'type': 'string'}, 'assignee': {'type': 'string'}}}},
    {
        'name': 'task.claim',
        'description': 'Claim a task with lease.',
        'inputSchema': {
            'type': 'object',
            'required': ['task_id', 'agent_id', 'resource_key'],
            'properties': {
                'task_id': {'type': 'string'},
                'agent_id': {'type': 'string'},
                'resource_key': {'type': 'string'},
                'lease_ttl': {'type': 'integer'},
            },
        },
    },
    {
        'name': 'task.update',
        'description': 'Update task fields.',
        'inputSchema': {
            'type': 'object',
            'required': ['task_id'],
            'properties': {
                'task_id': {'type': 'string'},
                'status': {'type': 'string'},
                'progress': {'type': 'integer'},
                'summary': {'type': 'string'},
                'blocked_reason': {'type': 'string'},
            },
        },
    },
    {
        'name': 'lock.acquire',
        'description': 'Acquire a resource lock.',
        'inputSchema': {
            'type': 'object',
            'required': ['resource_key', 'agent_id'],
            'properties': {
                'resource_key': {'type': 'string'},
                'agent_id': {'type': 'string'},
                'ttl': {'type': 'integer'},
            },
        },
    },
    {'name': 'lock.renew', 'description': 'Renew a lock.', 'inputSchema': {'type': 'object', 'required': ['lock_id', 'agent_id'], 'properties': {'lock_id': {'type': 'string'}, 'agent_id': {'type': 'string'}, 'ttl': {'type': 'integer'}}}},
    {'name': 'lock.release', 'description': 'Release a lock.', 'inputSchema': {'type': 'object', 'required': ['lock_id', 'agent_id'], 'properties': {'lock_id': {'type': 'string'}, 'agent_id': {'type': 'string'}}}},
    {'name': 'event.log', 'description': 'Log an event.', 'inputSchema': {'type': 'object', 'required': ['type'], 'properties': {'type': {'type': 'string'}, 'payload': {'type': 'object'}, 'severity': {'type': 'string'}, 'task_id': {'type': ['string', 'null']}, 'agent_id': {'type': ['string', 'null']}, 'repo_id': {'type': ['string', 'null']}}}},
    {'name': 'event.list', 'description': 'List events.', 'inputSchema': {'type': 'object', 'properties': {'task_id': {'type': ['string', 'null']}, 'agent_id': {'type': ['string', 'null']}, 'type': {'type': ['string', 'null']}, 'limit': {'type': 'integer'}}}},
    {'name': 'context.bundle', 'description': 'Build a compact context bundle for a task.', 'inputSchema': {'type': 'object', 'required': ['task_id'], 'properties': {'task_id': {'type': 'string'}, 'mode': {'type': 'string'}, 'include_recent': {'type': 'boolean'}}}},
]


class MCPToolService:
    def __init__(self, db: Session):
        self.db = db
        self.agents = AgentService(db)
        self.tasks = TaskService(db)
        self.locks = LockService(db)
        self.events = EventService(db)
        self.context = ContextService(db)

    def call(self, tool_name: str, arguments: dict) -> dict:
        if tool_name == 'agent.register':
            agent = self.agents.register(
                name=arguments['name'],
                agent_type=arguments['type'],
                capabilities=arguments.get('capabilities', {}),
                repo_id=arguments.get('repo_id'),
            )
            return {'id': agent.id, 'name': agent.name, 'type': agent.type, 'status': agent.status}

        if tool_name == 'agent.heartbeat':
            agent = self.agents.heartbeat(
                agent_id=arguments['agent_id'],
                status=arguments['status'],
                current_task=arguments.get('current_task'),
            )
            return {'id': agent.id, 'status': agent.status, 'last_heartbeat_at': agent.last_heartbeat_at}

        if tool_name == 'agent.list':
            agents = self.agents.list(repo_id=arguments.get('repo_id'))
            return {'items': [{'id': a.id, 'name': a.name, 'type': a.type, 'status': a.status} for a in agents]}

        if tool_name == 'task.create':
            task = self.tasks.create(
                goal=arguments['goal'],
                description=arguments.get('description', ''),
                scope=arguments.get('scope', {}),
                priority=arguments.get('priority', 3),
                acceptance_criteria=arguments.get('acceptance_criteria'),
                repo_id=arguments.get('repo_id'),
            )
            return {'id': task.id, 'status': task.status}

        if tool_name == 'task.list':
            tasks = self.tasks.list(
                status=arguments.get('status'),
                scope=arguments.get('scope'),
                assignee=arguments.get('assignee'),
            )
            return {'items': [{'id': t.id, 'goal': t.goal, 'status': t.status, 'assignee_agent_id': t.assignee_agent_id} for t in tasks]}

        if tool_name == 'task.claim':
            claim = self.tasks.claim(
                task_id=arguments['task_id'],
                agent_id=arguments['agent_id'],
                resource_key=arguments['resource_key'],
                lease_ttl=arguments.get('lease_ttl', 1800),
            )
            return {'id': claim.id, 'task_id': claim.task_id, 'agent_id': claim.agent_id, 'state': claim.state}

        if tool_name == 'task.update':
            task = self.tasks.update(
                task_id=arguments['task_id'],
                status=arguments.get('status'),
                progress=arguments.get('progress'),
                summary=arguments.get('summary'),
                blocked_reason=arguments.get('blocked_reason'),
            )
            return {'id': task.id, 'status': task.status, 'progress': task.progress}

        if tool_name == 'lock.acquire':
            lock = self.locks.acquire(
                resource_key=arguments['resource_key'],
                agent_id=arguments['agent_id'],
                ttl=arguments.get('ttl', 1800),
            )
            return {'id': lock.id, 'resource_key': lock.resource_key, 'state': lock.state, 'expires_at': lock.expires_at}

        if tool_name == 'lock.renew':
            lock = self.locks.renew(
                lock_id=arguments['lock_id'],
                agent_id=arguments['agent_id'],
                ttl=arguments.get('ttl', 1800),
            )
            return {'id': lock.id, 'state': lock.state, 'expires_at': lock.expires_at}

        if tool_name == 'lock.release':
            lock = self.locks.release(lock_id=arguments['lock_id'], agent_id=arguments['agent_id'])
            return {'id': lock.id, 'state': lock.state, 'released_at': lock.released_at}

        if tool_name == 'event.log':
            event = self.events.log(
                event_type=arguments['type'],
                payload=arguments.get('payload', {}),
                severity=arguments.get('severity', 'info'),
                task_id=arguments.get('task_id'),
                agent_id=arguments.get('agent_id'),
                repo_id=arguments.get('repo_id'),
            )
            return {'id': event.id, 'type': event.type, 'severity': event.severity}

        if tool_name == 'event.list':
            events = self.events.list(
                task_id=arguments.get('task_id'),
                agent_id=arguments.get('agent_id'),
                event_type=arguments.get('type'),
                limit=arguments.get('limit', 100),
            )
            return {
                'items': [
                    {'id': e.id, 'type': e.type, 'severity': e.severity, 'task_id': e.task_id, 'created_at': e.created_at}
                    for e in events
                ]
            }

        if tool_name == 'context.bundle':
            bundle = self.context.bundle(
                task_id=arguments['task_id'],
                mode=arguments.get('mode', 'compact'),
                include_recent=arguments.get('include_recent', True),
            )
            return bundle

        raise ValueError(f'Unknown tool: {tool_name}')

    @staticmethod
    def definitions() -> list[dict]:
        return TOOL_DEFINITIONS
