from infrastructure.duckdb.connection import DuckDBConnection


class PatentRanksRepository:

    def get_ranks_row(self, appln_id: int) -> dict:
        conn = DuckDBConnection.get_connection()

        q = """
        SELECT
            appln_id,

            blocking_power_index,
            blocking_power_pct,
            blocking_power_tier,

            licensing_readiness_score,
            licensing_readiness_pct,
            licensing_readiness_tier,

            tech_axis_score,
            tech_axis_score_pct_global,
            tech_axis_score_rank_global,

            market_axis_score,
            market_axis_score_pct_global,
            market_axis_score_rank_global,

            legal_strength_score,
            legal_strength_score_pct_global,
            legal_strength_score_rank_global,

            blocking_power_index_rank_global,
            blocking_power_index_pct_global
        FROM patent_core_w_ranks
        WHERE appln_id = ?
        """
        
        df = conn.execute(q, [appln_id]).fetchdf()
        if df.empty:
            return None
        return df.iloc[0].to_dict()