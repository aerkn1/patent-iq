# infrastructure/repositories/portfolio_final_repo.py

from infrastructure.duckdb.connection import DuckDBConnection


from typing import Optional


class PortfolioFinalRepository:

    def get(self, owner_id: int) -> Optional[dict]:
        conn = DuckDBConnection.get_connection()

        q = f"""
        SELECT
            blocking_power_portfolio,
            licensing_readiness_portfolio,
            legal_strength_portfolio,
            abandoned_ratio,
            legal_unknown_ratio,
            n_patents,
            n_unique_patents,
            portfolio_power_score_pct,
            licensing_readiness_portfolio_pct,
            blocking_power_portfolio_pct
        FROM portfolio_final
        WHERE owner_id = ?
        """

        df = conn.execute(q, [owner_id]).fetchdf()
        if df.empty:
            return None

        return df.iloc[0].to_dict()