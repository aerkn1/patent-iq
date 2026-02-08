from infrastructure.duckdb.connection import DuckDBConnection

class PortfolioCitationsRepository:
    def __init__(self):
        self.conn = DuckDBConnection.get_connection()

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