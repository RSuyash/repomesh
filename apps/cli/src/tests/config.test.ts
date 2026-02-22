import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';
import assert from 'node:assert/strict';

import { initRepoMesh, readConfig } from '../lib/config.js';

test('initRepoMesh creates config and token', () => {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'repomesh-cli-'));
  fs.mkdirSync(path.join(tmp, 'infra', 'docker'), { recursive: true });
  fs.writeFileSync(path.join(tmp, 'infra', 'docker', '.env.example'), 'API_PORT=8787\n', 'utf8');

  const result = initRepoMesh(tmp);
  assert.ok(fs.existsSync(result.paths.configPath));
  assert.ok(fs.existsSync(result.paths.tokenPath));

  const loaded = readConfig(tmp);
  assert.equal(loaded.config.api_url, 'http://127.0.0.1:8787');
  assert.ok(loaded.token.startsWith('rm_'));
});
