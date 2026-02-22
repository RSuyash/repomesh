# RepoMesh MCP

RepoMesh MCP is a repo-scoped coordination and memory layer for multi-agent software development.

## MVP Scope (Phase 1-2)
- Monorepo with pnpm and turbo
- FastAPI backend with REST + MCP endpoints
- Dual MCP transport (HTTP + stdio)
- Task claims, lock leases, events, context bundle
- Node CLI for local operations

## Quick Start (One Click)
1. Install prerequisites: Node.js, pnpm, Python 3.12, Docker Desktop.
2. Run one command from repo root:
   - `pnpm oneclick`

Windows double-click option:
- Run `oneclick.bat`

What this does automatically:
- installs dependencies
- builds all packages
- initializes RepoMesh config
- starts Docker services
- runs health checks
- prints MCP connection details

## Repository Layout
- `apps/cli`: CLI package.
- `apps/api`: API service and MCP server.
- `packages/shared-contracts`: shared schemas/types.
- `infra/docker`: compose stack.
- `docs`: API, MCP, and ops docs.

## MVP CLI Commands
- `repomesh init`
- `repomesh up`
- `repomesh down`
- `repomesh doctor`
- `repomesh status`
- `repomesh mcp`
- `repomesh task create`
- `repomesh task list`
- `repomesh task claim <task-id>`
- `repomesh logs`
- `repomesh context <task-id>`
