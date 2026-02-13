from infrastructure.duckdb.connection import DuckDBConnection


from typing import Optional

class PatentCoreRepository:

    def get_core(self, appln_id: int) -> Optional[dict]:
        conn = DuckDBConnection.get_connection()

        q = """
        SELECT
            appln_id,
            appln_title,
            filing_date,
            grant_date,
            publn_date,
            publn_auth,
            docdb_family_id,
            patent_age_years,
            CASE
                WHEN is_abandoned = 1 THEN 'ABANDONED'
                WHEN grant_date IS NOT NULL THEN 'GRANTED'
                ELSE 'PENDING'
            END AS status,
            patent_category
        FROM patent_core
        WHERE appln_id = ?
        """

        df = conn.execute(q, [appln_id]).fetchdf()
        if df.empty:
            return None

        r = df.iloc[0].to_dict()
        return r

    def exists(self, appln_id: int) -> bool:
        conn = DuckDBConnection.get_connection()
        
        q = f"""
        SELECT 1
        FROM patent_core
        WHERE appln_id = ?
        LIMIT 1
        """
        df = conn.execute(q, [appln_id]).fetchdf()
        return not df.empty

    def get_core_metrics(self, appln_id: int) -> Optional[dict]:
        conn = DuckDBConnection.get_connection()
        
        q = f"""
        SELECT
            -- citations breakdown
            X_backward_patent_count,
            Y_backward_patent_count,
            X_backward_npl_count,
            Y_backward_npl_count,
            self_backward_patent_count,
            forward_patent_citation_count,
            X_forward_patent_count,
            Y_forward_patent_count,
            self_forward_citation_count,
            self_forward_rate,
            self_blocking_rate,
            claim_chartability_score,

            -- blocking power breakdown components
            forward_impact_score,
            family_breadth_normalized,
            tech_breadth_penalty,
            BPI,

            -- legal diagnostics
            opposition_count,
            lapse_count,
            renewal_payment_count,
            last_renewal_date,
            legal_confidence_score,
            is_legal_unknown,

            -- innovation diagnostics
            innovation_score,
            h_index_proxy,
            field_normalized_citations,

            -- legal strength (raw)
            legal_strength_score
        FROM patent_core
        WHERE appln_id = ?
        """
        df = conn.execute(q, [appln_id]).fetchdf()
        if df.empty:
            return None

        r = df.iloc[0]

        return r.to_dict()

    def search_by_publn_id(self, query: str, limit: int = 10) -> list[dict]:
        conn = DuckDBConnection.get_connection()
        
        # Determine strict or partial matching strategy
        # For huge datasets, ILIKE '%...%' can be slow without FTS. 
        # Assuming dataset size is manageable or we rely on prefix search for speed if needed.
        # Let's try basic ILIKE first.
        pattern = f"%{query}%"

        q = """
        SELECT
            appln_id,
            appln_title,
            ep_publn_id_full
        FROM patent_core
        WHERE ep_publn_id_full ILIKE ?
        ORDER BY LENGTH(ep_publn_id_full) ASC
        LIMIT ?
        """

        try:
            df = conn.execute(q, [pattern, limit]).fetchdf()
            if df.empty:
                return []
            return df.to_dict(orient="records")
        except Exception:
            return []