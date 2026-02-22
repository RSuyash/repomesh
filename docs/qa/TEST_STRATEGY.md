# Test Strategy (MVP)

## Test Layers
- Unit tests: service logic (lock conflicts, status transitions).
- Integration tests: REST + DB + MCP HTTP and stdio behaviors.
- CLI smoke tests: initialization and config generation.

## Commands
- `pnpm build`
- `pnpm typecheck`
- `pnpm test`

## Current Coverage Focus
- Lock lease anti-overlap behavior.
- Task claim and stale recovery transitions.
- Event logging and context bundle retrieval.
- MCP parity for HTTP and stdio transports.

## Deferred for Next Phase
- Performance/load tests.
- Security and fuzz testing.
- Full dockerized end-to-end agent simulation.
