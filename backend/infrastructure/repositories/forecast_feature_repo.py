"""
Repository for fetching inference features from the ml_training_table
and portfolio membership / owner-share data.
"""
from typing import Optional

import pandas as pd

from infrastructure.duckdb.connection import DuckDBConnection


# The 10 model input features — order matches metadata.feature_list
_FEATURE_COLS = [
    "cites_pre_asof",
    "family_members_count",
    "family_jurisdiction_count",
    "major_office_grant_auth_count",
    "family_cpc_subclass_count",
    "has_us_grant",
    "has_cn_grant",
    "has_jp_grant",
    "has_kr_grant",
    "as_of_year",
]

# Context columns returned alongside features
_CONTEXT_COLS = ["appln_id", "filing_date", "as_of_date", "as_of_year"]

_SELECT_COLS = ", ".join(list(dict.fromkeys(_CONTEXT_COLS + _FEATURE_COLS)))


class ForecastFeatureRepository:
    """Reads inference features from the ml_training_table DuckDB view."""

    # ── single patent ───────────────────────────────────────────────────

    def get_features(self, appln_id: int) -> Optional[dict]:
        conn = DuckDBConnection.get_connection()
        q = f"""
        SELECT {_SELECT_COLS}
        FROM ml_training_table
        WHERE appln_id = ?
        """
        df = conn.execute(q, [appln_id]).fetchdf()
        if df.empty:
            return None
        return df.iloc[0].to_dict()

    # ── batch (portfolio) ──────────────────────────────────────────────

    def get_features_batch(self, appln_ids: list[int]) -> pd.DataFrame:
        if not appln_ids:
            return pd.DataFrame()
        conn = DuckDBConnection.get_connection()
        placeholders = ", ".join(["?"] * len(appln_ids))
        q = f"""
        SELECT {_SELECT_COLS}
        FROM ml_training_table
        WHERE appln_id IN ({placeholders})
        """
        return conn.execute(q, appln_ids).fetchdf()

    # ── portfolio membership ───────────────────────────────────────────

    def get_portfolio_appln_ids(self, owner_id: int) -> list[int]:
        conn = DuckDBConnection.get_connection()
        q = """
        SELECT DISTINCT appln_id
        FROM patent_portfolio_map
        WHERE owner_id = ?
        """
        df = conn.execute(q, [owner_id]).fetchdf()
        return df["appln_id"].tolist()

    def get_owner_shares(self, appln_ids: list[int]) -> dict[int, float]:
        """
        Compute owner_share = 1 / n_owners(appln_id) for each appln_id.
        Returns {appln_id: owner_share}.
        """
        if not appln_ids:
            return {}
        conn = DuckDBConnection.get_connection()
        placeholders = ", ".join(["?"] * len(appln_ids))
        q = f"""
        SELECT
            appln_id,
            1.0 / COUNT(*) OVER (PARTITION BY appln_id) AS owner_share
        FROM patent_portfolio_map
        WHERE appln_id IN ({placeholders})
        """
        df = conn.execute(q, appln_ids).fetchdf()
        # Deduplicate — each appln_id gets the same owner_share
        df = df.drop_duplicates(subset=["appln_id"])
        return dict(zip(df["appln_id"], df["owner_share"]))

    def get_portfolio_cpc_top_n_per_patent(
        self,
        owner_id: int,
        top_n_per_patent: int,
    ) -> pd.DataFrame:
        """Return top CPC subclasses (by cpc_freq) per patent in a portfolio.

        Output columns: appln_id, cpc_subclass, cpc_freq.
        """
        if top_n_per_patent <= 0:
            return pd.DataFrame(columns=["appln_id", "cpc_subclass", "cpc_freq"])

        conn = DuckDBConnection.get_connection()

        q = """
        WITH p AS (
            SELECT DISTINCT appln_id
            FROM patent_portfolio_map
            WHERE owner_id = ?
        ), ranked AS (
            SELECT
                f.appln_id,
                f.cpc_subclass,
                f.cpc_freq,
                ROW_NUMBER() OVER (PARTITION BY f.appln_id ORDER BY f.cpc_freq DESC) AS rn
            FROM patent_tech_lens_freq f
            JOIN p ON p.appln_id = f.appln_id
            WHERE f.cpc_freq > 0
        )
        SELECT appln_id, cpc_subclass, cpc_freq
        FROM ranked
        WHERE rn <= ?
        """

        return conn.execute(q, [owner_id, top_n_per_patent]).fetchdf()
