# infrastructure/repositories/portfolio_master_repo.py

from infrastructure.duckdb.connection import DuckDBConnection

from typing import Optional

class PortfolioMasterRepository:

    def get(self, owner_id: int) -> Optional[dict]:
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

    def search_by_name(self, query: str, limit: int = 20) -> list[dict]:
        conn = DuckDBConnection.get_connection()
        # Case-insensitive partial match
        pattern = f"%{query}%"
        
        q = """
        SELECT
            portfolio_id AS owner_id,
            owner_name_norm AS owner_name,
            owner_type,
            person_ctry_code AS country
        FROM portfolio_master
        WHERE owner_name_norm ILIKE ?
        ORDER BY LENGTH(owner_name_norm) ASC
        LIMIT ?
        """
        
        try:
            df = conn.execute(q, [pattern, limit]).fetchdf()
            if df.empty:
                return []
            if "country" in df.columns:
                df["country"] = df["country"].fillna("")
            return df.to_dict(orient="records")
        except Exception:
            return []