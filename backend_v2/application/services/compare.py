from __future__ import annotations

from typing import Any

from domain.schemas.common import Caveat, PageIdentity, ResponseMeta
from domain.schemas.compare import (
    CompareFamilySuggestion,
    CompareFamilySuggestionResponse,
    CompareResponse,
    CompareScopeLookupResponse,
    CompareTimesliceOptionsResponse,
)
from infrastructure.repositories.family_repository import FamilyRepository
from infrastructure.repositories.portfolio_repository import PortfolioRepository


class CompareService:
    def __init__(
        self,
        portfolio_repository: PortfolioRepository | None = None,
        family_repository: FamilyRepository | None = None,
    ) -> None:
        self.portfolio_repository = portfolio_repository or PortfolioRepository()
        self.family_repository = family_repository or FamilyRepository()

    def _to_float(self, value: Any, default: float = 0.0) -> float:
        if value is None:
            return default
        try:
            candidate = float(value)
            return candidate if candidate == candidate else default
        except (TypeError, ValueError):
            return default

    def _to_int(self, value: Any, default: int = 0) -> int:
        if value is None:
            return default
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    def _to_optional_int(self, value: Any) -> int | None:
        if value is None:
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def _to_str(self, value: Any, default: str = "") -> str:
        if value is None:
            return default
        text = str(value).strip()
        return text if text else default

    def _portfolio_peer_bucket_label(self, bucket_code: str | None) -> str | None:
        labels = {
            "1": "1 family",
            "2_5": "2-5 families",
            "6_20": "6-20 families",
            "21_100": "21-100 families",
            "101_500": "101-500 families",
            "501_plus": "501+ families",
        }
        if bucket_code is None:
            return None
        return labels.get(str(bucket_code).strip())

    def _band_code_from_percentile(self, percentile: Any) -> str | None:
        if percentile is None:
            return None
        score = self._to_float(percentile, default=-1.0)
        if score < 0.0:
            return None
        if score < 25.0:
            return "low"
        if score < 50.0:
            return "medium"
        if score < 75.0:
            return "high"
        return "very_high"

    def _portfolio_metric_band_label(self, metric_key: str, band_code: str | None) -> str | None:
        labels = {
            "portfolio_total_mass_score": {
                "low": "Light Footprint",
                "medium": "Meaningful Footprint",
                "high": "Heavy Footprint",
                "very_high": "Outsize Footprint",
            },
            "portfolio_current_threat_score": {
                "low": "Low Pressure",
                "medium": "Moderate Pressure",
                "high": "High Pressure",
                "very_high": "Severe Pressure",
            },
            "portfolio_heritage_score": {
                "low": "Thin Heritage",
                "medium": "Established Heritage",
                "high": "Deep Heritage",
                "very_high": "Foundational Heritage",
            },
            "portfolio_hit_rate_top_decile": {
                "low": "Sparse",
                "medium": "Selective",
                "high": "Broad",
                "very_high": "Dense",
            },
            "portfolio_crown_jewel_index": {
                "low": "Limited Arsenal",
                "medium": "Competitive Arsenal",
                "high": "Elite Arsenal",
                "very_high": "Dominant Arsenal",
            },
        }
        if band_code is None:
            return None
        return labels.get(metric_key, {}).get(band_code)

    def _family_metric_band_label(self, metric_key: str, band_code: str | None) -> str | None:
        labels = {
            "family_ui_blocking_power_score": {
                "low": "Limited",
                "medium": "Established",
                "high": "Strong",
                "very_high": "Leading",
            },
            "family_enforceability_score_asof": {
                "low": "Fragile",
                "medium": "Mixed",
                "high": "Durable",
                "very_high": "Highly Durable",
            },
            "citation_heritage": {
                "low": "Thin",
                "medium": "Established",
                "high": "Deep",
                "very_high": "Foundational",
            },
        }
        if band_code is None:
            return None
        return labels.get(metric_key, {}).get(band_code)

    def _portfolio_metric_band_meta(
        self,
        peer_context: dict[str, object],
        metric_key: str,
        percentile_key: str,
    ) -> dict[str, object]:
        percentile = peer_context.get(percentile_key)
        band_code = self._band_code_from_percentile(percentile)
        if band_code is None:
            return {}
        peer_bucket = self._to_str(peer_context.get("peer_bucket"), "")
        peer_bucket_label = self._portfolio_peer_bucket_label(peer_bucket)
        return {
            "band_code": band_code,
            "band_label": self._portfolio_metric_band_label(metric_key, band_code),
            "peer_bucket": peer_bucket or None,
            "peer_bucket_label": peer_bucket_label,
            "peer_percentile": round(self._to_float(percentile, 0.0), 1),
        }

    def _winner_from_values(self, left_value: Any, right_value: Any) -> str | None:
        left_score = self._to_float(left_value, 0.0)
        right_score = self._to_float(right_value, 0.0)
        if left_score > right_score:
            return "left"
        if right_score > left_score:
            return "right"
        return "tie"

    def _winner_from_bands(
        self,
        left_band_code: str | None,
        right_band_code: str | None,
    ) -> str | None:
        order = {"low": 0, "medium": 1, "high": 2, "very_high": 3}
        if left_band_code not in order or right_band_code not in order:
            return None
        left_rank = order[left_band_code]
        right_rank = order[right_band_code]
        if left_rank > right_rank:
            return "left"
        if right_rank > left_rank:
            return "right"
        return "tie"

    def _family_metric_band_meta(
        self,
        metric_key: str,
        percentile: Any,
        cohort_code: str | None,
        cohort_label: str | None,
    ) -> dict[str, object]:
        band_code = self._band_code_from_percentile(percentile)
        if band_code is None:
            return {}
        return {
            "band_code": band_code,
            "band_label": self._family_metric_band_label(metric_key, band_code),
            "peer_percentile": round(self._to_float(percentile, 0.0), 1),
            "peer_cohort": cohort_code,
            "peer_cohort_label": cohort_label,
        }

    def _optional_repo_call(self, repository: Any, method_name: str, default: Any, *args: Any, **kwargs: Any) -> Any:
        method = getattr(repository, method_name, None)
        if not callable(method):
            return default
        return method(*args, **kwargs)

    def _to_optional_float(self, value: Any) -> float | None:
        if value is None:
            return None
        try:
            candidate = float(value)
            return candidate if candidate == candidate else None
        except (TypeError, ValueError):
            return None

    def _metric_row(
        self,
        *,
        key: str,
        label: str,
        display_kind: str,
        left_value: Any,
        right_value: Any,
        left_note: str | None = None,
        right_note: str | None = None,
        note: str | None = None,
        winner: str | None = None,
        winner_basis: str | None = None,
    ) -> dict[str, object]:
        delta_value: float | None = None
        left_numeric = self._to_optional_float(left_value)
        right_numeric = self._to_optional_float(right_value)
        if left_numeric is not None and right_numeric is not None and display_kind != "text":
            delta_value = round(left_numeric - right_numeric, 4)
        return {
            "key": key,
            "label": label,
            "display_kind": display_kind,
            "left_value": left_value,
            "right_value": right_value,
            "delta_value": delta_value,
            "left_note": left_note,
            "right_note": right_note,
            "note": note,
            "winner": winner,
            "winner_basis": winner_basis,
        }

    def _identity_context_row(
        self,
        *,
        side: str,
        title: str,
        subtitle: str | None = None,
        badges: list[str] | None = None,
        href: str | None = None,
    ) -> dict[str, object]:
        return {
            "side": side,
            "title": title,
            "subtitle": subtitle,
            "badges": [badge for badge in (badges or []) if badge],
            "href": href,
        }

    def _range_overlap_state(
        self,
        left_low: float | None,
        left_high: float | None,
        right_low: float | None,
        right_high: float | None,
    ) -> str:
        if None in (left_low, left_high, right_low, right_high):
            return "partial"
        return "overlap" if max(left_low, right_low) <= min(left_high, right_high) else "separate"

    def _presence_state(self, left_value: float, right_value: float) -> str:
        if left_value > 0 and right_value > 0:
            return "shared"
        if left_value > 0:
            return "left_only"
        if right_value > 0:
            return "right_only"
        return "empty"

    def _field_overlap_row(
        self,
        *,
        key: str,
        label: str,
        left_share: float,
        right_share: float,
        left_rank: int | None,
        right_rank: int | None,
        left_note: str | None = None,
        right_note: str | None = None,
    ) -> dict[str, object]:
        return {
            "key": key,
            "label": label,
            "left_share": round(left_share, 6),
            "right_share": round(right_share, 6),
            "overlap_share": round(min(left_share, right_share), 6),
            "left_rank": left_rank,
            "right_rank": right_rank,
            "presence": self._presence_state(left_share, right_share),
            "left_note": left_note,
            "right_note": right_note,
        }

    def _build_family_field_overlap_rows(
        self,
        left_rows: list[dict[str, object]],
        right_rows: list[dict[str, object]],
        limit: int = 8,
    ) -> list[dict[str, object]]:
        left_map: dict[str, dict[str, object]] = {}
        right_map: dict[str, dict[str, object]] = {}
        for index, row in enumerate(left_rows, start=1):
            field = self._to_str(row.get("wipo_industry_code") or row.get("field") or row.get("primary_wipo_field"), "Unknown")
            if field not in left_map:
                left_map[field] = {"rank": index, **row}
        for index, row in enumerate(right_rows, start=1):
            field = self._to_str(row.get("wipo_industry_code") or row.get("field") or row.get("primary_wipo_field"), "Unknown")
            if field not in right_map:
                right_map[field] = {"rank": index, **row}

        ranked_fields = sorted(
            set(left_map) | set(right_map),
            key=lambda field: (
                max(
                    self._to_float(left_map.get(field, {}).get("base_fraction"), 0.0),
                    self._to_float(right_map.get(field, {}).get("base_fraction"), 0.0),
                ),
                min(
                    self._to_float(left_map.get(field, {}).get("base_fraction"), 0.0),
                    self._to_float(right_map.get(field, {}).get("base_fraction"), 0.0),
                ),
                field,
            ),
            reverse=True,
        )

        rows: list[dict[str, object]] = []
        for field in ranked_fields[:limit]:
            left_row = left_map.get(field, {})
            right_row = right_map.get(field, {})
            rows.append(
                self._field_overlap_row(
                    key=field.lower().replace(" ", "_"),
                    label=field,
                    left_share=self._to_float(left_row.get("base_fraction"), 0.0),
                    right_share=self._to_float(right_row.get("base_fraction"), 0.0),
                    left_rank=self._to_int(left_row.get("rank"), 0) or None,
                    right_rank=self._to_int(right_row.get("rank"), 0) or None,
                    left_note=f"heritage {self._to_float(left_row.get('heritage_contribution_score'), 0.0):.2f}" if left_row else None,
                    right_note=f"heritage {self._to_float(right_row.get('heritage_contribution_score'), 0.0):.2f}" if right_row else None,
                )
            )
        return rows

    def _build_portfolio_field_overlap_rows(
        self,
        left_rows: list[dict[str, object]],
        right_rows: list[dict[str, object]],
        limit: int = 8,
    ) -> list[dict[str, object]]:
        left_map: dict[str, dict[str, object]] = {}
        right_map: dict[str, dict[str, object]] = {}
        for index, row in enumerate(left_rows, start=1):
            field = self._to_str(row.get("field"), "Unknown")
            if field not in left_map:
                left_map[field] = {"rank": index, **row}
        for index, row in enumerate(right_rows, start=1):
            field = self._to_str(row.get("field"), "Unknown")
            if field not in right_map:
                right_map[field] = {"rank": index, **row}

        ranked_fields = sorted(
            set(left_map) | set(right_map),
            key=lambda field: (
                max(
                    self._to_float(left_map.get(field, {}).get("active_share"), 0.0),
                    self._to_float(right_map.get(field, {}).get("active_share"), 0.0),
                ),
                min(
                    self._to_float(left_map.get(field, {}).get("active_share"), 0.0),
                    self._to_float(right_map.get(field, {}).get("active_share"), 0.0),
                ),
                field,
            ),
            reverse=True,
        )

        rows: list[dict[str, object]] = []
        for field in ranked_fields[:limit]:
            left_row = left_map.get(field, {})
            right_row = right_map.get(field, {})
            rows.append(
                self._field_overlap_row(
                    key=field.lower().replace(" ", "_"),
                    label=field,
                    left_share=self._to_float(left_row.get("active_share"), 0.0),
                    right_share=self._to_float(right_row.get("active_share"), 0.0),
                    left_rank=self._to_int(left_row.get("rank"), 0) or None,
                    right_rank=self._to_int(right_row.get("rank"), 0) or None,
                    left_note=self._to_str(left_row.get("hotspot_direction")) or None,
                    right_note=self._to_str(right_row.get("hotspot_direction")) or None,
                )
            )
        return rows

    def _build_family_forecast_rows(
        self,
        left_rows: list[dict[str, object]],
        right_rows: list[dict[str, object]],
    ) -> list[dict[str, object]]:
        left_by_horizon = {self._to_str(row.get("horizon"), "unknown"): row for row in left_rows}
        right_by_horizon = {self._to_str(row.get("horizon"), "unknown"): row for row in right_rows}
        ordered_horizons = sorted(set(left_by_horizon) | set(right_by_horizon), key=lambda value: (value.replace("y", "").replace("m", ""), value))
        rows: list[dict[str, object]] = []
        for horizon in ordered_horizons:
            left_row = left_by_horizon.get(horizon, {})
            right_row = right_by_horizon.get(horizon, {})
            left_low = self._to_optional_float(left_row.get("interval_lower"))
            left_high = self._to_optional_float(left_row.get("interval_upper"))
            right_low = self._to_optional_float(right_row.get("interval_lower"))
            right_high = self._to_optional_float(right_row.get("interval_upper"))
            rows.append(
                {
                    "key": f"family_forecast_{horizon}",
                    "label": f"{horizon} citation outlook",
                    "display_kind": "decimal",
                    "left_value": self._to_optional_float(left_row.get("point_forecast")),
                    "right_value": self._to_optional_float(right_row.get("point_forecast")),
                    "left_range_low": left_low,
                    "left_range_high": left_high,
                    "right_range_low": right_low,
                    "right_range_high": right_high,
                    "left_note": self._to_str(left_row.get("selected_variant")) or None,
                    "right_note": self._to_str(right_row.get("selected_variant")) or None,
                    "overlap_state": self._range_overlap_state(left_low, left_high, right_low, right_high),
                    "note": "Directional interval-first Phase 03 family forecast.",
                }
            )
        return rows

    def _build_portfolio_forecast_rows(
        self,
        left_summary: dict[str, object],
        right_summary: dict[str, object],
    ) -> list[dict[str, object]]:
        rows: list[dict[str, object]] = []
        for horizon in ("3y", "5y"):
            suffix = horizon
            left_low = self._to_optional_float(left_summary.get(f"portfolio_expected_future_citations_lower_{suffix}"))
            left_high = self._to_optional_float(left_summary.get(f"portfolio_expected_future_citations_upper_{suffix}"))
            right_low = self._to_optional_float(right_summary.get(f"portfolio_expected_future_citations_lower_{suffix}"))
            right_high = self._to_optional_float(right_summary.get(f"portfolio_expected_future_citations_upper_{suffix}"))
            rows.append(
                {
                    "key": f"portfolio_forecast_{horizon}",
                    "label": f"{horizon} future citations",
                    "display_kind": "decimal",
                    "left_value": self._to_optional_float(left_summary.get(f"portfolio_expected_future_citations_total_{suffix}")),
                    "right_value": self._to_optional_float(right_summary.get(f"portfolio_expected_future_citations_total_{suffix}")),
                    "left_range_low": left_low,
                    "left_range_high": left_high,
                    "right_range_low": right_low,
                    "right_range_high": right_high,
                    "left_note": f"coverage {round(self._to_float(left_summary.get(f'portfolio_phase03_feature_completeness_pct_{suffix}'), 0.0) * 100.0, 1)}%",
                    "right_note": f"coverage {round(self._to_float(right_summary.get(f'portfolio_phase03_feature_completeness_pct_{suffix}'), 0.0) * 100.0, 1)}%",
                    "overlap_state": self._range_overlap_state(left_low, left_high, right_low, right_high),
                    "note": "Bottom-up portfolio future-citation interval from the forecast summary mart.",
                }
            )
        return rows

    def _top_support_row(
        self,
        *,
        kind: str,
        side: str,
        title: str,
        subtitle: str | None = None,
        badge: str | None = None,
        primary_metric_label: str | None = None,
        primary_metric_value: Any = None,
        secondary_metric_label: str | None = None,
        secondary_metric_value: Any = None,
        href: str | None = None,
    ) -> dict[str, object]:
        return {
            "kind": kind,
            "side": side,
            "title": title,
            "subtitle": subtitle,
            "badge": badge,
            "primary_metric_label": primary_metric_label,
            "primary_metric_value": primary_metric_value,
            "secondary_metric_label": secondary_metric_label,
            "secondary_metric_value": secondary_metric_value,
            "href": href,
        }

    def _timeslice_pair(
        self,
        rows: list[dict[str, object]],
    ) -> tuple[dict[str, object], dict[str, object]]:
        ordered = sorted(rows, key=lambda row: self._to_int(row.get("as_of_year"), 0), reverse=True)
        if len(ordered) < 2:
            return {}, {}
        return ordered[0], ordered[1]

    def _support_badge(self, value: Any, positive: str, fallback: str) -> str:
        return positive if bool(value) else fallback

    def get_family_compare(
        self,
        left_family_id: str | None = None,
        right_family_id: str | None = None,
    ) -> CompareResponse:
        contexts = self.family_repository.get_family_compare_contexts([left_family_id, right_family_id])
        left_context = contexts.get(self._to_str(left_family_id), {}) if left_family_id else {}
        right_context = contexts.get(self._to_str(right_family_id), {}) if right_family_id else {}

        left_identity = (
            PageIdentity(
                id=self._to_str(left_context.get("docdb_family_id"), left_family_id or ""),
                label=f"Family {self._to_str(left_context.get('docdb_family_id'), left_family_id or '')}",
                page_kind="family",
            )
            if left_family_id
            else None
        )
        right_identity = (
            PageIdentity(
                id=self._to_str(right_context.get("docdb_family_id"), right_family_id or ""),
                label=f"Family {self._to_str(right_context.get('docdb_family_id'), right_family_id or '')}",
                page_kind="family",
            )
            if right_family_id
            else None
        )

        if not left_context or not right_context:
            return CompareResponse(
                compare_kind="families",
                left_entity=left_identity if left_context else None,
                right_entity=right_identity if right_context else None,
                rows=[],
                meta=ResponseMeta(
                    page="compare.families",
                    artifact_sources=[str(path) for path in self.family_repository.artifacts()],
                    caveats=[
                        Caveat(
                            code="family_compare_unavailable",
                            title="Family compare unavailable",
                            detail="One or both family ids could not be resolved in the current family serving marts.",
                        )
                    ],
                ),
            )

        rows: list[dict[str, str | int | float | bool | None]] = []
        caveats = [
            Caveat(
                code="family_compare_lenses",
                title="Three family compare lenses",
                detail="Family compare separates blocking posture, legal durability, and citation heritage instead of collapsing them into one blended score.",
            ),
            Caveat(
                code="field_relative_blocking",
                title="Blocking is field-relative",
                detail="Blocking posture comes from the rebuilt UI blocking score, which is already normalized within primary WIPO field cohorts.",
            ),
        ]

        blocking_left_field = self._to_str(
            left_context.get("primary_wipo_field_current") or left_context.get("primary_wipo_field"),
            "unknown",
        )
        blocking_right_field = self._to_str(
            right_context.get("primary_wipo_field_current") or right_context.get("primary_wipo_field"),
            "unknown",
        )
        legal_left_field = self._to_str(left_context.get("primary_wipo_field_current") or left_context.get("primary_wipo_field"), "unknown")
        legal_right_field = self._to_str(right_context.get("primary_wipo_field_current") or right_context.get("primary_wipo_field"), "unknown")
        legal_left_status = self._to_str(left_context.get("family_composite_status_asof") or left_context.get("family_composite_status"), "unknown")
        legal_right_status = self._to_str(right_context.get("family_composite_status_asof") or right_context.get("family_composite_status"), "unknown")
        citation_left_field = self._to_str(left_context.get("primary_wipo_field"), "unknown")
        citation_right_field = self._to_str(right_context.get("primary_wipo_field"), "unknown")
        citation_left_year = self._to_int(left_context.get("family_priority_year"), 0)
        citation_right_year = self._to_int(right_context.get("family_priority_year"), 0)

        lenses = [
            {
                "lens": "blocking_posture",
                "label": "Blocking Posture",
                "metric_key": "family_ui_blocking_power_score",
                "metric_label": "Blocking Power Score",
                "left_raw_value": self._to_float(left_context.get("family_ui_blocking_power_score"), 0.0),
                "right_raw_value": self._to_float(right_context.get("family_ui_blocking_power_score"), 0.0),
                "left_percentile": self._to_float(left_context.get("family_ui_blocking_power_score"), 0.0),
                "right_percentile": self._to_float(right_context.get("family_ui_blocking_power_score"), 0.0),
                "left_peer_cohort": blocking_left_field,
                "right_peer_cohort": blocking_right_field,
                "left_peer_cohort_label": blocking_left_field,
                "right_peer_cohort_label": blocking_right_field,
                "same_cohort": blocking_left_field == blocking_right_field,
            },
            {
                "lens": "legal_durability",
                "label": "Legal Durability",
                "metric_key": "family_enforceability_score_asof",
                "metric_label": "Enforceability Score",
                "left_raw_value": self._to_float(left_context.get("family_enforceability_score_asof"), 0.0),
                "right_raw_value": self._to_float(right_context.get("family_enforceability_score_asof"), 0.0),
                "left_percentile": self._to_float(left_context.get("legal_durability_percentile"), 0.0),
                "right_percentile": self._to_float(right_context.get("legal_durability_percentile"), 0.0),
                "left_peer_cohort": f"{legal_left_field}|{legal_left_status}",
                "right_peer_cohort": f"{legal_right_field}|{legal_right_status}",
                "left_peer_cohort_label": f"{legal_left_field} / {legal_left_status}",
                "right_peer_cohort_label": f"{legal_right_field} / {legal_right_status}",
                "same_cohort": legal_left_field == legal_right_field and legal_left_status == legal_right_status,
            },
            {
                "lens": "citation_heritage",
                "label": "Citation Heritage",
                "metric_key": "citation_heritage",
                "metric_label": "Weighted Forward Citation Heritage",
                "left_raw_value": self._to_float(
                    left_context.get("pre_asof_forward_citations_weighted") or left_context.get("oecd_quality_proxy_score"),
                    0.0,
                ),
                "right_raw_value": self._to_float(
                    right_context.get("pre_asof_forward_citations_weighted") or right_context.get("oecd_quality_proxy_score"),
                    0.0,
                ),
                "left_percentile": self._to_float(left_context.get("citation_heritage_percentile"), 0.0),
                "right_percentile": self._to_float(right_context.get("citation_heritage_percentile"), 0.0),
                "left_peer_cohort": f"{citation_left_year}|{citation_left_field}",
                "right_peer_cohort": f"{citation_right_year}|{citation_right_field}",
                "left_peer_cohort_label": f"{citation_left_year} / {citation_left_field}",
                "right_peer_cohort_label": f"{citation_right_year} / {citation_right_field}",
                "same_cohort": citation_left_year == citation_right_year and citation_left_field == citation_right_field,
            },
        ]

        if any(not bool(lens["same_cohort"]) for lens in lenses):
            caveats.append(
                Caveat(
                    code="cross_cohort_family_compare",
                    title="Cross-cohort family compare",
                    detail="At least one family lens compares different cohorts. In those cases the band is safer than a direct percentile winner claim.",
                )
            )
        if any(
            self._to_float(context.get("pre_asof_forward_citations_weighted"), -1.0) < 0.0
            and self._to_float(context.get("oecd_quality_proxy_score"), -1.0) >= 0.0
            for context in (left_context, right_context)
        ):
            caveats.append(
                Caveat(
                    code="citation_proxy_fallback",
                    title="Citation proxy fallback",
                detail="Citation heritage falls back to OECD-quality proxy evidence when weighted forward citation history is incomplete in the current compare mart.",
                )
            )

        family_field_rows_left = self._optional_repo_call(
            self.family_repository,
            "get_family_field_rows",
            [],
            left_family_id,
        )
        family_field_rows_right = self._optional_repo_call(
            self.family_repository,
            "get_family_field_rows",
            [],
            right_family_id,
        )
        family_forecast_rows_left = self._optional_repo_call(
            self.family_repository,
            "get_family_forecasts",
            [],
            left_family_id,
        )
        family_forecast_rows_right = self._optional_repo_call(
            self.family_repository,
            "get_family_forecasts",
            [],
            right_family_id,
        )
        family_jurisdiction_rows_left = self._optional_repo_call(
            self.family_repository,
            "get_family_jurisdiction_legal_rows",
            [],
            left_family_id,
        )
        family_jurisdiction_rows_right = self._optional_repo_call(
            self.family_repository,
            "get_family_jurisdiction_legal_rows",
            [],
            right_family_id,
        )

        for lens in lenses:
            left_band = self._family_metric_band_meta(
                metric_key=str(lens["metric_key"]),
                percentile=lens["left_percentile"],
                cohort_code=self._to_str(lens["left_peer_cohort"]),
                cohort_label=self._to_str(lens["left_peer_cohort_label"]),
            )
            right_band = self._family_metric_band_meta(
                metric_key=str(lens["metric_key"]),
                percentile=lens["right_percentile"],
                cohort_code=self._to_str(lens["right_peer_cohort"]),
                cohort_label=self._to_str(lens["right_peer_cohort_label"]),
            )
            same_cohort = bool(lens["same_cohort"])
            comparison_mode = "same_cohort_percentile" if same_cohort else "cross_cohort_band_first"
            winner: str | None = None
            winner_basis: str | None = None
            if same_cohort:
                winner = self._winner_from_values(left_band.get("peer_percentile"), right_band.get("peer_percentile"))
                winner_basis = "peer_percentile"
            else:
                winner = self._winner_from_bands(
                    self._to_str(left_band.get("band_code")) or None,
                    self._to_str(right_band.get("band_code")) or None,
                )
                if winner and winner != "tie":
                    winner_basis = "band"

            rows.append(
                {
                    "kind": "lens",
                    "lens": str(lens["lens"]),
                    "label": str(lens["label"]),
                    "metric_key": str(lens["metric_key"]),
                    "metric_label": str(lens["metric_label"]),
                    "left_family_id": left_identity.id,
                    "left_family_label": left_identity.label,
                    "left_raw_value": self._to_float(lens["left_raw_value"], 0.0),
                    "left_band_code": self._to_str(left_band.get("band_code")) or None,
                    "left_band_label": self._to_str(left_band.get("band_label")) or None,
                    "left_peer_percentile": left_band.get("peer_percentile"),
                    "left_peer_cohort": self._to_str(left_band.get("peer_cohort")) or None,
                    "left_peer_cohort_label": self._to_str(left_band.get("peer_cohort_label")) or None,
                    "right_family_id": right_identity.id,
                    "right_family_label": right_identity.label,
                    "right_raw_value": self._to_float(lens["right_raw_value"], 0.0),
                    "right_band_code": self._to_str(right_band.get("band_code")) or None,
                    "right_band_label": self._to_str(right_band.get("band_label")) or None,
                    "right_peer_percentile": right_band.get("peer_percentile"),
                    "right_peer_cohort": self._to_str(right_band.get("peer_cohort")) or None,
                    "right_peer_cohort_label": self._to_str(right_band.get("peer_cohort_label")) or None,
                    "same_cohort": same_cohort,
                    "comparison_mode": comparison_mode,
                    "winner": winner,
                    "winner_basis": winner_basis,
                }
            )

        caveats.append(
            Caveat(
                code="family_bands_secondary",
                title="Bands are secondary evidence",
                detail="Family bands help summarize posture, but exact legal status, active-jurisdiction evidence, and raw citation history remain the analyst-grade source evidence.",
            )
        )

        lens_by_key = {self._to_str(row.get("lens")): row for row in rows}
        forecast_3y_left = next((row for row in family_forecast_rows_left if self._to_str(row.get("horizon")) == "3y"), {})
        forecast_3y_right = next((row for row in family_forecast_rows_right if self._to_str(row.get("horizon")) == "3y"), {})

        identity_context = [
            self._identity_context_row(
                side="left",
                title=left_identity.label,
                subtitle=f"{blocking_left_field} / {legal_left_status}",
                badges=[
                    f"Priority {citation_left_year}" if citation_left_year else "",
                    f"{self._to_int(left_context.get('family_size_docdb'), 0)} members",
                    f"{self._to_int(left_context.get('active_jurisdiction_count') or left_context.get('family_jurisdiction_count_asof'), 0)} active jurisdictions",
                ],
                href=f"/family/{left_identity.id}",
            ),
            self._identity_context_row(
                side="right",
                title=right_identity.label,
                subtitle=f"{blocking_right_field} / {legal_right_status}",
                badges=[
                    f"Priority {citation_right_year}" if citation_right_year else "",
                    f"{self._to_int(right_context.get('family_size_docdb'), 0)} members",
                    f"{self._to_int(right_context.get('active_jurisdiction_count') or right_context.get('family_jurisdiction_count_asof'), 0)} active jurisdictions",
                ],
                href=f"/family/{right_identity.id}",
            ),
        ]

        summary_cards = [
            self._metric_row(
                key="family_size",
                label="Family size",
                display_kind="count",
                left_value=self._to_int(left_context.get("family_size_docdb"), 0),
                right_value=self._to_int(right_context.get("family_size_docdb"), 0),
                note="DOCDB family member count.",
                winner=self._winner_from_values(left_context.get("family_size_docdb"), right_context.get("family_size_docdb")),
                winner_basis="count",
            ),
            self._metric_row(
                key="blocking_posture",
                label="Blocking posture",
                display_kind="decimal",
                left_value=lens_by_key.get("blocking_posture", {}).get("left_raw_value"),
                right_value=lens_by_key.get("blocking_posture", {}).get("right_raw_value"),
                left_note=self._to_str(lens_by_key.get("blocking_posture", {}).get("left_band_label")) or None,
                right_note=self._to_str(lens_by_key.get("blocking_posture", {}).get("right_band_label")) or None,
                note="Field-relative blocking posture from the compare mart.",
                winner=self._to_str(lens_by_key.get("blocking_posture", {}).get("winner")) or None,
                winner_basis=self._to_str(lens_by_key.get("blocking_posture", {}).get("winner_basis")) or None,
            ),
            self._metric_row(
                key="legal_durability",
                label="Legal durability score",
                display_kind="decimal",
                left_value=lens_by_key.get("legal_durability", {}).get("left_peer_percentile"),
                right_value=lens_by_key.get("legal_durability", {}).get("right_peer_percentile"),
                left_note=self._to_str(lens_by_key.get("legal_durability", {}).get("left_band_label")) or None,
                right_note=self._to_str(lens_by_key.get("legal_durability", {}).get("right_band_label")) or None,
                note="Current legal durability percentile within the compare-safe field and lifecycle cohort.",
                winner=self._to_str(lens_by_key.get("legal_durability", {}).get("winner")) or None,
                winner_basis=self._to_str(lens_by_key.get("legal_durability", {}).get("winner_basis")) or None,
            ),
            self._metric_row(
                key="citation_heritage",
                label="Citation heritage",
                display_kind="decimal",
                left_value=lens_by_key.get("citation_heritage", {}).get("left_raw_value"),
                right_value=lens_by_key.get("citation_heritage", {}).get("right_raw_value"),
                left_note=self._to_str(lens_by_key.get("citation_heritage", {}).get("left_band_label")) or None,
                right_note=self._to_str(lens_by_key.get("citation_heritage", {}).get("right_band_label")) or None,
                note="Weighted forward-citation heritage, with proxy fallback caveated where needed.",
                winner=self._to_str(lens_by_key.get("citation_heritage", {}).get("winner")) or None,
                winner_basis=self._to_str(lens_by_key.get("citation_heritage", {}).get("winner_basis")) or None,
            ),
            self._metric_row(
                key="future_outlook_3y",
                label="3y citation outlook",
                display_kind="decimal",
                left_value=self._to_optional_float(forecast_3y_left.get("point_forecast")),
                right_value=self._to_optional_float(forecast_3y_right.get("point_forecast")),
                left_note=self._to_str(forecast_3y_left.get("selected_variant")) or None,
                right_note=self._to_str(forecast_3y_right.get("selected_variant")) or None,
                note="Directional interval-first family forecast midpoint.",
                winner=self._winner_from_values(forecast_3y_left.get("point_forecast"), forecast_3y_right.get("point_forecast")),
                winner_basis="forecast_midpoint",
            ),
        ]

        contrast_rows = [
            self._metric_row(
                key="current_status",
                label="Current status",
                display_kind="text",
                left_value=legal_left_status,
                right_value=legal_right_status,
                note="Current family composite status from compare-safe current serving.",
            ),
            self._metric_row(
                key="active_jurisdictions",
                label="Active jurisdictions",
                display_kind="count",
                left_value=self._to_int(left_context.get("active_jurisdiction_count") or left_context.get("family_jurisdiction_count_asof"), 0),
                right_value=self._to_int(right_context.get("active_jurisdiction_count") or right_context.get("family_jurisdiction_count_asof"), 0),
                note="Active branch or active-jurisdiction footprint.",
                winner=self._winner_from_values(
                    left_context.get("active_jurisdiction_count") or left_context.get("family_jurisdiction_count_asof"),
                    right_context.get("active_jurisdiction_count") or right_context.get("family_jurisdiction_count_asof"),
                ),
                winner_basis="count",
            ),
            self._metric_row(
                key="quality_proxy",
                label="OECD quality proxy",
                display_kind="decimal",
                left_value=self._to_optional_float(left_context.get("oecd_quality_proxy_score")),
                right_value=self._to_optional_float(right_context.get("oecd_quality_proxy_score")),
                note="Fallback-ready quality proxy used only as supporting evidence.",
                winner=self._winner_from_values(left_context.get("oecd_quality_proxy_score"), right_context.get("oecd_quality_proxy_score")),
                winner_basis="proxy_score",
            ),
            self._metric_row(
                key="data_completeness",
                label="Data completeness",
                display_kind="percent",
                left_value=self._to_optional_float(left_context.get("data_completeness_pct_asof")),
                right_value=self._to_optional_float(right_context.get("data_completeness_pct_asof")),
                note="Observed completeness of the PIT-safe compare context.",
                winner=self._winner_from_values(left_context.get("data_completeness_pct_asof"), right_context.get("data_completeness_pct_asof")),
                winner_basis="coverage",
            ),
        ]

        field_overlap_rows = self._build_family_field_overlap_rows(
            family_field_rows_left,
            family_field_rows_right,
        )
        forecast_rows = self._build_family_forecast_rows(
            family_forecast_rows_left,
            family_forecast_rows_right,
        )

        support_rows: list[dict[str, object]] = []
        for side, jurisdiction_rows in (("left", family_jurisdiction_rows_left), ("right", family_jurisdiction_rows_right)):
            for row in jurisdiction_rows[:4]:
                jurisdiction = self._to_str(row.get("jurisdiction_code"), "Unknown")
                support_rows.append(
                    self._top_support_row(
                        kind="jurisdiction_preview",
                        side=side,
                        title=jurisdiction,
                        subtitle=self._to_str(row.get("dominant_wipo_field")) or self._to_str(row.get("branch_state_label")) or None,
                        badge=self._to_str(row.get("jurisdiction_relative_enforceability_band")) or None,
                        primary_metric_label="Family share",
                        primary_metric_value=self._to_optional_float(row.get("jurisdiction_enforceability_share_of_family")),
                        secondary_metric_label="State",
                        secondary_metric_value=self._to_str(row.get("branch_state_label")) or self._to_str(row.get("replay_branch_state")) or None,
                    )
                )

        return CompareResponse(
            compare_kind="families",
            left_entity=left_identity,
            right_entity=right_identity,
            rows=rows,
            identity_context=identity_context,
            summary_cards=summary_cards,
            contrast_rows=contrast_rows,
            field_overlap_rows=field_overlap_rows,
            forecast_rows=forecast_rows,
            support_rows=support_rows,
            meta=ResponseMeta(
                page="compare.families",
                artifact_sources=[str(path) for path in self.family_repository.artifacts()],
                caveats=caveats,
            ),
        )

    def get_portfolio_compare(
        self,
        left_owner_id: str,
        right_owner_id: str,
        top_family_limit: int = 5,
    ) -> CompareResponse:
        left_summary = self.portfolio_repository.get_owner_summary(left_owner_id)
        right_summary = self.portfolio_repository.get_owner_summary(right_owner_id)
        left_peer = self.portfolio_repository.get_owner_summary_peer_context(left_owner_id)
        right_peer = self.portfolio_repository.get_owner_summary_peer_context(right_owner_id)

        left_identity = PageIdentity(
            id=self._to_str(left_summary.get("owner_name_harmonized"), left_owner_id),
            label=self._to_str(left_summary.get("owner_name_display"), left_owner_id),
            page_kind="portfolio",
        )
        right_identity = PageIdentity(
            id=self._to_str(right_summary.get("owner_name_harmonized"), right_owner_id),
            label=self._to_str(right_summary.get("owner_name_display"), right_owner_id),
            page_kind="portfolio",
        )

        if not left_summary or not right_summary:
            return CompareResponse(
                compare_kind="portfolios",
                left_entity=left_identity if left_summary else None,
                right_entity=right_identity if right_summary else None,
                rows=[],
                meta=ResponseMeta(
                    page="compare.portfolios",
                    artifact_sources=[str(path) for path in self.portfolio_repository.artifacts()],
                    caveats=[
                        Caveat(
                            code="portfolio_compare_unavailable",
                            title="Portfolio compare unavailable",
                            detail="One or both owner ids could not be resolved in the current portfolio serving mart.",
                        )
                    ],
                ),
            )

        left_family_count = self._to_int(left_summary.get("portfolio_family_count_within_mega_cluster"), 0)
        right_family_count = self._to_int(right_summary.get("portfolio_family_count_within_mega_cluster"), 0)

        lenses = [
            {
                "lens": "mass",
                "label": "Blocking Footprint",
                "metric_key": "portfolio_total_mass_score",
                "metric_label": "Granted Blocking Mass",
                "percentile_key": "portfolio_total_mass_score_percentile",
            },
            {
                "lens": "density",
                "label": "Elite Family Density",
                "metric_key": "portfolio_hit_rate_top_decile",
                "metric_label": "Top-Decile Hit Rate",
                "percentile_key": "portfolio_hit_rate_top_decile_percentile",
            },
            {
                "lens": "crown_jewel",
                "label": "Crown-Jewel Strength",
                "metric_key": "portfolio_crown_jewel_index",
                "metric_label": "Crown Jewel Index",
                "percentile_key": "portfolio_crown_jewel_index_percentile",
            },
            {
                "lens": "current_threat",
                "label": "Current Threat",
                "metric_key": "portfolio_current_threat_score",
                "metric_label": "Threat Pressure",
                "percentile_key": "portfolio_current_threat_score_percentile",
            },
        ]

        rows: list[dict[str, str | int | float | bool | None]] = []
        caveats = [
            Caveat(
                code="portfolio_compare_lenses",
                title="Four compare lenses",
                detail="Portfolio compare separates mass, density, crown-jewel strength, and current threat rather than collapsing all portfolio differences into one score.",
            ),
            Caveat(
                code="peer_relative_bands",
                title="Peer-relative bands",
                detail="Qualitative bands are percentile-based within portfolio-size peer buckets. Raw values remain the source evidence for analyst drill-down.",
            ),
        ]
        same_bucket = self._to_str(left_peer.get("peer_bucket")) == self._to_str(right_peer.get("peer_bucket"))
        if not same_bucket:
            caveats.append(
                Caveat(
                    code="cross_scale_compare",
                    title="Cross-scale portfolio compare",
                    detail="The compared portfolios belong to different portfolio-size peer buckets, so percentiles are cohort-relative. Use crown-jewel and top-family support rows before claiming a strict winner.",
                )
            )

        left_status_counts = self._optional_repo_call(
            self.portfolio_repository,
            "get_owner_family_status_counts",
            {},
            left_owner_id,
        )
        right_status_counts = self._optional_repo_call(
            self.portfolio_repository,
            "get_owner_family_status_counts",
            {},
            right_owner_id,
        )
        left_fields = self._optional_repo_call(
            self.portfolio_repository,
            "get_owner_fields",
            [],
            left_owner_id,
        )
        right_fields = self._optional_repo_call(
            self.portfolio_repository,
            "get_owner_fields",
            [],
            right_owner_id,
        )
        left_forecast_summary = self._optional_repo_call(
            self.portfolio_repository,
            "get_owner_forecast_summary",
            {},
            left_owner_id,
        )
        right_forecast_summary = self._optional_repo_call(
            self.portfolio_repository,
            "get_owner_forecast_summary",
            {},
            right_owner_id,
        )
        left_contributors = self._optional_repo_call(
            self.portfolio_repository,
            "get_owner_forecast_contributors",
            [],
            left_owner_id,
            horizon="3y",
            limit=3,
            offset=0,
            current_state_only=True,
        )
        right_contributors = self._optional_repo_call(
            self.portfolio_repository,
            "get_owner_forecast_contributors",
            [],
            right_owner_id,
            horizon="3y",
            limit=3,
            offset=0,
            current_state_only=True,
        )

        for lens in lenses:
            metric_key = lens["metric_key"]
            left_band = self._portfolio_metric_band_meta(left_peer, metric_key, lens["percentile_key"])
            right_band = self._portfolio_metric_band_meta(right_peer, metric_key, lens["percentile_key"])
            suppressed = False
            suppression_reason: str | None = None
            if lens["lens"] == "density" and (left_family_count < 5 or right_family_count < 5):
                suppressed = True
                suppression_reason = "Density compare is suppressed when either portfolio has fewer than 5 in-scope families."
            comparison_mode = "same_bucket_percentile" if same_bucket else "cross_bucket_band_first"
            winner: str | None = None
            winner_basis: str | None = None
            if not suppressed:
                if same_bucket:
                    winner = self._winner_from_values(left_band.get("peer_percentile"), right_band.get("peer_percentile"))
                    winner_basis = "peer_percentile"
                else:
                    winner = self._winner_from_bands(
                        self._to_str(left_band.get("band_code")) or None,
                        self._to_str(right_band.get("band_code")) or None,
                    )
                    if winner and winner != "tie":
                        winner_basis = "band"
            rows.append(
                {
                    "kind": "lens",
                    "lens": str(lens["lens"]),
                    "label": str(lens["label"]),
                    "metric_key": str(metric_key),
                    "metric_label": str(lens["metric_label"]),
                    "left_owner_id": left_identity.id,
                    "left_owner_label": left_identity.label,
                    "left_raw_value": self._to_float(left_summary.get(metric_key), 0.0),
                    "left_band_code": self._to_str(left_band.get("band_code")) or None,
                    "left_band_label": self._to_str(left_band.get("band_label")) or None,
                    "left_peer_percentile": left_band.get("peer_percentile"),
                    "left_peer_bucket": self._to_str(left_band.get("peer_bucket")) or None,
                    "left_peer_bucket_label": self._to_str(left_band.get("peer_bucket_label")) or None,
                    "right_owner_id": right_identity.id,
                    "right_owner_label": right_identity.label,
                    "right_raw_value": self._to_float(right_summary.get(metric_key), 0.0),
                    "right_band_code": self._to_str(right_band.get("band_code")) or None,
                    "right_band_label": self._to_str(right_band.get("band_label")) or None,
                    "right_peer_percentile": right_band.get("peer_percentile"),
                    "right_peer_bucket": self._to_str(right_band.get("peer_bucket")) or None,
                    "right_peer_bucket_label": self._to_str(right_band.get("peer_bucket_label")) or None,
                    "same_peer_bucket": same_bucket,
                    "comparison_mode": comparison_mode,
                    "suppressed": suppressed,
                    "suppression_reason": suppression_reason,
                    "winner": winner,
                    "winner_basis": winner_basis,
                }
            )
            if suppressed:
                caveats.append(
                    Caveat(
                        code="density_small_sample",
                        title="Density compare suppressed",
                        detail=suppression_reason,
                    )
                )

        safe_top_family_limit = max(1, min(self._to_int(top_family_limit, 5), 10))
        for side, owner in (("left", left_owner_id), ("right", right_owner_id)):
            for rank, row in enumerate(
                self.portfolio_repository.get_owner_families(
                    owner,
                    limit=safe_top_family_limit,
                    sort="blocking",
                    exclude_inactive=True,
                ),
                start=1,
            ):
                rows.append(
                    {
                        "kind": "top_family_preview",
                        "side": side,
                        "owner_id": left_identity.id if side == "left" else right_identity.id,
                        "owner_label": left_identity.label if side == "left" else right_identity.label,
                        "rank": rank,
                        "family_id": self._to_str(row.get("family_id")),
                        "blocking_score": self._to_float(row.get("blocking_score"), 0.0),
                        "forecast_contributor": self._to_float(row.get("forecast_contributor"), 0.0),
                        "primary_field": self._to_str(row.get("primary_field"), "unknown"),
                        "status": self._to_str(row.get("status"), "unknown"),
                    }
                )

        caveats.append(
            Caveat(
                code="crown_jewel_preview",
                title="Crown-jewel support rows",
                detail="Top-family preview rows support cross-scale interpretation, but dedicated top-10 and top-10-percent crown-jewel variants are still the next compare-layer implementation step.",
            )
        )
        caveats.append(
            Caveat(
                code="forecast_current_state_support",
                title="Projected contributors stay current-state constrained",
                detail="Compare support rows exclude dead families, but keep partially lapsed or under-fire families visible with explicit status badges when live or contested rights still remain.",
            )
        )

        lens_by_key = {self._to_str(row.get("lens")): row for row in rows if row.get("kind") == "lens"}

        identity_context = [
            self._identity_context_row(
                side="left",
                title=left_identity.label,
                subtitle=self._portfolio_peer_bucket_label(self._to_str(left_peer.get("peer_bucket")) or None),
                badges=[
                    f"{left_family_count} families",
                    self._to_str(left_summary.get("portfolio_prediction_coverage_status"), "").replace("_", " "),
                ],
                href=f"/portfolio/{left_identity.id}",
            ),
            self._identity_context_row(
                side="right",
                title=right_identity.label,
                subtitle=self._portfolio_peer_bucket_label(self._to_str(right_peer.get("peer_bucket")) or None),
                badges=[
                    f"{right_family_count} families",
                    self._to_str(right_summary.get("portfolio_prediction_coverage_status"), "").replace("_", " "),
                ],
                href=f"/portfolio/{right_identity.id}",
            ),
        ]

        heritage_left_band = self._portfolio_metric_band_meta(
            left_peer,
            "portfolio_heritage_score",
            "portfolio_heritage_score_percentile",
        )
        heritage_right_band = self._portfolio_metric_band_meta(
            right_peer,
            "portfolio_heritage_score",
            "portfolio_heritage_score_percentile",
        )

        summary_cards = [
            self._metric_row(
                key="family_count",
                label="Families in scope",
                display_kind="count",
                left_value=left_family_count,
                right_value=right_family_count,
                note="Current in-scope family count within the compare summary mart.",
                winner=self._winner_from_values(left_family_count, right_family_count),
                winner_basis="count",
            ),
            self._metric_row(
                key="mass",
                label="Blocking footprint",
                display_kind="decimal",
                left_value=lens_by_key.get("mass", {}).get("left_raw_value"),
                right_value=lens_by_key.get("mass", {}).get("right_raw_value"),
                left_note=self._to_str(lens_by_key.get("mass", {}).get("left_band_label")) or None,
                right_note=self._to_str(lens_by_key.get("mass", {}).get("right_band_label")) or None,
                note="Peer-relative granted blocking mass.",
                winner=self._to_str(lens_by_key.get("mass", {}).get("winner")) or None,
                winner_basis=self._to_str(lens_by_key.get("mass", {}).get("winner_basis")) or None,
            ),
            self._metric_row(
                key="density",
                label="Elite family density",
                display_kind="percent",
                left_value=lens_by_key.get("density", {}).get("left_raw_value"),
                right_value=lens_by_key.get("density", {}).get("right_raw_value"),
                left_note=self._to_str(lens_by_key.get("density", {}).get("left_band_label")) or None,
                right_note=self._to_str(lens_by_key.get("density", {}).get("right_band_label")) or None,
                note="Top-decile hit rate within peer-bucket logic.",
                winner=self._to_str(lens_by_key.get("density", {}).get("winner")) or None,
                winner_basis=self._to_str(lens_by_key.get("density", {}).get("winner_basis")) or None,
            ),
            self._metric_row(
                key="heritage",
                label="Heritage depth",
                display_kind="decimal",
                left_value=self._to_optional_float(left_summary.get("portfolio_heritage_score")),
                right_value=self._to_optional_float(right_summary.get("portfolio_heritage_score")),
                left_note=self._to_str(heritage_left_band.get("band_label")) or None,
                right_note=self._to_str(heritage_right_band.get("band_label")) or None,
                note="Portfolio-level heritage score from the summary mart.",
                winner=self._winner_from_values(left_summary.get("portfolio_heritage_score"), right_summary.get("portfolio_heritage_score")),
                winner_basis="score",
            ),
            self._metric_row(
                key="future_outlook_3y",
                label="3y future citations",
                display_kind="decimal",
                left_value=self._to_optional_float(left_forecast_summary.get("portfolio_expected_future_citations_total_3y")),
                right_value=self._to_optional_float(right_forecast_summary.get("portfolio_expected_future_citations_total_3y")),
                left_note=f"coverage {round(self._to_float(left_forecast_summary.get('phase03_family_coverage_pct'), 0.0) * 100.0, 1)}%",
                right_note=f"coverage {round(self._to_float(right_forecast_summary.get('phase03_family_coverage_pct'), 0.0) * 100.0, 1)}%",
                note="Phase 03 future-citation overlay, compared on the 3y horizon.",
                winner=self._winner_from_values(
                    left_forecast_summary.get("portfolio_expected_future_citations_total_3y"),
                    right_forecast_summary.get("portfolio_expected_future_citations_total_3y"),
                ),
                winner_basis="forecast_midpoint",
            ),
        ]

        contrast_rows = [
            self._metric_row(
                key="active_families",
                label="Active families",
                display_kind="count",
                left_value=self._to_int(left_status_counts.get("active_family_count"), 0),
                right_value=self._to_int(right_status_counts.get("active_family_count"), 0),
                note="Fully active family count in the current owner bridge.",
                winner=self._winner_from_values(left_status_counts.get("active_family_count"), right_status_counts.get("active_family_count")),
                winner_basis="count",
            ),
            self._metric_row(
                key="pending_families",
                label="Pending families",
                display_kind="count",
                left_value=self._to_int(left_status_counts.get("pending_family_count"), 0),
                right_value=self._to_int(right_status_counts.get("pending_family_count"), 0),
                note="Pending or emerging family count.",
                winner=self._winner_from_values(left_status_counts.get("pending_family_count"), right_status_counts.get("pending_family_count")),
                winner_basis="count",
            ),
            self._metric_row(
                key="abandoned_families",
                label="Abandoned / lapsed families",
                display_kind="count",
                left_value=self._to_int(left_status_counts.get("abandoned_family_count"), 0),
                right_value=self._to_int(right_status_counts.get("abandoned_family_count"), 0),
                note="Families currently reading as dead or partially lapsed.",
                winner=self._winner_from_values(right_status_counts.get("abandoned_family_count"), left_status_counts.get("abandoned_family_count")),
                winner_basis="inverse_count",
            ),
        ]

        field_overlap_rows = self._build_portfolio_field_overlap_rows(left_fields, right_fields)
        forecast_rows = self._build_portfolio_forecast_rows(left_forecast_summary, right_forecast_summary)

        support_rows: list[dict[str, object]] = []
        preview_rows = [row for row in rows if row.get("kind") == "top_family_preview"]
        for row in preview_rows:
            support_rows.append(
                self._top_support_row(
                    kind="top_family_preview",
                    side=self._to_str(row.get("side"), "left"),
                    title=f"Family {self._to_str(row.get('family_id'))}",
                    subtitle=self._to_str(row.get("primary_field")) or None,
                    badge=self._to_str(row.get("status")) or None,
                    primary_metric_label="Blocking",
                    primary_metric_value=self._to_optional_float(row.get("blocking_score")),
                    secondary_metric_label="Forecast",
                    secondary_metric_value=self._to_optional_float(row.get("forecast_contributor")),
                    href=f"/family/{self._to_str(row.get('family_id'))}",
                )
            )
        for side, contributor_rows in (("left", left_contributors), ("right", right_contributors)):
            for row in contributor_rows:
                contributor_id = self._to_str(row.get("contributor_entity_id"))
                support_rows.append(
                    self._top_support_row(
                        kind="forecast_contributor",
                        side=side,
                        title=f"Contributor {contributor_id}",
                        subtitle=" / ".join(
                            value
                            for value in [
                                self._to_str(row.get("jurisdiction_code")) or None,
                                self._to_str(row.get("horizon")) or None,
                            ]
                            if value
                        )
                        or None,
                        badge=self._to_str(row.get("status")) or self._to_str(row.get("horizon")) or None,
                        primary_metric_label="Contribution share",
                        primary_metric_value=self._to_optional_float(row.get("contribution_share")),
                        secondary_metric_label="Contribution value",
                        secondary_metric_value=self._to_optional_float(row.get("contribution_value")),
                        href=f"/family/{contributor_id}" if contributor_id else None,
                    )
                )

        return CompareResponse(
            compare_kind="portfolios",
            left_entity=left_identity,
            right_entity=right_identity,
            rows=rows,
            identity_context=identity_context,
            summary_cards=summary_cards,
            contrast_rows=contrast_rows,
            field_overlap_rows=field_overlap_rows,
            forecast_rows=forecast_rows,
            support_rows=support_rows,
            meta=ResponseMeta(
                page="compare.portfolios",
                artifact_sources=[str(path) for path in self.portfolio_repository.artifacts()],
                caveats=caveats,
            ),
        )

    def get_family_timeslice_compare(
        self,
        family_id: str,
        base_year: int | None = None,
        compare_year: int | None = None,
    ) -> CompareResponse:
        timeslice_rows = self._optional_repo_call(
            self.family_repository,
            "get_family_compare_timeslice",
            [],
            family_id,
            base_year=base_year,
            compare_year=compare_year,
        )
        left_row, right_row = self._timeslice_pair(timeslice_rows)
        resolved_family_id = self._to_str(left_row.get("docdb_family_id"), family_id)

        if not left_row or not right_row:
            identity = PageIdentity(
                id=resolved_family_id or family_id,
                label=f"Family {resolved_family_id or family_id}",
                page_kind="family",
            )
            return CompareResponse(
                compare_kind="families",
                compare_mode="timeslice",
                left_entity=identity if resolved_family_id or family_id else None,
                rows=[],
                meta=ResponseMeta(
                    page="compare.families.timeslice",
                    artifact_sources=[str(path) for path in self.family_repository.artifacts()],
                    caveats=[
                        Caveat(
                            code="family_timeslice_unavailable",
                            title="Family time-slice compare unavailable",
                            detail="A stable year pair could not be resolved for the requested family in the compare PIT.",
                        )
                    ],
                ),
            )

        left_year = self._to_int(left_row.get("as_of_year"), 0)
        right_year = self._to_int(right_row.get("as_of_year"), 0)
        left_status = self._to_str(left_row.get("family_composite_status_asof"), "unknown")
        right_status = self._to_str(right_row.get("family_composite_status_asof"), "unknown")
        left_field = self._to_str(left_row.get("primary_wipo_field_current"), "unknown")
        right_field = self._to_str(right_row.get("primary_wipo_field_current"), "unknown")

        left_identity = PageIdentity(
            id=f"{resolved_family_id}:{left_year}",
            label=f"Family {resolved_family_id} • {left_year}",
            page_kind="family",
        )
        right_identity = PageIdentity(
            id=f"{resolved_family_id}:{right_year}",
            label=f"Family {resolved_family_id} • {right_year}",
            page_kind="family",
        )

        family_field_rows_left = self._optional_repo_call(
            self.family_repository,
            "get_family_field_rows",
            [],
            resolved_family_id,
            as_of_year=left_year,
        )
        family_field_rows_right = self._optional_repo_call(
            self.family_repository,
            "get_family_field_rows",
            [],
            resolved_family_id,
            as_of_year=right_year,
        )
        family_jurisdiction_rows_left = self._optional_repo_call(
            self.family_repository,
            "get_family_jurisdiction_legal_rows",
            [],
            resolved_family_id,
            as_of_year=left_year,
        )
        family_jurisdiction_rows_right = self._optional_repo_call(
            self.family_repository,
            "get_family_jurisdiction_legal_rows",
            [],
            resolved_family_id,
            as_of_year=right_year,
        )

        caveats = [
            Caveat(
                code="family_timeslice_compare",
                title="Family time-slice compare",
                detail="Time-slice compare reads historical as-of PIT values for the same family instead of comparing two separate families.",
            ),
            Caveat(
                code="timeslice_current_vs_historical",
                title="Current versus historical context",
                detail="Later years use the current snapshot context, while earlier years use historical as-of values. Read year badges before interpreting deltas.",
            ),
        ]
        if any(
            self._to_int(row.get("as_of_year"), 0) == 2025
            and self._to_float(row.get("family_enforceability_score_asof"), 0.0) == 0.0
            for row in (left_row, right_row)
        ):
            caveats.append(
                Caveat(
                    code="family_2025_enforceability_gap",
                    title="2025 enforceability gap",
                    detail="If 2025 is selected, legal durability can be understated because the historical market-weight support for that year is still being rebuilt.",
                )
            )
        if any(bool(row.get("current_owner_metadata_only")) for row in (left_row, right_row)):
            caveats.append(
                Caveat(
                    code="owner_metadata_only",
                    title="Current-owner metadata only",
                    detail="Owner context in family history is metadata-only and should not be read as full owner-by-year truth.",
                )
            )

        identity_context = [
            self._identity_context_row(
                side="left",
                title=f"Family {resolved_family_id}",
                subtitle=f"{left_year} / {left_field} / {left_status}",
                badges=[
                    f"{self._to_int(left_row.get('family_size_docdb_asof'), 0)} members",
                    f"{self._to_int(left_row.get('active_jurisdiction_count_asof'), 0)} active jurisdictions",
                    self._support_badge(left_row.get("historical_compare_safe"), "compare safe", "limited support"),
                ],
                href=f"/family/{resolved_family_id}",
            ),
            self._identity_context_row(
                side="right",
                title=f"Family {resolved_family_id}",
                subtitle=f"{right_year} / {right_field} / {right_status}",
                badges=[
                    f"{self._to_int(right_row.get('family_size_docdb_asof'), 0)} members",
                    f"{self._to_int(right_row.get('active_jurisdiction_count_asof'), 0)} active jurisdictions",
                    self._support_badge(right_row.get("historical_compare_safe"), "compare safe", "limited support"),
                ],
                href=f"/family/{resolved_family_id}",
            ),
        ]

        summary_cards = [
            self._metric_row(
                key="family_size_asof",
                label="Family size",
                display_kind="count",
                left_value=self._to_int(left_row.get("family_size_docdb_asof"), 0),
                right_value=self._to_int(right_row.get("family_size_docdb_asof"), 0),
                note="Observed family member count at each as-of year.",
                winner=self._winner_from_values(left_row.get("family_size_docdb_asof"), right_row.get("family_size_docdb_asof")),
                winner_basis="count",
            ),
            self._metric_row(
                key="blocking_power_asof",
                label="Blocking power",
                display_kind="decimal",
                left_value=self._to_optional_float(left_row.get("family_blocking_power_score_asof")),
                right_value=self._to_optional_float(right_row.get("family_blocking_power_score_asof")),
                note="Historical family blocking power score.",
                winner=self._winner_from_values(left_row.get("family_blocking_power_score_asof"), right_row.get("family_blocking_power_score_asof")),
                winner_basis="score",
            ),
            self._metric_row(
                key="legal_durability_asof",
                label="Legal durability",
                display_kind="decimal",
                left_value=self._to_optional_float(left_row.get("family_enforceability_score_asof")),
                right_value=self._to_optional_float(right_row.get("family_enforceability_score_asof")),
                note="Historical enforceability score at each selected year.",
                winner=self._winner_from_values(left_row.get("family_enforceability_score_asof"), right_row.get("family_enforceability_score_asof")),
                winner_basis="score",
            ),
            self._metric_row(
                key="unique_citing_families_asof",
                label="Distinct citing families",
                display_kind="count",
                left_value=self._to_int(left_row.get("pre_asof_unique_citing_family_count"), 0),
                right_value=self._to_int(right_row.get("pre_asof_unique_citing_family_count"), 0),
                note="Breadth of external citing families accumulated by each as-of year.",
                winner=self._winner_from_values(left_row.get("pre_asof_unique_citing_family_count"), right_row.get("pre_asof_unique_citing_family_count")),
                winner_basis="count",
            ),
            self._metric_row(
                key="field_breadth_asof",
                label="Field breadth",
                display_kind="count",
                left_value=self._to_int(left_row.get("family_tech_breadth_wipo_count_asof"), 0),
                right_value=self._to_int(right_row.get("family_tech_breadth_wipo_count_asof"), 0),
                note="Covered WIPO-field breadth at each selected year.",
                winner=self._winner_from_values(left_row.get("family_tech_breadth_wipo_count_asof"), right_row.get("family_tech_breadth_wipo_count_asof")),
                winner_basis="count",
            ),
        ]

        contrast_rows = [
            self._metric_row(
                key="current_status",
                label="Observed status",
                display_kind="text",
                left_value=left_status,
                right_value=right_status,
                note="Family composite status at each selected year.",
            ),
            self._metric_row(
                key="active_jurisdictions",
                label="Active jurisdictions",
                display_kind="count",
                left_value=self._to_int(left_row.get("active_jurisdiction_count_asof"), 0),
                right_value=self._to_int(right_row.get("active_jurisdiction_count_asof"), 0),
                note="Active jurisdiction count on the selected year snapshot.",
                winner=self._winner_from_values(left_row.get("active_jurisdiction_count_asof"), right_row.get("active_jurisdiction_count_asof")),
                winner_basis="count",
            ),
            self._metric_row(
                key="active_grant_branches",
                label="Active grant branches",
                display_kind="count",
                left_value=self._to_int(left_row.get("active_grant_branch_count_asof"), 0),
                right_value=self._to_int(right_row.get("active_grant_branch_count_asof"), 0),
                note="Granted active branches visible at each selected year.",
                winner=self._winner_from_values(left_row.get("active_grant_branch_count_asof"), right_row.get("active_grant_branch_count_asof")),
                winner_basis="count",
            ),
            self._metric_row(
                key="lapsed_jurisdictions",
                label="Lapsed jurisdictions",
                display_kind="count",
                left_value=self._to_int(left_row.get("lapsed_jurisdiction_count_asof"), 0),
                right_value=self._to_int(right_row.get("lapsed_jurisdiction_count_asof"), 0),
                note="Observed lapsed jurisdiction count at each selected year.",
                winner=self._winner_from_values(right_row.get("lapsed_jurisdiction_count_asof"), left_row.get("lapsed_jurisdiction_count_asof")),
                winner_basis="inverse_count",
            ),
            self._metric_row(
                key="coverage_stability",
                label="Coverage stability",
                display_kind="percent",
                left_value=self._to_optional_float(left_row.get("family_coverage_stability_score_asof")),
                right_value=self._to_optional_float(right_row.get("family_coverage_stability_score_asof")),
                note="Jurisdiction stability proxy across the covered family footprint.",
                winner=self._winner_from_values(left_row.get("family_coverage_stability_score_asof"), right_row.get("family_coverage_stability_score_asof")),
                winner_basis="share",
            ),
            self._metric_row(
                key="attacker_density",
                label="Attacker density",
                display_kind="decimal",
                left_value=self._to_optional_float(left_row.get("pre_asof_attacker_density_score")),
                right_value=self._to_optional_float(right_row.get("pre_asof_attacker_density_score")),
                note="Citation pressure concentration proxy at each year.",
                winner=self._winner_from_values(left_row.get("pre_asof_attacker_density_score"), right_row.get("pre_asof_attacker_density_score")),
                winner_basis="score",
            ),
            self._metric_row(
                key="data_completeness",
                label="Data completeness",
                display_kind="percent",
                left_value=self._to_optional_float(left_row.get("data_completeness_pct_asof")),
                right_value=self._to_optional_float(right_row.get("data_completeness_pct_asof")),
                note="Observed compare-PIT completeness for the selected years.",
                winner=self._winner_from_values(left_row.get("data_completeness_pct_asof"), right_row.get("data_completeness_pct_asof")),
                winner_basis="coverage",
            ),
        ]

        field_overlap_rows = self._build_family_field_overlap_rows(
            family_field_rows_left,
            family_field_rows_right,
        )
        forecast_rows = [
            {
                "key": "family_trajectory_weighted_citations",
                "label": "Weighted citation trajectory",
                "display_kind": "decimal",
                "left_value": self._to_optional_float(left_row.get("pre_asof_forward_citations_weighted")),
                "right_value": self._to_optional_float(right_row.get("pre_asof_forward_citations_weighted")),
                "left_range_low": None,
                "left_range_high": None,
                "right_range_low": None,
                "right_range_high": None,
                "left_note": f"{left_year} as-of",
                "right_note": f"{right_year} as-of",
                "overlap_state": "historical",
                "note": "Historical citation-weight trajectory, not a forward forecast interval.",
            },
            {
                "key": "family_trajectory_rcf",
                "label": "RCF trajectory",
                "display_kind": "decimal",
                "left_value": self._to_optional_float(left_row.get("family_rcf_score_asof")),
                "right_value": self._to_optional_float(right_row.get("family_rcf_score_asof")),
                "left_range_low": None,
                "left_range_high": None,
                "right_range_low": None,
                "right_range_high": None,
                "left_note": f"{left_year} as-of",
                "right_note": f"{right_year} as-of",
                "overlap_state": "historical",
                "note": "Historical RCF intensity for the same family across the selected years.",
            },
        ]

        support_rows: list[dict[str, object]] = []
        for side, year, jurisdiction_rows, row in (
            ("left", left_year, family_jurisdiction_rows_left, left_row),
            ("right", right_year, family_jurisdiction_rows_right, right_row),
        ):
            for jurisdiction_row in jurisdiction_rows[:3]:
                jurisdiction = self._to_str(jurisdiction_row.get("jurisdiction_code"), "Unknown")
                support_rows.append(
                    self._top_support_row(
                        kind="jurisdiction_preview",
                        side=side,
                        title=f"{jurisdiction} • {year}",
                        subtitle=self._to_str(jurisdiction_row.get("dominant_wipo_field")) or self._to_str(jurisdiction_row.get("branch_state_label")) or None,
                        badge=self._to_str(jurisdiction_row.get("jurisdiction_relative_enforceability_band")) or None,
                        primary_metric_label="Family share",
                        primary_metric_value=self._to_optional_float(jurisdiction_row.get("jurisdiction_enforceability_share_of_family")),
                        secondary_metric_label="State",
                        secondary_metric_value=self._to_str(jurisdiction_row.get("branch_state_label")) or self._to_str(jurisdiction_row.get("replay_branch_state")) or None,
                    )
                )
            support_rows.append(
                self._top_support_row(
                    kind="timeslice_support",
                    side=side,
                    title=f"Historical support • {year}",
                    subtitle="Year-level support flags for the compare PIT.",
                    badge=self._support_badge(row.get("historical_compare_safe"), "compare safe", "limited"),
                    primary_metric_label="Completeness",
                    primary_metric_value=self._to_optional_float(row.get("data_completeness_pct_asof")),
                    secondary_metric_label="Owner metadata only",
                    secondary_metric_value=self._support_badge(not row.get("current_owner_metadata_only"), "no", "yes"),
                )
            )

        return CompareResponse(
            compare_kind="families",
            compare_mode="timeslice",
            left_entity=left_identity,
            right_entity=right_identity,
            rows=[],
            identity_context=identity_context,
            summary_cards=summary_cards,
            contrast_rows=contrast_rows,
            field_overlap_rows=field_overlap_rows,
            forecast_rows=forecast_rows,
            support_rows=support_rows,
            meta=ResponseMeta(
                page="compare.families.timeslice",
                artifact_sources=[str(path) for path in self.family_repository.artifacts()],
                caveats=caveats,
            ),
        )

    def get_family_timeslice_options(self, family_id: str) -> CompareTimesliceOptionsResponse:
        options = self._optional_repo_call(
            self.family_repository,
            "get_family_compare_timeslice_options",
            {},
            family_id,
        )
        return CompareTimesliceOptionsResponse(
            entity_id=self._to_str(options.get("entity_id"), family_id),
            available_years=[int(year) for year in options.get("available_years", []) if year is not None],
            compare_safe_years=[int(year) for year in options.get("compare_safe_years", []) if year is not None],
            default_base_year=self._to_optional_int(options.get("default_base_year")),
            default_compare_year=self._to_optional_int(options.get("default_compare_year")),
        )

    def get_family_compare_lookup(self, family_id: str) -> CompareScopeLookupResponse:
        normalized_family_id = self._to_str(family_id)
        context = self._optional_repo_call(
            self.family_repository,
            "get_family_compare_context",
            {},
            normalized_family_id,
        )
        options = self.get_family_timeslice_options(normalized_family_id) if normalized_family_id else CompareTimesliceOptionsResponse(entity_id="")

        primary_field = self._to_str(
            context.get("primary_wipo_field_current") or context.get("primary_wipo_field"),
            "",
        ) or None
        status = self._to_str(
            context.get("family_composite_status_asof") or context.get("family_composite_status"),
            "",
        ) or None
        in_scope = bool(context)
        note = None
        if normalized_family_id and not in_scope:
            note = "This family is not available in the current compare serving scope."
        elif in_scope and not options.compare_safe_years:
            note = "This family is in compare scope, but no compare-safe historical year pair is available."

        return CompareScopeLookupResponse(
            compare_kind="families",
            entity_id=self._to_str(context.get("docdb_family_id"), normalized_family_id),
            label=f"Family {self._to_str(context.get('docdb_family_id'), normalized_family_id)}" if normalized_family_id else None,
            in_scope=in_scope,
            primary_field=primary_field,
            status=status,
            family_count=self._to_optional_int(context.get("family_size_docdb")),
            timeslice_available=len(options.compare_safe_years) > 0,
            default_base_year=options.default_base_year,
            default_compare_year=options.default_compare_year,
            note=note,
        )

    def get_family_compare_suggestions(self, query: str, limit: int = 8) -> CompareFamilySuggestionResponse:
        rows = self._optional_repo_call(
            self.family_repository,
            "get_family_compare_suggestions",
            [],
            query,
            limit=limit,
        )
        return CompareFamilySuggestionResponse(
            query=self._to_str(query),
            rows=[
                CompareFamilySuggestion(
                    family_id=self._to_str(row.get("family_id")),
                    label=self._to_str(row.get("label") or row.get("family_id")),
                    owner_label=self._to_str(row.get("owner_name_display"), "") or None,
                    primary_field=self._to_str(row.get("primary_field"), "") or None,
                    status=self._to_str(row.get("status"), "") or None,
                )
                for row in rows
                if self._to_str(row.get("family_id"))
            ],
        )

    def get_portfolio_timeslice_compare(
        self,
        owner_id: str,
        base_year: int | None = None,
        compare_year: int | None = None,
    ) -> CompareResponse:
        timeslice_rows = self._optional_repo_call(
            self.portfolio_repository,
            "get_owner_compare_timeslice",
            [],
            owner_id,
            base_year=base_year,
            compare_year=compare_year,
        )
        left_row, right_row = self._timeslice_pair(timeslice_rows)
        resolved_owner_id = self._to_str(left_row.get("owner_name_harmonized"), owner_id)
        resolved_owner_label = self._to_str(left_row.get("owner_name_display_current"), owner_id)

        if not left_row or not right_row:
            identity = PageIdentity(
                id=resolved_owner_id or owner_id,
                label=resolved_owner_label or owner_id,
                page_kind="portfolio",
            )
            return CompareResponse(
                compare_kind="portfolios",
                compare_mode="timeslice",
                left_entity=identity if resolved_owner_id or owner_id else None,
                rows=[],
                meta=ResponseMeta(
                    page="compare.portfolios.timeslice",
                    artifact_sources=[str(path) for path in self.portfolio_repository.artifacts()],
                    caveats=[
                        Caveat(
                            code="portfolio_timeslice_unavailable",
                            title="Portfolio time-slice compare unavailable",
                            detail="A stable year pair could not be resolved for the requested owner in the portfolio compare PIT.",
                        )
                    ],
                ),
            )

        left_year = self._to_int(left_row.get("as_of_year"), 0)
        right_year = self._to_int(right_row.get("as_of_year"), 0)
        left_identity = PageIdentity(
            id=f"{resolved_owner_id}:{left_year}",
            label=f"{resolved_owner_label} • {left_year}",
            page_kind="portfolio",
        )
        right_identity = PageIdentity(
            id=f"{resolved_owner_id}:{right_year}",
            label=f"{resolved_owner_label} • {right_year}",
            page_kind="portfolio",
        )

        left_fields = self._optional_repo_call(
            self.portfolio_repository,
            "get_owner_fields",
            [],
            resolved_owner_id,
            as_of_year=left_year,
        )
        right_fields = self._optional_repo_call(
            self.portfolio_repository,
            "get_owner_fields",
            [],
            resolved_owner_id,
            as_of_year=right_year,
        )

        caveats = [
            Caveat(
                code="portfolio_timeslice_compare",
                title="Portfolio time-slice compare",
                detail="Time-slice compare reads the same owner across two as-of years instead of comparing two different owners.",
            ),
            Caveat(
                code="historical_owner_replay",
                title="Historical owner replay",
                detail="Historical owner slices can depend on current-owner replay. Read support rows before treating old years as perfect owner-by-year truth.",
            ),
        ]
        if any(
            self._to_int(row.get("as_of_year"), 0) == 2025
            and self._to_float(row.get("portfolio_avg_enforceability_score_asof"), 0.0) == 0.0
            for row in (left_row, right_row)
        ):
            caveats.append(
                Caveat(
                    code="portfolio_2025_enforceability_gap",
                    title="2025 enforceability gap",
                    detail="If 2025 is selected, average enforceability can be understated because the historical legal-weight support for that year is still incomplete.",
                )
            )
        if any(not bool(row.get("historical_field_mix_supported")) for row in (left_row, right_row)):
            caveats.append(
                Caveat(
                    code="historical_field_mix_limit",
                    title="Historical field-mix limit",
                    detail="At least one selected year lacks fully certified field-mix support, so field overlap should be read as supporting evidence rather than final truth.",
                )
            )

        identity_context = [
            self._identity_context_row(
                side="left",
                title=resolved_owner_label,
                subtitle=f"{left_year} portfolio snapshot",
                badges=[
                    f"{self._to_int(left_row.get('portfolio_family_count_hist_proxy'), 0)} families",
                    f"{self._to_int(left_row.get('portfolio_active_family_count_asof'), 0)} active families",
                    self._support_badge(left_row.get("historical_compare_safe"), "compare safe", "limited support"),
                ],
                href=f"/portfolio/{resolved_owner_id}",
            ),
            self._identity_context_row(
                side="right",
                title=resolved_owner_label,
                subtitle=f"{right_year} portfolio snapshot",
                badges=[
                    f"{self._to_int(right_row.get('portfolio_family_count_hist_proxy'), 0)} families",
                    f"{self._to_int(right_row.get('portfolio_active_family_count_asof'), 0)} active families",
                    self._support_badge(right_row.get("historical_compare_safe"), "compare safe", "limited support"),
                ],
                href=f"/portfolio/{resolved_owner_id}",
            ),
        ]

        summary_cards = [
            self._metric_row(
                key="families_in_scope",
                label="Families in scope",
                display_kind="count",
                left_value=self._to_int(left_row.get("portfolio_family_count_hist_proxy"), 0),
                right_value=self._to_int(right_row.get("portfolio_family_count_hist_proxy"), 0),
                note="Historical family-count proxy for the selected owner and year.",
                winner=self._winner_from_values(left_row.get("portfolio_family_count_hist_proxy"), right_row.get("portfolio_family_count_hist_proxy")),
                winner_basis="count",
            ),
            self._metric_row(
                key="total_blocking_power",
                label="Total blocking power",
                display_kind="decimal",
                left_value=self._to_optional_float(left_row.get("portfolio_total_blocking_power_score_asof")),
                right_value=self._to_optional_float(right_row.get("portfolio_total_blocking_power_score_asof")),
                note="Total blocking-power mass across the owner slice.",
                winner=self._winner_from_values(left_row.get("portfolio_total_blocking_power_score_asof"), right_row.get("portfolio_total_blocking_power_score_asof")),
                winner_basis="score",
            ),
            self._metric_row(
                key="avg_enforceability",
                label="Average enforceability",
                display_kind="decimal",
                left_value=self._to_optional_float(left_row.get("portfolio_avg_enforceability_score_asof")),
                right_value=self._to_optional_float(right_row.get("portfolio_avg_enforceability_score_asof")),
                note="Average enforceability across the historical owner slice.",
                winner=self._winner_from_values(left_row.get("portfolio_avg_enforceability_score_asof"), right_row.get("portfolio_avg_enforceability_score_asof")),
                winner_basis="score",
            ),
            self._metric_row(
                key="legal_durability_index",
                label="Legal durability index",
                display_kind="decimal",
                left_value=self._to_optional_float(left_row.get("portfolio_legal_durability_index_asof")),
                right_value=self._to_optional_float(right_row.get("portfolio_legal_durability_index_asof")),
                note="Portfolio-level legal durability index at each selected year.",
                winner=self._winner_from_values(left_row.get("portfolio_legal_durability_index_asof"), right_row.get("portfolio_legal_durability_index_asof")),
                winner_basis="score",
            ),
            self._metric_row(
                key="field_breadth",
                label="Field breadth",
                display_kind="count",
                left_value=self._to_int(left_row.get("portfolio_field_breadth_asof"), 0),
                right_value=self._to_int(right_row.get("portfolio_field_breadth_asof"), 0),
                note="Breadth of field footprint across the selected years.",
                winner=self._winner_from_values(left_row.get("portfolio_field_breadth_asof"), right_row.get("portfolio_field_breadth_asof")),
                winner_basis="count",
            ),
        ]

        contrast_rows = [
            self._metric_row(
                key="active_families",
                label="Active families",
                display_kind="count",
                left_value=self._to_int(left_row.get("portfolio_active_family_count_asof"), 0),
                right_value=self._to_int(right_row.get("portfolio_active_family_count_asof"), 0),
                note="Active family count in the selected owner slice.",
                winner=self._winner_from_values(left_row.get("portfolio_active_family_count_asof"), right_row.get("portfolio_active_family_count_asof")),
                winner_basis="count",
            ),
            self._metric_row(
                key="active_jurisdictions",
                label="Active jurisdiction instances",
                display_kind="count",
                left_value=self._to_int(left_row.get("portfolio_active_jurisdiction_count_asof"), 0),
                right_value=self._to_int(right_row.get("portfolio_active_jurisdiction_count_asof"), 0),
                note="Summed active family-jurisdiction count across the portfolio slice, not a distinct jurisdiction count.",
                winner=self._winner_from_values(left_row.get("portfolio_active_jurisdiction_count_asof"), right_row.get("portfolio_active_jurisdiction_count_asof")),
                winner_basis="count",
            ),
            self._metric_row(
                key="lapsed_jurisdictions",
                label="Lapsed jurisdiction instances",
                display_kind="count",
                left_value=self._to_int(left_row.get("portfolio_lapsed_jurisdiction_count_asof"), 0),
                right_value=self._to_int(right_row.get("portfolio_lapsed_jurisdiction_count_asof"), 0),
                note="Summed lapsed family-jurisdiction count across the portfolio slice, not a distinct jurisdiction count.",
                winner=self._winner_from_values(right_row.get("portfolio_lapsed_jurisdiction_count_asof"), left_row.get("portfolio_lapsed_jurisdiction_count_asof")),
                winner_basis="inverse_count",
            ),
            self._metric_row(
                key="top_family_blocking_share",
                label="Top-family blocking share",
                display_kind="percent",
                left_value=self._to_optional_float(left_row.get("portfolio_top_family_blocking_share_asof")),
                right_value=self._to_optional_float(right_row.get("portfolio_top_family_blocking_share_asof")),
                note="How much blocking mass is concentrated in the top family.",
                winner=self._winner_from_values(right_row.get("portfolio_top_family_blocking_share_asof"), left_row.get("portfolio_top_family_blocking_share_asof")),
                winner_basis="inverse_share",
            ),
            self._metric_row(
                key="total_rcf",
                label="Total RCF",
                display_kind="decimal",
                left_value=self._to_optional_float(left_row.get("portfolio_total_rcf_score_asof")),
                right_value=self._to_optional_float(right_row.get("portfolio_total_rcf_score_asof")),
                note="Historical RCF aggregate for the owner slice.",
                winner=self._winner_from_values(left_row.get("portfolio_total_rcf_score_asof"), right_row.get("portfolio_total_rcf_score_asof")),
                winner_basis="score",
            ),
            self._metric_row(
                key="data_completeness",
                label="Data completeness",
                display_kind="percent",
                left_value=self._to_optional_float(left_row.get("portfolio_data_completeness_pct_asof")),
                right_value=self._to_optional_float(right_row.get("portfolio_data_completeness_pct_asof")),
                note="Observed completeness of the historical portfolio compare slice.",
                winner=self._winner_from_values(left_row.get("portfolio_data_completeness_pct_asof"), right_row.get("portfolio_data_completeness_pct_asof")),
                winner_basis="coverage",
            ),
        ]

        field_overlap_rows = self._build_portfolio_field_overlap_rows(left_fields, right_fields)
        forecast_rows = [
            {
                "key": "portfolio_trajectory_avg_blocking",
                "label": "Average blocking trajectory",
                "display_kind": "decimal",
                "left_value": self._to_optional_float(left_row.get("portfolio_avg_blocking_power_score_asof")),
                "right_value": self._to_optional_float(right_row.get("portfolio_avg_blocking_power_score_asof")),
                "left_range_low": None,
                "left_range_high": None,
                "right_range_low": None,
                "right_range_high": None,
                "left_note": f"{left_year} as-of",
                "right_note": f"{right_year} as-of",
                "overlap_state": "historical",
                "note": "Historical average blocking score, shown as a trajectory contrast rather than a forecast.",
            },
            {
                "key": "portfolio_trajectory_top_field_share",
                "label": "Top-field share trajectory",
                "display_kind": "percent",
                "left_value": self._to_optional_float(left_row.get("portfolio_top_field_share_asof")),
                "right_value": self._to_optional_float(right_row.get("portfolio_top_field_share_asof")),
                "left_range_low": None,
                "left_range_high": None,
                "right_range_low": None,
                "right_range_high": None,
                "left_note": f"{left_year} as-of",
                "right_note": f"{right_year} as-of",
                "overlap_state": "historical",
                "note": "Field concentration proxy across the selected historical years.",
            },
            {
                "key": "portfolio_trajectory_field_concentration",
                "label": "Field concentration HHI",
                "display_kind": "decimal",
                "left_value": self._to_optional_float(left_row.get("portfolio_field_concentration_hhi_asof")),
                "right_value": self._to_optional_float(right_row.get("portfolio_field_concentration_hhi_asof")),
                "left_range_low": None,
                "left_range_high": None,
                "right_range_low": None,
                "right_range_high": None,
                "left_note": self._support_badge(left_row.get("historical_field_mix_supported"), "field mix supported", "field mix limited"),
                "right_note": self._support_badge(right_row.get("historical_field_mix_supported"), "field mix supported", "field mix limited"),
                "overlap_state": "historical",
                "note": "Historical concentration proxy for the owner field mix.",
            },
        ]

        support_rows = [
            self._top_support_row(
                kind="timeslice_support",
                side="left",
                title=f"Historical support • {left_year}",
                subtitle="Portfolio compare support flags for this year.",
                badge=self._support_badge(left_row.get("historical_compare_safe"), "compare safe", "limited"),
                primary_metric_label="Completeness",
                primary_metric_value=self._to_optional_float(left_row.get("portfolio_data_completeness_pct_asof")),
                secondary_metric_label="Field mix",
                secondary_metric_value=self._support_badge(left_row.get("historical_field_mix_supported"), "supported", "limited"),
            ),
            self._top_support_row(
                kind="timeslice_support",
                side="left",
                title=f"Owner truth • {left_year}",
                subtitle="Historical owner interpretation guardrail.",
                badge=self._support_badge(not left_row.get("current_owner_bridge_replayed_to_history"), "owner truth", "replayed history"),
                primary_metric_label="Historical owner truth",
                primary_metric_value=self._support_badge(left_row.get("historical_owner_truth_supported"), "yes", "no"),
                secondary_metric_label="Replay flag",
                secondary_metric_value=self._support_badge(left_row.get("current_owner_bridge_replayed_to_history"), "yes", "no"),
            ),
            self._top_support_row(
                kind="timeslice_support",
                side="right",
                title=f"Historical support • {right_year}",
                subtitle="Portfolio compare support flags for this year.",
                badge=self._support_badge(right_row.get("historical_compare_safe"), "compare safe", "limited"),
                primary_metric_label="Completeness",
                primary_metric_value=self._to_optional_float(right_row.get("portfolio_data_completeness_pct_asof")),
                secondary_metric_label="Field mix",
                secondary_metric_value=self._support_badge(right_row.get("historical_field_mix_supported"), "supported", "limited"),
            ),
            self._top_support_row(
                kind="timeslice_support",
                side="right",
                title=f"Owner truth • {right_year}",
                subtitle="Historical owner interpretation guardrail.",
                badge=self._support_badge(not right_row.get("current_owner_bridge_replayed_to_history"), "owner truth", "replayed history"),
                primary_metric_label="Historical owner truth",
                primary_metric_value=self._support_badge(right_row.get("historical_owner_truth_supported"), "yes", "no"),
                secondary_metric_label="Replay flag",
                secondary_metric_value=self._support_badge(right_row.get("current_owner_bridge_replayed_to_history"), "yes", "no"),
            ),
        ]

        return CompareResponse(
            compare_kind="portfolios",
            compare_mode="timeslice",
            left_entity=left_identity,
            right_entity=right_identity,
            rows=[],
            identity_context=identity_context,
            summary_cards=summary_cards,
            contrast_rows=contrast_rows,
            field_overlap_rows=field_overlap_rows,
            forecast_rows=forecast_rows,
            support_rows=support_rows,
            meta=ResponseMeta(
                page="compare.portfolios.timeslice",
                artifact_sources=[str(path) for path in self.portfolio_repository.artifacts()],
                caveats=caveats,
            ),
        )

    def get_portfolio_timeslice_options(self, owner_id: str) -> CompareTimesliceOptionsResponse:
        options = self._optional_repo_call(
            self.portfolio_repository,
            "get_owner_compare_timeslice_options",
            {},
            owner_id,
        )
        return CompareTimesliceOptionsResponse(
            entity_id=self._to_str(options.get("entity_id"), owner_id),
            available_years=[int(year) for year in options.get("available_years", []) if year is not None],
            compare_safe_years=[int(year) for year in options.get("compare_safe_years", []) if year is not None],
            default_base_year=self._to_optional_int(options.get("default_base_year")),
            default_compare_year=self._to_optional_int(options.get("default_compare_year")),
        )

    def get_portfolio_compare_lookup(self, owner_id: str) -> CompareScopeLookupResponse:
        normalized_owner_id = self._to_str(owner_id)
        summary = self._optional_repo_call(
            self.portfolio_repository,
            "get_owner_summary",
            {},
            normalized_owner_id,
        )
        options = self.get_portfolio_timeslice_options(normalized_owner_id) if normalized_owner_id else CompareTimesliceOptionsResponse(entity_id="")

        in_scope = bool(summary)
        primary_field = self._to_str(summary.get("primary_wipo_field"), "") or None
        status = self._to_str(
            summary.get("portfolio_primary_status")
            or summary.get("owner_primary_status")
            or summary.get("portfolio_prediction_coverage_status"),
            "",
        ) or None
        family_count = self._to_optional_int(
            summary.get("portfolio_family_count_within_mega_cluster")
            or summary.get("portfolio_family_count_hist_proxy"),
        )
        note = None
        if normalized_owner_id and not in_scope:
            note = "This portfolio is not available in the current compare serving scope."
        elif in_scope and not options.compare_safe_years:
            note = "This portfolio is in compare scope, but no compare-safe historical year pair is available."

        return CompareScopeLookupResponse(
            compare_kind="portfolios",
            entity_id=self._to_str(summary.get("owner_name_harmonized"), normalized_owner_id),
            label=self._to_str(summary.get("owner_name_display"), normalized_owner_id) or None,
            in_scope=in_scope,
            primary_field=primary_field,
            status=status,
            family_count=family_count,
            timeslice_available=len(options.compare_safe_years) > 0,
            default_base_year=options.default_base_year,
            default_compare_year=options.default_compare_year,
            note=note,
        )
