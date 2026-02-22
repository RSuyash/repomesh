# Test Strategy (MVP)

## Test Layers
- Unit tests: service logic (lock conflicts, status transitions).
- Integration tests: REST + DB + MCP HTTP and stdio behaviors.
- CLI smoke tests: initialization and config generation.

## Commands
- `pnpm build`
- `pnpm typecheck`
- `pnpm test`

## Qwen CLI MCP Smoke
- Run from repo root: `D:\Projects\RepoMesh MCP`
- Run `pnpm oneclick` to generate `.repomesh/mcp-servers.json`
- Add server: `qwen mcp add repomesh-stdio python scripts/repomesh_mcp_stdio.py`
- Verify: `qwen mcp list`
- One-shot prompt check:
  - `qwen -p "Call task.list from repomesh-stdio and return only json." --allowed-mcp-server-names repomesh-stdio --output-format json`

## Current Coverage Focus
- Lock lease anti-overlap behavior.
- Task claim and stale recovery transitions.
- Event logging and context bundle retrieval.
- MCP parity for HTTP and stdio transports.

## Deferred for Next Phase
- Performance/load tests.
- Security and fuzz testing.
- Full dockerized end-to-end agent simulation.
