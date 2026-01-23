# infrastructure/repositories/portfolio_rank_repo.py

from infrastructure.duckdb.connection import DuckDBConnection


class PortfolioRankRepository:

    def get(self, owner_id: int) -> dict | None:
        conn = DuckDBConnection.get_connection()

        q = f"""
        SELECT
            portfolio_power_score,
            portfolio_power_score_pct,
            portfolio_percentile,
            portfolio_rank,
            portfolio_tier,
            tech_axis_score_norm,
            market_axis_score_norm
        FROM portfolio_ranking_final
        WHERE owner_id = ?
        """

        df = conn.execute(q, [owner_id]).fetchdf()
        if df.empty:
            return None

        return df.iloc[0].to_dict()

    def get_by_owner_ids(self, owner_ids: list[int]) -> list[dict]:
        conn = DuckDBConnection.get_connection()
        q = """
        SELECT *
        FROM portfolio_ranking_final
        WHERE owner_id IN ({})
        """.format(",".join(["?"] * len(owner_ids)))

        df = conn.execute(q, owner_ids).fetchdf()
        return df.to_dict(orient="records")