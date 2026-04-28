from infrastructure.duckdb.connection import DuckDBConnection
from typing import Optional

class PortfolioFamilyMetricsRepository:
    def get(self, owner_id: int) -> Optional[dict]:
        conn = DuckDBConnection.get_connection()

        q = """
        SELECT
            n_families_unique,
            n_patents_effective,
            family_members_count_avg,
            family_jurisdiction_count_avg,
            major_office_grant_coverage_index,
            has_ep_grant_share,
            has_us_grant_share,
            has_cn_grant_share,
            has_jp_grant_share,
            has_kr_grant_share
        FROM portfolio_family_metrics
        WHERE owner_id = ?
        """

        df = conn.execute(q, [owner_id]).fetchdf()
        if df.empty:
            return None

        return df.iloc[0].to_dict()
