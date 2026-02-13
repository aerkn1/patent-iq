from infrastructure.duckdb.connection import DuckDBConnection

class PortfolioCitationsRepository:
    def __init__(self):
        self.conn = DuckDBConnection.get_connection()

    def get_cumulative_timeseries(self, owner_id: int) -> list[dict]:
        """Aggregate cumulative citations by calendar year for a portfolio."""
        
        # 1. Get metadata (min/max year) to confirm portfolio exists
        q_meta = """
        SELECT
            MIN(date_part('year', CAST(pc.filing_date AS DATE)))::INT as min_year,
            MAX(date_part('year', CAST(pc.filing_date AS DATE)) + COALESCE(pc.patent_age_years, 0))::INT as max_year
        FROM patent_portfolio_map ppm
        JOIN patent_core pc ON pc.appln_id = ppm.appln_id
        WHERE ppm.owner_id = ?
        """
        df_meta = self.conn.execute(q_meta, [owner_id]).fetchdf()
        
        if df_meta.empty or df_meta.iloc[0]["min_year"] is None:
            # Portfolio doesn't exist or has no patents
            return []

        # Handle NaNs from DuckDB -> pandas
        min_year_val = df_meta.iloc[0]["min_year"]
        max_year_val = df_meta.iloc[0]["max_year"]
        
        # Check for NaN (float('nan') != float('nan'))
        if isinstance(min_year_val, float) and min_year_val != min_year_val:
            return []
            
        min_year = int(min_year_val)
        if isinstance(max_year_val, float) and max_year_val != max_year_val:
            max_year = min_year
        else:
            max_year = int(max_year_val)
            
        if max_year < min_year: max_year = min_year

        # 2. Get citation timeseries
        # 2. Get citation timeseries with dense grid + forward fill for monotonicity
        q = """
        WITH portfolio_events AS (
            SELECT
                ppm.appln_id,
                (date_part('year', CAST(pc.filing_date AS DATE)) + y.age_year)::INT AS year,
                y.cum_forward_cites
            FROM patent_portfolio_map ppm
            JOIN patent_citation_events_yearly y ON y.appln_id = ppm.appln_id
            JOIN patent_core pc ON pc.appln_id = ppm.appln_id
            WHERE ppm.owner_id = ?
        ),
        years AS (
            SELECT unnest(generate_series(MIN(year), MAX(year), 1))::INT AS year
            FROM portfolio_events
        ),
        patents AS (
            SELECT DISTINCT appln_id FROM portfolio_events
        ),
        frame AS (
            SELECT p.appln_id, y.year
            FROM patents p, years y
        ),
        filled_data AS (
            SELECT
                f.year,
                LAST_VALUE(e.cum_forward_cites IGNORE NULLS) OVER (
                    PARTITION BY f.appln_id 
                    ORDER BY f.year
                    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                ) as ffilled_cites
            FROM frame f
            LEFT JOIN portfolio_events e ON f.appln_id = e.appln_id AND f.year = e.year
        )
        SELECT
            year,
            SUM(COALESCE(ffilled_cites, 0))::INT AS cum_cites,
            COUNT(DISTINCT CASE WHEN ffilled_cites > 0 THEN 1 END)::INT AS n_patents
        FROM filled_data
        GROUP BY year
        ORDER BY year ASC
        """
        df = self.conn.execute(q, [owner_id]).fetchdf()
        
        if df.empty:
            # Return flat 0 line
            return [
                {"year": min_year, "cum_cites": 0, "n_patents": 0},
                {"year": max_year, "cum_cites": 0, "n_patents": 0}
            ]
        
        return df.to_dict(orient="records")

    def get_totals(self, owner_id: int) -> dict:
        q = """
        SELECT
            SUM(pc.forward_patent_citation_count)::INT AS forward_total,
            SUM(pc.X_backward_patent_count + pc.Y_backward_patent_count)::INT AS backward_total,
            SUM(pc.X_backward_npl_count + pc.Y_backward_npl_count)::INT AS backward_npl_total,
            SUM(pc.self_forward_citation_count)::INT AS self_forward_total,
            SUM(pc.self_backward_patent_count)::INT AS self_backward_total,
            AVG(pc.self_forward_rate) AS avg_self_forward_rate,
            AVG(pc.self_blocking_rate) AS avg_self_blocking_rate
        FROM patent_portfolio_map ppm
        JOIN patent_core pc
          ON pc.appln_id = ppm.appln_id
        WHERE ppm.owner_id = ?
        """
        df = self.conn.execute(q, [owner_id]).fetchdf()
        if df.empty:
            return {
                "forward_total": 0, "backward_total": 0, "backward_npl_total": 0,
                "self_forward_total": 0, "self_backward_total": 0,
                "avg_self_forward_rate": 0.0, "avg_self_blocking_rate": 0.0,
            }
        r = df.iloc[0]
        return {
            "forward_total": int(r["forward_total"] or 0),
            "backward_total": int(r["backward_total"] or 0),
            "backward_npl_total": int(r["backward_npl_total"] or 0),
            "self_forward_total": int(r["self_forward_total"] or 0),
            "self_backward_total": int(r["self_backward_total"] or 0),
            "avg_self_forward_rate": float(r["avg_self_forward_rate"] or 0.0),
            "avg_self_blocking_rate": float(r["avg_self_blocking_rate"] or 0.0),
        }

    def get_forward_buckets(self, owner_id: int) -> list[dict]:
        q = """
        WITH t AS (
          SELECT pc.forward_patent_citation_count AS fw
          FROM patent_portfolio_map ppm
          JOIN patent_core pc ON pc.appln_id = ppm.appln_id
          WHERE ppm.owner_id = ?
        )
        SELECT
          CASE
            WHEN fw = 0 THEN '0'
            WHEN fw BETWEEN 1 AND 5 THEN '1-5'
            WHEN fw BETWEEN 6 AND 20 THEN '6-20'
            WHEN fw BETWEEN 21 AND 50 THEN '21-50'
            ELSE '50+'
          END AS bucket,
          COUNT(*)::INT AS count
        FROM t
        GROUP BY bucket
        ORDER BY
          CASE bucket
            WHEN '0' THEN 1
            WHEN '1-5' THEN 2
            WHEN '6-20' THEN 3
            WHEN '21-50' THEN 4
            ELSE 5
          END
        """
        df = self.conn.execute(q, [owner_id]).fetchdf()
        if df.empty:
            return []
        return [{"bucket": str(r["bucket"]), "count": int(r["count"])} for _, r in df.iterrows()]

    def get_citation_metrics(self, owner_id: int) -> dict:
        q = """
        SELECT *
        FROM portfolio_citation_metrics
        WHERE owner_id = ?
        """
        df = self.conn.execute(q, [owner_id]).fetchdf()
        if df.empty:
            return None
        return df.iloc[0].to_dict()

    def get_citation_timeseries(self, owner_id: int) -> list[dict]:
        q = """
        SELECT *
        FROM portfolio_citation_timeseries
        WHERE owner_id = ?
        ORDER BY year ASC
        """
        df = self.conn.execute(q, [owner_id]).fetchdf()
        if df.empty:
            return []
        return df.to_dict(orient="records")

    def get_backward_buckets(self, owner_id: int) -> list[dict]:
        q = """
        WITH t AS (
          SELECT (pc.X_backward_patent_count + pc.Y_backward_patent_count) AS bw
          FROM patent_portfolio_map ppm
          JOIN patent_core pc ON pc.appln_id = ppm.appln_id
          WHERE ppm.owner_id = ?
        )
        SELECT
          CASE
            WHEN bw BETWEEN 0 AND 5 THEN '0-5'
            WHEN bw BETWEEN 6 AND 20 THEN '6-20'
            WHEN bw BETWEEN 21 AND 50 THEN '21-50'
            ELSE '50+'
          END AS bucket,
          COUNT(*)::INT AS count
        FROM t
        GROUP BY bucket
        ORDER BY
          CASE bucket
            WHEN '0-5' THEN 1
            WHEN '6-20' THEN 2
            WHEN '21-50' THEN 3
            ELSE 4
          END
        """
        df = self.conn.execute(q, [owner_id]).fetchdf()
        if df.empty:
            return []
        return [{"bucket": str(r["bucket"]), "count": int(r["count"])} for _, r in df.iterrows()]