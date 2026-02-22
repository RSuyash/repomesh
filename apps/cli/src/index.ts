#!/usr/bin/env node
import fs from 'node:fs';
import { spawnSync } from 'node:child_process';
import { Command } from 'commander';

import { apiRequest } from './lib/api.js';
import { dockerAvailable, runDockerCompose } from './lib/docker.js';
import { initRepoMesh, readConfig, resolvePaths } from './lib/config.js';
import { printJson } from './lib/output.js';

const program = new Command();

program.name('repomesh').description('RepoMesh CLI').version('0.1.0');

program
  .command('init')
  .description('Initialize RepoMesh config in current repository')
  .action(() => {
    const { paths, token, config } = initRepoMesh();
    printJson({
      message: 'RepoMesh initialized',
      config_path: paths.configPath,
      token_path: paths.tokenPath,
      api_url: config.api_url,
      mcp_http_url: config.mcp_http_url,
      token_preview: `${token.slice(0, 8)}...`
    });
  });

program
  .command('up')
  .description('Start RepoMesh core services')
  .action(() => {
    const paths = resolvePaths();
    const code = runDockerCompose(paths, ['up', '-d', '--build']);
    process.exitCode = code;
  });

program
  .command('down')
  .description('Stop RepoMesh core services')
  .action(() => {
    const paths = resolvePaths();
    const code = runDockerCompose(paths, ['down']);
    process.exitCode = code;
  });

program
  .command('doctor')
  .description('Run local diagnostics for RepoMesh')
  .action(async () => {
    const paths = resolvePaths();
    const checks = {
      docker_daemon: dockerAvailable(),
      compose_file: fs.existsSync(paths.composePath),
      initialized: fs.existsSync(paths.configPath) && fs.existsSync(paths.tokenPath),
      api_health: false
    };

    if (checks.initialized) {
      try {
        const { config } = readConfig();
        const res = await fetch(`${config.api_url}/healthz`);
        checks.api_health = res.ok;
      } catch {
        checks.api_health = false;
      }
    }

    printJson(checks);

    if (!checks.docker_daemon) {
      process.stderr.write('Docker daemon is not reachable. Start Docker Desktop and retry.\n');
      process.exitCode = 1;
    }
  });

program
  .command('status')
  .description('Show service and API status')
  .action(async () => {
    const paths = resolvePaths();
    if (fs.existsSync(paths.composePath)) {
      spawnSync('docker', ['compose', '--env-file', paths.envPath, '-f', paths.composePath, 'ps'], { stdio: 'inherit' });
    }

    try {
      const { config } = readConfig();
      const res = await fetch(`${config.api_url}/readyz`);
      printJson({ readyz: res.status, ok: res.ok });
    } catch (err) {
      printJson({ readyz: null, ok: false, error: (err as Error).message });
      process.exitCode = 1;
    }
  });

program
  .command('mcp')
  .description('Show MCP connection details')
  .action(() => {
    const { config, token } = readConfig();
    printJson({
      mcp_http_url: config.mcp_http_url,
      mcp_stdio_command: config.mcp_stdio_command,
      token
    });
  });

const task = program.command('task').description('Task operations');

task
  .command('create')
  .requiredOption('--goal <goal>', 'Task goal')
  .option('--description <description>', 'Task description', '')
  .option('--scope-file <file...>', 'Scope files')
  .option('--priority <priority>', 'Priority', '3')
  .action(async (options: { goal: string; description: string; scopeFile?: string[]; priority: string }) => {
    const created = await apiRequest('POST', '/v1/tasks', {
      goal: options.goal,
      description: options.description,
      scope: { files: options.scopeFile ?? [] },
      priority: Number(options.priority)
    });
    printJson(created);
  });

task
  .command('list')
  .option('--status <status>', 'Filter by status')
  .action(async (options: { status?: string }) => {
    const suffix = options.status ? `?status=${encodeURIComponent(options.status)}` : '';
    const tasks = await apiRequest('GET', `/v1/tasks${suffix}`);
    printJson(tasks);
  });

task
  .command('claim <taskId>')
  .requiredOption('--agent <agentId>', 'Agent ID')
  .requiredOption('--resource <resourceKey>', 'Resource key')
  .option('--ttl <ttl>', 'Lease TTL seconds', '1800')
  .action(async (taskId: string, options: { agent: string; resource: string; ttl: string }) => {
    const claim = await apiRequest('POST', `/v1/tasks/${taskId}/claim`, {
      agent_id: options.agent,
      resource_key: options.resource,
      lease_ttl: Number(options.ttl)
    });
    printJson(claim);
  });

program
  .command('logs')
  .description('Fetch recent events')
  .option('--task-id <taskId>', 'Filter events by task ID')
  .action(async (options: { taskId?: string }) => {
    const suffix = options.taskId ? `?task_id=${encodeURIComponent(options.taskId)}` : '';
    const events = await apiRequest('GET', `/v1/events${suffix}`);
    printJson(events);
  });

program
  .command('context <taskId>')
  .description('Fetch context bundle for a task')
  .action(async (taskId: string) => {
    const bundle = await apiRequest('GET', `/v1/context/bundle/${taskId}`);
    printJson(bundle);
  });

program.parseAsync(process.argv).catch((err: Error) => {
  process.stderr.write(`${err.message}\n`);
  process.exit(1);
});
