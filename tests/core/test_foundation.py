import os
import pytest
from core.config import get_settings
from core.config.settings import Settings
from core.logging import bind_context, get_context


def test_settings_load(monkeypatch):
    """환경변수가 올바르게 로드되는지 테스트"""
    get_settings.cache_clear()  # 캐시 초기화
    
    # 1. Test loading from env vars (overriding .env)
    os.environ["GEMINI_API_KEY"] = "test_key"
    os.environ["JWT_SECRET_KEY"] = "test_secret"

    settings = get_settings()
    assert settings.gemini_api_key.get_secret_value() == "test_key"

    # 2. Test missing required field
    # We need to disable .env file loading to verify that missing env var raises error
    # even if .env file exists (which it does in our test environment)
    # We patch the model_config to ignore the .env file
    monkeypatch.setattr(Settings, "model_config", {**Settings.model_config, "env_file": None})
    
    del os.environ["GEMINI_API_KEY"]
    get_settings.cache_clear()  # Clear cache to force reload with patched config

    with pytest.raises(Exception):  # ValidationError
        get_settings()

    # Clean up (restore os.environ is handled by pytest, but we modified Settings class?)
    # monkeypatch undoes changes to objects, so Settings.model_config should be restored.