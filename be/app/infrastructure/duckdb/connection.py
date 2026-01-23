import duckdb
from pathlib import Path
from infrastructure.duckdb.parquet_registry import PARQUETS


class DuckDBConnection:
    _conn: duckdb.DuckDBPyConnection | None = None

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

        # Register parquet views
        DuckDBConnection._register_parquets(conn)

    @staticmethod
    def _register_parquets(conn: duckdb.DuckDBPyConnection):
        for view_name, parquet_url in PARQUETS.items():
            conn.execute(
                f"""
                CREATE TABLE {view_name} AS
                SELECT * FROM read_parquet('{parquet_url}')
                """
            )