# MCP Tool Spec (MVP)

HTTP transport endpoint: `POST /mcp/http`
Stdio transport entrypoint: `python -m app.mcp.stdio`

Request schema (both transports):

```json
{
  "jsonrpc": "2.0",
  "id": "1",
  "method": "tool.call",
  "params": {
    "name": "task.create",
    "arguments": {}
  }
}
```

## Tools
- `agent.register`
- `agent.heartbeat`
- `agent.list`
- `task.create`
- `task.list`
- `task.claim`
- `task.update`
- `lock.acquire`
- `lock.renew`
- `lock.release`
- `event.log`
- `event.list`
- `context.bundle`

## Notes
- Both transports call the same internal service layer.
- Error responses return deterministic `code` values.
- `context.bundle` returns the compact context bundle contract.
