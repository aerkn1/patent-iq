from __future__ import annotations

from typing import Any
from infrastructure.duckdb.connection import DuckDBConnection


class PortfolioLicensingRepository:
    """
    Reads precomputed overlap candidates and returns ranked list for a given owner_id.
    """

    def __init__(self) -> None:
        self.conn = DuckDBConnection.get_connection()

    def get_candidates(
        self,
        owner_id: int,
        limit: int = 50,
        offset: int = 0,
        min_industry_overlap: float | None = None,
        min_cpc_overlap: float | None = None,
    ) -> list[dict[str, Any]]:

        where = ["owner_id = ?"]
        params: list[Any] = [owner_id]

        if min_industry_overlap is not None:
            where.append("industry_overlap_score >= ?")
            params.append(min_industry_overlap)

        if min_cpc_overlap is not None:
            where.append("cpc_overlap_score >= ?")
            params.append(min_cpc_overlap)

        where_clause = " AND ".join(where)

        q = f"""
        SELECT
            owner_id,
            candidate_owner_id,
            candidate_owner_name,
            candidate_country,
            candidate_peer_class,
            candidate_portfolio_size,
            cpc_overlap_score,
            shared_cpc_codes,
            industry_overlap_score,
            shared_industry_codes
        FROM portfolio_licensing
        WHERE {where_clause}
        ORDER BY
            industry_overlap_score DESC NULLS LAST,
            cpc_overlap_score DESC NULLS LAST,
            candidate_portfolio_size DESC NULLS LAST,
            CASE candidate_peer_class
                WHEN 'STRONG' THEN 3
                WHEN 'AVERAGE' THEN 2
                WHEN 'WEAK' THEN 1
                ELSE 0
            END DESC,
            candidate_owner_id ASC
        LIMIT ? OFFSET ?
        """

        cursor = self.conn.execute(q, params + [limit, offset])

        rows = cursor.fetchall()
        if not rows:
            return []

        columns = [col[0] for col in cursor.description]

        return [
            dict(zip(columns, row))
            for row in rows
        ]