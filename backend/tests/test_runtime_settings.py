from config.settings import get_settings
from main import app


def test_settings_defaults(monkeypatch):
    monkeypatch.delenv("API_V1_PREFIX", raising=False)
    monkeypatch.delenv("CORS_ORIGINS", raising=False)
    monkeypatch.delenv("DUCKDB_THREADS", raising=False)
    monkeypatch.delenv("DUCKDB_MEMORY_LIMIT", raising=False)
    monkeypatch.delenv("PARQUET_BASE_URL", raising=False)
    monkeypatch.delenv("LOAD_ML_MODELS_ON_STARTUP", raising=False)
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.api_v1_prefix == "/api/v1"
    assert settings.cors_origins == ("http://localhost:3000",)
    assert settings.duckdb_threads == 4
    assert settings.duckdb_memory_limit == "8GB"
    assert settings.parquet_base_url.endswith("/patent-iq")
    assert settings.load_ml_models_on_startup is True


def test_settings_env_overrides(monkeypatch):
    monkeypatch.setenv("API_V1_PREFIX", "/api/test")
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000,https://example.com")
    monkeypatch.setenv("DUCKDB_THREADS", "2")
    monkeypatch.setenv("DUCKDB_MEMORY_LIMIT", "4GB")
    monkeypatch.setenv("PARQUET_BASE_URL", "https://example.com/parquets")
    monkeypatch.setenv("LOAD_ML_MODELS_ON_STARTUP", "false")
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.api_v1_prefix == "/api/test"
    assert settings.cors_origins == ("http://localhost:3000", "https://example.com")
    assert settings.duckdb_threads == 2
    assert settings.duckdb_memory_limit == "4GB"
    assert settings.parquet_base_url == "https://example.com/parquets"
    assert settings.load_ml_models_on_startup is False


def test_route_prefixes_stay_under_api_v1():
    route_paths = {route.path for route in app.routes}

    assert "/api/v1/patents/search" in route_paths
    assert "/api/v1/portfolios/search" in route_paths
    assert "/api/v1/stats/" in route_paths
