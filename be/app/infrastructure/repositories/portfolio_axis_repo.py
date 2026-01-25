from infrastructure.duckdb.connection import DuckDBConnection


from typing import Optional

class PortfolioAxisRepository:

    def get(self, owner_id: int) -> Optional[dict]:
        conn = DuckDBConnection.get_connection()

        q = f"""
        SELECT
            tech_frequency_portfolio,
            market_frequency_portfolio,
            tech_presence_portfolio,
            market_presence_portfolio,
            tech_axis_score,
            market_axis_score
        FROM portfolio_axis_scores
        WHERE owner_id = ?
        """

        df = conn.execute(q, [owner_id]).fetchdf()
        if df.empty:
            return None

        return df.iloc[0].to_dict()