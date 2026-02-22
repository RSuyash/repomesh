from __future__ import annotations

import os
import sys


def _load_env_file(env_path: str) -> dict[str, str]:
    values: dict[str, str] = {}
    if not os.path.exists(env_path):
        return values
    with open(env_path, 'r', encoding='utf-8') as handle:
        for line in handle:
            raw = line.strip()
            if not raw or raw.startswith('#') or '=' not in raw:
                continue
            key, value = raw.split('=', 1)
            values[key.strip()] = value.strip()
    return values


def main() -> None:
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    api_dir = os.path.join(repo_root, 'apps', 'api')
    env_file = os.path.join(repo_root, 'infra', 'docker', '.env')
    env_values = _load_env_file(env_file)

    db_url = env_values.get(
        'DATABASE_URL',
        'postgresql+psycopg://repomesh:repomesh@127.0.0.1:5432/repomesh',
    )
    os.environ.setdefault('DATABASE_URL', db_url)

    # Make app importable regardless of where qwen is launched from.
    sys.path.insert(0, api_dir)
    os.chdir(api_dir)

    from app.mcp.stdio import main as stdio_main

    stdio_main()


if __name__ == '__main__':
    main()
