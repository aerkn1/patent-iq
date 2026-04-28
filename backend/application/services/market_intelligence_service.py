from __future__ import annotations

import json
from statistics import median
from typing import Any

from config.settings import get_settings
from domain.errors import ValidationError
from infrastructure.repositories.market_intelligence_repo import MarketIntelligenceRepository


ALLOWED_MARKET_STATES = {"all", "rising", "cooling", "stable"}
SUPPORT_LEVEL_RANK = {"limited": 0, "moderate": 1, "strong": 2}


class MarketIntelligenceService:
    def __init__(self, repo: MarketIntelligenceRepository | None = None) -> None:
        self.repo = repo or MarketIntelligenceRepository()

    @staticmethod
    def _as_float(value: Any, digits: int = 3) -> float | None:
        if value is None:
            return None
        return round(float(value), digits)

    @staticmethod
    def _as_int(value: Any) -> int | None:
        if value is None:
            return None
        return int(round(float(value)))

    @staticmethod
    def _normalize_text(value: Any, fallback: str = "—") -> str:
        if value is None:
            return fallback
        text = str(value).strip()
        return text if text else fallback

    @staticmethod
    def _state_label(value: str) -> str:
        return value.replace("_", " ").title()

    @staticmethod
    def _support_rank(value: str | None) -> int:
        return SUPPORT_LEVEL_RANK.get(str(value or "limited").strip().lower(), 0)

    def _crowding_label(self, owner_count: int | None, top_owner_share: float | None) -> str:
        if owner_count is None or top_owner_share is None:
            return "coverage pending"
        if owner_count >= 200000 and top_owner_share <= 0.02:
            return "crowded"
        if top_owner_share >= 0.05:
            return "concentrated"
        if owner_count <= 80000:
            return "open"
        return "balanced"

    def _concentration_role(self, share: float | None, owner_count: int | None = None) -> str:
        if share is None:
            return "coverage pending"
        if share >= 0.08:
            return "dominant"
        if share >= 0.04:
            return "contender"
        if owner_count is not None and owner_count >= 150000:
            return "fragmented"
        return "present"

    def _is_whitespace_candidate(
        self,
        blocking_density: float | None,
        top_owner_share: float | None,
        crowding_label: str,
        momentum_delta: float | None,
    ) -> bool:
        if blocking_density is None or top_owner_share is None or momentum_delta is None:
            return False
        return (
            blocking_density <= 35.0
            and top_owner_share <= 0.05
            and crowding_label in {"open", "balanced"}
            and momentum_delta >= -0.02
        )

    def _build_market_reference_map(self, rows: list[dict[str, Any]]) -> dict[int, float]:
        buckets: dict[int, list[int]] = {}
        for row in rows:
            year = self._as_int(row.get("family_priority_year"))
            count = self._as_int(row.get("family_count"))
            if year is None or count is None:
                continue
            buckets.setdefault(year, []).append(count)
        return {year: round(float(median(values)), 1) for year, values in buckets.items() if values}

    def _map_segment_timeseries(self, rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
        grouped: dict[str, list[dict[str, Any]]] = {}
        market_reference = self._build_market_reference_map(rows)
        for row in rows:
            segment = self._normalize_text(row.get("wipo_industry_code"), "")
            if not segment:
                continue
            year = self._as_int(row.get("family_priority_year"))
            if year is None:
                continue
            current_count = self._as_int(row.get("family_count")) or 0
            prior_count = self._as_int(row.get("prior_family_count")) or 0
            growth_rate = 0.0
            if prior_count > 0:
                growth_rate = (current_count - prior_count) / prior_count
            market_median = market_reference.get(year, 0.0)
            grouped.setdefault(segment, []).append(
                {
                    "year": year,
                    "family_count": current_count,
                    "prior_family_count": prior_count,
                    "market_state": self._normalize_text(row.get("market_state"), "stable"),
                    "market_state_ui_safe": bool(row.get("market_state_ui_safe")),
                    "is_recent_priority_year_incomplete": bool(row.get("is_recent_priority_year_incomplete")),
                    "latest_comparable_year": self._as_int(row.get("latest_comparable_year")) or year,
                    "growth_rate": round(growth_rate, 4),
                    "market_median_family_count": market_median,
                    "delta_from_market_median": round(current_count - market_median, 1),
                    "year_over_year_delta_pct": round(growth_rate, 4),
                }
            )
        return grouped

    def _map_overview(self, raw: dict[str, Any]) -> dict[str, Any]:
        return {
            "segment_count": self._as_int(raw.get("segment_count")) or 0,
            "rising_segment_count": self._as_int(raw.get("rising_segment_count")) or 0,
            "cooling_segment_count": self._as_int(raw.get("cooling_segment_count")) or 0,
            "total_family_count": self._as_int(raw.get("total_family_count")) or 0,
            "avg_segment_family_count": self._as_float(raw.get("avg_segment_family_count"), 1) or 0.0,
        }

    def _map_scope(self, raw: dict[str, Any]) -> dict[str, Any]:
        return {
            "scope_type": "mega_cluster_bounded",
            "covered_field_count": self._as_int(raw.get("covered_field_count")) or 0,
            "coverage_year_range": {
                "start_year": self._as_int(raw.get("start_year")) or 0,
                "end_year": self._as_int(raw.get("end_year")) or 0,
            },
            "snapshot_date": raw.get("snapshot_date"),
            "latest_market_year": self._as_int(raw.get("latest_market_year")) or 0,
            "latest_comparable_market_year": self._as_int(raw.get("latest_comparable_market_year"))
            or self._as_int(raw.get("latest_market_year"))
            or 0,
            "latest_cpc_year": self._as_int(raw.get("latest_cpc_year")) or 0,
        }

    def _map_segment_row(
        self,
        row: dict[str, Any],
        sparkline: list[dict[str, Any]],
    ) -> dict[str, Any]:
        owner_count = self._as_int(row.get("segment_owner_count_hist_proxy_asof"))
        top_owner_share = self._as_float(row.get("segment_top_owner_share_hist_proxy"), 4)
        current_count = self._as_int(row.get("segment_family_count_asof")) or 0
        prior_count = self._as_int(row.get("segment_prior_family_count_asof")) or 0
        momentum_delta = 0.0
        if prior_count > 0:
            momentum_delta = (current_count - prior_count) / prior_count
        crowding_label = self._crowding_label(owner_count, top_owner_share)

        return {
            "segment_id": self._normalize_text(row.get("segment_id")),
            "wipo_industry_code": self._normalize_text(row.get("wipo_industry_code")),
            "market_state": self._normalize_text(row.get("market_state"), "stable"),
            "total_family_count": self._as_int(row.get("total_family_count")) or 0,
            "latest_year": self._as_int(row.get("latest_year")) or 0,
            "latest_comparable_year": self._as_int(row.get("segment_latest_comparable_year"))
            or self._as_int(row.get("latest_year"))
            or 0,
            "latest_year_incomplete": bool(row.get("segment_priority_year_incomplete_asof")),
            "latest_market_year": self._as_int(row.get("latest_market_year")) or 0,
            "snapshot_date": row.get("snapshot_date"),
            "segment_heat_state_asof": self._normalize_text(row.get("segment_heat_state_asof"), "stable"),
            "segment_market_state_ui_safe_asof": bool(row.get("segment_market_state_ui_safe_asof")),
            "segment_priority_year_incomplete_asof": bool(row.get("segment_priority_year_incomplete_asof")),
            "segment_latest_comparable_year": self._as_int(row.get("segment_latest_comparable_year"))
            or self._as_int(row.get("latest_year"))
            or 0,
            "segment_family_count_stock_asof": self._as_int(row.get("segment_family_count_stock_asof")) or 0,
            "segment_priority_year_family_count_asof": current_count,
            "segment_prior_priority_year_family_count_asof": prior_count,
            "segment_growth_index_asof": self._as_float(row.get("segment_growth_index_asof"), 4) or 0.0,
            "segment_owner_count_hist_proxy_asof": owner_count or 0,
            "segment_blocking_density_asof": self._as_float(row.get("segment_blocking_density_asof"), 2) or 0.0,
            "segment_field_balance_asof": self._as_float(row.get("segment_field_balance_asof"), 3) or 0.0,
            "segment_active_family_count_asof": self._as_int(row.get("segment_active_family_count_asof")) or 0,
            "segment_active_weight_asof": self._as_float(row.get("segment_active_weight_asof"), 4) or 0.0,
            "segment_active_jurisdiction_share_asof": self._as_float(
                row.get("segment_active_jurisdiction_share_asof"), 4
            )
            or 0.0,
            "segment_enforceability_density_asof": self._as_float(row.get("segment_enforceability_density_asof"), 2)
            or 0.0,
            "segment_top_owner_share_hist_proxy": top_owner_share or 0.0,
            "historical_compare_safe": bool(row.get("historical_compare_safe")),
            "historical_owner_truth_supported": bool(row.get("historical_owner_truth_supported")),
            "current_owner_bridge_replayed_to_history": bool(row.get("current_owner_bridge_replayed_to_history")),
            "historical_oecd_supported": bool(row.get("historical_oecd_supported")),
            "momentum_delta_pct": round(momentum_delta, 4),
            "crowding_label": crowding_label,
            "concentration_role": self._concentration_role(top_owner_share, owner_count),
            "whitespace_candidate": self._is_whitespace_candidate(
                self._as_float(row.get("segment_blocking_density_asof"), 2),
                top_owner_share,
                crowding_label,
                momentum_delta,
            ),
            "sparkline": sparkline[-8:],
        }

    def _map_state_options(self, segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
        counts: dict[str, int] = {"all": len(segments)}
        for row in segments:
            state = self._normalize_text(row.get("market_state"), "stable")
            counts[state] = counts.get(state, 0) + 1

        ordered_values = ["all", "rising", "cooling", "stable"]
        options: list[dict[str, Any]] = []
        for value in ordered_values:
            options.append(
                {
                    "value": value,
                    "label": "All segments" if value == "all" else self._state_label(value),
                    "count": counts.get(value, 0),
                }
            )
        return options

    def _map_segment_options(self, segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "value": row["wipo_industry_code"],
                "label": row["wipo_industry_code"],
                "market_state": row["market_state"],
                "total_family_count": row["total_family_count"],
            }
            for row in segments
        ]

    def _map_selected_summary(self, row: dict[str, Any]) -> dict[str, Any]:
        return {
            "as_of_year": row["latest_market_year"],
            "snapshot_date": row["snapshot_date"],
            "market_state": row["market_state"],
            "segment_heat_state_asof": row["segment_heat_state_asof"],
            "total_family_count": row["total_family_count"],
            "segment_family_count_stock_asof": row["segment_family_count_stock_asof"],
            "segment_family_count_asof": row["segment_priority_year_family_count_asof"],
            "segment_priority_year_family_count_asof": row["segment_priority_year_family_count_asof"],
            "segment_prior_family_count_asof": row["segment_prior_priority_year_family_count_asof"],
            "segment_prior_priority_year_family_count_asof": row["segment_prior_priority_year_family_count_asof"],
            "segment_growth_index_asof": row["segment_growth_index_asof"],
            "segment_owner_count_hist_proxy_asof": row["segment_owner_count_hist_proxy_asof"],
            "segment_blocking_density_asof": row["segment_blocking_density_asof"],
            "segment_field_balance_asof": row["segment_field_balance_asof"],
            "segment_active_family_count_asof": row["segment_active_family_count_asof"],
            "segment_active_weight_asof": row["segment_active_weight_asof"],
            "segment_active_jurisdiction_share_asof": row["segment_active_jurisdiction_share_asof"],
            "segment_enforceability_density_asof": row["segment_enforceability_density_asof"],
            "segment_top_owner_share_hist_proxy": row["segment_top_owner_share_hist_proxy"],
            "segment_market_state_ui_safe_asof": row["segment_market_state_ui_safe_asof"],
            "segment_priority_year_incomplete_asof": row["segment_priority_year_incomplete_asof"],
            "segment_latest_comparable_year": row["segment_latest_comparable_year"],
            "latest_comparable_year": row["latest_comparable_year"],
            "latest_year": row["latest_year"],
            "latest_year_incomplete": row["latest_year_incomplete"],
            "crowding_label": row["crowding_label"],
            "concentration_role": row["concentration_role"],
            "whitespace_candidate": row["whitespace_candidate"],
            "historical_compare_safe": row["historical_compare_safe"],
            "historical_owner_truth_supported": row["historical_owner_truth_supported"],
            "current_owner_bridge_replayed_to_history": row["current_owner_bridge_replayed_to_history"],
            "historical_oecd_supported": row["historical_oecd_supported"],
        }

    def _map_citation_trend(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        payload: list[dict[str, Any]] = []
        for row in rows:
            payload.append(
                {
                    "as_of_year": self._as_int(row.get("as_of_year")) or 0,
                    "wipo_field": self._normalize_text(row.get("wipo_industry_code")),
                    "citation_event_count": self._as_int(row.get("citation_event_count")) or 0,
                    "citation_count": self._as_float(row.get("citation_count"), 2) or 0.0,
                    "citation_lethality_sum": self._as_float(row.get("citation_lethality_sum_raw"), 2) or 0.0,
                    "distinct_citing_assignee_count": self._as_int(row.get("distinct_citing_assignee_count")) or 0,
                    "distinct_citing_jurisdiction_count": self._as_int(row.get("distinct_citing_jurisdiction_count")) or 0,
                    "citation_pressure_index": self._as_float(row.get("citation_pressure_index"), 2) or 0.0,
                    "market_citation_state": self._normalize_text(row.get("market_citation_state"), "stable"),
                    "market_state_reference": self._normalize_text(row.get("market_state_reference"), "stable"),
                }
            )
        return payload

    def _map_jurisdictions(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        payload: list[dict[str, Any]] = []
        for row in rows:
            payload.append(
                {
                    "as_of_year": self._as_int(row.get("as_of_year")) or 0,
                    "wipo_field": self._normalize_text(row.get("wipo_industry_code")),
                    "jurisdiction_code": self._normalize_text(row.get("jurisdiction_code")),
                    "citation_event_count": self._as_int(row.get("citation_event_count")) or 0,
                    "distinct_citing_assignee_count": self._as_int(row.get("distinct_citing_assignee_count")) or 0,
                    "citation_count": self._as_float(row.get("citation_count"), 2) or 0.0,
                    "citation_lethality_sum": self._as_float(row.get("citation_lethality_sum_raw"), 2) or 0.0,
                    "citation_pressure_index": self._as_float(row.get("citation_pressure_index"), 2) or 0.0,
                }
            )
        return payload

    def _map_attackers(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        payload: list[dict[str, Any]] = []
        for row in rows:
            attacker_name = self._normalize_text(row.get("citing_assignee_name"), "Metadata-only assignee").replace("_", " ")
            payload.append(
                {
                    "as_of_year": self._as_int(row.get("as_of_year")) or 0,
                    "wipo_field": self._normalize_text(row.get("wipo_industry_code")),
                    "citing_assignee": attacker_name,
                    "citation_event_count": self._as_int(row.get("citation_event_count")) or 0,
                    "distinct_citing_jurisdiction_count": self._as_int(row.get("distinct_citing_jurisdiction_count")) or 0,
                    "citation_count": self._as_float(row.get("citation_count"), 2) or 0.0,
                    "citation_lethality_sum": self._as_float(row.get("citation_lethality_sum_raw"), 2) or 0.0,
                    "attacker_pressure_index": self._as_float(row.get("attacker_pressure_index"), 2) or 0.0,
                }
            )
        return payload

    def _map_top_owners(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        payload: list[dict[str, Any]] = []
        for row in rows:
            display_name = self._normalize_text(row.get("owner_name_display_current"), "")
            harmonized = self._normalize_text(row.get("owner_name_harmonized"), "")
            owner_name = display_name or harmonized.replace("_", " ") or "Metadata-only owner bridge"
            share = self._as_float(row.get("in_segment_family_share_hist_proxy"), 4) or 0.0
            payload.append(
                {
                    "as_of_year": self._as_int(row.get("as_of_year")) or 0,
                    "leaderboard_rank": self._as_int(row.get("leaderboard_rank")) or 0,
                    "owner_name": owner_name,
                    "owner_id": harmonized or None,
                    "in_segment_family_count_hist_proxy": self._as_int(row.get("in_segment_family_count_hist_proxy")) or 0,
                    "in_segment_family_share_hist_proxy": share,
                    "avg_blocking_score_asof": self._as_float(row.get("avg_blocking_score_asof"), 2) or 0.0,
                    "total_blocking_score_asof": self._as_float(row.get("total_blocking_score_asof"), 2) or 0.0,
                    "field_presence_weight_asof": self._as_float(row.get("field_presence_weight_asof"), 3) or 0.0,
                    "family_composite_status_asof": self._normalize_text(row.get("family_composite_status_asof"), "n/a"),
                    "concentration_role": self._concentration_role(share),
                }
            )
        return payload

    def _map_segment_cpcs(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        payload: list[dict[str, Any]] = []
        for row in rows:
            payload.append(
                {
                    "as_of_year": self._as_int(row.get("as_of_year")) or 0,
                    "current_snapshot_date": row.get("current_snapshot_date"),
                    "wipo_field": self._normalize_text(row.get("wipo_industry_code")),
                    "cpc_main_group": self._normalize_text(row.get("cpc_main_group")),
                    "cpc_main_group_label": self._normalize_text(row.get("cpc_main_group_label")),
                    "cpc_family_count_asof": self._as_int(row.get("cpc_family_count_asof")) or 0,
                    "cpc_active_family_count_asof": self._as_int(row.get("cpc_active_family_count_asof")) or 0,
                    "cpc_family_share_within_segment_asof": self._as_float(row.get("cpc_family_share_within_segment_asof"), 4)
                    or 0.0,
                    "cpc_active_family_share_within_segment_asof": self._as_float(
                        row.get("cpc_active_family_share_within_segment_asof"), 4
                    )
                    or 0.0,
                    "cpc_blocking_density_asof": self._as_float(row.get("cpc_blocking_density_asof"), 2) or 0.0,
                    "cpc_enforceability_density_asof": self._as_float(row.get("cpc_enforceability_density_asof"), 2)
                    or 0.0,
                    "cpc_pre_asof_forward_citations_clean_avg_asof": self._as_float(
                        row.get("cpc_pre_asof_forward_citations_clean_avg_asof"), 2
                    )
                    or 0.0,
                    "cpc_avg_rcf_score_asof": self._as_float(row.get("cpc_avg_rcf_score_asof"), 2) or 0.0,
                    "cpc_prior_family_count_asof": self._as_int(row.get("cpc_prior_family_count_asof")) or 0,
                    "cpc_growth_index_asof": self._as_float(row.get("cpc_growth_index_asof"), 4) or 0.0,
                    "cpc_heat_state_asof": self._normalize_text(row.get("cpc_heat_state_asof"), "stable"),
                    "cpc_rank_within_segment_year": self._as_int(row.get("cpc_rank_within_segment_year")) or 0,
                    "classification_jurisdiction_support_level": self._normalize_text(
                        row.get("classification_jurisdiction_support_level"), "limited"
                    ),
                }
            )
        return payload

    def _map_global_cpcs(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        payload: list[dict[str, Any]] = []
        for row in rows:
            payload.append(
                {
                    "as_of_year": self._as_int(row.get("as_of_year")) or 0,
                    "current_snapshot_date": row.get("current_snapshot_date"),
                    "cpc_main_group": self._normalize_text(row.get("cpc_main_group")),
                    "cpc_main_group_label": self._normalize_text(row.get("cpc_main_group_label")),
                    "cpc_family_count_asof": self._as_int(row.get("cpc_family_count_asof")) or 0,
                    "cpc_segment_count_asof": self._as_int(row.get("cpc_segment_count_asof")) or 0,
                    "cpc_family_share_global_asof": self._as_float(row.get("cpc_family_share_global_asof"), 4) or 0.0,
                    "cpc_segment_presence_share_asof": self._as_float(row.get("cpc_segment_presence_share_asof"), 4) or 0.0,
                    "cpc_blocking_density_asof": self._as_float(row.get("cpc_blocking_density_asof"), 2) or 0.0,
                    "cpc_enforceability_density_asof": self._as_float(row.get("cpc_enforceability_density_asof"), 2)
                    or 0.0,
                    "cpc_avg_rcf_score_asof": self._as_float(row.get("cpc_avg_rcf_score_asof"), 2) or 0.0,
                    "cpc_growth_index_asof": self._as_float(row.get("cpc_growth_index_asof"), 4) or 0.0,
                    "cpc_importance_score_asof": self._as_float(row.get("cpc_importance_score_asof"), 4) or 0.0,
                    "cpc_importance_band_asof": self._normalize_text(row.get("cpc_importance_band_asof"), "n/a"),
                    "cpc_importance_rank_within_year": self._as_int(row.get("cpc_importance_rank_within_year")) or 0,
                }
            )
        return payload

    def _summarize_forecasts(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        grouped: dict[int, list[dict[str, Any]]] = {}
        for row in rows:
            horizon = self._as_int(row.get("horizon"))
            if horizon is None:
                continue
            grouped.setdefault(horizon, []).append(row)

        summaries: list[dict[str, Any]] = []
        for horizon, forecast_rows in sorted(grouped.items()):
            direction_weights: dict[str, float] = {}
            strength_weights: dict[str, float] = {}
            support_rank = min(self._support_rank(row.get("support_level")) for row in forecast_rows)
            weighted_probability = 0.0
            weighted_growth = 0.0
            total_weight = 0.0
            for row in forecast_rows:
                direction = self._normalize_text(row.get("predicted_direction_band"), "stable")
                strength = self._normalize_text(row.get("trend_strength_band"), "limited")
                filings_weight = max(float(row.get("local_family_filings_asof") or 0.0), 1.0)
                probability = float(row.get("predicted_direction_probability") or 0.0)
                weight = filings_weight * max(probability, 0.05)
                direction_weights[direction] = direction_weights.get(direction, 0.0) + weight
                strength_weights[strength] = strength_weights.get(strength, 0.0) + weight
                weighted_probability += probability * weight
                weighted_growth += float(row.get("predicted_growth_rate_reference") or 0.0) * weight
                total_weight += weight

            if total_weight <= 0:
                total_weight = 1.0

            summaries.append(
                {
                    "horizon": horizon,
                    "as_of_year": self._as_int(forecast_rows[0].get("as_of_year")) or 0,
                    "predicted_direction_band": max(direction_weights.items(), key=lambda item: item[1])[0],
                    "trend_strength_band": max(strength_weights.items(), key=lambda item: item[1])[0],
                    "support_level": next(
                        level for level, rank in SUPPORT_LEVEL_RANK.items() if rank == support_rank
                    ),
                    "predicted_direction_probability": round(weighted_probability / total_weight, 4),
                    "predicted_growth_rate_reference": round(weighted_growth / total_weight, 4),
                    "jurisdiction_count": len(forecast_rows),
                }
            )
        return summaries

    def _state_rationale(self, summary: dict[str, Any], forecast: list[dict[str, Any]]) -> dict[str, Any]:
        market_state = self._normalize_text(summary.get("market_state"), "stable")
        momentum_delta = self._as_float(summary.get("segment_growth_index_asof"), 4) or 0.0
        blocking_density = self._as_float(summary.get("segment_blocking_density_asof"), 2) or 0.0
        top_owner_share = self._as_float(summary.get("segment_top_owner_share_hist_proxy"), 4) or 0.0
        crowding_label = self._normalize_text(summary.get("crowding_label"), "balanced")

        if market_state == "rising":
            headline = "Momentum is still positive inside the current bounded replay window."
        elif market_state == "cooling":
            headline = "Momentum has softened versus the prior comparable year."
        else:
            headline = "The segment is currently reading as stable rather than directionally decisive."

        evidence = [
            f"Priority-year delta: {round(momentum_delta * 100.0, 1)}%.",
            f"Blocking density: {round(blocking_density, 1)}.",
            f"Top-owner share: {round(top_owner_share * 100.0, 1)}% with a {crowding_label} crowding flag.",
        ]
        if forecast:
            near_term = forecast[0]
            evidence.append(
                f"{near_term['horizon']}y overlay: {near_term['predicted_direction_band']} with {near_term['support_level']} support."
            )

        detail = (
            "State labels are explained through bounded family-count chronology first, then tempered by blocking, ownership "
            "concentration, and any forecast overlay support."
        )
        return {
            "headline": headline,
            "detail": detail,
            "evidence": evidence,
        }

    def _serving_release_id(self) -> str | None:
        manifest_path = get_settings().repo_root / "etl" / "data" / "serving" / "serving_snapshot_manifest.json"
        if not manifest_path.exists():
            return None
        try:
            payload = json.loads(manifest_path.read_text())
        except Exception:
            return None
        source_gold_release = payload.get("source_gold_release")
        return str(source_gold_release) if source_gold_release else None

    def _reduced_context_mode(self) -> bool:
        gold_dir = get_settings().repo_root / "etl" / "data" / "gold"
        supporting_paths = [
            gold_dir / "gold_market_summary_pit.parquet",
            gold_dir / "gold_market_leaderboard_pit.parquet",
            gold_dir / "gold_market_citation_trend_pit.parquet",
            gold_dir / "gold_market_citation_pressure_by_jurisdiction_pit.parquet",
            gold_dir / "gold_market_attacker_leaderboard_pit.parquet",
            gold_dir / "gold_market_cpc_trend_pit.parquet",
            gold_dir / "gold_cpc_importance_pit.parquet",
        ]
        return not all(path.exists() for path in supporting_paths)

    def _build_methodology(self, scope: dict[str, Any], release_id: str | None) -> list[dict[str, Any]]:
        return [
            {
                "code": "SCOPE_BOUNDARY",
                "title": "Bounded mega-cluster scope",
                "detail": (
                    "All market metrics are bounded to the approved mega-cluster family universe and should not be read as "
                    "whole-world patent activity."
                ),
            },
            {
                "code": "PIT_LATEST",
                "title": "Current-state PIT serving",
                "detail": (
                    "Density, ownership, and CPC panels use the latest point-in-time slice. Historical trend lines and current-state "
                    "overlays should be interpreted separately."
                ),
            },
            {
                "code": "RELEASE_LINEAGE",
                "title": "Release lineage",
                "detail": (
                    f"Scope {scope['scope_type']} is served from release `{release_id}`."
                    if release_id
                    else "Serving release metadata is not currently attached to the workspace response."
                ),
            },
        ]

    def _build_meta(
        self,
        forecast: list[dict[str, Any]],
        release_id: str | None,
        reduced_context_mode: bool,
    ) -> dict[str, Any]:
        support_level = "limited"
        if forecast:
            support_level = min(
                (self._normalize_text(row.get("support_level"), "limited").lower() for row in forecast),
                key=self._support_rank,
            )

        caveats = [
            {
                "code": "OWNER_HISTORY",
                "title": "Owner history is partially replayed",
                "detail": (
                    "Ownership panels emphasize current display metadata and latest PIT concentration rather than literal historical "
                    "ownership truth."
                ),
            },
            {
                "code": "STATE_RATIONALE",
                "title": "State labels need an evidence path",
                "detail": "Read the market-state chip together with chronology, blocking density, and forecast support rather than in isolation.",
            },
        ]
        if reduced_context_mode:
            caveats.append(
                {
                    "code": "REDUCED_CONTEXT",
                    "title": "Reduced context mode",
                    "detail": "Only the core market marts are available, so owner, blocking, or CPC enrichment may be partially suppressed.",
                }
            )

        return {
            "page": "market_intelligence.workspace",
            "support_level": support_level,
            "release_id": release_id,
            "reduced_context_mode": reduced_context_mode,
            "methodology_path": "/data-room/manifests",
            "state_label_methodology_path": "/data-room/manifests",
            "forecast_overlay_available": bool(forecast),
            "caveats": caveats,
        }

    def get_workspace(self, market_state: str = "all", segment: str | None = None) -> dict[str, Any]:
        normalized_state = (market_state or "all").strip().lower()
        if normalized_state not in ALLOWED_MARKET_STATES:
            raise ValidationError(f"market_state must be one of {', '.join(sorted(ALLOWED_MARKET_STATES))}")

        overview = self._map_overview(self.repo.get_overview())
        scope = self._map_scope(self.repo.get_scope())
        raw_segments = self.repo.get_segments()
        timeseries_map = self._map_segment_timeseries(self.repo.get_timeseries())

        mapped_segments = [
            self._map_segment_row(row, timeseries_map.get(self._normalize_text(row.get("wipo_industry_code")), []))
            for row in raw_segments
        ]

        filtered_segments = (
            mapped_segments if normalized_state == "all" else [row for row in mapped_segments if row["market_state"] == normalized_state]
        )

        selected_segment_code: str | None = None
        if segment:
            candidate = segment.strip()
            if any(row["wipo_industry_code"] == candidate for row in filtered_segments):
                selected_segment_code = candidate

        if selected_segment_code is None and filtered_segments:
            selected_segment_code = filtered_segments[0]["wipo_industry_code"]

        selected_segment_payload: dict[str, Any] | None = None
        selected_forecasts: list[dict[str, Any]] = []
        if selected_segment_code:
            selected_row = next((row for row in filtered_segments if row["wipo_industry_code"] == selected_segment_code), None)
            if selected_row:
                top_owners = self._map_top_owners(self.repo.get_segment_top_owners(selected_segment_code))
                selected_forecasts = self._summarize_forecasts(self.repo.get_segment_forecasts(selected_segment_code))
                selected_segment_payload = {
                    "segment_id": selected_row["segment_id"],
                    "wipo_industry_code": selected_row["wipo_industry_code"],
                    "market_state": selected_row["market_state"],
                    "summary": self._map_selected_summary(selected_row),
                    "timeseries": timeseries_map.get(selected_segment_code, []),
                    "citation_trend": self._map_citation_trend(self.repo.get_segment_citation_trend(selected_segment_code)),
                    "top_jurisdictions": self._map_jurisdictions(self.repo.get_segment_top_jurisdictions(selected_segment_code)),
                    "top_attackers": self._map_attackers(self.repo.get_segment_top_attackers(selected_segment_code)),
                    "top_owners": top_owners,
                    "top_cpcs": self._map_segment_cpcs(self.repo.get_segment_top_cpcs(selected_segment_code)),
                    "forecast": selected_forecasts,
                    "state_rationale": self._state_rationale(selected_row, selected_forecasts),
                    "linked_portfolios": [
                        {"owner_id": row["owner_id"], "owner_name": row["owner_name"]}
                        for row in top_owners
                        if row.get("owner_id")
                    ][:4],
                }

        release_id = self._serving_release_id()
        reduced_context_mode = self._reduced_context_mode()
        methodology = self._build_methodology(scope, release_id)

        return {
            "identity": {
                "id": "market-intelligence",
                "label": "Market Intelligence",
                "page_kind": "market_intelligence",
                "selected_year": scope["latest_comparable_market_year"],
            },
            "scope": scope,
            "overview": overview,
            "filters": {
                "market_state": normalized_state,
                "state_options": self._map_state_options(mapped_segments),
                "segment_options": self._map_segment_options(filtered_segments),
                "selected_segment": selected_segment_code,
            },
            "segments": filtered_segments,
            "selected_segment": selected_segment_payload,
            "global_cpc_importance": self._map_global_cpcs(self.repo.get_global_cpc_importance()),
            "methodology": methodology,
            "meta": self._build_meta(selected_forecasts, release_id, reduced_context_mode),
        }
