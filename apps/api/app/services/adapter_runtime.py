from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select

from app.db import SessionLocal
from app.models.entities import Agent
from app.services.adapters import AdapterService


class AdapterRuntime:
    def __init__(self) -> None:
        self._task: asyncio.Task | None = None
        self._guard = asyncio.Lock()
        self._cycles = 0
        self._executed_tasks = 0
        self._last_cycle_at: datetime | None = None
        self._last_error: str | None = None

    async def start(self) -> dict[str, Any]:
        async with self._guard:
            if self._task and not self._task.done():
                return self.status()
            self._task = asyncio.create_task(self._run_loop(), name='repomesh-adapter-runtime')
            return self.status()

    async def stop(self) -> dict[str, Any]:
        async with self._guard:
            task = self._task
            self._task = None
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        return self.status()

    def status(self) -> dict[str, Any]:
        running = self._task is not None and not self._task.done()
        return {
            'running': running,
            'cycles': self._cycles,
            'executed_tasks': self._executed_tasks,
            'last_cycle_at': self._last_cycle_at.isoformat() if self._last_cycle_at else None,
            'last_error': self._last_error,
        }

    def run_once_sync(self, *, max_tasks_per_agent: int = 2) -> dict[str, Any]:
        with SessionLocal() as db:
            agents = list(
                db.execute(
                    select(Agent).where(
                        Agent.status == 'active',
                        Agent.type != 'orchestrator',
                    )
                ).scalars().all()
            )
            results: list[dict[str, Any]] = []
            for agent in agents:
                run = AdapterService(db).execute(
                    agent_id=agent.id,
                    dry_run=False,
                    max_tasks=max_tasks_per_agent,
                )
                if run['executed']:
                    results.append(run)

        self._cycles += 1
        self._last_cycle_at = datetime.now(timezone.utc)
        self._last_error = None
        self._executed_tasks += sum(len(item['executed']) for item in results)
        return {'runs': results}

    async def _run_loop(self) -> None:
        from app.config.settings import get_settings

        while True:
            try:
                self.run_once_sync(max_tasks_per_agent=get_settings().adapter_max_tasks_per_agent_cycle)
            except Exception as exc:  # pragma: no cover - defensive guardrail
                self._last_error = str(exc)
            await asyncio.sleep(max(get_settings().adapter_poll_seconds, 1))


adapter_runtime = AdapterRuntime()
