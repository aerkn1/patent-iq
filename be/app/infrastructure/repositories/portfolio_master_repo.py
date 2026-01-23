# infrastructure/repositories/portfolio_master_repo.py

from infrastructure.duckdb.connection import DuckDBConnection

class PortfolioMasterRepository:

    def get(self, owner_id: int) -> dict | None:
        conn = DuckDBConnection.get_connection()

        q = f"""
        SELECT
            portfolio_id AS owner_id,
            owner_name_norm AS owner_name,
            owner_type,
            person_ctry_code AS country
        FROM portfolio_master
        WHERE portfolio_id = ?
        """

        df = conn.execute(q, [owner_id]).fetchdf()
        if df.empty:
            return None

        return df.iloc[0].to_dict()

    def get_owner_names(self, owner_ids: list[int]) -> dict:
        conn = DuckDBConnection.get_connection()
        q = """
        SELECT portfolio_id AS owner_id, owner_name_norm
        FROM portfolio_master
        WHERE portfolio_id IN ({})
        """.format(",".join(["?"] * len(owner_ids)))

        df = conn.execute(q, owner_ids).fetchdf()
        return dict(zip(df["owner_id"], df["owner_name_norm"]))