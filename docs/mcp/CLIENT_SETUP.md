# MCP Client Setup

RepoMesh now generates a single MCP config file at:
- `.repomesh/mcp-servers.json`

Generate it with:
- `pnpm oneclick`

## Generated JSON format

```json
{
  "mcpServers": {
    "repomesh_http": {
      "transport": "http",
      "url": "http://127.0.0.1:8787/mcp/http",
      "headers": {
        "x-repomesh-token": "<token>"
      }
    },
    "repomesh_stdio": {
      "transport": "stdio",
      "command": "python",
      "args": [
        "D:/Projects/RepoMesh MCP/scripts/repomesh_mcp_stdio.py"
      ]
    }
  }
}
```

## Qwen CLI

Qwen currently uses `qwen mcp add/remove/list`, not direct JSON import.
Use the generated stdio launcher:

```powershell
qwen mcp remove repomesh-stdio
qwen mcp add repomesh-stdio python scripts/repomesh_mcp_stdio.py
qwen mcp list
```

Then test:

```powershell
qwen -p "Call task.list from repomesh-stdio and return only JSON." --allowed-mcp-server-names repomesh-stdio --output-format json
```

## Other MCP clients

For clients that accept `mcpServers` JSON directly, copy from `.repomesh/mcp-servers.json`.
Use:
- `repomesh_http` for HTTP MCP transport
- `repomesh_stdio` for stdio MCP transport
