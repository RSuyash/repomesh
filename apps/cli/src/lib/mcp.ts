import fs from 'node:fs';
import path from 'node:path';

import { RepoMeshConfig, RepoMeshPaths } from './config.js';

export interface McpServerEntry {
  transport: 'http' | 'stdio';
  url?: string;
  headers?: Record<string, string>;
  command?: string;
  args?: string[];
}

export interface McpServersConfig {
  mcpServers: Record<string, McpServerEntry>;
}

export function buildMcpServersConfig(
  config: RepoMeshConfig,
  token: string,
  repoRoot: string
): McpServersConfig {
  const launcherPath = path.join(repoRoot, 'scripts', 'repomesh_mcp_stdio.py');
  return {
    mcpServers: {
      repomesh_http: {
        transport: 'http',
        url: config.mcp_http_url,
        headers: {
          'x-repomesh-token': token
        }
      },
      repomesh_stdio: {
        transport: 'stdio',
        command: 'python',
        args: [launcherPath]
      }
    }
  };
}

export function writeMcpConfig(paths: RepoMeshPaths, config: McpServersConfig): string {
  const outPath = path.join(paths.repomeshDir, 'mcp-servers.json');
  fs.mkdirSync(paths.repomeshDir, { recursive: true });
  fs.writeFileSync(outPath, JSON.stringify(config, null, 2), 'utf8');
  return outPath;
}

export function mcpClientHints(repoRoot: string): Record<string, string> {
  const launcher = path.join(repoRoot, 'scripts', 'repomesh_mcp_stdio.py');
  return {
    qwen_remove_hivemind: 'qwen mcp remove hivemind',
    qwen_add: `qwen mcp add repomesh-stdio python "${launcher}"`,
    qwen_test:
      'qwen -p "Call task.list from repomesh-stdio and return only JSON." --allowed-mcp-server-names repomesh-stdio --output-format json',
    codex_note:
      'Use .repomesh/mcp-servers.json directly in Codex MCP config and remove any unrelated servers such as hivemind.',
    json_note:
      'Use .repomesh/mcp-servers.json in any client that accepts MCP mcpServers JSON directly (Codex/Gemini-compatible clients).'
  };
}
