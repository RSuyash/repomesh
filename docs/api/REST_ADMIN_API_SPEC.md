# REST Admin API Spec (MVP)

Base URL: `http://127.0.0.1:8787`
Auth: `x-repomesh-token: <token>` or `Authorization: Bearer <token>`

## Health
- `GET /healthz`
- `GET /readyz`

## Agents
- `POST /v1/agents/register`
- `POST /v1/agents/{agent_id}/heartbeat`
- `GET /v1/agents`

`POST /v1/agents/register` optional fields:
- `reuse_existing` (default `true`): idempotent registration by `(repo_id, name)`
- `takeover_if_stale` (default `true`): reclaim stale/inactive identity

## Tasks
- `POST /v1/tasks`
- `GET /v1/tasks`
- `POST /v1/tasks/{task_id}/claim`
- `PATCH /v1/tasks/{task_id}`

## Locks
- `POST /v1/locks/acquire`
- `POST /v1/locks/{lock_id}/renew`
- `POST /v1/locks/{lock_id}/release`

## Events
- `POST /v1/events`
- `GET /v1/events`

## Context
- `GET /v1/context/bundle/{task_id}`

## Recovery
- `POST /v1/recovery/reconcile`

## Error Envelope

```json
{
  "error": {
    "code": "CONFLICT",
    "message": "Resource already locked",
    "details": {}
  }
}
```

## Deterministic Error Codes
- `NOT_FOUND`
- `CONFLICT`
- `UNAUTHORIZED`
- `VALIDATION_ERROR`
- `INVALID_METHOD`
- `UNKNOWN_TOOL`
