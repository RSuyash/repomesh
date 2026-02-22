# Local Development Guide

## Prerequisites
- Node.js 22+
- pnpm 10+
- Python 3.12+
- Docker Desktop (daemon running)

## Bootstrap
### One-click setup (recommended)
1. `pnpm oneclick`

Windows double-click option:
- `oneclick.bat`

What one-click does:
- installs dependencies
- builds all packages
- initializes RepoMesh config
- syncs API token into Docker `.env`
- starts services and runs health checks

### Manual setup
1. `pnpm install`
2. `pnpm build`
3. `pnpm test`

## RepoMesh CLI Flow
1. `pnpm --filter @repomesh/cli build`
2. `node apps/cli/dist/index.js init`
3. `node apps/cli/dist/index.js up`
4. `node apps/cli/dist/index.js doctor`
5. `node apps/cli/dist/index.js status`

## Docker Compose
- Stack file: `infra/docker/docker-compose.yml`
- Env file: `infra/docker/.env`
- If `.env` does not exist, `repomesh init` copies from `.env.example`.

## Troubleshooting
- If Docker checks fail on Windows, start Docker Desktop and confirm `docker info` works.
- API auth failures usually mean token mismatch. Use `repomesh mcp` to inspect token.
- Run `POST /v1/recovery/reconcile` when validating stale lease recovery.
