# src/core/config/settings.py
from functools import lru_cache
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # 기본 설정
    app_name: str = "AI Moderator"
    env: Literal["dev", "prod", "test"] = "dev"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    # 보안 설정 (필수값)
    # .env 파일에 없으면 서버 실행 시 에러 발생
    gemini_api_key: SecretStr
    jwt_secret_key: SecretStr

    # 선택적 설정 (기본값 제공)
    host: str = "0.0.0.0"
    port: int = 8000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # 정의되지 않은 환경변수는 무시
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
