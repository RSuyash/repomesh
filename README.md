# RepoMesh MCP

RepoMesh MCP is a repo-scoped coordination layer for multi-agent software development.

It gives you:
- MCP server (HTTP + stdio)
- Orchestrator + adapter runtime
- Task/lock/event primitives
- AST code tools + strict search/replace edits
- Summarizer compression jobs

## Prerequisites
- Node.js 20+
- pnpm
- Python 3.12+
- Docker Desktop (or Docker Engine + Compose)

## 1) Install And Run (Fastest)
From a fresh machine:

```bash
git clone <YOUR_REPO_URL>
cd <REPO_FOLDER>
pnpm oneclick
```

Windows shortcut:

```bat
oneclick.bat
```

What `pnpm oneclick` does:
1. Installs/builds workspace.
2. Initializes `.repomesh` config + token.
3. Syncs token into `infra/docker/.env`.
4. Starts Docker stack.
5. Runs health checks.
6. Runs founder smoke test (MCP tool registry + claim/execute + AST + summarizer).
7. Prints MCP connection info.

## 2) Run RepoMesh From Its Own Folder But Target Another Repo
Use this when RepoMesh is installed once, but should operate on a different project.

Windows PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/oneclick.ps1 -TargetRepoPath "D:\Projects\YourRepo"
```

Windows batch:

```bat
oneclick.bat -TargetRepoPath "D:\Projects\YourRepo"
```

This sets:
- `TARGET_REPO_HOST_PATH` in `infra/docker/.env`
- `ADAPTER_WORKSPACE_ROOT=/workspace/target-repo`

So API/adapter tools execute against the mounted target repo.

## 3) Daily Commands
```bash
node apps/cli/dist/index.js status
node apps/cli/dist/index.js doctor
node apps/cli/dist/index.js mcp
node apps/cli/dist/index.js up
node apps/cli/dist/index.js down
```

Task workflow examples:

```bash
node apps/cli/dist/index.js task create --goal "Ship onboarding flow" --description "MVP"
node apps/cli/dist/index.js task list --status pending
node apps/cli/dist/index.js logs
```

## 4) MCP Tooling (Current)
Core:
- `agent.register`, `agent.heartbeat`, `agent.list`
- `task.create`, `task.list`, `task.claim`, `task.update`
- `lock.acquire`, `lock.renew`, `lock.release`
- `event.log`, `event.list`, `event.inbox`, `event.thread`
- `context.bundle`

Runtime:
- `orchestrator.tick`, `orchestrator.status`
- `adapter.execute`, `adapter.tick`, `adapter.status`
- `summarizer.tick`, `summarizer.status`

Code tools:
- `file.skeleton`
- `file.symbol_logic`
- `file.search_replace`

## 5) MCP Config Snippets (Copy-Paste)
First generate your canonical file:

```bash
node apps/cli/dist/index.js mcp --write --client json
```

This writes:
- `.repomesh/mcp-servers.json`

### Generic `mcpServers` JSON (Codex/Gemini-compatible)
```json
{
  "mcpServers": {
    "repomesh_http": {
      "transport": "http",
      "url": "http://127.0.0.1:8787/mcp/http",
      "headers": {
        "x-repomesh-token": "<YOUR_TOKEN_FROM_.repomesh/token>"
      }
    },
    "repomesh_stdio": {
      "transport": "stdio",
      "command": "python",
      "args": ["<REPO_ROOT>/scripts/repomesh_mcp_stdio.py"]
    }
  }
}
```

### Codex (`C:\Users\<you>\.codex\config.toml`) example
```toml
[mcp_servers.repomesh_http]
command = "npx"
args = ["-y", "mcp-remote", "http://127.0.0.1:8787/mcp/http", "--header", "x-repomesh-token:<YOUR_TOKEN>"]
enabled = true
```

### Gemini / JSON clients
Point the client to `.repomesh/mcp-servers.json` directly if supported, or copy the JSON above into its MCP settings.

### Qwen CLI helper
```bash
node apps/cli/dist/index.js mcp --client qwen
```

## 6) Recommended Founder Workflow
1. Start stack (`pnpm oneclick` or `repomesh up`).
2. Connect MCP in your AI clients.
3. Create tasks through agent/chat.
4. Let orchestrator assign (`orchestrator.tick`) and adapters execute (`adapter.tick`).
5. Review summarized outcomes (`summarizer.tick` + `event.list`).

## 7) Repository Layout
- `apps/cli`: Node CLI.
- `apps/api`: FastAPI + MCP server.
- `infra/docker`: Compose stack.
- `packages/shared-contracts`: Shared schemas.
- `docs`: plans/specs/audits.
