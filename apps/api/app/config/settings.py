from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    api_host: str = Field(default='0.0.0.0', alias='API_HOST')
    api_port: int = Field(default=8787, alias='API_PORT')
    database_url: str = Field(default='sqlite:///./repomesh.db', alias='DATABASE_URL')
    redis_url: str = Field(default='redis://localhost:6379/0', alias='REDIS_URL')
    qdrant_url: str = Field(default='http://localhost:6333', alias='QDRANT_URL')
    local_token: str = Field(default='repomesh-local-token', alias='REPO_MESH_LOCAL_TOKEN')
    session_ttl_seconds: int = Field(default=120, alias='SESSION_TTL_SECONDS')
    orchestrator_autostart: bool = Field(default=False, alias='ORCHESTRATOR_AUTOSTART')
    orchestrator_poll_seconds: int = Field(default=5, alias='ORCHESTRATOR_POLL_SECONDS')
    orchestrator_dispatch_limit: int = Field(default=10, alias='ORCHESTRATOR_DISPATCH_LIMIT')
    adapter_autostart: bool = Field(default=False, alias='ADAPTER_AUTOSTART')
    adapter_poll_seconds: int = Field(default=5, alias='ADAPTER_POLL_SECONDS')
    adapter_max_tasks_per_agent_cycle: int = Field(default=2, alias='ADAPTER_MAX_TASKS_PER_AGENT_CYCLE')
    adapter_default_timeout_seconds: int = Field(default=600, alias='ADAPTER_DEFAULT_TIMEOUT_SECONDS')
    adapter_workspace_root: str = Field(default='.', alias='ADAPTER_WORKSPACE_ROOT')
    adapter_allowed_commands_csv: str = Field(default='', alias='ADAPTER_ALLOWED_COMMANDS')
    adapter_prepass_commands_csv: str = Field(default='', alias='ADAPTER_PREPASS_COMMANDS')
    summarizer_autostart: bool = Field(default=False, alias='SUMMARIZER_AUTOSTART')
    summarizer_poll_seconds: int = Field(default=30, alias='SUMMARIZER_POLL_SECONDS')
    summarizer_max_tasks_cycle: int = Field(default=10, alias='SUMMARIZER_MAX_TASKS_CYCLE')


@lru_cache
def get_settings() -> Settings:
    return Settings()
