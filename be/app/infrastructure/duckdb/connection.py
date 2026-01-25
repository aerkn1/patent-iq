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

        # Install and load httpfs for reading remote parquets
        conn.execute("INSTALL httpfs;")
        conn.execute("LOAD httpfs;")

        # Register Hugging Face token if available
        import os
        hf_token = os.getenv("HF_TOKEN")
        if hf_token:
            try:
                # DuckDB 0.10+ secret syntax
                conn.execute(f"CREATE SECRET IF NOT EXISTS hf_secret (TYPE HUGGINGFACE, TOKEN '{hf_token}');")
            except Exception as e:
                # Fallback or older version warning
                print(f"Warning: Failed to create HF secret: {e}")

        # Register parquet views
        DuckDBConnection._register_parquets(conn)

    @staticmethod
    def _register_parquets(conn: duckdb.DuckDBPyConnection):
        for view_name, parquet_url in PARQUETS.items():
            conn.execute(
                f"""
                CREATE OR REPLACE VIEW {view_name} AS
                SELECT * FROM read_parquet('{parquet_url}')
                """
            )