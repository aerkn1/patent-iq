from infrastructure.duckdb.connection import DuckDBConnection

class PatentCpcFrequencyRepository:
    def __init__(self):
        self.conn = DuckDBConnection.get_connection()

    def get_cpc_distribution(self, appln_id: int, top_n: int = 20) -> dict:
        # 1) total unique CPCs
        q_total = f"""
        SELECT COUNT(*) AS n
        FROM patent_tech_lens_freq
        WHERE appln_id = ?
        """
        total_df = self.conn.execute(q_total, [appln_id]).fetchdf()
        total = int(total_df.iloc[0]["n"]) if not total_df.empty else 0

        # 2) top list
        q_top = f"""
        SELECT
            cpc_subclass,
            cpc_count,
            cpc_freq,
            tech_contribution_freq,
            market_contribution_freq
        FROM patent_tech_lens_freq
        WHERE appln_id = ?
        ORDER BY cpc_freq DESC
        LIMIT ?
        """
        top_df = self.conn.execute(q_top, [appln_id, top_n]).fetchdf()

        top_items = []
        top_sum = 0.0

        if not top_df.empty:
            for _, row in top_df.iterrows():
                freq = float(row["cpc_freq"])
                top_sum += freq
                top_items.append({
                    "cpc_subclass": str(row["cpc_subclass"]),
                    "count": int(row["cpc_count"]),
                    "frequency": freq,
                    "tech_contribution": float(row["tech_contribution_freq"]),
                    "market_contribution": float(row["market_contribution_freq"]),
                })

        return {
            "basis": "frequency",
            "total_cpc_classes": total,
            "top_cpcs": top_items,
            "long_tail_share": float(max(0.0, 1.0 - top_sum)) if total > 0 else 0.0,
        }