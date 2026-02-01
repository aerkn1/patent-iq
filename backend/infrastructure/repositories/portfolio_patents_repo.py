from infrastructure.duckdb.connection import DuckDBConnection

class PortfolioPatentsRepository:
    def __init__(self):
        self.conn = DuckDBConnection.get_connection()

    def list_appln_ids(self, owner_id: int) -> list[int]:
        q = """
        SELECT appln_id
        FROM patent_portfolio_map
        WHERE owner_id = ?
        """
        df = self.conn.execute(q, [owner_id]).fetchdf()
        if df.empty:
            return []
        return [int(x) for x in df["appln_id"].tolist()]