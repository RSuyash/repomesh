import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import yaml from 'js-yaml';

export interface RepoMeshConfig {
  api_url: string;
  mcp_http_url: string;
  mcp_stdio_command: string;
  repo_id: string;
}

export interface RepoMeshPaths {
  repoRoot: string;
  repomeshDir: string;
  configPath: string;
  tokenPath: string;
  composePath: string;
  envExamplePath: string;
  envPath: string;
}

function defaultConfig(paths: RepoMeshPaths): RepoMeshConfig {
  return {
    api_url: 'http://127.0.0.1:8787',
    mcp_http_url: 'http://127.0.0.1:8787/mcp/http',
    mcp_stdio_command: 'python -m app.mcp.stdio',
    repo_id: path.basename(paths.repoRoot)
  };
}

export function resolvePaths(cwd = process.cwd()): RepoMeshPaths {
  const repoRoot = cwd;
  const repomeshDir = path.join(repoRoot, '.repomesh');
  return {
    repoRoot,
    repomeshDir,
    configPath: path.join(repomeshDir, 'config.yml'),
    tokenPath: path.join(repomeshDir, 'token'),
    composePath: path.join(repoRoot, 'infra', 'docker', 'docker-compose.yml'),
    envExamplePath: path.join(repoRoot, 'infra', 'docker', '.env.example'),
    envPath: path.join(repoRoot, 'infra', 'docker', '.env')
  };
}

export function ensureInitialized(cwd = process.cwd()): RepoMeshPaths {
  const paths = resolvePaths(cwd);
  if (!fs.existsSync(paths.configPath) || !fs.existsSync(paths.tokenPath)) {
    throw new Error('RepoMesh is not initialized. Run `repomesh init` first.');
  }
  return paths;
}

export function initRepoMesh(cwd = process.cwd()): { paths: RepoMeshPaths; token: string; config: RepoMeshConfig } {
  const paths = resolvePaths(cwd);
  fs.mkdirSync(paths.repomeshDir, { recursive: true });

  if (!fs.existsSync(paths.envPath) && fs.existsSync(paths.envExamplePath)) {
    fs.copyFileSync(paths.envExamplePath, paths.envPath);
  }

  if (fs.existsSync(paths.configPath) && fs.existsSync(paths.tokenPath)) {
    const configRaw = fs.readFileSync(paths.configPath, 'utf8');
    const config = yaml.load(configRaw) as RepoMeshConfig;
    const token = fs.readFileSync(paths.tokenPath, 'utf8').trim();
    return { paths, token, config };
  }

  const token = `rm_${crypto.randomUUID().replace(/-/g, '')}`;
  const config = defaultConfig(paths);

  fs.writeFileSync(paths.configPath, yaml.dump(config), 'utf8');
  fs.writeFileSync(paths.tokenPath, token, 'utf8');

  return { paths, token, config };
}

export function readConfig(cwd = process.cwd()): { paths: RepoMeshPaths; token: string; config: RepoMeshConfig } {
  const paths = ensureInitialized(cwd);
  const configRaw = fs.readFileSync(paths.configPath, 'utf8');
  const config = yaml.load(configRaw) as RepoMeshConfig;
  const token = fs.readFileSync(paths.tokenPath, 'utf8').trim();
  return { paths, token, config };
}
