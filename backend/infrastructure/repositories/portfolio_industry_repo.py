from infrastructure.duckdb.connection import DuckDBConnection


class PortfolioIndustryRepository:

    def get_top(
        self,
        owner_id: int,
        top_n: int = 5,
    ) -> list[dict]:
        conn = DuckDBConnection.get_connection()

        q = """
        SELECT
            wipo_industry_code,
            weight
        FROM portfolio_industry
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
                "code": row["wipo_industry_code"],
                "weight": round(float(row["weight"]), 3),
            }
            for _, row in df.iterrows()
        ]

    def get_owners_by_industry(self, industry_code: str, limit: int = 50) -> list[int]:
        conn = DuckDBConnection.get_connection()
        
        # Join with size reference to sort by "Effective Industry Patents"
        # (Total Patents * Industry Weight) -> Largest players in this space
        q = """
        SELECT pi.owner_id
        FROM portfolio_industry pi
        JOIN portfolio_size_reference ps ON pi.owner_id = ps.owner_id
        WHERE pi.wipo_industry_code = ?
        ORDER BY (ps.n_patents * pi.weight) DESC
        LIMIT ?
        """
        df = conn.execute(q, [industry_code, limit]).fetchdf()
        return df["owner_id"].tolist()
    