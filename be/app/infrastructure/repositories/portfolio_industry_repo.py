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

    def get_owners_by_industry(self, industry_code: str) -> list[int]:
        conn = DuckDBConnection.get_connection()
        q = """
        SELECT DISTINCT owner_id
        FROM portfolio_industry
        WHERE wipo_industry_code = ?
        """
        df = conn.execute(q, [industry_code]).fetchdf()
        return df["owner_id"].tolist()
    