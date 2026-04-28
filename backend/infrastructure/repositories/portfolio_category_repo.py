from infrastructure.duckdb.connection import DuckDBConnection

class PortfolioCategoryRepository:
    def __init__(self):
        self.conn = DuckDBConnection.get_connection()

    def get_category_counts(self, owner_id: int) -> dict[str, int]:
        q = """
        SELECT
            pc.patent_category AS category,
            COUNT(*)::INT AS n
        FROM patent_portfolio_map ppm
        JOIN patent_core pc
          ON pc.appln_id = ppm.appln_id
        WHERE ppm.owner_id = ?
        GROUP BY pc.patent_category
        """
        df = self.conn.execute(q, [owner_id]).fetchdf()
        if df.empty:
            return {}
        return {str(r["category"]): int(r["n"]) for _, r in df.iterrows()}