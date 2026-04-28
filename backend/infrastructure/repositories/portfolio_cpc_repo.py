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

    def get_owners_by_cpc(self, cpc_subclass: str, limit: int = 50) -> list[int]:
        conn = DuckDBConnection.get_connection()
        
        # Join with size reference to sort by "Effective CPC Patents"
        q = """
        SELECT pc.owner_id
        FROM portfolio_cpc pc
        JOIN portfolio_size_reference ps ON pc.owner_id = ps.owner_id
        WHERE pc.cpc_subclass = ?
        ORDER BY (ps.n_patents * pc.weight) DESC
        LIMIT ?
        """
        df = conn.execute(q, [cpc_subclass, limit]).fetchdf()
        return df["owner_id"].tolist()