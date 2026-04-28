from config.settings import get_settings


def test_settings_defaults() -> None:
    settings = get_settings()
    assert settings.api_prefix == "/api/v1"
    assert settings.etl_data_root.name == "data"
    assert settings.duckdb_threads >= 1
    assert settings.duckdb_temp_directory.name == "duckdb_tmp"
    assert settings.raw_parquet_fallback_enabled is False
