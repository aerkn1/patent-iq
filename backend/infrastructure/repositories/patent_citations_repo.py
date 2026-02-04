from infrastructure.duckdb.connection import DuckDBConnection


class PatentCitationsRepository:

    def get_citations(self, appln_id: int) -> dict:
        conn = DuckDBConnection.get_connection()

        q = f"""
        SELECT
            X_backward_patent_count,
            Y_backward_patent_count,
            X_backward_npl_count,
            Y_backward_npl_count,
            forward_patent_citation_count,
            field_normalized_citations,
            forward_impact_score,
            family_size
        FROM patent_core
        WHERE appln_id = ?
        """

        df = conn.execute(q, [appln_id]).fetchdf()

        if df.empty:
            return {
                "backward": {"count": 0, "x_normalized": 0.0},
                "forward": {"count": 0, "x_normalized": 0.0},
                "family_citations": 0,
            }

        r = df.iloc[0]

        backward_count = (
            r.X_backward_patent_count
            + r.Y_backward_patent_count
            + r.X_backward_npl_count
            + r.Y_backward_npl_count
        )

        return {
            "backward": {
                "count": int(backward_count),
                "x_normalized": float(r.field_normalized_citations),
            },
            "forward": {
                "count": int(r.forward_patent_citation_count),
                "x_normalized": float(r.forward_impact_score),
            },
            "family_citations": int(r.family_size),
        }

    def get_citation_metrics(self, appln_id: int) -> dict:
        conn = DuckDBConnection.get_connection()

        q = """
        SELECT
            early_cites,
            mid_cites,
            late_cites,
            trajectory_score,
            durability_score,
            sustainability_score_ui,
            timing_score,
            timing_class,
            early_signal,
            is_sustaining,
            citation_span_years,
            peak_age
        FROM patent_citation_metrics
        WHERE appln_id = ?
        """
        
        df = conn.execute(q, [appln_id]).fetchdf()
        
        if df.empty:
            return None
            
        return df.iloc[0].to_dict()

    def get_citation_timeseries(self, appln_id: int) -> dict:
        conn = DuckDBConnection.get_connection()

        # Get filing year from events core
        q_core = """
        SELECT date_part('year', CAST(filing_date AS DATE)) as filing_year
        FROM patent_citation_events_core
        WHERE cited_appln_id = ?
        """
        
        df_core = conn.execute(q_core, [appln_id]).fetchdf()
        
        if df_core.empty:
            return None

        filing_year = int(df_core.iloc[0]["filing_year"])

        # Get timeseries
        q_series = """
        SELECT
            age_year,
            new_forward_cites,
            cum_forward_cites
        FROM patent_citation_events_yearly
        WHERE cited_appln_id = ?
        ORDER BY age_year ASC
        """
        
        df_series = conn.execute(q_series, [appln_id]).fetchdf()
        
        series_data = df_series.to_dict(orient="records")
        
        return {
            "appln_id": appln_id,
            "filing_date": filing_year,
            "series": series_data
        }