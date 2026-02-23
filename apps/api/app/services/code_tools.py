from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

from app.config.settings import get_settings
from app.services.errors import AppError, ERROR_VALIDATION


class CodeToolsService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def file_skeleton(self, *, file_path: str) -> dict[str, Any]:
        path = self._resolve_path(file_path)
        source = path.read_text(encoding='utf-8')
        if path.suffix != '.py':
            return {
                'file_path': file_path,
                'language': path.suffix.lstrip('.') or 'text',
                'symbols': [],
                'note': 'AST skeleton is currently implemented for Python files.',
            }

        module = ast.parse(source)
        symbols: list[dict[str, Any]] = []
        for node in module.body:
            item = self._node_signature(node)
            if item:
                symbols.append(item)
        return {'file_path': file_path, 'language': 'python', 'symbols': symbols}

    def symbol_logic(self, *, file_path: str, symbol_name: str) -> dict[str, Any]:
        path = self._resolve_path(file_path)
        if path.suffix != '.py':
            raise AppError(code=ERROR_VALIDATION, message='symbol_logic currently supports Python files only', status_code=400)
        source = path.read_text(encoding='utf-8')
        lines = source.splitlines()
        module = ast.parse(source)
        for node in ast.walk(module):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.name == symbol_name:
                start = node.lineno
                end = getattr(node, 'end_lineno', node.lineno)
                snippet = '\n'.join(lines[start - 1 : end])
                return {
                    'file_path': file_path,
                    'symbol_name': symbol_name,
                    'kind': 'class' if isinstance(node, ast.ClassDef) else 'function',
                    'start_line': start,
                    'end_line': end,
                    'source': snippet,
                }
        raise AppError(code=ERROR_VALIDATION, message='Symbol not found', status_code=404, details={'symbol_name': symbol_name})

    def search_replace(
        self,
        *,
        file_path: str,
        search: str,
        replace: str,
        expected_count: int = 1,
    ) -> dict[str, Any]:
        if expected_count < 1:
            raise AppError(code=ERROR_VALIDATION, message='expected_count must be >= 1', status_code=400)
        path = self._resolve_path(file_path)
        source = path.read_text(encoding='utf-8')
        matches = source.count(search)
        if matches != expected_count:
            raise AppError(
                code=ERROR_VALIDATION,
                message='Search/replace strict count mismatch',
                status_code=409,
                details={'expected_count': expected_count, 'actual_count': matches},
            )
        updated = source.replace(search, replace, expected_count)
        path.write_text(updated, encoding='utf-8')
        return {'file_path': file_path, 'replaced_count': expected_count}

    def _resolve_path(self, file_path: str) -> Path:
        root = Path(self.settings.adapter_workspace_root).resolve()
        candidate = (root / file_path).resolve() if not Path(file_path).is_absolute() else Path(file_path).resolve()
        if not str(candidate).startswith(str(root)):
            raise AppError(
                code=ERROR_VALIDATION,
                message='Path escapes workspace root',
                status_code=400,
                details={'workspace_root': str(root), 'path': str(candidate)},
            )
        if not candidate.exists():
            raise AppError(code=ERROR_VALIDATION, message='File not found', status_code=404, details={'path': str(candidate)})
        if candidate.is_dir():
            raise AppError(code=ERROR_VALIDATION, message='Expected file path, got directory', status_code=400)
        return candidate

    @staticmethod
    def _node_signature(node: ast.AST) -> dict[str, Any] | None:
        if isinstance(node, ast.ClassDef):
            return {
                'kind': 'class',
                'name': node.name,
                'line': node.lineno,
                'doc': ast.get_docstring(node),
            }
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = [arg.arg for arg in node.args.args]
            return {
                'kind': 'function',
                'name': node.name,
                'line': node.lineno,
                'signature': f"{node.name}({', '.join(args)})",
                'async': isinstance(node, ast.AsyncFunctionDef),
                'doc': ast.get_docstring(node),
            }
        return None
