from infrastructure.duckdb.connection import DuckDBConnection


class PatentClassificationRepository:

    def get_classification(self, appln_id: int) -> dict:
        conn = DuckDBConnection.get_connection()

        q_cpc = """
        SELECT
          cpc_subclass AS code,
          cpc_freq AS weight
        FROM patent_tech_lens_freq
        WHERE appln_id = ?
        ORDER BY weight DESC
        """

        q_industry = """
        SELECT
            wipo_industry_code AS code,
            market_frequency_score AS weight
        FROM patent_industry_freq
        WHERE appln_id = ?
          AND market_frequency_score > 0
        ORDER BY weight DESC
        """

        cpc_df = conn.execute(q_cpc, [appln_id]).fetchdf()
        ind_df = conn.execute(q_industry, [appln_id]).fetchdf()

        return {
            "cpc_subclasses": cpc_df.to_dict(orient="records"),
            "industries": ind_df.to_dict(orient="records"),
        }