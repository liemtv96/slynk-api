from core.config import Settings


def test_settings_use_community_defaults(monkeypatch):
    monkeypatch.setenv("SLYNK_DEFAULT_FILE_TTL_HOURS", "8")
    monkeypatch.setenv("SLYNK_MAX_UPLOAD_BYTES", str(3 * 1024 * 1024 * 1024))
    monkeypatch.setenv("SLYNK_CORS_ORIGINS", "https://community.example,https://www.example")

    settings = Settings()

    assert settings.DEFAULT_FILE_TTL_HOURS == 8
    assert settings.MAX_UPLOAD_BYTES == 3 * 1024 * 1024 * 1024
    assert settings.CORS_ORIGINS == ["https://community.example", "https://www.example"]
