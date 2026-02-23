from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

from app.config.settings import get_settings
from app.db import SessionLocal
from app.services.event_stream import event_stream_broker
from app.services.orchestrator import OrchestratorEngine


class OrchestratorRuntime:
    def __init__(self) -> None:
        self._loop_task: asyncio.Task | None = None
        self._guard = asyncio.Lock()
        self._engine = OrchestratorEngine()
        self._last_cycle_at: datetime | None = None
        self._last_error: str | None = None
        self._cycles = 0
        self._assignments = 0

    async def start(self) -> dict[str, Any]:
        async with self._guard:
            if self._loop_task and not self._loop_task.done():
                return self.status()
            self._loop_task = asyncio.create_task(self._run_loop(), name='repomesh-orchestrator-runtime')
            return self.status()

    async def stop(self) -> dict[str, Any]:
        async with self._guard:
            task = self._loop_task
            self._loop_task = None

        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        return self.status()

    def status(self) -> dict[str, Any]:
        running = self._loop_task is not None and not self._loop_task.done()
        return {
            'running': running,
            'cycles': self._cycles,
            'assignments': self._assignments,
            'last_cycle_at': self._last_cycle_at.isoformat() if self._last_cycle_at else None,
            'last_error': self._last_error,
        }

    def run_once_sync(self, *, max_assignments: int = 10) -> dict[str, Any]:
        with SessionLocal() as db:
            result = self._engine.run_once(db, max_assignments=max_assignments)
        self._cycles += 1
        self._assignments += len(result['assignments'])
        self._last_cycle_at = datetime.now(timezone.utc)
        self._last_error = None
        return result

    async def _run_loop(self) -> None:
        settings = get_settings()
        poll_seconds = max(settings.orchestrator_poll_seconds, 1)
        subscriber = await event_stream_broker.subscribe(
            recipient_id=None,
            channel='orchestration',
            include_broadcast=True,
        )
        try:
            while True:
                try:
                    await asyncio.wait_for(subscriber.queue.get(), timeout=poll_seconds)
                except asyncio.TimeoutError:
                    pass
                try:
                    self.run_once_sync(max_assignments=settings.orchestrator_dispatch_limit)
                except Exception as exc:  # pragma: no cover - guardrail
                    self._last_error = str(exc)
        finally:
            await event_stream_broker.unsubscribe(subscriber.id)


orchestrator_runtime = OrchestratorRuntime()
