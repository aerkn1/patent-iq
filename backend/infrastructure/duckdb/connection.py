import duckdb
from pathlib import Path
from config.settings import get_settings
from infrastructure.duckdb.parquet_registry import get_parquet_registry

from typing import Optional


class DuckDBConnection:
    _conn: Optional[duckdb.DuckDBPyConnection] = None

    @classmethod
    def close(cls) -> None:
        if cls._conn is not None:
            cls._conn.close()
            cls._conn = None

    @classmethod
    def get_connection(cls) -> duckdb.DuckDBPyConnection:
        if cls._conn is None:
            settings = get_settings()
            db_path = settings.duckdb_path.as_posix()
            cls._conn = duckdb.connect(
                database=db_path,
                read_only=False,
            )
            cls._initialize(cls._conn)
        return cls._conn

    @staticmethod
    def _initialize(conn: duckdb.DuckDBPyConnection):
        settings = get_settings()
        # Performance & stability
        conn.execute(f"PRAGMA threads={settings.duckdb_threads};")
        conn.execute("PRAGMA enable_progress_bar=false;")
        conn.execute(f"PRAGMA memory_limit='{settings.duckdb_memory_limit}';")

        # Caching Strategy: Download files to local disk to avoid slow HTTP seeks
        from infrastructure.caching import CacheManager
        
        # This will block on startup if files are missing/stale
        local_parquets = CacheManager.ensure_cache(get_parquet_registry())

        # Register parquet views using LOCAL paths
        DuckDBConnection._register_parquets(conn, local_parquets)

    @staticmethod
    def _register_parquets(conn: duckdb.DuckDBPyConnection, registry: dict):
        for view_name, local_path in registry.items():
            # Use View for zero-copy read on local parquet
            conn.execute(
                f"""
                CREATE OR REPLACE VIEW {view_name} AS
                SELECT * FROM read_parquet('{local_path}')
                """
            )
