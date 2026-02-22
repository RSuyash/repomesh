# RepoMesh MCP

RepoMesh MCP is a repo-scoped coordination and memory layer for multi-agent software development.

## MVP Scope (Phase 1-2)
- Monorepo with pnpm and turbo
- FastAPI backend with REST + MCP endpoints
- Dual MCP transport (HTTP + stdio)
- Task claims, lock leases, events, context bundle
- Node CLI for local operations

## Quick Start
1. Install prerequisites: Node.js, pnpm, Python 3.12, Docker Desktop.
2. Run `pnpm install` at repo root.
3. Run `repomesh init` from `apps/cli` build output once built.

## Repository Layout
- `apps/cli`: CLI package.
- `apps/api`: API service and MCP server.
- `packages/shared-contracts`: shared schemas/types.
- `infra/docker`: compose stack.
- `docs`: API, MCP, and ops docs.
