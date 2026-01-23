# infrastructure/repositories/portfolio_size_repo.py

from infrastructure.duckdb.connection import DuckDBConnection


class PortfolioSizeRepository:

    def get(self, owner_id: int) -> dict | None:
        conn = DuckDBConnection.get_connection()

        q = f"""
        SELECT
            n_patents,
            n_unique_patents
        FROM portfolio_size_reference
        WHERE owner_id = ?
        """

        df = conn.execute(q, [owner_id]).fetchdf()
        if df.empty:
            return None

        return df.iloc[0].to_dict()