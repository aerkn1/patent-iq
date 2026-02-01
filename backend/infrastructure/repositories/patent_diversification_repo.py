from infrastructure.duckdb.connection import DuckDBConnection

class PatentDiversificationRepository:
    def __init__(self):
        self.conn = DuckDBConnection.get_connection()

    def get_diversification(self, appln_id: int) -> dict:
        q = """
        SELECT
            tech_entropy,
            tech_diversification_score,
            market_entropy,
            market_diversification_score
        FROM patent_industry_presence
        WHERE appln_id = ?
        """
        df = self.conn.execute(q, [appln_id]).fetchdf()
        if df.empty:
            # Conservative defaults
            return {
                "tech_entropy": 0.0,
                "tech_norm": 0.0,
                "market_entropy": 0.0,
                "market_norm": 0.0,
            }
        r = df.iloc[0]
        return {
            "tech_entropy": float(r.tech_entropy),
            "tech_norm": float(r.tech_diversification_score),
            "market_entropy": float(r.market_entropy),
            "market_norm": float(r.market_diversification_score),
        }