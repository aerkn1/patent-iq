# infrastructure/repositories/portfolio_peer_meta_repo.py

from infrastructure.duckdb.connection import DuckDBConnection


class PortfolioPeerMetaRepository:

    def get(self, owner_id: int) -> dict | None:
        conn = DuckDBConnection.get_connection()

        q = f"""
        SELECT
            peer_group_id,
            peer_percentile,
            peer_class,
            peer_zscore,
            n_peers,
            portfolio_size_bucket
        FROM portfolio_peer_benchmark
        WHERE owner_id = ?
        """

        df = conn.execute(q, [owner_id]).fetchdf()
        if df.empty:
            return None

        return df.iloc[0].to_dict()