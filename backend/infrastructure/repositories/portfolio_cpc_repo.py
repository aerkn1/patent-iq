from infrastructure.duckdb.connection import DuckDBConnection


class PortfolioCpcRepository:

    def get_top(
        self,
        owner_id: int,
        top_n: int = 5,
    ) -> list[dict]:
        conn = DuckDBConnection.get_connection()

        q = """
        SELECT
            cpc_subclass,
            weight
        FROM portfolio_cpc
        WHERE owner_id = ?
          AND weight > 0
        ORDER BY weight DESC
        LIMIT ?
        """

        df = conn.execute(q, [owner_id, top_n]).fetchdf()

        if df.empty:
            return []

        return [
            {
                "code": row["cpc_subclass"],
                "weight": round(float(row["weight"]), 3),
            }
            for _, row in df.iterrows()
        ]

    def get_owners_by_cpc(self, cpc_subclass: str) -> list[int]:
        conn = DuckDBConnection.get_connection()
        q = """
        SELECT DISTINCT owner_id
        FROM portfolio_cpc
        WHERE cpc_subclass = ?
        """
        df = conn.execute(q, [cpc_subclass]).fetchdf()
        return df["owner_id"].tolist()