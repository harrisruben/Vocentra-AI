import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


def _resolve_env_file() -> str:
    env_state = os.getenv("ENVIRONMENT", "development")
    base_dirs = [Path.cwd(), Path(__file__).resolve().parents[2]]

    for base_dir in base_dirs:
        for env_name in [f".env.{env_state}", ".env", ".env.development", ".env.production"]:
            candidate = base_dir / env_name
            if candidate.exists():
                return str(candidate)

    return str(base_dirs[1] / f".env.{env_state}")


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./vocentra.db"
    REDIS_URL: Optional[str] = "redis://localhost:6379/0"
    JWT_SECRET: str = "supersecretjwtkeyforvocentraai2026!"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    ENVIRONMENT: str = "development"

    # Third-Party Integrations Settings
    HUBSPOT_API_KEY: Optional[str] = None
    GOOGLE_CALENDAR_CREDENTIALS: Optional[str] = None
    SLACK_WEBHOOK_URL: Optional[str] = None
    WHATSAPP_API_TOKEN: Optional[str] = None
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    VAPI_API_KEY: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=_resolve_env_file(),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
