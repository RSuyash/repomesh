# Local Development Guide

## Prerequisites
- Node.js 22+
- pnpm 10+
- Python 3.12+
- Docker Desktop (daemon running)

## Setup
1. Copy `infra/docker/.env.example` to `infra/docker/.env`.
2. Run `pnpm install`.
3. Build packages with `pnpm build`.
4. Start services: `docker compose --env-file infra/docker/.env -f infra/docker/docker-compose.yml up -d`.

## Troubleshooting
- If Docker checks fail on Windows, start Docker Desktop and confirm `docker info` works.
- Use `repomesh doctor` to verify daemon, compose file, and API health.
