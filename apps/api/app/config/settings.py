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


@lru_cache
def get_settings() -> Settings:
    return Settings()
