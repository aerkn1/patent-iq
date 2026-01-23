from infrastructure.duckdb.connection import DuckDBConnection


class PortfolioPatentRepository:
    def fetch_patents(
        self,
        owner_id: int,
        filters: dict,
        sort: str,
        order: str,
        limit: int,
        offset: int,
    ):
        conn = DuckDBConnection.get_connection()

        where = ["ppm.owner_id = ?"]
        params = [owner_id]

        if filters.get("category"):
            where.append("pc.patent_category = ?")
            params.append(filters["category"])
            
        where_clause = " AND ".join(where)

        sort_col = sort or "blocking_power_pct"
        order = "DESC" if order != "asc" else "ASC"

        base_query = f"""
        FROM patent_portfolio_map ppm
        JOIN patent_core pc ON pc.appln_id = ppm.appln_id
        JOIN patent_core_w_ranks pr ON pr.appln_id = ppm.appln_id
        WHERE {where_clause}
        """

        # total count
        count_query = f"""
        SELECT COUNT(DISTINCT pc.appln_id)
        FROM patent_portfolio_map ppm
        JOIN patent_core pc ON pc.appln_id = ppm.appln_id
        WHERE {where_clause}
        """
        total = conn.execute(count_query, params).fetchone()[0]
        
        # data
        data_query = f"""
        SELECT
            pc.appln_id,
            pc.appln_title,
            pc.patent_category,
            pc.innovation_score,
            pc.legal_strength_score AS legal_strength,
            pc.forward_patent_citation_count,
            pc.is_abandoned,
            pc.publn_auth,
            pr.blocking_power_pct,
            pc.filing_date AS filing_date
        {base_query}
        ORDER BY {sort_col} {order}
        LIMIT ? OFFSET ?
        """

        rows = conn.execute(
            data_query, params + [limit, offset]
        ).fetchdf()

        return rows.to_dict(orient="records"), total