import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';
import assert from 'node:assert/strict';

import { buildMcpServersConfig, writeMcpConfig } from '../lib/mcp.js';

test('buildMcpServersConfig returns stdio and http entries', () => {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'repomesh-mcp-'));
  const config = buildMcpServersConfig(
    {
      api_url: 'http://127.0.0.1:8787',
      mcp_http_url: 'http://127.0.0.1:8787/mcp/http',
      mcp_stdio_command: 'python -m app.mcp.stdio',
      repo_id: 'demo'
    },
    'rm_token',
    tmp
  );

  assert.equal(config.mcpServers.repomesh_http.transport, 'http');
  assert.equal(config.mcpServers.repomesh_stdio.transport, 'stdio');
  assert.equal(config.mcpServers.repomesh_http.headers?.['x-repomesh-token'], 'rm_token');
  assert.ok(config.mcpServers.repomesh_stdio.args?.[0].endsWith(path.join('scripts', 'repomesh_mcp_stdio.py')));
});

test('writeMcpConfig writes mcp-servers.json', () => {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'repomesh-mcp-write-'));
  const paths = {
    repoRoot: tmp,
    repomeshDir: path.join(tmp, '.repomesh'),
    configPath: path.join(tmp, '.repomesh', 'config.yml'),
    tokenPath: path.join(tmp, '.repomesh', 'token'),
    composePath: path.join(tmp, 'infra', 'docker', 'docker-compose.yml'),
    envExamplePath: path.join(tmp, 'infra', 'docker', '.env.example'),
    envPath: path.join(tmp, 'infra', 'docker', '.env')
  };
  const file = writeMcpConfig(paths, {
    mcpServers: {
      repomesh_http: {
        transport: 'http',
        url: 'http://127.0.0.1:8787/mcp/http'
      }
    }
  });

  assert.ok(fs.existsSync(file));
  const raw = fs.readFileSync(file, 'utf8');
  const parsed = JSON.parse(raw) as { mcpServers: Record<string, { transport: string }> };
  assert.equal(parsed.mcpServers.repomesh_http.transport, 'http');
});
