import { readConfig } from './config.js';

export async function apiRequest<T>(
  method: string,
  endpoint: string,
  body?: unknown,
  cwd = process.cwd()
): Promise<T> {
  const { config, token } = readConfig(cwd);
  const res = await fetch(`${config.api_url}${endpoint}`, {
    method,
    headers: {
      'content-type': 'application/json',
      'x-repomesh-token': token
    },
    body: body === undefined ? undefined : JSON.stringify(body)
  });

  const payload = await res.json().catch(() => ({}));
  if (!res.ok) {
    const message = payload?.error?.message ?? `API request failed (${res.status})`;
    throw new Error(message);
  }

  return payload as T;
}
