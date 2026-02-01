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