import pytest

from core.config import Settings

DB_ENGINES = ["sqlite", "mysql", "postgres", "mongo", "dynamodb"]
STORAGE_ENGINES = ["local", "s3"]


@pytest.mark.parametrize("db_engine", DB_ENGINES)
@pytest.mark.parametrize("storage_engine", STORAGE_ENGINES)
def test_settings_supports_engine_combinations(monkeypatch, db_engine, storage_engine):
    db_url = f"{db_engine}://example"
    monkeypatch.setenv("SLYNK_DB_ENGINE", db_engine.upper())
    monkeypatch.setenv("SLYNK_DATABASE_URL", db_url)
    monkeypatch.setenv("SLYNK_STORAGE_ENGINE", storage_engine.upper())

    settings = Settings()

    assert settings.DB_ENGINE == db_engine
    assert settings.DATABASE_URL == db_url
    assert settings.STORAGE_ENGINE == storage_engine