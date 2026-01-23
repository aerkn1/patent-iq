from infrastructure.duckdb.connection import DuckDBConnection


class PortfolioIndustryStatsRepository:

    def get(self, owner_id: int) -> dict | None:
        conn = DuckDBConnection.get_connection()

        q = f"""
        SELECT
            entropy_norm,
            top_k_share,
            long_tail_share,
            n_industries
        FROM portfolio_industry_stats
        WHERE owner_id = ?
        """

        df = conn.execute(q, [owner_id]).fetchdf()
        if df.empty:
            return None

        return df.iloc[0].to_dict()