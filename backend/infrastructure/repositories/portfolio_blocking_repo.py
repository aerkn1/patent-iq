from infrastructure.duckdb.connection import DuckDBConnection


class PortfolioBlockingRepository:
    def __init__(self):
        self.conn = DuckDBConnection.get_connection()

    def get_blocking_drivers(self, owner_id: int) -> dict:
        q = """
        SELECT
            AVG(forward_impact_score) AS forward_impact_avg,
            AVG(family_breadth_normalized) AS family_breadth_avg,
            AVG(tech_breadth_penalty) AS tech_penalty_avg,
            AVG(self_blocking_rate) AS self_blocking_avg
        FROM patent_portfolio_map ppm
        JOIN patent_core pc ON pc.appln_id = ppm.appln_id
        WHERE ppm.owner_id = ?
        """
        df = self.conn.execute(q, [owner_id]).fetchdf()
        if df.empty:
            return {}

        r = df.iloc[0]
        return {
            "forward_impact_score": round(float(r["forward_impact_avg"] or 0.0), 4),
            "family_breadth_normalized": round(float(r["family_breadth_avg"] or 0.0), 4),
            "tech_breadth_penalty": round(float(r["tech_penalty_avg"] or 0.0), 4),
            "self_blocking_rate": round(float(r["self_blocking_avg"] or 0.0), 4),
        }

    def get_top_blocking_patents(self, owner_id: int, k: int = 5) -> list[dict]:
        q = """
        SELECT
            pc.appln_id,
            pc.blocking_power_pct
        FROM patent_portfolio_map ppm
        JOIN patent_core_w_ranks pc ON pc.appln_id = ppm.appln_id
        WHERE ppm.owner_id = ?
        ORDER BY pc.blocking_power_pct DESC
        LIMIT ?
        """
        df = self.conn.execute(q, [owner_id, k]).fetchdf()
        if df.empty:
            return []

        return [
            {
                "appln_id": int(r["appln_id"]),
                "blocking_power_pct": round(float(r["blocking_power_pct"]), 4),
            }
            for _, r in df.iterrows()
        ]