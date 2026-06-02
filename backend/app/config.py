from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Resume AI Analyzer"
    app_env: str = "local"
    allowed_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    ai_provider: str = "openai_compatible"
    ai_base_url: str = "https://api.openai.com/v1"
    ai_api_key: str = ""
    ai_model: str = "gpt-4o-mini"

    redis_url: str = ""
    cache_dir: str = ".cache"
    database_path: str = "resume_ai.db"
    auth_secret: str = "change-me-in-production"
    token_expire_hours: int = 24

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8-sig", extra="ignore")

    @property
    def cors_origins(self) -> List[str]:
        return [item.strip() for item in self.allowed_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
