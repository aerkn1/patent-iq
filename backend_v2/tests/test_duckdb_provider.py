from pathlib import Path

from config.settings import get_settings
from infrastructure.duckdb import DuckDbProvider


def test_duckdb_provider_sets_temp_directory(monkeypatch, tmp_path: Path) -> None:
    temp_dir = tmp_path / "duckdb-tmp"
    monkeypatch.setenv("PATENTIQ_V2_DUCKDB_TEMP_DIRECTORY", str(temp_dir))
    get_settings.cache_clear()
    try:
        with DuckDbProvider().connect() as con:
            configured = con.execute("select current_setting('temp_directory')").fetchone()[0]
        assert Path(configured) == temp_dir
        assert temp_dir.exists()
    finally:
        get_settings.cache_clear()
