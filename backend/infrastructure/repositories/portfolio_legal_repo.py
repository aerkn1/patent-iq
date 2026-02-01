from infrastructure.duckdb.connection import DuckDBConnection


class PortfolioLegalRepository:
    def __init__(self):
        self.conn = DuckDBConnection.get_connection()

    def get_legal_aggregation(self, owner_id: int) -> dict:
        q = """
        SELECT
            COUNT(*)::INT AS n_patents,
            SUM(CASE WHEN is_abandoned = 1 THEN 1 ELSE 0 END)::INT AS abandoned_count,
            SUM(CASE WHEN is_legal_unknown = 1 THEN 1 ELSE 0 END)::INT AS unknown_count,
            AVG(legal_strength_score) AS avg_legal_strength
        FROM patent_portfolio_map ppm
        JOIN patent_core pc ON pc.appln_id = ppm.appln_id
        WHERE ppm.owner_id = ?
        """
        df = self.conn.execute(q, [owner_id]).fetchdf()
        if df.empty:
            return {}

        r = df.iloc[0]
        total = int(r["n_patents"])

        return {
            "n_patents": total,
            "abandoned_ratio": round(r["abandoned_count"] / total, 4) if total else 0.0,
            "legal_unknown_ratio": round(r["unknown_count"] / total, 4) if total else 0.0,
            "legal_strength_avg": round(float(r["avg_legal_strength"] or 0.0), 4),
        }