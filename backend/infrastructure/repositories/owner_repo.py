from infrastructure.duckdb.connection import DuckDBConnection


class OwnerRepository:

    def get_owners(self, appln_id: int) -> list[dict]:
        conn = DuckDBConnection.get_connection()

        q = """
        SELECT
            o.owner_id,
            o.owner_name_norm AS name,
            o.person_ctry_code AS country
        FROM patent_portfolio_map ppm
        JOIN owner_reference o
          ON ppm.owner_id = o.owner_id
        WHERE ppm.appln_id = ?
        ORDER BY ppm.applt_seq_nr
        """

        df = conn.execute(q, [appln_id]).fetchdf()
        return df.to_dict(orient="records") if not df.empty else []