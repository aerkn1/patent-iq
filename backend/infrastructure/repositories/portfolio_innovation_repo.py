from infrastructure.duckdb.connection import DuckDBConnection


class PortfolioInnovationRepository:
    def __init__(self):
        self.conn = DuckDBConnection.get_connection()

    def get_innovation_aggregation(self, owner_id: int) -> dict:
        q = """
        SELECT
            AVG(innovation_score) AS avg_innovation,
            MEDIAN(innovation_score) AS median_innovation,
            AVG(h_index_proxy) AS avg_h_index,
            AVG(field_normalized_citations) AS avg_fnc
        FROM patent_portfolio_map ppm
        JOIN patent_core pc ON pc.appln_id = ppm.appln_id
        WHERE ppm.owner_id = ?
        """
        df = self.conn.execute(q, [owner_id]).fetchdf()
        if df.empty:
            return {}

        r = df.iloc[0]
        return {
            "innovation_score_avg": round(float(r["avg_innovation"] or 0.0), 4),
            "innovation_score_median": round(float(r["median_innovation"] or 0.0), 4),
            "h_index_proxy_avg": round(float(r["avg_h_index"] or 0.0), 4),
            "field_normalized_citations_avg": round(float(r["avg_fnc"] or 0.0), 4),
        }

    def get_top_innovative_patents(self, owner_id: int, k: int = 5) -> list[dict]:
        q = """
        SELECT
            pc.appln_id,
            pc.ep_publn_id_full,
            pc.innovation_score
        FROM patent_portfolio_map ppm
        JOIN patent_core pc ON pc.appln_id = ppm.appln_id
        WHERE ppm.owner_id = ?
        ORDER BY pc.innovation_score DESC
        LIMIT ?
        """
        df = self.conn.execute(q, [owner_id, k]).fetchdf()
        if df.empty:
            return []

        return [
            {
                "appln_id": int(r["appln_id"]),
                "ep_publn_id_full": str(r["ep_publn_id_full"]) if r["ep_publn_id_full"] is not None else None,
                "innovation_score": round(float(r["innovation_score"]), 4),
            }
            for _, r in df.iterrows()
        ]