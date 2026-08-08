from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    database_url: str = "sqlite:///./widgetforge.db"
    jwt_secret: str = "development-only-change-me"
    jwt_expire_minutes: int = 60
    public_base_url: str = "http://localhost:8000"
    allowed_widget_origins: str = "http://localhost:8080"
    max_submission_bytes: int = 16384
    rate_limit_max_requests: int = 5
    rate_limit_window_seconds: int = 60
    ip_hash_secret: str = "development-ip-hash-secret"
    notifier_mode: str = "console"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def widget_origins(self) -> List[str]:
        return [origin.strip() for origin in self.allowed_widget_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
