from infrastructure.duckdb.connection import DuckDBConnection

class PortfolioCountryRepository:

    def get_by_country(
        self,
        country: str,
    ):
        conn = DuckDBConnection.get_connection()

        q = f"""
        SELECT
            pr.owner_id,
            pm.owner_name_norm AS owner_name,
            ps.n_patents,
            pr.portfolio_power_score_pct AS portfolio_power_pct,
            pr.portfolio_tier,
            pui.peer_class
        FROM portfolio_ranking_final pr
        JOIN portfolio_master pm
          ON pr.owner_id = pm.portfolio_id
        JOIN portfolio_size_reference ps
          ON pr.owner_id = ps.owner_id
        LEFT JOIN portfolio_peer_benchmark pui
          ON pr.owner_id = pui.owner_id
        WHERE pm.person_ctry_code = ?
        ORDER BY pr.portfolio_power_score_pct DESC
        """

        df = conn.execute(q, [country]).fetchdf()
        return df["owner_id"].tolist()