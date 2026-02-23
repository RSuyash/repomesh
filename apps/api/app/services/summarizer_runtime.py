from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

from app.config.settings import get_settings
from app.db import SessionLocal
from app.services.summarizer import SummarizerService


class SummarizerRuntime:
    def __init__(self) -> None:
        self._task: asyncio.Task | None = None
        self._guard = asyncio.Lock()
        self._cycles = 0
        self._compressed = 0
        self._last_cycle_at: datetime | None = None
        self._last_error: str | None = None

    async def start(self) -> dict[str, Any]:
        async with self._guard:
            if self._task and not self._task.done():
                return self.status()
            self._task = asyncio.create_task(self._run_loop(), name='repomesh-summarizer-runtime')
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
            'compressed': self._compressed,
            'last_cycle_at': self._last_cycle_at.isoformat() if self._last_cycle_at else None,
            'last_error': self._last_error,
        }

    def run_once_sync(self, *, max_tasks: int = 10) -> dict[str, Any]:
        with SessionLocal() as db:
            result = SummarizerService(db).run_once(max_tasks=max_tasks)
        self._cycles += 1
        self._compressed += int(result.get('count', 0))
        self._last_cycle_at = datetime.now(timezone.utc)
        self._last_error = None
        return result

    async def _run_loop(self) -> None:
        poll_seconds = max(get_settings().summarizer_poll_seconds, 5)
        while True:
            try:
                self.run_once_sync(max_tasks=get_settings().summarizer_max_tasks_cycle)
            except Exception as exc:  # pragma: no cover - defensive guardrail
                self._last_error = str(exc)
            await asyncio.sleep(poll_seconds)


summarizer_runtime = SummarizerRuntime()
