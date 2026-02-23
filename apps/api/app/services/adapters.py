from __future__ import annotations

import subprocess
import time
from pathlib import Path
from typing import Any

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.config.settings import get_settings
from app.models.entities import ResourceLock, Task, TaskClaim
from app.repositories.common import utc_now
from app.services.events import EventService
from app.services.tasks import TaskService


class AdapterService:
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()
        self.events = EventService(db)
        self.tasks = TaskService(db)

    def execute(
        self,
        *,
        agent_id: str,
        task_id: str | None = None,
        dry_run: bool = False,
        max_tasks: int = 5,
    ) -> dict[str, Any]:
        stmt = (
            select(Task)
            .where(
                Task.assignee_agent_id == agent_id,
                Task.status.in_(['claimed', 'in_progress']),
            )
            .order_by(Task.priority.desc(), Task.created_at.asc())
            .limit(max_tasks)
        )
        if task_id:
            stmt = stmt.where(Task.id == task_id)

        tasks = list(self.db.execute(stmt).scalars().all())
        executed: list[dict[str, Any]] = []
        skipped: list[dict[str, Any]] = []

        for task in tasks:
            command, cwd, timeout_seconds = self._extract_exec_plan(task.scope or {})
            if not command:
                skipped.append({'task_id': task.id, 'reason': 'no command configured'})
                continue

            if dry_run:
                self.events.log(
                    event_type='adapter.execution.planned',
                    payload={'task_id': task.id, 'command': command, 'cwd': cwd, 'timeout_seconds': timeout_seconds},
                    severity='info',
                    task_id=task.id,
                    agent_id=agent_id,
                    repo_id=task.repo_id,
                    recipient_id=None,
                    parent_message_id=None,
                    channel='execution',
                )
                executed.append({'task_id': task.id, 'status': 'planned', 'command': command, 'cwd': cwd})
                continue

            executed.append(
                self._execute_task(
                    task=task,
                    agent_id=agent_id,
                    command=command,
                    cwd=cwd,
                    timeout_seconds=timeout_seconds,
                )
            )

        return {
            'agent_id': agent_id,
            'requested_task_id': task_id,
            'dry_run': dry_run,
            'executed': executed,
            'skipped': skipped,
        }

    def _execute_task(
        self,
        *,
        task: Task,
        agent_id: str,
        command: str,
        cwd: str,
        timeout_seconds: int,
    ) -> dict[str, Any]:
        route = self._resolve_route(task.scope or {})
        started = utc_now()
        self.events.log(
            event_type='adapter.execution.started',
            payload={
                'task_id': task.id,
                'command': command,
                'cwd': cwd,
                'timeout_seconds': timeout_seconds,
                'route': route,
            },
            severity='info',
            task_id=task.id,
            agent_id=agent_id,
            repo_id=task.repo_id,
            recipient_id=None,
            parent_message_id=None,
            channel='execution',
        )
        self.events.log(
            event_type='adapter.hook.pre_execute',
            payload={'task_id': task.id, 'route': route},
            severity='info',
            task_id=task.id,
            agent_id=agent_id,
            repo_id=task.repo_id,
            recipient_id=None,
            parent_message_id=None,
            channel='execution',
        )

        self.tasks.update(task_id=task.id, status='in_progress', progress=10, summary=None, blocked_reason=None)

        try:
            initial = self._run_command(command=command, cwd=cwd, timeout_seconds=timeout_seconds)
            if initial['exit_code'] == 0:
                return self._mark_execution_success(
                    task=task,
                    agent_id=agent_id,
                    started_at=started.isoformat(),
                    result=initial,
                    event_type='adapter.execution.completed',
                )

            prepass = self._run_prepass(task=task, agent_id=agent_id, cwd=cwd)
            if prepass['applied']:
                retry = self._run_command(command=command, cwd=cwd, timeout_seconds=timeout_seconds)
                if retry['exit_code'] == 0:
                    success = self._mark_execution_success(
                        task=task,
                        agent_id=agent_id,
                        started_at=started.isoformat(),
                        result=retry,
                        event_type='adapter.execution.retried_success',
                    )
                    success['prepass'] = prepass
                    return success
                initial = retry

            self.tasks.update(
                task_id=task.id,
                status='blocked',
                progress=10,
                summary=None,
                blocked_reason=f"Execution failed (exit {initial['exit_code']})",
            )
            self.events.log(
                event_type='adapter.execution.failed',
                payload={
                    'task_id': task.id,
                    'exit_code': initial['exit_code'],
                    'duration_ms': initial['duration_ms'],
                    'stdout_preview': initial['stdout'][:1000],
                    'stderr_preview': initial['stderr'][:2000],
                    'prepass': prepass,
                },
                severity='warning',
                task_id=task.id,
                agent_id=agent_id,
                repo_id=task.repo_id,
                recipient_id=None,
                parent_message_id=None,
                channel='execution',
            )
            self.events.log(
                event_type='adapter.hook.on_failure',
                payload={'task_id': task.id, 'next_step': 'escalate_to_llm', 'route': route},
                severity='warning',
                task_id=task.id,
                agent_id=agent_id,
                repo_id=task.repo_id,
                recipient_id=None,
                parent_message_id=None,
                channel='execution',
            )
            return {'task_id': task.id, 'status': 'failed', 'exit_code': initial['exit_code'], 'duration_ms': initial['duration_ms']}
        except subprocess.TimeoutExpired:
            self.tasks.update(
                task_id=task.id,
                status='blocked',
                progress=10,
                summary=None,
                blocked_reason=f'Execution timeout after {timeout_seconds}s',
            )
            self.events.log(
                event_type='adapter.execution.timeout',
                payload={'task_id': task.id, 'timeout_seconds': timeout_seconds},
                severity='warning',
                task_id=task.id,
                agent_id=agent_id,
                repo_id=task.repo_id,
                recipient_id=None,
                parent_message_id=None,
                channel='execution',
            )
            return {'task_id': task.id, 'status': 'timeout', 'timeout_seconds': timeout_seconds}

    def _run_command(self, *, command: str, cwd: str, timeout_seconds: int) -> dict[str, Any]:
        start = time.monotonic()
        completed = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
        duration_ms = int((time.monotonic() - start) * 1000)
        return {
            'exit_code': completed.returncode,
            'stdout': (completed.stdout or '').strip(),
            'stderr': (completed.stderr or '').strip(),
            'duration_ms': duration_ms,
        }

    def _run_prepass(self, *, task: Task, agent_id: str, cwd: str) -> dict[str, Any]:
        commands = self._prepass_commands(task.scope or {})
        if not commands:
            return {'applied': False, 'commands': []}

        self.events.log(
            event_type='adapter.prepass.started',
            payload={'task_id': task.id, 'commands': commands},
            severity='info',
            task_id=task.id,
            agent_id=agent_id,
            repo_id=task.repo_id,
            recipient_id=None,
            parent_message_id=None,
            channel='execution',
        )

        results: list[dict[str, Any]] = []
        for item in commands:
            try:
                result = self._run_command(command=item, cwd=cwd, timeout_seconds=self.settings.adapter_default_timeout_seconds)
                results.append({'command': item, **result})
            except subprocess.TimeoutExpired:
                results.append({'command': item, 'exit_code': -1, 'stdout': '', 'stderr': 'prepass timeout', 'duration_ms': 0})

        success = all(entry.get('exit_code') == 0 for entry in results)
        self.events.log(
            event_type='adapter.prepass.completed' if success else 'adapter.prepass.failed',
            payload={'task_id': task.id, 'results': results},
            severity='info' if success else 'warning',
            task_id=task.id,
            agent_id=agent_id,
            repo_id=task.repo_id,
            recipient_id=None,
            parent_message_id=None,
            channel='execution',
        )
        return {'applied': True, 'ok': success, 'results': results, 'commands': commands}

    def _mark_execution_success(
        self,
        *,
        task: Task,
        agent_id: str,
        started_at: str,
        result: dict[str, Any],
        event_type: str,
    ) -> dict[str, Any]:
        self.tasks.update(
            task_id=task.id,
            status='completed',
            progress=100,
            summary=self._summarize_output(result['stdout']),
            blocked_reason=None,
        )
        self._release_claims_and_locks(task_id=task.id, agent_id=agent_id)
        self.events.log(
            event_type=event_type,
            payload={
                'task_id': task.id,
                'exit_code': result['exit_code'],
                'duration_ms': result['duration_ms'],
                'stdout_preview': result['stdout'][:2000],
                'stderr_preview': result['stderr'][:500],
                'started_at': started_at,
                'finished_at': utc_now().isoformat(),
            },
            severity='info',
            task_id=task.id,
            agent_id=agent_id,
            repo_id=task.repo_id,
            recipient_id=None,
            parent_message_id=None,
            channel='execution',
        )
        return {
            'task_id': task.id,
            'status': 'completed',
            'exit_code': result['exit_code'],
            'duration_ms': result['duration_ms'],
        }

    def _extract_exec_plan(self, scope: dict[str, Any]) -> tuple[str | None, str, int]:
        adapter_cfg = scope.get('adapter') if isinstance(scope.get('adapter'), dict) else {}
        command = adapter_cfg.get('command') or scope.get('command')
        cwd_value = adapter_cfg.get('cwd') or scope.get('cwd') or '.'
        timeout = adapter_cfg.get('timeout_seconds') or scope.get('timeout_seconds') or self.settings.adapter_default_timeout_seconds

        resolved_cwd = self._resolve_cwd(str(cwd_value))
        timeout_seconds = int(timeout)
        if command:
            self._validate_command(str(command))
        return (str(command) if command else None, resolved_cwd, timeout_seconds)

    def _resolve_cwd(self, cwd: str) -> str:
        root = Path(self.settings.adapter_workspace_root).resolve()
        target = (root / cwd).resolve() if not Path(cwd).is_absolute() else Path(cwd).resolve()
        if not str(target).startswith(str(root)):
            raise ValueError(f'Adapter cwd must stay inside workspace root: {root}')
        return str(target)

    def _validate_command(self, command: str) -> None:
        allowlist = [item.strip() for item in self.settings.adapter_allowed_commands_csv.split(',') if item.strip()]
        if not allowlist:
            return
        if not any(command.startswith(prefix) for prefix in allowlist):
            raise ValueError('Command not allowed by adapter allowlist')

    def _prepass_commands(self, scope: dict[str, Any]) -> list[str]:
        adapter_cfg = scope.get('adapter') if isinstance(scope.get('adapter'), dict) else {}
        explicit = adapter_cfg.get('prepass_commands') or scope.get('prepass_commands')
        if isinstance(explicit, list):
            return [str(item) for item in explicit if str(item).strip()]
        csv_value = self.settings.adapter_prepass_commands_csv.strip()
        if not csv_value:
            return []
        return [item.strip() for item in csv_value.split(',') if item.strip()]

    @staticmethod
    def _resolve_route(scope: dict[str, Any]) -> dict[str, Any]:
        adapter_cfg = scope.get('adapter') if isinstance(scope.get('adapter'), dict) else {}
        return {
            'tier': adapter_cfg.get('tier') or scope.get('tier') or 'small',
            'profile': adapter_cfg.get('profile') or scope.get('adapter_profile') or 'generic-shell',
        }

    def _release_claims_and_locks(self, *, task_id: str, agent_id: str) -> None:
        now = utc_now()
        claims = list(
            self.db.execute(
                select(TaskClaim).where(
                    and_(
                        TaskClaim.task_id == task_id,
                        TaskClaim.agent_id == agent_id,
                        TaskClaim.state == 'active',
                    )
                )
            ).scalars().all()
        )
        for claim in claims:
            claim.state = 'released'
            claim.released_at = now
            lock = self.db.execute(
                select(ResourceLock).where(
                    and_(
                        ResourceLock.resource_key == claim.resource_key,
                        ResourceLock.owner_agent_id == agent_id,
                        ResourceLock.state == 'active',
                    )
                )
            ).scalars().first()
            if lock:
                lock.state = 'released'
                lock.released_at = now
        if claims:
            self.db.commit()

    @staticmethod
    def _summarize_output(stdout: str) -> str:
        if not stdout:
            return 'Execution completed successfully'
        first_lines = '\n'.join(stdout.splitlines()[:5]).strip()
        return first_lines[:500]
