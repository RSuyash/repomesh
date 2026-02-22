import fs from 'node:fs';
import { spawnSync } from 'node:child_process';
import { RepoMeshPaths } from './config.js';

export function runDockerCompose(paths: RepoMeshPaths, args: string[]): number {
  if (!fs.existsSync(paths.composePath)) {
    throw new Error(`Compose file not found: ${paths.composePath}`);
  }

  if (!fs.existsSync(paths.envPath) && fs.existsSync(paths.envExamplePath)) {
    fs.copyFileSync(paths.envExamplePath, paths.envPath);
  }

  const result = spawnSync(
    'docker',
    ['compose', '--env-file', paths.envPath, '-f', paths.composePath, ...args],
    { stdio: 'inherit' }
  );

  return result.status ?? 1;
}

export function dockerAvailable(): boolean {
  const result = spawnSync('docker', ['info'], { stdio: 'ignore' });
  return result.status === 0;
}
