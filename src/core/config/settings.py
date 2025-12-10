# src/core/config/settings.py
from functools import lru_cache
from typing import Literal, Optional
from pathlib import Path

from pydantic import SecretStr, Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # 기본 설정
    app_name: str = "AI Moderator"
    env: Literal["dev", "prod", "test"] = "dev"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    # 보안 설정 (필수값)
    gemini_api_key: SecretStr
    jwt_secret_key: SecretStr

    # 선택적 설정 (기본값 제공)
    host: str = "0.0.0.0"
    port: int = 8000

    # Database
    database_url: str = "sqlite+aiosqlite:///./app.db"

    # [DNA Fix] Google Cloud 인증 파일 경로 (MEDIUM-003)
    google_application_credentials: Optional[Path] = Field(
        default=None, description="Google Cloud 인증 JSON 파일 경로"
    )

    @validator("google_application_credentials")
    def validate_google_credentials(cls, v):
        if v and not v.exists():
            raise ValueError(f"Google credentials file not found: {v}")
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
