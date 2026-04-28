from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Any

from config.settings import get_settings
from infrastructure.duckdb.connection import DuckDBConnection


class MarketIntelligenceRepository:
    def __init__(self) -> None:
        gold_dir = get_settings().repo_root / "etl" / "data" / "gold"
        ml_dir = get_settings().repo_root / "etl" / "data" / "ml"
        self._overview_path = self._escape_path(gold_dir / "gold_market_intelligence_overview.parquet")
        self._segments_path = self._escape_path(gold_dir / "gold_market_intelligence_segments.parquet")
        self._timeseries_path = self._escape_path(gold_dir / "gold_market_intelligence_timeseries.parquet")
        self._summary_path = self._escape_path(gold_dir / "gold_market_summary_pit.parquet")
        self._leaderboard_path = self._escape_path(gold_dir / "gold_market_leaderboard_pit.parquet")
        self._citation_trend_path = self._escape_path(gold_dir / "gold_market_citation_trend_pit.parquet")
        self._citation_jurisdiction_path = self._escape_path(
            gold_dir / "gold_market_citation_pressure_by_jurisdiction_pit.parquet"
        )
        self._attacker_path = self._escape_path(gold_dir / "gold_market_attacker_leaderboard_pit.parquet")
        self._cpc_trend_path = self._escape_path(gold_dir / "gold_market_cpc_trend_pit.parquet")
        self._cpc_importance_path = self._escape_path(gold_dir / "gold_cpc_importance_pit.parquet")
        self._forecast_path_raw = ml_dir / "ml_prediction_jurisdiction_field_trend_forecast.parquet"
        self._forecast_path = self._escape_path(self._forecast_path_raw)

    @staticmethod
    def _escape_path(path: Path) -> str:
        return path.as_posix().replace("'", "''")

    @staticmethod
    def _normalize_value(value: Any) -> Any:
        if value is None:
            return None

        if hasattr(value, "item"):
            try:
                value = value.item()
            except Exception:
                pass

        if isinstance(value, float) and value != value:
            return None

        if isinstance(value, (date, datetime)):
            return value.isoformat()

        return value

    def _fetch_all(self, query: str, params: list[Any] | None = None) -> list[dict[str, Any]]:
        conn = DuckDBConnection.get_connection()
        rows = conn.execute(query, params or []).fetchall()
        columns = [column[0] for column in conn.description]
        payload: list[dict[str, Any]] = []
        for row in rows:
            payload.append(
                {
                    columns[index]: self._normalize_value(value)
                    for index, value in enumerate(row)
                }
            )
        return payload

    def _fetch_one(self, query: str, params: list[Any] | None = None) -> dict[str, Any] | None:
        rows = self._fetch_all(query, params)
        return rows[0] if rows else None

    def get_scope(self) -> dict[str, Any]:
        query = f"""
        WITH timeline AS (
            SELECT
                COUNT(DISTINCT wipo_industry_code) AS covered_field_count,
                MIN(family_priority_year) AS start_year,
                MAX(family_priority_year) AS end_year,
                MAX(latest_comparable_year) AS latest_comparable_market_year
            FROM read_parquet('{self._timeseries_path}')
        ),
        market_snapshot AS (
            SELECT
                MAX(as_of_year) AS latest_market_year,
                MAX(current_snapshot_date) AS snapshot_date
            FROM read_parquet('{self._summary_path}')
        ),
        cpc_snapshot AS (
            SELECT
                MAX(as_of_year) AS latest_cpc_year
            FROM read_parquet('{self._cpc_trend_path}')
        )
        SELECT
            covered_field_count,
            start_year,
            end_year,
            latest_comparable_market_year,
            latest_market_year,
            latest_cpc_year,
            snapshot_date
        FROM timeline
        CROSS JOIN market_snapshot
        CROSS JOIN cpc_snapshot
        """
        return self._fetch_one(query) or {}

    def get_overview(self) -> dict[str, Any]:
        query = f"""
        SELECT
            segment_count,
            rising_segment_count,
            cooling_segment_count,
            total_family_count,
            avg_segment_family_count
        FROM read_parquet('{self._overview_path}')
        LIMIT 1
        """
        return self._fetch_one(query) or {}

    def get_segments(self) -> list[dict[str, Any]]:
        query = f"""
        WITH latest_summary AS (
            SELECT
                wipo_industry_code,
                as_of_year,
                current_snapshot_date,
                segment_heat_state_asof,
                segment_market_state_ui_safe_asof,
                segment_priority_year_incomplete_asof,
                segment_latest_comparable_year,
                segment_family_count_asof,
                segment_prior_family_count_asof,
                segment_growth_index_asof,
                segment_owner_count_hist_proxy_asof,
                segment_blocking_density_asof,
                segment_field_balance_asof,
                segment_active_family_count_asof,
                segment_active_weight_asof,
                segment_active_jurisdiction_share_asof,
                segment_enforceability_density_asof,
                segment_top_owner_share_hist_proxy,
                historical_compare_safe,
                historical_owner_truth_supported,
                current_owner_bridge_replayed_to_history,
                historical_oecd_supported
            FROM read_parquet('{self._summary_path}')
            WHERE as_of_year = (SELECT MAX(as_of_year) FROM read_parquet('{self._summary_path}'))
        )
        SELECT
            segments.segment_id,
            segments.wipo_industry_code,
            segments.market_state,
            segments.total_family_count,
            segments.latest_year,
            summary.as_of_year AS latest_market_year,
            summary.current_snapshot_date AS snapshot_date,
            summary.segment_heat_state_asof,
            summary.segment_market_state_ui_safe_asof,
            summary.segment_priority_year_incomplete_asof,
            summary.segment_latest_comparable_year,
            summary.segment_family_count_asof,
            summary.segment_prior_family_count_asof,
            summary.segment_growth_index_asof,
            summary.segment_owner_count_hist_proxy_asof,
            summary.segment_blocking_density_asof,
            summary.segment_field_balance_asof,
            summary.segment_active_family_count_asof,
            summary.segment_active_weight_asof,
            summary.segment_active_jurisdiction_share_asof,
            summary.segment_enforceability_density_asof,
            summary.segment_top_owner_share_hist_proxy,
            summary.historical_compare_safe,
            summary.historical_owner_truth_supported,
            summary.current_owner_bridge_replayed_to_history,
            summary.historical_oecd_supported
        FROM read_parquet('{self._segments_path}') AS segments
        LEFT JOIN latest_summary AS summary
          ON summary.wipo_industry_code = segments.wipo_industry_code
        ORDER BY segments.total_family_count DESC, segments.wipo_industry_code ASC
        """
        return self._fetch_all(query)

    def get_timeseries(self) -> list[dict[str, Any]]:
        query = f"""
        SELECT
            family_priority_year,
            wipo_industry_code,
            family_count,
            prior_family_count,
            market_state,
            market_state_ui_safe,
            is_recent_priority_year_incomplete,
            latest_comparable_year
        FROM read_parquet('{self._timeseries_path}')
        ORDER BY wipo_industry_code ASC, family_priority_year ASC
        """
        return self._fetch_all(query)

    def get_segment_citation_trend(self, segment: str) -> list[dict[str, Any]]:
        query = f"""
        SELECT
            as_of_year,
            wipo_industry_code,
            citation_event_count,
            citation_count,
            citation_lethality_sum_raw,
            distinct_citing_assignee_count,
            distinct_citing_jurisdiction_count,
            citation_pressure_index,
            market_citation_state,
            market_state_reference,
            historical_citation_safe,
            historical_classification_truth_supported,
            method_version
        FROM read_parquet('{self._citation_trend_path}')
        WHERE wipo_industry_code = ?
        ORDER BY as_of_year ASC
        """
        return self._fetch_all(query, [segment])

    def get_segment_top_jurisdictions(self, segment: str, limit: int = 8) -> list[dict[str, Any]]:
        query = f"""
        WITH latest_year AS (
            SELECT MAX(as_of_year) AS value
            FROM read_parquet('{self._citation_jurisdiction_path}')
            WHERE wipo_industry_code = ?
        )
        SELECT
            pressure.as_of_year,
            pressure.wipo_industry_code,
            pressure.jurisdiction_code,
            pressure.citation_event_count,
            pressure.distinct_citing_assignee_count,
            pressure.citation_count,
            pressure.citation_lethality_sum_raw,
            pressure.citation_pressure_index,
            pressure.method_version
        FROM read_parquet('{self._citation_jurisdiction_path}') AS pressure
        JOIN latest_year
          ON latest_year.value = pressure.as_of_year
        WHERE pressure.wipo_industry_code = ?
        ORDER BY pressure.citation_pressure_index DESC, pressure.citation_event_count DESC, pressure.jurisdiction_code ASC
        LIMIT ?
        """
        return self._fetch_all(query, [segment, segment, limit])

    def get_segment_top_attackers(self, segment: str, limit: int = 8) -> list[dict[str, Any]]:
        query = f"""
        WITH latest_year AS (
            SELECT MAX(as_of_year) AS value
            FROM read_parquet('{self._attacker_path}')
            WHERE wipo_industry_code = ?
        )
        SELECT
            attackers.as_of_year,
            attackers.wipo_industry_code,
            attackers.citing_assignee_name,
            attackers.citation_event_count,
            attackers.distinct_citing_jurisdiction_count,
            attackers.citation_count,
            attackers.citation_lethality_sum_raw,
            attackers.attacker_pressure_index,
            attackers.method_version
        FROM read_parquet('{self._attacker_path}') AS attackers
        JOIN latest_year
          ON latest_year.value = attackers.as_of_year
        WHERE attackers.wipo_industry_code = ?
        ORDER BY attackers.attacker_pressure_index DESC, attackers.citation_event_count DESC, attackers.citing_assignee_name ASC
        LIMIT ?
        """
        return self._fetch_all(query, [segment, segment, limit])

    def get_segment_top_owners(self, segment: str, limit: int = 8) -> list[dict[str, Any]]:
        query = f"""
        WITH latest_year AS (
            SELECT MAX(as_of_year) AS value
            FROM read_parquet('{self._leaderboard_path}')
            WHERE segment_key = ?
              AND leaderboard_entity_type = 'owner'
        )
        SELECT
            leaderboard.as_of_year,
            leaderboard.leaderboard_rank,
            leaderboard.owner_name_harmonized,
            leaderboard.owner_name_display_current,
            leaderboard.in_segment_family_count_hist_proxy,
            leaderboard.in_segment_family_share_hist_proxy,
            leaderboard.avg_blocking_score_asof,
            leaderboard.total_blocking_score_asof,
            leaderboard.field_presence_weight_asof,
            leaderboard.family_composite_status_asof,
            leaderboard.historical_compare_safe,
            leaderboard.historical_owner_truth_supported,
            leaderboard.current_owner_bridge_replayed_to_history,
            leaderboard.current_owner_metadata_only
        FROM read_parquet('{self._leaderboard_path}') AS leaderboard
        JOIN latest_year
          ON latest_year.value = leaderboard.as_of_year
        WHERE leaderboard.segment_key = ?
          AND leaderboard.leaderboard_entity_type = 'owner'
        ORDER BY leaderboard.leaderboard_rank ASC
        LIMIT ?
        """
        return self._fetch_all(query, [segment, segment, limit])

    def get_segment_forecasts(self, segment: str) -> list[dict[str, Any]]:
        if not self._forecast_path_raw.exists():
            return []

        query = f"""
        WITH latest_year AS (
            SELECT MAX(as_of_year) AS value
            FROM read_parquet('{self._forecast_path}')
            WHERE wipo_industry_code = ?
        )
        SELECT
            forecast.horizon,
            forecast.as_of_year,
            forecast.jurisdiction_code,
            forecast.wipo_industry_code,
            forecast.local_family_filings_asof,
            forecast.predicted_direction_band,
            forecast.trend_strength_band,
            forecast.support_level,
            forecast.predicted_direction_probability,
            forecast.predicted_margin,
            forecast.predicted_growth_rate_reference,
            forecast.predicted_count_reference
        FROM read_parquet('{self._forecast_path}') AS forecast
        JOIN latest_year
          ON latest_year.value = forecast.as_of_year
        WHERE forecast.wipo_industry_code = ?
        ORDER BY forecast.horizon ASC, forecast.jurisdiction_code ASC
        """
        return self._fetch_all(query, [segment, segment])

    def get_segment_top_cpcs(self, segment: str, limit: int = 10) -> list[dict[str, Any]]:
        query = f"""
        WITH latest_year AS (
            SELECT MAX(as_of_year) AS value
            FROM read_parquet('{self._cpc_trend_path}')
            WHERE wipo_industry_code = ?
        )
        SELECT
            trends.as_of_year,
            trends.current_snapshot_date,
            trends.cpc_main_group,
            trends.cpc_main_group_label,
            trends.cpc_family_count_asof,
            trends.cpc_active_family_count_asof,
            trends.cpc_family_share_within_segment_asof,
            trends.cpc_active_family_share_within_segment_asof,
            trends.cpc_blocking_density_asof,
            trends.cpc_enforceability_density_asof,
            trends.cpc_pre_asof_forward_citations_clean_avg_asof,
            trends.cpc_avg_rcf_score_asof,
            trends.segment_heat_state_asof,
            trends.cpc_prior_family_count_asof,
            trends.cpc_growth_index_asof,
            trends.cpc_heat_state_asof,
            trends.cpc_rank_within_segment_year,
            trends.classification_visibility_policy,
            trends.classification_membership_replayed_to_history,
            trends.historical_classification_truth_supported,
            trends.historical_compare_safe
        FROM read_parquet('{self._cpc_trend_path}') AS trends
        JOIN latest_year
          ON latest_year.value = trends.as_of_year
        WHERE trends.wipo_industry_code = ?
        ORDER BY trends.cpc_rank_within_segment_year ASC
        LIMIT ?
        """
        return self._fetch_all(query, [segment, segment, limit])

    def get_global_cpc_importance(self, limit: int = 10) -> list[dict[str, Any]]:
        query = f"""
        WITH latest_year AS (
            SELECT MAX(as_of_year) AS value
            FROM read_parquet('{self._cpc_importance_path}')
        )
        SELECT
            importance.as_of_year,
            importance.current_snapshot_date,
            importance.cpc_main_group,
            importance.cpc_main_group_label,
            importance.cpc_family_count_asof,
            importance.cpc_segment_count_asof,
            importance.cpc_family_share_global_asof,
            importance.cpc_segment_presence_share_asof,
            importance.cpc_blocking_density_asof,
            importance.cpc_enforceability_density_asof,
            importance.cpc_pre_asof_forward_citations_clean_avg_asof,
            importance.cpc_avg_rcf_score_asof,
            importance.cpc_prior_family_count_asof,
            importance.cpc_growth_index_asof,
            importance.cpc_importance_score_asof,
            importance.cpc_importance_band_asof,
            importance.cpc_importance_rank_within_year,
            importance.historical_compare_safe,
            importance.historical_classification_truth_supported
        FROM read_parquet('{self._cpc_importance_path}') AS importance
        JOIN latest_year
          ON latest_year.value = importance.as_of_year
        ORDER BY importance.cpc_importance_rank_within_year ASC
        LIMIT ?
        """
        return self._fetch_all(query, [limit])
