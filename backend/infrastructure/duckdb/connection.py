import duckdb
from pathlib import Path
from infrastructure.duckdb.parquet_registry import PARQUETS


from typing import Optional

class DuckDBConnection:
    _conn: Optional[duckdb.DuckDBPyConnection] = None

    @classmethod
    def get_connection(cls) -> duckdb.DuckDBPyConnection:
        if cls._conn is None:
            cls._conn = duckdb.connect(
                database="analytics.duckdb",
                read_only=False,
            )
            cls._initialize(cls._conn)
        return cls._conn

    @staticmethod
    def _initialize(conn: duckdb.DuckDBPyConnection):
        # Performance & stability
        conn.execute("PRAGMA threads=4;")
        conn.execute("PRAGMA enable_progress_bar=false;")
        conn.execute("PRAGMA memory_limit='8GB';")

        # Caching Strategy: Download files to local disk to avoid slow HTTP seeks
        from infrastructure.caching import CacheManager
        
        # This will block on startup if files are missing/stale
        local_parquets = CacheManager.ensure_cache(PARQUETS)

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