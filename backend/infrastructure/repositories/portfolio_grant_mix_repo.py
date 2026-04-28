from infrastructure.duckdb.connection import DuckDBConnection
from typing import Optional

class PortfolioGrantMixRepository:
    def get(self, owner_id: int) -> list[dict]:
        conn = DuckDBConnection.get_connection()

        q = """
        SELECT
            publn_auth,
            granted_share
        FROM portfolio_family_grant_mix
        WHERE owner_id = ?
        ORDER BY granted_share DESC
        """

        df = conn.execute(q, [owner_id]).fetchdf()
        if df.empty:
            return []

        return df.to_dict(orient="records")
