from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

import duckdb

from config.settings import get_settings


class DuckDbProvider:
    def __init__(self, database_path: Path | None = None) -> None:
        settings = get_settings()
        self._database_path = database_path or settings.duckdb_path
        self._settings = settings

    @contextmanager
    def connect(self) -> Iterator[duckdb.DuckDBPyConnection]:
        # The V2 repositories are read-mostly and operate against parquet files or
        # read-only attached serving snapshots. Using a file-backed scratch database
        # here introduces lock contention when the UI fires many concurrent requests.
        connection = duckdb.connect(":memory:")
        self._settings.duckdb_temp_directory.mkdir(parents=True, exist_ok=True)
        connection.execute(f"SET threads={self._settings.duckdb_threads}")
        connection.execute(f"SET memory_limit='{self._settings.duckdb_memory_limit}'")
        connection.execute(f"SET temp_directory='{self._settings.duckdb_temp_directory.as_posix()}'")
        try:
            yield connection
        finally:
            connection.close()
