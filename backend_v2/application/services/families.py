from __future__ import annotations

from datetime import date, datetime
from typing import Any

from domain.schemas.common import Caveat, CoverageMetadata, PaginationMetadata, PageIdentity, ResponseMeta, SupportLevel
from domain.schemas.family import FamilyOverviewResponse, FamilySectionResponse, FamilySuggestion, FamilySuggestionResponse
from infrastructure.repositories.family_repository import FamilyRepository
from infrastructure.repositories.publication_repository import PublicationRepository


class FamilyService:
    def __init__(
        self,
        repository: FamilyRepository | None = None,
        publication_repository: PublicationRepository | None = None,
    ) -> None:
        self.repository = repository or FamilyRepository()
        self.publication_repository = publication_repository or PublicationRepository()

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

    def _to_bool(self, value: Any) -> bool:
        return bool(value)

    def _to_str(self, value: Any, default: str = "") -> str:
        if value is None:
            return default
        text = str(value).strip()
        return text if text else default

    def _serialize_scalar(self, value: Any) -> Any:
        if isinstance(value, (date, datetime)):
            return value.isoformat()
        return value

    def _serialize_row(self, row: dict[str, Any]) -> dict[str, Any]:
        return {key: self._serialize_scalar(value) for key, value in row.items()}

    def _artifact_sources(self, include_publication: bool = False) -> list[str]:
        sources = [str(path) for path in self.repository.artifacts()]
        publication_artifacts = getattr(self.publication_repository, "artifacts", None)
        if include_publication and callable(publication_artifacts):
            sources.extend(str(path) for path in publication_artifacts())
        return list(dict.fromkeys(sources))

    def get_family_suggestions(self, query: str, limit: int = 8) -> FamilySuggestionResponse:
        rows = self.repository.get_family_suggestions(query=query, limit=limit)
        return FamilySuggestionResponse(
            query=self._to_str(query),
            rows=[
                FamilySuggestion(
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

    def _band_code_from_percentile(self, percentile: Any) -> str | None:
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

    def _family_metric_band_meta(
        self,
        metric_key: str,
        percentile: Any,
        cohort_label: str | None,
    ) -> dict[str, Any]:
        band_code = self._band_code_from_percentile(percentile)
        if band_code is None:
            return {}
        return {
            "band_code": band_code,
            "band_label": self._family_metric_band_label(metric_key, band_code),
            "peer_percentile": round(self._to_float(percentile, 0.0), 1),
            "peer_cohort_label": cohort_label,
        }

    def _support_level_from_rows(self, rows: list[dict[str, Any]]) -> SupportLevel:
        if not rows:
            return SupportLevel.limited
        order = {
            "strong": SupportLevel.strong,
            "high": SupportLevel.strong,
            "moderate": SupportLevel.moderate,
            "limited": SupportLevel.limited,
            "candidate_only": SupportLevel.candidate_only,
        }
        for candidate in ["strong", "high", "moderate", "limited", "candidate_only"]:
            if any(self._to_str(row.get("office_support_level")).lower() == candidate for row in rows):
                return order[candidate]
        return SupportLevel.moderate

    def _latest_dated_anchor(self, rows: list[dict[str, Any]]) -> tuple[str | None, str | None]:
        latest_date: str | None = None
        latest_type: str | None = None
        for row in rows:
            candidate_date = self._serialize_scalar(row.get("last_event_date"))
            if not candidate_date:
                continue
            if latest_date is None or str(candidate_date) > latest_date:
                latest_date = str(candidate_date)
                latest_type = self._to_str(row.get("last_event_type")) or self._to_str(row.get("last_event_code")) or None
        return latest_date, latest_type

    def _identity_from_context(
        self,
        family_id: str,
        context: dict[str, Any],
        as_of_year: int | None,
    ) -> PageIdentity:
        owner_display = self._to_str(context.get("owner_name_display"))
        primary_field = self._to_str(
            context.get("primary_wipo_field_current") or context.get("primary_wipo_field"),
        )
        pieces = [f"Family {family_id}"]
        if owner_display:
            pieces.append(owner_display)
        if primary_field:
            pieces.append(primary_field)
        return PageIdentity(
            id=family_id,
            label=" · ".join(pieces),
            page_kind="family",
            selected_year=as_of_year,
        )

    def _overview_caveats(self, context: dict[str, Any]) -> list[Caveat]:
        caveats: list[Caveat] = []
        if self._to_bool(context.get("current_owner_metadata_only")):
            caveats.append(
                Caveat(
                    code="current_owner_metadata_only",
                    title="Owner context is current-owner metadata",
                    detail="Owner labeling reflects the current owner mapping, not point-in-time historical owner truth.",
                )
            )
        if not self._to_bool(context.get("historical_oecd_supported")):
            caveats.append(
                Caveat(
                    code="historical_oecd_supported",
                    title="Historical OECD support is partial",
                    detail="OECD-style quality context is reliable for current-family description, but historical playback remains limited.",
                )
            )
        return caveats

    def _curated_family_citation_summary(
        self,
        row: dict[str, Any],
        event_summary: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not row and not event_summary:
            return {}
        event_summary = event_summary or {}
        return self._serialize_row(
            {
                "forward_citations_clean": row.get("family_forward_citations_clean"),
                "forward_citations_7y": row.get("family_fwd_cits7"),
                "forward_citing_owner_count": event_summary.get("forward_citing_owner_count"),
                "backward_citations_clean": row.get("family_backward_citations_clean"),
                "backward_cited_owner_count": event_summary.get("backward_cited_owner_count"),
                "backward_npl_citation_count": row.get("family_backward_npl_citation_count"),
            }
        )

    def _curated_family_citation_timeseries(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            self._serialize_row(
                {
                    "as_of_date": row.get("as_of_date"),
                    "as_of_year": row.get("as_of_year"),
                    "is_observed_as_of_snapshot": row.get("is_observed_as_of_snapshot"),
                    "forward_citation_event_count_year": row.get("forward_citation_event_count_year"),
                    "pre_asof_forward_citation_event_count": row.get("pre_asof_forward_citation_event_count"),
                    "pre_asof_forward_clean_citation_event_count": row.get("pre_asof_forward_clean_citation_event_count"),
                    "pre_asof_forward_citations_weighted": row.get("pre_asof_forward_citations_weighted"),
                    "pre_asof_unique_citing_family_count": row.get("pre_asof_unique_citing_family_count"),
                    "pre_asof_unique_citing_owner_count": row.get("pre_asof_unique_citing_owner_count"),
                    "backward_citation_event_count_year": row.get("backward_citation_event_count_year"),
                    "pre_asof_backward_citation_event_count": row.get("pre_asof_backward_citation_event_count"),
                    "pre_asof_backward_clean_citation_event_count": row.get("pre_asof_backward_clean_citation_event_count"),
                    "pre_asof_distinct_cited_family_count": row.get("pre_asof_distinct_cited_family_count"),
                    "pre_asof_citing_assignee_diversity": row.get("pre_asof_citing_assignee_diversity"),
                    "pre_asof_attacker_density_score": row.get("pre_asof_attacker_density_score"),
                    "first_forward_citation_date_asof": row.get("first_forward_citation_date_asof"),
                    "latest_forward_citation_date_asof": row.get("latest_forward_citation_date_asof"),
                    "window_5y_closed": row.get("window_5y_closed"),
                    "window_7y_closed": row.get("window_7y_closed"),
                    "pre_asof_forward_clean_5y": row.get("pre_asof_forward_clean_5y"),
                    "pre_asof_forward_clean_7y": row.get("pre_asof_forward_clean_7y"),
                    "data_completeness_pct_asof": row.get("data_completeness_pct_asof"),
                    "historical_citation_safe": row.get("historical_citation_safe"),
                    "chronology_support_level": row.get("chronology_support_level"),
                }
            )
            for row in rows
        ]

    def _get_family_member_publications(
        self,
        family_id: str,
        *,
        limit: int,
        offset: int,
    ) -> tuple[list[dict[str, Any]], int]:
        getter = getattr(self.publication_repository, "get_family_publications", None)
        if callable(getter):
            try:
                return getter(int(family_id), limit=limit, offset=offset)
            except (TypeError, ValueError):
                return [], 0
        return self.repository.get_family_member_publications(family_id, limit=limit, offset=offset)

    def _get_family_member_publication_summary(self, family_id: str) -> dict[str, Any]:
        getter = getattr(self.publication_repository, "get_family_publication_summary", None)
        if callable(getter):
            try:
                return getter(int(family_id))
            except (TypeError, ValueError):
                return {}
        return self.repository.get_family_member_publication_summary(family_id)

    def _representative_publication_title(self, family_id: str) -> str | None:
        member_rows, _ = self._get_family_member_publications(family_id, limit=1, offset=0)
        if not member_rows:
            return None
        appln_id = member_rows[0].get("appln_id")
        try:
            normalized_appln_id = int(appln_id) if appln_id is not None else None
        except (TypeError, ValueError):
            normalized_appln_id = None
        if normalized_appln_id is None:
            return None
        title_row = self.publication_repository.get_title_for_application(normalized_appln_id)
        title_text = self._to_str((title_row or {}).get("title_text"))
        return title_text or None

    def get_overview(self, family_id: str, as_of_year: int | None = None) -> FamilyOverviewResponse:
        context = self.repository.get_family_overview_context(family_id)
        heritage_percentile_getter = getattr(self.repository, "get_family_heritage_percentile", None)
        if callable(heritage_percentile_getter):
            corrected_heritage_percentile = heritage_percentile_getter(family_id)
            if corrected_heritage_percentile is not None:
                context["citation_heritage_percentile"] = corrected_heritage_percentile
        representative_title = self._representative_publication_title(family_id)
        identity = self._identity_from_context(family_id, context, as_of_year)
        primary_field = self._to_str(context.get("primary_wipo_field_current") or context.get("primary_wipo_field"), "Unknown")
        family_status = self._to_str(context.get("family_composite_status_asof") or context.get("family_composite_status"), "unknown")
        priority_year = self._to_int(context.get("family_priority_year"), 0)
        blocking_band = self._family_metric_band_meta(
            "family_ui_blocking_power_score",
            context.get("family_ui_blocking_power_score"),
            primary_field,
        )
        citation_band = self._family_metric_band_meta(
            "citation_heritage",
            context.get("citation_heritage_percentile"),
            f"{priority_year} / {primary_field}" if priority_year else primary_field,
        )
        raw_heritage_score = round(self._to_float(context.get("family_heritage_score"), 0.0), 2)
        heritage_percentile_value = context.get("citation_heritage_percentile")

        summary_cards = [
            {
                "key": "blocking_power",
                "label": "Blocking Power",
                "value": round(self._to_float(context.get("family_ui_blocking_power_score"), 0.0), 1),
                "tooltip": "Current family blocking posture from the rebuilt family blocking mart.",
                **blocking_band,
            },
            {
                "key": "family_size",
                "label": "DOCDB family size",
                "value": self._to_int(context.get("family_size_docdb"), 0),
                "tooltip": "Current DOCDB family size across known member publications.",
            },
            {
                "key": "active_reach",
                "label": "Active Reach",
                "value": self._to_int(context.get("active_jurisdiction_count"), 0),
                "tooltip": "Count of active jurisdictions or active grant branches visible in the current summary mart.",
            },
            {
                "key": "heritage",
                "label": "Heritage",
                "value": round(self._to_float(heritage_percentile_value), 1) if heritage_percentile_value is not None else "—",
                "tooltip": (
                    "Peer percentile for the family heritage score within the same priority-year and primary-field cohort. "
                    f"Raw heritage score: {raw_heritage_score:.2f}."
                ),
                **citation_band,
            },
        ]

        overview_metrics = [
            {
                "group": "identity",
                "label": "Primary owner",
                "value": self._to_str(context.get("owner_name_display"), "Unknown"),
            },
            {
                "group": "identity",
                "label": "Representative publication title",
                "value": representative_title,
            },
            {
                "group": "identity",
                "label": "Primary WIPO field",
                "value": primary_field,
            },
            {
                "group": "identity",
                "label": "Status",
                "value": family_status,
            },
            {
                "group": "identity",
                "label": "Earliest priority date",
                "value": self._serialize_scalar(context.get("family_earliest_priority_date")),
            },
            {
                "group": "scope",
                "label": "Scope type",
                "value": self._to_str(context.get("scope_type"), "unknown"),
            },
            {
                "group": "scope",
                "label": "Main window",
                "value": self._to_bool(context.get("is_main_window_family")),
            },
            {
                "group": "scope",
                "label": "Heritage backfill",
                "value": self._to_bool(context.get("is_heritage_backfill_family")),
            },
            {
                "group": "coverage",
                "label": "Data completeness",
                "value": round(self._to_float(context.get("data_completeness_pct_asof"), 0.0), 4),
            },
            {
                "group": "coverage",
                "label": "Historical compare safe",
                "value": self._to_bool(context.get("historical_compare_safe")),
            },
            {
                "group": "quality",
                "label": "Quality index 6",
                "value": self._serialize_scalar(context.get("family_quality_index_6_score")),
            },
            {
                "group": "quality",
                "label": "OECD quality index",
                "value": self._serialize_scalar(context.get("oecd_quality_percentile")),
            },
            {
                "group": "innovation",
                "label": "Generality percentile",
                "value": (
                    round(self._to_float(context.get("family_generality_percentile"), 0.0), 2)
                    if context.get("family_generality_percentile") is not None
                    else None
                ),
            },
            {
                "group": "innovation",
                "label": "Originality percentile",
                "value": (
                    round(self._to_float(context.get("family_originality_percentile"), 0.0), 2)
                    if context.get("family_originality_percentile") is not None
                    else None
                ),
            },
            {
                "group": "innovation",
                "label": "Radicalness percentile",
                "value": (
                    round(self._to_float(context.get("family_radicalness_percentile"), 0.0), 2)
                    if context.get("family_radicalness_percentile") is not None
                    else None
                ),
            },
            {
                "group": "innovation",
                "label": "Science grounding percentile",
                "value": (
                    round(self._to_float(context.get("family_science_grounding_percentile"), 0.0), 2)
                    if context.get("family_science_grounding_percentile") is not None
                    else None
                ),
            },
            {
                "group": "legal",
                "label": "Legal durability percentile",
                "value": round(self._to_float(context.get("legal_durability_percentile"), 0.0), 2),
            },
            {
                "group": "legal",
                "label": "Raw legal enforceability proxy",
                "value": round(self._to_float(context.get("family_overall_legal_enforceability_score"), 0.0), 4),
            },
            {
                "group": "legal",
                "label": "Current active jurisdiction share",
                "value": round(self._to_float(context.get("family_active_jurisdiction_share_asof"), 0.0), 4),
            },
            {
                "group": "citations",
                "label": "Raw family citation count",
                "value": self._to_int(context.get("raw_family_citation_count"), 0),
            },
            {
                "group": "citations",
                "label": "Weighted forward citations",
                "value": round(self._to_float(context.get("pre_asof_forward_citations_weighted"), 0.0), 2),
            },
        ]

        coverage = CoverageMetadata(
            status="high" if context else "unknown",
            pct=round(self._to_float(context.get("data_completeness_pct_asof"), 0.0), 4) if context else None,
            caveat_text="Family overview is current-state reliable; forecast and lapse overlays remain conditional on model coverage.",
        )
        return FamilyOverviewResponse(
            identity=identity,
            summary_cards=summary_cards,
            overview_metrics=overview_metrics,
            meta=ResponseMeta(
                page="family.overview",
                artifact_sources=self._artifact_sources(include_publication=True),
                support_level=SupportLevel.strong if context else SupportLevel.limited,
                coverage=coverage,
                caveats=self._overview_caveats(context),
            ),
        )

    def get_section(
        self,
        family_id: str,
        section: str,
        as_of_year: int | None = None,
        limit: int = 10,
        offset: int = 0,
        owner_filter: str | None = None,
    ) -> FamilySectionResponse:
        safe_limit = max(1, min(int(limit), 100))
        safe_offset = max(0, int(offset))
        context = self.repository.get_family_overview_context(family_id)
        caveats: list[Caveat] = []
        summary: dict[str, Any] | None = None
        rows: list[dict[str, Any]] = []
        series: list[dict[str, Any]] = []
        support_level = SupportLevel.strong if context else SupportLevel.limited
        pagination: PaginationMetadata | None = None

        if section == "fields":
            caveats.append(
                Caveat(
                    code="classification_visibility",
                    title="First-seen classification visibility",
                    detail="Family classification membership becomes visible by first publication-year evidence rather than flat replay.",
                )
            )
            summary = self._serialize_row(
                {
                    "primary_wipo_field": self._to_str(
                        context.get("primary_wipo_field_current") or context.get("primary_wipo_field"),
                        "Unknown",
                    ),
                    "covered_wipo_fields": context.get("covered_wipo_fields"),
                    "tech_breadth_wipo_count": self._to_int(context.get("family_tech_breadth_wipo_count"), 0),
                    **self.repository.get_family_classification_snapshot(family_id, as_of_year=as_of_year),
                }
            )
            rows = [self._serialize_row(row) for row in self.repository.get_family_field_rows(family_id, as_of_year=as_of_year)]
            series = [self._serialize_row(row) for row in self.repository.get_family_field_timeseries(family_id)]
        elif section == "legal":
            jurisdiction_rows = self.repository.get_family_jurisdiction_legal_rows(family_id, as_of_year=as_of_year)
            status_history_rows = self.repository.get_family_status_history(family_id)
            latest_event_date, latest_event_type = self._latest_dated_anchor(jurisdiction_rows)
            summary = self._serialize_row(
                {
                    "status": self._to_str(context.get("family_composite_status_asof") or context.get("family_composite_status")),
                    "active_jurisdiction_count": self._to_int(context.get("active_jurisdiction_count"), 0),
                    "active_grant_branch_count": self._to_int(context.get("active_grant_branch_count"), 0),
                    "lapsed_jurisdiction_count": self._to_int(context.get("lapsed_jurisdiction_count"), 0),
                    "opposed_branch_count": self._to_int(context.get("opposed_branch_count"), 0),
                    "coverage_stability_score": round(self._to_float(context.get("family_coverage_stability_score"), 0.0), 4),
                    "jurisdiction_footprint_count": len(jurisdiction_rows),
                    "status_history_points": len(status_history_rows),
                    "last_event_date": latest_event_date,
                    "last_event_type": latest_event_type,
                }
            )
            rows = [self._serialize_row(row) for row in jurisdiction_rows]
            series = [
                self._serialize_row(
                    {
                        "series_kind": "status_history",
                        **row,
                    }
                )
                for row in status_history_rows
            ]
            support_level = SupportLevel.moderate if jurisdiction_rows else SupportLevel.limited
            caveats.append(
                Caveat(
                    code="jurisdiction_legal_contribution",
                    title="Jurisdiction legal view is contribution-based",
                    detail="Jurisdiction legal rows show each office contribution into family-level enforceability. Relative strength is normalized only within this family footprint, not as a universal 0-100 office truth score.",
                )
            )
            if not jurisdiction_rows:
                caveats.append(
                    Caveat(
                        code="jurisdiction_footprint_unavailable",
                        title="Jurisdiction legal footprint unavailable",
                        detail="No jurisdiction-level enforceability rows were found for the selected family snapshot.",
                    )
                )
        elif section == "timeseries":
            blocking_rows = self.repository.get_family_blocking_timeseries(family_id)
            field_rows = self.repository.get_family_field_timeseries(family_id)
            series = [
                self._serialize_row(
                    {
                        "series_kind": "blocking_history",
                        **row,
                    }
                )
                for row in blocking_rows
            ]
            series.extend(
                self._serialize_row(
                    {
                        "series_kind": "field_history",
                        **row,
                    }
                )
                for row in field_rows
            )
            blocking_years = [self._to_int(row.get("snapshot_year"), 0) for row in blocking_rows if self._to_int(row.get("snapshot_year"), 0) > 0]
            field_years = [self._to_int(row.get("snapshot_year"), 0) for row in field_rows if self._to_int(row.get("snapshot_year"), 0) > 0]
            trajectory_years = sorted({*blocking_years, *field_years})
            summary = {
                "blocking_history_points": len(blocking_rows),
                "field_history_rows": len(field_rows),
                "field_history_years": len(set(field_years)),
                "first_trajectory_year": trajectory_years[0] if trajectory_years else None,
                "latest_trajectory_year": trajectory_years[-1] if trajectory_years else None,
            }
            if not blocking_rows:
                caveats.append(
                    Caveat(
                        code="blocking_trajectory_unavailable",
                        title="Blocking trajectory unavailable",
                        detail="The rebuilt family blocking-history mart returned no rows for this family.",
                    )
                )
            if not field_rows:
                caveats.append(
                    Caveat(
                        code="field_trajectory_unavailable",
                        title="Field trajectory unavailable",
                        detail="The family field-contribution timeseries mart returned no rows for this family.",
                    )
                )
        elif section == "members":
            member_rows, total_count = self._get_family_member_publications(
                family_id,
                limit=safe_limit,
                offset=safe_offset,
            )
            rows = [self._serialize_row(row) for row in member_rows]
            summary = self._serialize_row(self._get_family_member_publication_summary(family_id))
            pagination = PaginationMetadata(
                limit=safe_limit,
                offset=safe_offset,
                returned_count=len(rows),
                total_count=total_count,
            )
        elif section == "semantic_context":
            summary = self._serialize_row(
                {
                    "is_semantic_candidate": self._to_bool(context.get("is_semantic_candidate")),
                    "is_in_vector_sample": self._to_bool(context.get("is_in_vector_sample")),
                    "scope_type": self._to_str(context.get("scope_type")),
                }
            )
            caveats.append(
                Caveat(
                    code="semantic_contract_pending",
                    title="Semantic evidence contract is pending",
                    detail="Family semantic status is exposed now, but the deeper publication-backed evidence drilldown still needs the dedicated publication workspace.",
                )
            )
        elif section == "forecasts":
            forecast_rows = self.repository.get_family_forecasts(family_id)
            lapse_rows = self.repository.get_family_lapse_risk_rows(family_id)
            rows = [
                self._serialize_row(
                    {
                        **row,
                        "coverage_available": True,
                    }
                )
                for row in forecast_rows
            ]
            series = [
                self._serialize_row(
                    {
                        "series_kind": "lapse_risk",
                        **row,
                        "probability_display_allowed": self._to_str(row.get("office_support_level")).lower() in {"strong", "high"},
                    }
                )
                for row in lapse_rows
            ]
            summary = {
                "forecast_available": bool(forecast_rows),
                "lapse_available": bool(lapse_rows),
                "forecast_horizons": [self._to_str(row.get("horizon")) for row in forecast_rows],
                "lapse_horizons": sorted({self._to_str(row.get("horizon")) for row in lapse_rows}),
                "data_completeness_pct": round(self._to_float(context.get("data_completeness_pct_asof"), 0.0), 4),
            }
            support_level = self._support_level_from_rows(lapse_rows) if lapse_rows else SupportLevel.moderate
            if not forecast_rows:
                caveats.append(
                    Caveat(
                        code="forecast_unavailable",
                        title="Citation forecast unavailable",
                        detail="This family has no current phase-03 citation forecast rows, so the family page should not present forecast as a guaranteed workspace block.",
                    )
                )
        elif section == "citations":
            family_list_limit = max(1, min(int(limit), 1000))
            summary = self._curated_family_citation_summary(
                self.repository.get_family_citation_metrics(family_id),
                self.repository.get_family_citation_event_summary(family_id),
            )
            rows = self._curated_family_citation_timeseries(self.repository.get_family_citation_chronology(family_id))
            top_cited_member_rows = self.repository.get_family_top_cited_members(family_id, limit=10)
            top_citing_owner_rows = self.repository.get_family_top_citing_owners(family_id, limit=100)
            citing_family_rows, citing_family_total_count = self.repository.get_family_citing_families(
                family_id,
                limit=family_list_limit,
                offset=safe_offset,
                owner_filter=owner_filter,
            )
            series = [
                self._serialize_row(
                    {
                        "series_kind": "top_cited_member",
                        **row,
                    }
                )
                for row in top_cited_member_rows
            ]
            series.extend(
                self._serialize_row(
                    {
                        "series_kind": "top_citing_owner",
                        **row,
                    }
                )
                for row in top_citing_owner_rows
            )
            series = [
                *series,
                *[
                    self._serialize_row(
                        {
                            "series_kind": "citing_family",
                            **row,
                        }
                    )
                    for row in citing_family_rows
                ],
            ]
            pagination = PaginationMetadata(
                limit=family_list_limit,
                offset=safe_offset,
                returned_count=len(citing_family_rows),
                total_count=citing_family_total_count,
            )
            caveats.append(
                Caveat(
                    code="citation_summary_curated_proxy",
                    title="Citation summary is curated for serving",
                    detail="The family citation panel exposes clean family counts, owner breadth, NPL grounding, and PIT-safe chronology only. Raw weighted and cohort-normalized intermediates remain hidden.",
                )
            )
            caveats.append(
                Caveat(
                    code="citing_family_list_clean_grain",
                    title="Citing-family list is clean family-level evidence",
                    detail="Rows are grouped one per external clean citing family, with owner reference and distinct cited-member breadth rather than publication-pair event rows.",
                )
            )
            caveats.append(
                Caveat(
                    code="citation_owner_ranking_excludes_unknown",
                    title="Citing-owner ranking excludes unknown owner labels",
                    detail="Top citing owners hide empty and placeholder owner labels so the family evidence lane stays interpretable.",
                )
            )
            if not summary:
                caveats.append(
                    Caveat(
                        code="citation_summary_unavailable",
                        title="Citation summary unavailable",
                        detail="The family citation mart returned no current row for this family.",
                    )
                )
        elif section == "classification":
            summary = self._serialize_row(self.repository.get_family_classification_snapshot(family_id, as_of_year=as_of_year))
            rows = [self._serialize_row(row) for row in self.repository.get_family_classification_timeseries(family_id)]
            caveats.append(
                Caveat(
                    code="stable_classification_replay",
                    title="Classification chronology is replayed",
                    detail="Historical classification visibility uses stable family classification replay, not dated code-mutation truth.",
                )
            )

        return FamilySectionResponse(
            family_id=family_id,
            summary=summary,
            rows=rows,
            series=series,
            meta=ResponseMeta(
                page=f"family.{section}",
                artifact_sources=self._artifact_sources(include_publication=section == "members"),
                support_level=support_level,
                caveats=caveats,
                pagination=pagination,
            ),
        )
