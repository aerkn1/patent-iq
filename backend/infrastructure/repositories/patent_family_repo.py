from typing import Optional, List
from infrastructure.duckdb.connection import DuckDBConnection
import logging

logger = logging.getLogger(__name__)

class PatentFamilyRepository:
    def get_family_data(self, appln_id: int) -> Optional[dict]:
        conn = DuckDBConnection.get_connection()

        q = """
        SELECT
            family_members_count,
            family_jurisdiction_count,
            major_office_grant_auths,
            family_cpc_subclass_count
        FROM patent_family_enriched
        WHERE appln_id = ?
        """

        try:
            row = conn.execute(q, [appln_id]).fetchone()
            if row is None:
                return None
            
            return {
                "family_members_count": row[0],
                "family_jurisdiction_count": row[1],
                "major_office_grant_auths": row[2],  # DuckDB returns list for ARRAY type
                "family_cpc_subclass_count": row[3]
            }
        except Exception as e:
            logger.error(f"Error fetching family data for {appln_id}: {e}")
            return None
