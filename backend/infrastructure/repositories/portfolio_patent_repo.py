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

        categories = filters.get("categories")
        if categories:
            placeholders = ", ".join(["?"] * len(categories))
            where.append(f"pc.patent_category IN ({placeholders})")
            params.extend(categories)

        jurisdictions = filters.get("jurisdictions")
        if jurisdictions:
            placeholders = ", ".join(["?"] * len(jurisdictions))
            where.append(f"pc.publn_auth IN ({placeholders})")
            params.extend(jurisdictions)

        status = filters.get("status")
        if status == "ACTIVE":
            where.append("pc.is_abandoned = false")
        elif status == "ABANDONED":
            where.append("pc.is_abandoned = true")

        blocking_min = filters.get("blocking_power_min")
        blocking_max = filters.get("blocking_power_max")
        if blocking_min is not None and blocking_max is not None:
            where.append("pr.blocking_power_pct IS NOT NULL")
            where.append("pr.blocking_power_pct BETWEEN ? AND ?")
            params.extend([blocking_min, blocking_max])

        innovation_min = filters.get("innovation_score_min")
        innovation_max = filters.get("innovation_score_max")
        if innovation_min is not None and innovation_max is not None:
            where.append("pc.innovation_score IS NOT NULL")
            where.append("pc.innovation_score BETWEEN ? AND ?")
            params.extend([innovation_min, innovation_max])
            
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
        JOIN patent_core_w_ranks pr ON pr.appln_id = ppm.appln_id
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

        summary_query = f"""
        SELECT
            COUNT(DISTINCT pc.appln_id)::INT AS total,
            SUM(CASE WHEN pc.is_abandoned = true THEN 1 ELSE 0 END)::INT AS abandoned,
            SUM(CASE WHEN pc.is_abandoned = false THEN 1 ELSE 0 END)::INT AS active
        FROM patent_portfolio_map ppm
        JOIN patent_core pc ON pc.appln_id = ppm.appln_id
        JOIN patent_core_w_ranks pr ON pr.appln_id = ppm.appln_id
        WHERE {where_clause}
        """

        summary_row = conn.execute(summary_query, params).fetchone()
        summary = {
            "total": int(summary_row[0] or 0),
            "abandoned": int(summary_row[1] or 0),
            "active": int(summary_row[2] or 0),
        }

        return rows.to_dict(orient="records"), total, summary