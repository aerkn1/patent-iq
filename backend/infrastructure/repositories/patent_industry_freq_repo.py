from infrastructure.duckdb.connection import DuckDBConnection

class PatentIndustryFrequencyRepository:
    def __init__(self):
        self.conn = DuckDBConnection.get_connection()

    def get_industry_distribution(self, appln_id: int, top_n: int = 20) -> dict:
        # total industries
        q_total = f"""
        SELECT COUNT(*) AS n
        FROM patent_industry_freq
        WHERE appln_id = ?
        """
        total_df = self.conn.execute(q_total, [appln_id]).fetchdf()
        total = int(total_df.iloc[0]["n"]) if not total_df.empty else 0

        # top industries by market_frequency_score
        q_top = f"""
        SELECT
            wipo_industry_code,
            market_frequency_score
        FROM patent_industry_freq
        WHERE appln_id = ?
          AND market_frequency_score > 0
        ORDER BY market_frequency_score DESC
        LIMIT ?
        """
        top_df = self.conn.execute(q_top, [appln_id, top_n]).fetchdf()

        top_items = []
        top_sum = 0.0

        if not top_df.empty:
            for _, row in top_df.iterrows():
                w = float(row["market_frequency_score"])
                top_sum += w
                top_items.append({
                    "industry_code": str(row["wipo_industry_code"]),
                    "frequency": w,
                })

        return {
            "basis": "frequency",
            "total_industries": total,
            "top_industries": top_items,
            "long_tail_share": float(max(0.0, 1.0 - top_sum)) if total > 0 else 0.0,
        }