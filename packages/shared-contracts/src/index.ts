export type TaskStatus = 'pending' | 'claimed' | 'in_progress' | 'blocked' | 'completed' | 'stalled';

export interface ContextBundle {
  task: {
    id: string;
    goal: string;
    description: string;
    status: TaskStatus;
    priority: number;
    acceptance_criteria: string | null;
    assignee_agent_id: string | null;
    progress: number;
  };
  scope_files: string[];
  recent_events: Array<{
    id: string;
    type: string;
    severity: string;
    payload: Record<string, unknown>;
    created_at: string;
  }>;
  lock_status: Array<{
    id: string;
    resource_key: string;
    owner_agent_id: string;
    state: string;
    expires_at: string;
  }>;
  placeholders: {
    errors: {
      latest: unknown[];
      note: string;
    };
    tests: {
      latest_runs: unknown[];
      note: string;
    };
    mode: 'compact' | 'full' | string;
  };
}

export const MCP_TOOLS = [
  'agent.register',
  'agent.heartbeat',
  'agent.list',
  'task.create',
  'task.list',
  'task.claim',
  'task.update',
  'lock.acquire',
  'lock.renew',
  'lock.release',
  'event.log',
  'event.list',
  'context.bundle'
] as const;

export type MCPToolName = (typeof MCP_TOOLS)[number];
