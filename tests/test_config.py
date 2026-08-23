"""Unit tests for configuration loading and validation."""

from aerocool_ai.config import Settings, get_settings


def test_settings_defaults():
    """Verify default configuration values."""
    settings = Settings()
    assert settings.app_port == 8000
    assert settings.api_prefix == "/api/v1"
    assert "postgresql+asyncpg://" in settings.async_database_url
    assert "redis://" in settings.effective_redis_url
    assert settings.seb_loss_weight > 0


def test_get_settings_cached():
    """Verify singleton caching of settings."""
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2
