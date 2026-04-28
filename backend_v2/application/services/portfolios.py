from datetime import date
import re
from typing import Any

from domain.schemas.common import Caveat, CoverageMetadata, PageIdentity, PaginationMetadata, ResponseMeta, SupportLevel
from domain.schemas.portfolio import (
    PortfolioCountScopes,
    PortfolioFamiliesResponse,
    PortfolioFieldsResponse,
    PortfolioForecastResponse,
    PortfolioOverviewResponse,
    PortfolioOwnerSearchResponse,
    PortfolioOwnerSearchResult,
    PortfolioClassificationResponse,
    PortfolioClassificationTimeseries,
    PortfolioClassificationTimeseriesPoint,
    PortfolioClassificationRow,
    PortfolioSectionResponse,
    PortfolioStatusSlice,
    PortfolioSummaryCard,
    PortfolioThreatResponse,
)
from infrastructure.repositories.family_repository import FamilyRepository
from infrastructure.repositories.portfolio_repository import PortfolioRepository
from infrastructure.repositories.publication_repository import PublicationRepository


class PortfolioService:
    def __init__(
        self,
        repository: PortfolioRepository | None = None,
        family_repository: FamilyRepository | None = None,
        publication_repository: PublicationRepository | None = None,
    ) -> None:
        self.repository = repository or PortfolioRepository()
        self.family_repository = (
            family_repository
            if family_repository is not None
            else FamilyRepository() if isinstance(self.repository, PortfolioRepository) else None
        )
        self.publication_repository = (
            publication_repository
            if publication_repository is not None
            else PublicationRepository() if isinstance(self.repository, PortfolioRepository) else None
        )

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

    def _to_top_change(self, value: float | int | None) -> str:
        if value is None:
            return "flat"
        direction = self._to_float(value, default=0.0)
        if direction > 0.0:
            return "gain"
        if direction < 0.0:
            return "loss"
        return "flat"

    def _to_str(self, value: object, default: str = "") -> str:
        if value is None:
            return default
        text = str(value).strip()
        return text if text else default

    def _artifact_sources(self, include_publication: bool = False) -> list[str]:
        sources = [str(path) for path in self.repository.artifacts()]
        publication_artifacts = getattr(self.publication_repository, "artifacts", None)
        if include_publication and callable(publication_artifacts):
            sources.extend(str(path) for path in publication_artifacts())
        return list(dict.fromkeys(sources))

    def _representative_family_title(self, family_id: str) -> str | None:
        if self.publication_repository is None:
            return None
        try:
            publication_getter = getattr(self.publication_repository, "get_family_publications", None)
            if callable(publication_getter):
                member_rows, _ = publication_getter(int(family_id), limit=1, offset=0)
            elif self.family_repository is not None:
                member_rows, _ = self.family_repository.get_family_member_publications(family_id, limit=1, offset=0)
            else:
                return None
            if not member_rows:
                return None
            appln_id = member_rows[0].get("appln_id")
            normalized_appln_id = int(appln_id) if appln_id is not None else None
            if normalized_appln_id is None:
                return None
            title_row = self.publication_repository.get_title_for_application(normalized_appln_id)
            title_text = self._to_str((title_row or {}).get("title_text"))
            return title_text or None
        except (TypeError, ValueError):
            return None

    def _is_placeholder_owner(self, owner_name: str | None) -> bool:
        normalized = re.sub(r"[^A-Z0-9]+", "_", (owner_name or "").strip().upper()).strip("_")
        return normalized in {"", "_", "UNKNOWN", "UNKNOWN_OWNER", "UNASSIGNED"}

    def _to_series_point(self, row: dict[str, object]) -> PortfolioClassificationTimeseriesPoint:
        raw_portfolio = row.get("portfolio")
        return PortfolioClassificationTimeseriesPoint(
            year=self._to_int(row.get("year"), default=0),
            share=self._to_float(row.get("share"), default=0.0),
            portfolio=self._to_float(raw_portfolio, 0.0) if raw_portfolio is not None else None,
        )

    def _tone_from_value(self, value: Any) -> str:
        if value is None:
            return "neutral"
        try:
            numeric = float(value)
            if numeric >= 70:
                return "positive"
            if numeric <= 0:
                return "warning"
        except (TypeError, ValueError):
            pass
        return "neutral"

    def _support_from_status(self, status: Any) -> SupportLevel:
        normalized = str(status).strip().lower() if status is not None else ""
        if normalized in {"high", "strong"}:
            return SupportLevel.strong
        if normalized in {"medium", "moderate"}:
            return SupportLevel.moderate
        return SupportLevel.limited

    def _forecast_status_support(self, row: dict[str, object]) -> SupportLevel:
        status = row.get("portfolio_prediction_coverage_status")
        if status is not None:
            return self._support_from_status(status)

        coverage = self._forecast_family_coverage_pct(row)
        if coverage >= 0.75:
            return SupportLevel.strong
        if coverage >= 0.50:
            return SupportLevel.moderate
        return SupportLevel.limited

    def _forecast_family_coverage_pct(self, row: dict[str, object]) -> float:
        return self._to_float(
            row.get("portfolio_phase03_family_coverage_pct")
            or row.get("phase03_family_coverage_pct"),
            default=0.0,
        )

    def _to_year(self, value: Any) -> int | None:
        if value is None:
            return None
        if isinstance(value, str) and len(value) >= 4 and value[:4].isdigit():
            return int(value[:4])
        try:
            return int(value)
        except (TypeError, ValueError):
            if hasattr(value, "year"):
                return int(value.year)
        return None

    def _bounded_page(self, limit: int, offset: int, default_limit: int = 10, max_limit: int = 100) -> tuple[int, int]:
        safe_limit = max(1, min(self._to_int(limit, default_limit), max_limit))
        safe_offset = max(0, self._to_int(offset, 0))
        return safe_limit, safe_offset

    def _extract_total_count(self, rows: list[dict[str, object]]) -> int | None:
        if not rows:
            return 0
        return self._to_int(rows[0].get("total_count"), 0)

    def _clamp_pct(self, value: float | int | None, scale: float = 1.0) -> float:
        numeric = self._to_float(value, 0.0) * scale
        if numeric < 0:
            return 0.0
        if numeric > 100:
            return 100.0
        return numeric

    def _coverage_status_from_pct(self, pct: float) -> str:
        if pct >= 0.95:
            return "high"
        if pct >= 0.75:
            return "medium"
        if pct > 0.0:
            return "low"
        return "unknown"

    def _history_support_level(self, coverage_pct: float, owner_truth_pct: float) -> SupportLevel:
        if coverage_pct < 0.75:
            return SupportLevel.limited
        if owner_truth_pct >= 0.75:
            return SupportLevel.strong
        return SupportLevel.moderate

    def _ratio(self, numerator: int | float | None, denominator: int | float | None) -> float:
        safe_denominator = self._to_float(denominator, 0.0)
        if safe_denominator <= 0:
            return 0.0
        return self._to_float(numerator, 0.0) / safe_denominator

    def _format_count_ratio(self, count: int | float | None, denominator: int | float | None) -> str:
        safe_count = self._to_int(count, 0)
        ratio = self._ratio(count, denominator) * 100.0
        return f"{safe_count} ({ratio:.1f}%)"

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

    def _append_band_tooltip(self, tooltip: str, band_meta: dict[str, object]) -> str:
        band_label = self._to_str(band_meta.get("band_label"), "")
        peer_bucket_label = self._to_str(band_meta.get("peer_bucket_label"), "")
        peer_percentile = band_meta.get("peer_percentile")
        if not band_label or not peer_bucket_label or peer_percentile is None:
            return tooltip
        return (
            f"{tooltip} "
            f"Current band: {band_label}, based on the {peer_percentile:.1f} percentile within the {peer_bucket_label} peer bucket."
        )

    def _portfolio_percentile_primary_value(self, band_meta: dict[str, object], fallback_value: float, decimals: int = 1) -> str:
        peer_percentile = band_meta.get("peer_percentile")
        if peer_percentile is None:
            return f"{fallback_value:.{decimals}f}"
        return f"{self._to_float(peer_percentile, 0.0):.{decimals}f}%"

    def _portfolio_mass_card_band_meta(self, band_meta: dict[str, object]) -> dict[str, object]:
        return {
            "band_code": band_meta.get("band_code"),
            "band_label": band_meta.get("band_label"),
            "peer_bucket": band_meta.get("peer_bucket"),
            "peer_bucket_label": band_meta.get("peer_bucket_label"),
            "peer_percentile": band_meta.get("peer_percentile"),
        }

    def get_overview(self, owner_id: str, as_of_year: int | None = None) -> PortfolioOverviewResponse:
        summary_row = self.repository.get_owner_summary(owner_id, as_of_year=as_of_year)
        peer_context = self.repository.get_owner_summary_peer_context(owner_id, as_of_year=as_of_year)
        forecast_row = self.repository.get_owner_forecast_summary(owner_id, as_of_year=as_of_year)
        family_status_counts = self.repository.get_owner_family_status_counts(owner_id)
        in_scope_status_counts = self.repository.get_owner_in_scope_family_status_counts(owner_id)
        top_families = self.repository.get_owner_families(owner_id, as_of_year=as_of_year, limit=5)

        family_count = self._to_int(summary_row.get("portfolio_family_count_within_mega_cluster"))
        active_grant_family_count = self._to_int(summary_row.get("portfolio_active_grant_family_count"))
        semantic_candidate_count = self._to_int(summary_row.get("semantic_candidate_family_count"))
        primary_owner_family_count = self._to_int(family_status_counts.get("family_count"), 0)
        status_denominator = primary_owner_family_count or family_count
        in_scope_pending_family_count = self._to_int(in_scope_status_counts.get("pending_family_count"), 0)
        fully_active_family_count = self._to_int(in_scope_status_counts.get("active_family_count"), 0)
        under_fire_family_count = self._to_int(in_scope_status_counts.get("under_fire_family_count"), 0)
        partially_lapsed_family_count = self._to_int(in_scope_status_counts.get("partially_lapsed_family_count"), 0)
        dead_family_count = self._to_int(in_scope_status_counts.get("dead_family_count"), 0)
        status_mix_total = (
            in_scope_pending_family_count
            + fully_active_family_count
            + under_fire_family_count
            + partially_lapsed_family_count
            + dead_family_count
        )
        unclassified_family_count = max(family_count - status_mix_total, 0)
        status_mix = [
            PortfolioStatusSlice(
                key="pending_emerging",
                label="Pending / filing",
                count=in_scope_pending_family_count,
                share=(in_scope_pending_family_count / status_mix_total) if status_mix_total else 0.0,
            ),
            PortfolioStatusSlice(
                key="fully_active",
                label="Fully active",
                count=fully_active_family_count,
                share=(fully_active_family_count / status_mix_total) if status_mix_total else 0.0,
            ),
            PortfolioStatusSlice(
                key="under_fire",
                label="Under fire",
                count=under_fire_family_count,
                share=(under_fire_family_count / status_mix_total) if status_mix_total else 0.0,
            ),
            PortfolioStatusSlice(
                key="partially_lapsed",
                label="Partially lapsed",
                count=partially_lapsed_family_count,
                share=(partially_lapsed_family_count / status_mix_total) if status_mix_total else 0.0,
            ),
            PortfolioStatusSlice(
                key="dead",
                label="Dead",
                count=dead_family_count,
                share=(dead_family_count / status_mix_total) if status_mix_total else 0.0,
            ),
        ]
        total_mass_band = self._portfolio_metric_band_meta(
            peer_context,
            "portfolio_total_mass_score",
            "portfolio_total_mass_score_percentile",
        )
        threat_band = self._portfolio_metric_band_meta(
            peer_context,
            "portfolio_current_threat_score",
            "portfolio_current_threat_score_percentile",
        )
        heritage_band = self._portfolio_metric_band_meta(
            peer_context,
            "portfolio_heritage_score",
            "portfolio_heritage_score_percentile",
        )

        support_level = self._forecast_status_support(forecast_row)
        if family_count == 0 and active_grant_family_count == 0 and semantic_candidate_count == 0:
            return PortfolioOverviewResponse(
                identity=PageIdentity(
                    id=owner_id,
                    label=owner_id.replace("_", " ").title(),
                    page_kind="portfolio",
                    selected_year=as_of_year,
                ),
                family_count=0,
                count_scopes=PortfolioCountScopes(
                    in_scope_family_count=0,
                    primary_owner_family_count=0,
                    active_grant_family_count=0,
                    semantic_candidate_family_count=0,
                    pending_family_count=0,
                    unclassified_family_count=0,
                ),
                active_grant_family_count=0,
                semantic_candidate_count=0,
                summary_cards=[],
                status_mix=[],
                top_family_preview=[],
                meta=ResponseMeta(
                    page="portfolio.overview",
                    artifact_sources=[str(path) for path in self.repository.artifacts()],
                    support_level=support_level,
                    caveats=[
                        Caveat(
                            code="owner_unknown",
                            title="Owner not found",
                            detail="No current owner slice is available for this owner id in the selected scope.",
                        )
                    ],
                ),
            )

        summary_cards = [
            PortfolioSummaryCard(
                key="portfolio_family_count_within_mega_cluster",
                label="In-Scope Families",
                value=str(family_count),
                tooltip="How many patent families are currently included in this portfolio view.",
            ),
            PortfolioSummaryCard(
                key="portfolio_primary_owner_family_count",
                label="Primary-Owner Families",
                value=str(primary_owner_family_count),
                tooltip="How many families this owner is currently treated as the lead owner of.",
            ),
            PortfolioSummaryCard(
                key="semantic_candidate_family_count",
                label="Semantic Candidate Families",
                value=self._format_count_ratio(semantic_candidate_count, family_count or status_denominator),
                tooltip="How many in-scope families have enough structured technical signal to support semantic search and prediction features.",
            ),
            PortfolioSummaryCard(
                key="portfolio_total_mass_score",
                label="Granted Blocking Mass",
                value=self._portfolio_percentile_primary_value(
                    total_mass_band,
                    self._to_float(summary_row.get("portfolio_total_mass_score", 0), 0),
                    decimals=1,
                ),
                tooltip=self._append_band_tooltip(
                    f"How large and defensible the granted portfolio's blocking footprint is relative to similar-sized portfolios. Higher means more of the granted families contribute meaningful blocking strength. Raw mass: {self._to_float(summary_row.get('portfolio_total_mass_score', 0), 0):.1f}.",
                    total_mass_band,
                ),
                caveat="Peer-relative percentile",
                **self._portfolio_mass_card_band_meta(total_mass_band),
            ),
            PortfolioSummaryCard(
                key="portfolio_current_threat_score",
                label="Granted Threat Mass",
                value=self._portfolio_percentile_primary_value(
                    threat_band,
                    self._to_float(summary_row.get("portfolio_current_threat_score", 0), 0),
                    decimals=1,
                ),
                tooltip=self._append_band_tooltip(
                    f"How much current market-facing pressure the granted portfolio carries relative to similar-sized portfolios. Higher means more of the granted families sit in strategically threatening positions. Raw mass: {self._to_float(summary_row.get('portfolio_current_threat_score', 0), 0):.1f}.",
                    threat_band,
                ),
                caveat="Peer-relative percentile",
                **self._portfolio_mass_card_band_meta(threat_band),
            ),
            PortfolioSummaryCard(
                key="portfolio_heritage_score",
                label="Citation Heritage Mass",
                value=self._portfolio_percentile_primary_value(
                    heritage_band,
                    self._to_float(summary_row.get("portfolio_heritage_score", 0), 0),
                    decimals=1,
                ),
                tooltip=self._append_band_tooltip(
                    f"How much accumulated citation legacy the portfolio has relative to similar-sized portfolios. Higher means the portfolio's families have built stronger downstream citation influence over time. Raw mass: {self._to_float(summary_row.get('portfolio_heritage_score', 0), 0):.2f}.",
                    heritage_band,
                ),
                caveat="Peer-relative percentile",
                **self._portfolio_mass_card_band_meta(heritage_band),
            ),
        ]

        mapped_top_families = []
        for row in top_families:
            mapped_top_families.append(
                {
                    "family_id": str(row.get("family_id", "")),
                    "owner_weight": self._to_float(row.get("owner_weight"), 0),
                    "blocking_score": self._to_float(row.get("blocking_score"), 0),
                    "status": str(row.get("status", "unknown")),
                    "heritage": str(row.get("heritage", "unknown")),
                    "primary_field": str(row.get("primary_field", "unknown")),
                    "forecast_contributor": self._to_float(row.get("forecast_contributor"), 0),
                }
            )

        caveats = [
            Caveat(
                code="current_owner_replay",
                title="Current-owner replay",
                detail="Portfolio history is currently replayed from current owner bridge for years where historical owner truth is unavailable.",
            ),
            Caveat(
                code="mixed_metric_scales",
                title="Mixed metric scales",
                detail="Overview cards combine bounded counts and ratios with unbounded mass indices; values should not be interpreted as a shared score scale.",
            ),
            Caveat(
                code="count_scope_split",
                title="Count scopes differ",
                detail="In-scope portfolio families, primary-owner families, and citation-family counts are related but not identical scopes. The family status distribution uses in-scope portfolio families; owner bridge totals and family drilldowns may use primary-owner scope.",
            ),
            Caveat(
                code="peer_relative_bands",
                title="Peer-relative bands",
                detail="Qualitative bands on unbounded portfolio indices are percentile-based within portfolio-size peer buckets; the raw values remain the source evidence.",
            ),
            Caveat(
                code="executive_metric_audit",
                title="Executive metric audit",
                detail="Blocking-rank-derived portfolio cards are temporarily withheld from the executive surface pending upstream family-score normalization fixes.",
            ),
        ]
        forecast_caveat = str(forecast_row.get("coverage_caveat_text", "")).strip()
        if forecast_caveat:
            caveats.append(
                Caveat(
                    code="forecast_coverage",
                    title="Forecast coverage",
                    detail=forecast_caveat,
                )
            )

        return PortfolioOverviewResponse(
            identity=PageIdentity(
                id=str(summary_row.get("owner_name_harmonized", owner_id)),
                label=str(summary_row.get("owner_name_display", owner_id)).replace("_", " ").title(),
                page_kind="portfolio",
                selected_year=as_of_year or self._to_year(summary_row.get("snapshot_date")),
            ),
            summary_cards=summary_cards,
            status_mix=status_mix,
            family_count=family_count,
            count_scopes=PortfolioCountScopes(
                in_scope_family_count=family_count,
                primary_owner_family_count=primary_owner_family_count,
                active_grant_family_count=active_grant_family_count,
                semantic_candidate_family_count=semantic_candidate_count,
                pending_family_count=in_scope_pending_family_count,
                unclassified_family_count=unclassified_family_count,
            ),
            active_grant_family_count=active_grant_family_count,
            semantic_candidate_count=semantic_candidate_count,
            top_family_preview=mapped_top_families,
            meta=ResponseMeta(
                page="portfolio.overview",
                artifact_sources=[str(path) for path in self.repository.artifacts()],
                support_level=support_level,
                coverage=CoverageMetadata(
                    status=str(forecast_row.get("portfolio_prediction_coverage_status", "unknown")),
                    pct=self._forecast_family_coverage_pct(forecast_row),
                    covered_count=self._to_int(forecast_row.get("phase03_family_covered_count")),
                    denominator_count=self._to_int(forecast_row.get("phase03_family_denominator_count")),
                    caveat_text=forecast_caveat or None,
                ),
                caveats=caveats,
            ),
        )

    def search_owners(self, query: str, limit: int = 8) -> PortfolioOwnerSearchResponse:
        rows = self.repository.search_owners(query=query, limit=limit)
        return PortfolioOwnerSearchResponse(
            query=(query or "").strip(),
            rows=[
                PortfolioOwnerSearchResult(
                    owner_id=self._to_str(row.get("owner_name_harmonized"), ""),
                    label=self._to_str(row.get("owner_name_display"), self._to_str(row.get("owner_name_harmonized"), "")),
                    family_count=self._to_int(row.get("family_count"), 0),
                )
                for row in rows
                if self._to_str(row.get("owner_name_harmonized"), "")
                and not self._is_placeholder_owner(self._to_str(row.get("owner_name_harmonized"), ""))
            ],
            meta=ResponseMeta(
                page="portfolio.search",
                artifact_sources=[str(path) for path in self.repository.artifacts()],
            ),
        )

    def get_families(
        self,
        owner_id: str,
        as_of_year: int | None = None,
        limit: int = 10,
        offset: int = 0,
        q: str | None = None,
        status: str | None = None,
        primary_field: str | None = None,
        sort: str | None = None,
    ) -> PortfolioFamiliesResponse:
        safe_limit, safe_offset = self._bounded_page(limit, offset)
        rows = self.repository.get_owner_families(
            owner_id,
            as_of_year=as_of_year,
            limit=safe_limit,
            offset=safe_offset,
            q=q,
            status=status,
            primary_field=primary_field,
            sort=sort,
        )
        title_map = {
            family_id: self._representative_family_title(family_id)
            for family_id in {
                self._to_str(row.get("family_id"))
                for row in rows
                if self._to_str(row.get("family_id"))
            }
        }
        return PortfolioFamiliesResponse(
            owner_id=owner_id,
            rows=[
                {
                    "family_id": str(row.get("family_id", "")),
                    "owner_weight": self._to_float(row.get("owner_weight"), 0),
                    "blocking_score": self._to_float(row.get("blocking_score"), 0),
                    "status": str(row.get("status", "unknown")),
                    "heritage": str(row.get("heritage", "unknown")),
                    "priority_year": str(row.get("priority_year", row.get("heritage", "unknown"))),
                    "title": self._to_str(title_map.get(self._to_str(row.get("family_id"))), ""),
                    "primary_field": str(row.get("primary_field", "unknown")),
                    "forecast_contributor": self._to_float(row.get("forecast_contributor"), 0),
                }
                for row in rows
            ],
            meta=ResponseMeta(
                page="portfolio.families",
                artifact_sources=self._artifact_sources(include_publication=True),
                pagination=PaginationMetadata(
                    limit=safe_limit,
                    offset=safe_offset,
                    returned_count=len(rows),
                    total_count=self._extract_total_count(rows),
                ),
            ),
        )

    def get_fields(self, owner_id: str, as_of_year: int | None = None) -> PortfolioFieldsResponse:
        rows = self.repository.get_owner_fields(owner_id, as_of_year=as_of_year, limit=30)
        return PortfolioFieldsResponse(
            owner_id=owner_id,
            rows=[
                {
                    "field": str(row.get("field", "unknown")),
                    "active_families": self._to_int(row.get("active_families"), 0),
                    "active_share": self._to_float(row.get("active_share"), 0),
                    "hotspot_direction": str(row.get("hotspot_direction", "stable")),
                    "change_12m": self._to_float(row.get("change_12m"), 0),
                    "confidence": self._support_from_status(row.get("confidence")),
                }
                for row in rows
            ],
            meta=ResponseMeta(
                page="portfolio.fields",
                artifact_sources=[str(path) for path in self.repository.artifacts()],
                caveats=[
                    Caveat(
                        code="classification_visibility",
                        title="First-seen classification visibility",
                        detail="Field mix follows first-seen classifications and current owner bridge replay where historical owner mapping is not yet first-order truth.",
                    )
                ],
            ),
        )

    def get_field_timeseries(
        self,
        owner_id: str,
        as_of_year: int | None = None,
        limit_fields: int = 8,
    ) -> PortfolioSectionResponse:
        rows = self.repository.get_owner_field_timeseries(owner_id, as_of_year=as_of_year, limit_fields=limit_fields)
        return PortfolioSectionResponse(
            owner_id=owner_id,
            rows=[
                {
                    "snapshot_date": str(row.get("snapshot_date", "")),
                    "wipo_field": self._to_str(row.get("wipo_field"), "unknown"),
                    "active_family_count": self._to_int(row.get("active_family_count"), 0),
                    "active_share": self._to_float(row.get("active_share"), 0.0),
                    "enforceability_score": self._to_float(row.get("enforceability_score"), 0.0),
                    "heritage_score": self._to_float(row.get("heritage_score"), 0.0),
                }
                for row in rows
            ],
            meta=ResponseMeta(
                page="portfolio.field_timeseries",
                artifact_sources=[str(path) for path in self.repository.artifacts()],
                caveats=[
                    Caveat(
                        code="current_owner_replay",
                        title="Current-owner replay",
                        detail="Historical field chronology is still replayed through current owner membership rather than true historical ownership truth.",
                    )
                ],
            ),
        )

    def get_citation_summary(
        self,
        owner_id: str,
        as_of_year: int | None = None,
    ) -> PortfolioSectionResponse:
        row = self.repository.get_owner_citation_summary(owner_id, as_of_year=as_of_year)
        has_summary = bool(row) and (
            self._to_int(row.get("family_count"), 0) > 0
            or self._to_int(row.get("as_of_year"), 0) > 0
        )
        return PortfolioSectionResponse(
            owner_id=owner_id,
            rows=(
                [
                    {
                        "as_of_year": self._to_int(row.get("as_of_year"), 0),
                        "family_count": self._to_int(row.get("family_count"), 0),
                        "forward_citations_clean_total": self._to_float(row.get("forward_citations_clean_total"), 0.0),
                        "forward_citations_weighted_total": self._to_float(row.get("forward_citations_weighted_total"), 0.0),
                        "backward_citations_clean_total": self._to_float(row.get("backward_citations_clean_total"), 0.0),
                        "backward_npl_citation_total": self._to_float(row.get("backward_npl_citation_total"), 0.0),
                        "distinct_citing_family_count": self._to_int(row.get("distinct_citing_family_count"), 0),
                        "distinct_cited_family_count": self._to_int(row.get("distinct_cited_family_count"), 0),
                        "avg_science_grounding_score": self._to_float(row.get("avg_science_grounding_score"), 0.0),
                        "avg_generality_percentile": self._to_float(row.get("avg_generality_percentile"), 0.0),
                        "avg_originality_percentile": self._to_float(row.get("avg_originality_percentile"), 0.0),
                        "avg_unique_citing_family_count": self._to_float(row.get("avg_unique_citing_family_count"), 0.0),
                        "avg_citing_assignee_diversity": self._to_float(row.get("avg_citing_assignee_diversity"), 0.0),
                        "avg_attacker_density_score": self._to_float(row.get("avg_attacker_density_score"), 0.0),
                        "avg_out_of_bounds_citation_share": self._to_float(row.get("avg_out_of_bounds_citation_share"), 0.0),
                    }
                ]
                if has_summary
                else []
            ),
            meta=ResponseMeta(
                page="portfolio.citation_summary",
                artifact_sources=[str(path) for path in self.repository.artifacts()],
                caveats=[
                    Caveat(
                        code="current_owner_replay",
                        title="Current-owner replay",
                        detail="Portfolio citation summaries are aggregated through current owner-family membership rather than true historical owner intervals.",
                    ),
                    Caveat(
                        code="backward_current_summary",
                        title="Backward NPL is current-summary-first",
                        detail="Patent forward/backward counts are aligned to the selected owner-year family scope. Backward NPL remains a current portfolio summary rather than a full owner-year history.",
                    ),
                ],
            ),
        )

    def get_citation_timeseries(
        self,
        owner_id: str,
        year_from: int | None = None,
        year_to: int | None = None,
    ) -> PortfolioSectionResponse:
        rows = self.repository.get_owner_citation_timeseries(owner_id, year_from=year_from, year_to=year_to)
        return PortfolioSectionResponse(
            owner_id=owner_id,
            rows=[
                {
                    "as_of_year": self._to_int(row.get("as_of_year"), 0),
                    "family_count": self._to_int(row.get("family_count"), 0),
                    "forward_citations_clean_total": self._to_float(row.get("forward_citations_clean_total"), 0.0),
                    "forward_citations_weighted_total": self._to_float(row.get("forward_citations_weighted_total"), 0.0),
                    "avg_unique_citing_family_count": self._to_float(row.get("avg_unique_citing_family_count"), 0.0),
                    "avg_citing_assignee_diversity": self._to_float(row.get("avg_citing_assignee_diversity"), 0.0),
                    "avg_attacker_density_score": self._to_float(row.get("avg_attacker_density_score"), 0.0),
                }
                for row in rows
            ],
            meta=ResponseMeta(
                page="portfolio.citation_timeseries",
                artifact_sources=[str(path) for path in self.repository.artifacts()],
                caveats=[
                    Caveat(
                        code="current_owner_replay",
                        title="Current-owner replay",
                        detail="Portfolio citation chronology is replayed through current owner-family membership over PIT family snapshots.",
                    )
                ],
            ),
        )

    def get_citation_families(
        self,
        owner_id: str,
        limit: int = 10,
        offset: int = 0,
        wipo_field: str | None = None,
        status: str | None = None,
        sort: str | None = None,
    ) -> PortfolioSectionResponse:
        safe_limit, safe_offset = self._bounded_page(limit, offset)
        rows = self.repository.get_owner_citation_families(
            owner_id,
            limit=safe_limit,
            offset=safe_offset,
            wipo_field=wipo_field,
            status=status,
            sort=sort,
        )
        return PortfolioSectionResponse(
            owner_id=owner_id,
            rows=[
                {
                    "family_id": self._to_str(row.get("family_id"), ""),
                    "family_priority_year": self._to_int(row.get("family_priority_year"), 0),
                    "primary_field": self._to_str(row.get("primary_field"), ""),
                    "status": self._to_str(row.get("status"), "unknown"),
                    "forward_citations_clean": self._to_float(row.get("forward_citations_clean"), 0.0),
                    "forward_citations_weighted": self._to_float(row.get("forward_citations_weighted"), 0.0),
                    "early_citations_5y": self._to_float(row.get("early_citations_5y"), 0.0),
                    "early_citations_7y": self._to_float(row.get("early_citations_7y"), 0.0),
                    "unique_citing_family_count": self._to_float(row.get("unique_citing_family_count"), 0.0),
                    "citing_assignee_diversity": self._to_float(row.get("citing_assignee_diversity"), 0.0),
                    "blocking_score": self._to_float(row.get("blocking_score"), 0.0),
                }
                for row in rows
            ],
            meta=ResponseMeta(
                page="portfolio.citation_families",
                artifact_sources=[str(path) for path in self.repository.artifacts()],
                pagination=PaginationMetadata(
                    limit=safe_limit,
                    offset=safe_offset,
                    returned_count=len(rows),
                    total_count=self._extract_total_count(rows),
                ),
                caveats=[
                    Caveat(
                        code="family_collapsed_citations",
                        title="Family-collapsed citations",
                        detail="Ranking reflects citations aggregated to the family level, including family-member publications rather than a single publication only.",
                    ),
                    Caveat(
                        code="current_owner_replay",
                        title="Current-owner replay",
                        detail="Portfolio family membership is replayed through the current owner bridge rather than true historical ownership intervals.",
                    ),
                    Caveat(
                        code="blocking_secondary",
                        title="Blocking is secondary context",
                        detail="Citation rank is the primary sort surface. Blocking remains a secondary contextual proxy, not the ranking truth.",
                    ),
                ],
            ),
        )

    def get_filing_timeseries(
        self,
        owner_id: str,
        year_from: int | None = None,
        year_to: int | None = None,
    ) -> PortfolioSectionResponse:
        latest_complete_filing_year = date.today().year - 2
        safe_year_to = min(year_to, latest_complete_filing_year) if year_to is not None else latest_complete_filing_year
        rows = self.repository.get_owner_filing_timeseries(owner_id, year_from=year_from, year_to=safe_year_to)
        rows = [
            row
            for row in rows
            if self._to_int(row.get("filing_year") or row.get("year"), 0) <= safe_year_to
        ]
        return PortfolioSectionResponse(
            owner_id=owner_id,
            rows=[
                {
                    "year": self._to_int(row.get("filing_year") or row.get("year"), 0),
                    "family_filing_count": self._to_int(row.get("family_filing_count"), 0),
                    "cumulative_family_count": self._to_int(row.get("cumulative_family_count"), 0),
                    "rolling_3y_family_filing_count": self._to_int(row.get("rolling_3y_family_filing_count"), 0),
                    "prior_3y_family_filing_count": self._to_int(row.get("prior_3y_family_filing_count"), 0),
                    "rolling_3y_change_pct": self._to_float(row.get("rolling_3y_change_pct"), 0.0),
                    "momentum_direction": self._to_str(row.get("momentum_direction"), "stable"),
                }
                for row in rows
            ],
            meta=ResponseMeta(
                page="portfolio.filing_timeseries",
                artifact_sources=[str(path) for path in self.repository.artifacts()],
                caveats=[
                    Caveat(
                        code="priority_year_anchor",
                        title="Family-priority-year chronology",
                        detail="Filing chronology is anchored on family filing year rather than publication year, so one family is counted once at its filing anchor.",
                    ),
                    Caveat(
                        code="current_owner_replay",
                        title="Current-owner replay",
                        detail="Portfolio filing history is replayed through the current owner-family bridge rather than true historical owner intervals.",
                    ),
                    Caveat(
                        code="last_complete_filing_year",
                        title="Shown through last complete filing year",
                        detail=f"Latest visible filing year is capped at {latest_complete_filing_year} to avoid partial latest-year undercount.",
                    ),
                    Caveat(
                        code="historical_strength_not_forecast",
                        title="Historical strength view",
                        detail="This is a descriptive filing-strength history view, not a forecast promise.",
                    ),
                ],
            ),
        )

    def get_status_timeseries(
        self,
        owner_id: str,
        year_from: int | None = None,
        year_to: int | None = None,
    ) -> PortfolioSectionResponse:
        rows = self.repository.get_owner_status_timeseries(owner_id, year_from=year_from, year_to=year_to)
        audited_years = len(rows)
        covered_years = sum(1 for row in rows if self._to_float(row.get("status_coverage_pct"), 0.0) >= 0.95)
        avg_status_coverage_pct = (
            sum(self._to_float(row.get("status_coverage_pct"), 0.0) for row in rows) / audited_years if audited_years else 0.0
        )
        avg_owner_truth_pct = (
            sum(self._to_float(row.get("historical_owner_truth_supported_pct"), 0.0) for row in rows) / audited_years
            if audited_years
            else 0.0
        )
        avg_current_owner_metadata_only_pct = (
            sum(self._to_float(row.get("current_owner_metadata_only_pct"), 0.0) for row in rows) / audited_years
            if audited_years
            else 0.0
        )
        support_level = self._history_support_level(avg_status_coverage_pct, avg_owner_truth_pct)

        return PortfolioSectionResponse(
            owner_id=owner_id,
            rows=[
                {
                    "as_of_year": self._to_int(row.get("as_of_year"), 0),
                    "current_snapshot_date": self._to_str(row.get("current_snapshot_date"), ""),
                    "family_count": self._to_int(row.get("family_count"), 0),
                    "pending_family_count": self._to_int(row.get("pending_family_count"), 0),
                    "fully_active_family_count": self._to_int(row.get("fully_active_family_count"), 0),
                    "under_fire_family_count": self._to_int(row.get("under_fire_family_count"), 0),
                    "partially_lapsed_family_count": self._to_int(row.get("partially_lapsed_family_count"), 0),
                    "dead_family_count": self._to_int(row.get("dead_family_count"), 0),
                    "pending_share": self._ratio(row.get("pending_family_count"), row.get("family_count")),
                    "fully_active_share": self._ratio(row.get("fully_active_family_count"), row.get("family_count")),
                    "under_fire_share": self._ratio(row.get("under_fire_family_count"), row.get("family_count")),
                    "partially_lapsed_share": self._ratio(row.get("partially_lapsed_family_count"), row.get("family_count")),
                    "dead_share": self._ratio(row.get("dead_family_count"), row.get("family_count")),
                    "status_coverage_pct": self._to_float(row.get("status_coverage_pct"), 0.0),
                    "owner_identity_coverage_pct": self._to_float(row.get("owner_identity_coverage_pct"), 0.0),
                    "historical_owner_truth_supported_pct": self._to_float(
                        row.get("historical_owner_truth_supported_pct"),
                        0.0,
                    ),
                    "current_owner_metadata_only_pct": self._to_float(row.get("current_owner_metadata_only_pct"), 0.0),
                    "avg_data_completeness_pct_asof": self._to_float(row.get("avg_data_completeness_pct_asof"), 0.0),
                }
                for row in rows
            ],
            meta=ResponseMeta(
                page="portfolio.status_timeseries",
                artifact_sources=[str(path) for path in self.repository.artifacts()],
                support_level=support_level,
                coverage=CoverageMetadata(
                    status=self._coverage_status_from_pct(avg_status_coverage_pct),
                    pct=avg_status_coverage_pct,
                    covered_count=covered_years,
                    denominator_count=audited_years,
                    caveat_text=(
                        "Status chronology is complete across the returned PIT years, but owner history is replayed from current owner metadata rather than true historical owner intervals."
                        if audited_years
                        else "No PIT family-status chronology is available for this owner in the current compare mart."
                    ),
                ),
                caveats=[
                    Caveat(
                        code="current_owner_replay",
                        title="Current-owner replay",
                        detail="Historical family status counts are replayed through current owner membership from the family compare PIT, not from historical owner truth intervals.",
                    ),
                    Caveat(
                        code="pit_status_counts",
                        title="PIT status counts",
                        detail="Rows reflect yearly family state snapshots rather than document-by-document legal event chronology.",
                    ),
                    Caveat(
                        code="owner_truth_support",
                        title="Historical owner truth is limited",
                        detail=(
                            f"Average historical-owner-truth support across the returned years is {avg_owner_truth_pct:.1%}; "
                            f"current-owner-metadata-only replay averages {avg_current_owner_metadata_only_pct:.1%}."
                        ),
                    ),
                ],
            ),
        )

    def get_jurisdiction_unlock_history(
        self,
        owner_id: str,
        year_from: int | None = None,
        year_to: int | None = None,
        jurisdiction_limit: int = 20,
    ) -> PortfolioSectionResponse:
        payload = self.repository.get_owner_jurisdiction_unlock_history(
            owner_id,
            year_from=year_from,
            year_to=year_to,
            jurisdiction_limit=jurisdiction_limit,
        )
        status_rows = self.repository.get_owner_status_timeseries(owner_id, year_from=year_from, year_to=year_to)
        audited_years = len(status_rows)
        covered_years = sum(
            1 for row in status_rows if self._to_float(row.get("status_coverage_pct"), 0.0) >= 0.95
        )
        avg_status_coverage_pct = (
            sum(self._to_float(row.get("status_coverage_pct"), 0.0) for row in status_rows) / audited_years
            if audited_years
            else 0.0
        )
        avg_owner_truth_pct = (
            sum(self._to_float(row.get("historical_owner_truth_supported_pct"), 0.0) for row in status_rows) / audited_years
            if audited_years
            else 0.0
        )
        support_level = self._history_support_level(avg_status_coverage_pct, avg_owner_truth_pct)
        summary = payload.get("summary", {}) if isinstance(payload, dict) else {}
        year_rows = payload.get("years", []) if isinstance(payload, dict) else []
        jurisdiction_rows = payload.get("jurisdictions", []) if isinstance(payload, dict) else []

        rows: list[dict[str, object]] = []
        if summary:
            rows.append(
                {
                    "kind": "summary",
                    "unlocked_jurisdiction_count": self._to_int(summary.get("unlocked_jurisdiction_count"), 0),
                    "first_unlock_year": self._to_int(summary.get("first_unlock_year"), 0),
                    "latest_unlock_year": self._to_int(summary.get("latest_unlock_year"), 0),
                    "latest_presence_year": self._to_int(summary.get("latest_presence_year"), 0),
                    "latest_active_jurisdiction_count": self._to_int(summary.get("latest_active_jurisdiction_count"), 0),
                    "latest_pending_jurisdiction_count": self._to_int(summary.get("latest_pending_jurisdiction_count"), 0),
                    "latest_lapsed_jurisdiction_count": self._to_int(summary.get("latest_lapsed_jurisdiction_count"), 0),
                    "ever_active_jurisdiction_count": self._to_int(summary.get("ever_active_jurisdiction_count"), 0),
                    "active_family_observations": self._to_int(summary.get("active_family_observations"), 0),
                    "pending_family_observations": self._to_int(summary.get("pending_family_observations"), 0),
                    "lapsed_family_observations": self._to_int(summary.get("lapsed_family_observations"), 0),
                }
            )
        rows.extend(
            {
                "kind": "year",
                "as_of_year": self._to_int(row.get("as_of_year"), 0),
                "unlocked_jurisdiction_count": self._to_int(row.get("unlocked_jurisdiction_count"), 0),
                "cumulative_unlocked_jurisdiction_count": self._to_int(
                    row.get("cumulative_unlocked_jurisdiction_count"),
                    0,
                ),
                "active_unlock_count": self._to_int(row.get("active_unlock_count"), 0),
                "pending_unlock_count": self._to_int(row.get("pending_unlock_count"), 0),
                "lapsed_only_unlock_count": self._to_int(row.get("lapsed_only_unlock_count"), 0),
                "active_jurisdiction_count": self._to_int(row.get("active_jurisdiction_count"), 0),
                "pending_jurisdiction_count": self._to_int(row.get("pending_jurisdiction_count"), 0),
                "lapsed_jurisdiction_count": self._to_int(row.get("lapsed_jurisdiction_count"), 0),
                "unlocked_jurisdictions": row.get("unlocked_jurisdictions") or [],
            }
            for row in year_rows
        )
        rows.extend(
            {
                "kind": "jurisdiction",
                "jurisdiction_code": self._to_str(row.get("jurisdiction_code"), ""),
                "first_unlock_year": self._to_int(row.get("first_unlock_year"), 0),
                "first_unlock_basis": self._to_str(row.get("first_unlock_basis"), "tracked"),
                "first_active_year": self._to_int(row.get("first_active_year"), 0),
                "first_pending_year": self._to_int(row.get("first_pending_year"), 0),
                "first_lapsed_year": self._to_int(row.get("first_lapsed_year"), 0),
                "tracked_family_count": self._to_int(row.get("tracked_family_count"), 0),
                "active_family_count": self._to_int(row.get("active_family_count"), 0),
                "pending_family_count": self._to_int(row.get("pending_family_count"), 0),
                "lapsed_family_count": self._to_int(row.get("lapsed_family_count"), 0),
            }
            for row in jurisdiction_rows
        )

        return PortfolioSectionResponse(
            owner_id=owner_id,
            rows=rows,
            meta=ResponseMeta(
                page="portfolio.jurisdiction_unlock_history",
                artifact_sources=[str(path) for path in self.repository.artifacts()],
                support_level=support_level,
                coverage=CoverageMetadata(
                    status=self._coverage_status_from_pct(avg_status_coverage_pct),
                    pct=avg_status_coverage_pct,
                    covered_count=covered_years,
                    denominator_count=audited_years,
                    caveat_text=(
                        "Unlock chronology is derived from first observed branch-state years in the dense branch ledger and filtered through current owner membership."
                        if rows
                        else "No branch-history-backed jurisdiction unlock chronology is available for this owner in the current serving slice."
                    ),
                ),
                caveats=[
                    Caveat(
                        code="branch_observation_first",
                        title="First observed branch year",
                        detail="Unlock years are the first observed branch-state years in the dense legal ledger, not exact filing, publication, or grant event dates.",
                    ),
                    Caveat(
                        code="current_owner_replay",
                        title="Current-owner replay",
                        detail="Jurisdiction unlock history uses the current owner-family bridge to scope families, so historical ownership transfers are not reconstructed.",
                    ),
                    Caveat(
                        code="in_scope_family_only",
                        title="Current in-scope families only",
                        detail="Unlock counts are limited to families that remain in the current in-scope portfolio denominator, so they do not represent every historical branch ever linked to the owner.",
                    ),
                ],
            ),
        )

    def get_citation_attackers(
        self,
        owner_id: str,
        limit: int = 10,
        offset: int = 0,
        wipo_field: str | None = None,
        jurisdiction_code: str | None = None,
        year_from: int | None = None,
        year_to: int | None = None,
    ) -> PortfolioSectionResponse:
        safe_limit, safe_offset = self._bounded_page(limit, offset)
        rows = self.repository.get_owner_citation_attackers(
            owner_id,
            limit=safe_limit,
            offset=safe_offset,
            wipo_field=wipo_field,
            jurisdiction_code=jurisdiction_code,
            year_from=year_from,
            year_to=year_to,
        )
        return PortfolioSectionResponse(
            owner_id=owner_id,
            rows=[
                {
                    "citing_assignee": self._to_str(row.get("citing_assignee_name"), ""),
                    "wipo_field": self._to_str(row.get("wipo_field"), ""),
                    "jurisdiction_code": self._to_str(row.get("jurisdiction_code"), ""),
                    "latest_citation_year": self._to_int(row.get("latest_citation_year"), 0),
                    "citation_event_count": self._to_int(row.get("citation_event_count"), 0),
                    "clean_citation_count": self._to_float(row.get("clean_citation_count"), 0.0),
                    "citation_lethality_sum": self._to_float(row.get("citation_lethality_sum"), 0.0),
                }
                for row in rows
            ],
            meta=ResponseMeta(
                page="portfolio.citation_attackers",
                artifact_sources=[str(path) for path in self.repository.artifacts()],
                pagination=PaginationMetadata(
                    limit=safe_limit,
                    offset=safe_offset,
                    returned_count=len(rows),
                    total_count=self._extract_total_count(rows),
                ),
                caveats=[
                    Caveat(
                        code="citation_event_ledger",
                        title="Citation-event ledger",
                        detail="Attacker rows are aggregated from enriched forward-citation events and ranked by lethality plus event count.",
                    )
                ],
            ),
        )

    def get_citation_fields(
        self,
        owner_id: str,
        limit: int = 10,
        offset: int = 0,
        jurisdiction_code: str | None = None,
        year_from: int | None = None,
        year_to: int | None = None,
    ) -> PortfolioSectionResponse:
        safe_limit, safe_offset = self._bounded_page(limit, offset)
        rows = self.repository.get_owner_citation_fields(
            owner_id,
            limit=safe_limit,
            offset=safe_offset,
            jurisdiction_code=jurisdiction_code,
            year_from=year_from,
            year_to=year_to,
        )
        return PortfolioSectionResponse(
            owner_id=owner_id,
            rows=[
                {
                    "wipo_field": self._to_str(row.get("wipo_field"), ""),
                    "latest_citation_year": self._to_int(row.get("latest_citation_year"), 0),
                    "citation_event_count": self._to_int(row.get("citation_event_count"), 0),
                    "citing_assignee_count": self._to_int(row.get("citing_assignee_count"), 0),
                    "clean_citation_count": self._to_float(row.get("clean_citation_count"), 0.0),
                    "citation_lethality_sum": self._to_float(row.get("citation_lethality_sum"), 0.0),
                }
                for row in rows
            ],
            meta=ResponseMeta(
                page="portfolio.citation_fields",
                artifact_sources=[str(path) for path in self.repository.artifacts()],
                pagination=PaginationMetadata(
                    limit=safe_limit,
                    offset=safe_offset,
                    returned_count=len(rows),
                    total_count=self._extract_total_count(rows),
                ),
                caveats=[
                    Caveat(
                        code="citation_event_ledger",
                        title="Citation-event ledger",
                        detail="Field rows aggregate enriched forward-citation events through current owner-family membership.",
                    )
                ],
            ),
        )

    def get_citation_jurisdictions(
        self,
        owner_id: str,
        limit: int = 10,
        offset: int = 0,
        wipo_field: str | None = None,
        year_from: int | None = None,
        year_to: int | None = None,
    ) -> PortfolioSectionResponse:
        safe_limit, safe_offset = self._bounded_page(limit, offset)
        rows = self.repository.get_owner_citation_jurisdictions(
            owner_id,
            limit=safe_limit,
            offset=safe_offset,
            wipo_field=wipo_field,
            year_from=year_from,
            year_to=year_to,
        )
        return PortfolioSectionResponse(
            owner_id=owner_id,
            rows=[
                {
                    "jurisdiction_code": self._to_str(row.get("jurisdiction_code"), ""),
                    "latest_citation_year": self._to_int(row.get("latest_citation_year"), 0),
                    "citation_event_count": self._to_int(row.get("citation_event_count"), 0),
                    "citing_assignee_count": self._to_int(row.get("citing_assignee_count"), 0),
                    "wipo_field_count": self._to_int(row.get("wipo_field_count"), 0),
                    "clean_citation_count": self._to_float(row.get("clean_citation_count"), 0.0),
                    "citation_lethality_sum": self._to_float(row.get("citation_lethality_sum"), 0.0),
                }
                for row in rows
            ],
            meta=ResponseMeta(
                page="portfolio.citation_jurisdictions",
                artifact_sources=[str(path) for path in self.repository.artifacts()],
                pagination=PaginationMetadata(
                    limit=safe_limit,
                    offset=safe_offset,
                    returned_count=len(rows),
                    total_count=self._extract_total_count(rows),
                ),
                caveats=[
                    Caveat(
                        code="citation_event_ledger",
                        title="Citation-event ledger",
                        detail="Jurisdiction rows aggregate enriched forward-citation events through current owner-family membership.",
                    )
                ],
            ),
        )

    def get_citation_cpc_groups(
        self,
        owner_id: str,
        limit: int = 10,
        offset: int = 0,
        wipo_field: str | None = None,
        jurisdiction_code: str | None = None,
        year_from: int | None = None,
        year_to: int | None = None,
    ) -> PortfolioSectionResponse:
        safe_limit, safe_offset = self._bounded_page(limit, offset)
        rows = self.repository.get_owner_citation_cpc_groups(
            owner_id,
            limit=safe_limit,
            offset=safe_offset,
            wipo_field=wipo_field,
            jurisdiction_code=jurisdiction_code,
            year_from=year_from,
            year_to=year_to,
        )
        return PortfolioSectionResponse(
            owner_id=owner_id,
            rows=[
                {
                    "cpc_main_group": self._to_str(row.get("cpc_main_group"), ""),
                    "latest_citation_year": self._to_int(row.get("latest_citation_year"), 0),
                    "citation_event_count": self._to_int(row.get("citation_event_count"), 0),
                    "clean_citation_count": self._to_float(row.get("clean_citation_count"), 0.0),
                    "citation_lethality_sum": self._to_float(row.get("citation_lethality_sum"), 0.0),
                    "cited_family_count": self._to_int(row.get("cited_family_count"), 0),
                }
                for row in rows
            ],
            meta=ResponseMeta(
                page="portfolio.citation_cpc_groups",
                artifact_sources=[str(path) for path in self.repository.artifacts()],
                pagination=PaginationMetadata(
                    limit=safe_limit,
                    offset=safe_offset,
                    returned_count=len(rows),
                    total_count=self._extract_total_count(rows),
                ),
                caveats=[
                    Caveat(
                        code="cited_family_cpc_replay",
                        title="CPC groups are attached to cited portfolio families",
                        detail="Rows are derived by attaching current CPC main-group membership to cited portfolio families, then aggregating forward-citation pressure across those family groups.",
                    ),
                    Caveat(
                        code="cpc_multi_membership",
                        title="CPC totals are multi-membership",
                        detail="A cited family can contribute to multiple CPC main groups, so CPC citation totals are useful for concentration but are not additive back to one portfolio total.",
                    ),
                ],
            ),
        )

    def get_threats(
        self,
        owner_id: str,
        limit: int = 10,
        offset: int = 0,
        wipo_field: str | None = None,
    ) -> PortfolioThreatResponse:
        safe_limit, safe_offset = self._bounded_page(limit, offset)
        rows = self.repository.get_owner_threats(
            owner_id,
            limit=safe_limit,
            offset=safe_offset,
            wipo_field=wipo_field,
        )
        return PortfolioThreatResponse(
            owner_id=owner_id,
            rows=[
                {
                    "citing_assignee": self._to_str(row.get("citing_assignee_name"), ""),
                    "wipo_field": self._to_str(row.get("wipo_field"), ""),
                    "citation_lethality": self._to_float(row.get("citation_lethality_sum"), 0),
                    "collided_family_count": self._to_int(row.get("collided_family_count"), 0),
                }
                for row in rows
            ],
            meta=ResponseMeta(
                page="portfolio.threats",
                artifact_sources=[str(path) for path in self.repository.artifacts()],
                pagination=PaginationMetadata(
                    limit=safe_limit,
                    offset=safe_offset,
                    returned_count=len(rows),
                    total_count=self._extract_total_count(rows),
                ),
            ),
        )

    def get_classification(
        self,
        owner_id: str,
        as_of_year: int | None = None,
        limit: int = 10,
        offset: int = 0,
        classification_type: str = "CPC_MAIN_GROUP",
        timeseries_fields: int = 6,
        wipo_field: str | None = None,
    ) -> PortfolioClassificationResponse:
        safe_limit, safe_offset = self._bounded_page(limit, offset)
        rows = self.repository.get_owner_classification(
            owner_id,
            as_of_year=as_of_year,
            limit=safe_limit,
            offset=safe_offset,
            classification_type=classification_type,
            wipo_field=wipo_field,
        )
        safe_timeseries_fields = max(int(timeseries_fields), 0)
        timeseries_rows = (
            self.repository.get_owner_classification_timeseries(
                owner_id,
                as_of_year=as_of_year,
                limit_fields=safe_timeseries_fields,
            )
            if safe_timeseries_fields > 0
            else []
        )

        buckets: dict[str, list[PortfolioClassificationTimeseriesPoint]] = {}
        for row in timeseries_rows:
            field = self._to_str(row.get("wipo_field"), "")
            if not field:
                continue
            buckets.setdefault(field, []).append(self._to_series_point(row))

        return PortfolioClassificationResponse(
            owner_id=owner_id,
            rows=[
                PortfolioClassificationRow(
                    segment=self._to_str(row.get("segment", "")),
                    classification_type=self._to_str(row.get("classification_type"), "CPC_MAIN_GROUP"),
                    wipo_field=(
                        self._to_str(row.get("classification_label"), self._to_str(row.get("segment", "")))
                        if self._to_str(row.get("classification_type"), "") == "WIPO_FIELD"
                        else self._to_str(
                            wipo_field,
                            self._to_str(row.get("wipo_field"), self._to_str(row.get("classification_label"), "")),
                        )
                    ),
                    family_share=self._to_float(row.get("family_share"), 0.0),
                    trajectory=self._to_float(row.get("trajectory"), 0.0),
                    top_change=self._to_top_change(row.get("trajectory")),
                ).model_dump()
                for row in rows
            ],
            timeseries=[
                PortfolioClassificationTimeseries(
                    field=field,
                    points=[
                        PortfolioClassificationTimeseriesPoint.model_validate(point)
                        if isinstance(point, dict)
                        else point
                        for point in points
                    ],
                )
                for field, points in buckets.items()
            ],
            meta=ResponseMeta(
                page="portfolio.classification",
                artifact_sources=[str(path) for path in self.repository.artifacts()],
                caveats=[
                    Caveat(
                        code="classification_visibility",
                        title="First-seen classification visibility",
                        detail="Portfolio classification share is computed from PIT visibility and owner replay logic, not true historical legal possession.",
                    )
                ],
                pagination=PaginationMetadata(
                    limit=safe_limit,
                    offset=safe_offset,
                    returned_count=len(rows),
                    total_count=self._extract_total_count(rows),
                ),
            ),
        )

    def get_forecast_contributors(
        self,
        owner_id: str,
        horizon: str = "3y",
        contributor_scope: str = "phase03_future_citations",
        limit: int = 10,
        offset: int = 0,
    ) -> PortfolioSectionResponse:
        safe_limit, safe_offset = self._bounded_page(limit, offset)
        rows = self.repository.get_owner_forecast_contributors(
            owner_id,
            horizon=horizon,
            contributor_scope=contributor_scope,
            limit=safe_limit,
            offset=safe_offset,
        )
        return PortfolioSectionResponse(
            owner_id=owner_id,
            rows=[
                {
                    "contributor_scope": self._to_str(row.get("contributor_scope"), ""),
                    "horizon": self._to_str(row.get("horizon"), ""),
                    "contributor_entity_id": self._to_str(row.get("contributor_entity_id"), ""),
                    "jurisdiction_code": self._to_str(row.get("jurisdiction_code"), ""),
                    "contribution_value": self._to_float(row.get("contribution_value"), 0.0),
                    "contribution_share": self._to_float(row.get("contribution_share"), 0.0),
                    "contributor_rank": self._to_int(row.get("contributor_rank"), 0),
                }
                for row in rows
            ],
            meta=ResponseMeta(
                page="portfolio.forecast_contributors",
                artifact_sources=[str(path) for path in self.repository.artifacts()],
                pagination=PaginationMetadata(
                    limit=safe_limit,
                    offset=safe_offset,
                    returned_count=len(rows),
                    total_count=self._extract_total_count(rows),
                ),
                caveats=[
                    Caveat(
                        code="contributor_scope_contract",
                        title="Contributor scope contract",
                        detail="Current canonical scopes are phase03 future-citation contributors and phase04 lapse-risk contributors; pending-grant remains candidate-only.",
                    )
                ],
            ),
        )

    def get_market_context(
        self,
        owner_id: str,
        horizon: str = "3y",
        as_of_year: int | None = None,
    ) -> PortfolioSectionResponse:
        summary_row, segment_rows = self.repository.get_owner_market_context(
            owner_id,
            horizon=horizon,
            as_of_year=as_of_year,
        )
        rows: list[dict[str, object]] = []
        if summary_row:
            rows.append(
                {
                    "kind": "summary",
                    "horizon": horizon,
                    "heating_market_exposure_count": self._to_float(
                        summary_row.get(f"portfolio_heating_market_exposure_count_{horizon}"),
                        0.0,
                    ),
                    "cooling_market_exposure_count": self._to_float(
                        summary_row.get(f"portfolio_cooling_market_exposure_count_{horizon}"),
                        0.0,
                    ),
                    "hotspot_coverage_pct": self._to_float(
                        summary_row.get(f"portfolio_hotspot_coverage_pct_{horizon}"),
                        0.0,
                    ),
                }
            )
        rows.extend(
            [
                {
                    "kind": "segment",
                    "horizon": self._to_str(row.get("horizon"), horizon),
                    "wipo_field": self._to_str(row.get("wipo_field"), ""),
                    "predicted_direction_band": self._to_str(row.get("predicted_direction_band"), "stable"),
                    "support_level": self._to_str(row.get("support_level"), "limited"),
                    "predicted_growth_rate_reference": self._to_float(row.get("predicted_growth_rate_reference"), 0.0),
                    "predicted_count_reference": self._to_float(row.get("predicted_count_reference"), 0.0),
                    "portfolio_active_family_count_in_field": self._to_int(
                        row.get("portfolio_active_family_count_in_field"),
                        0,
                    ),
                }
                for row in segment_rows
            ]
        )
        return PortfolioSectionResponse(
            owner_id=owner_id,
            rows=rows,
            meta=ResponseMeta(
                page="portfolio.market_context",
                artifact_sources=[str(path) for path in self.repository.artifacts()],
                caveats=[
                    Caveat(
                        code="phase06_direction_first",
                        title="Direction-first market context",
                        detail="Heating and cooling bands are the primary output; raw count references are secondary context only.",
                    )
                ],
            ),
        )

    def get_compare_timeslice(
        self,
        owner_id: str,
        base_year: int | None = None,
        compare_year: int | None = None,
    ) -> PortfolioSectionResponse:
        rows = self.repository.get_owner_compare_timeslice(owner_id, base_year=base_year, compare_year=compare_year)
        if len(rows) < 2:
            return PortfolioSectionResponse(
                owner_id=owner_id,
                rows=[],
                meta=ResponseMeta(
                    page="portfolio.compare_timeslice",
                    artifact_sources=[str(path) for path in self.repository.artifacts()],
                    caveats=[
                        Caveat(
                            code="compare_unavailable",
                            title="Compare view unavailable",
                            detail="A compare-safe year pair is not available for this owner in the current PIT compare mart.",
                        )
                    ],
                ),
            )

        current_row = rows[0]
        prior_row = rows[1]
        current_year = self._to_int(current_row.get("as_of_year"), 0)
        prior_year = self._to_int(prior_row.get("as_of_year"), 0)
        metrics = [
            {
                "metric": "blocking_strength",
                "label": "Blocking Strength",
                "current_value": self._to_float(current_row.get("portfolio_avg_blocking_power_score_asof"), 0.0),
                "compare_value": self._to_float(prior_row.get("portfolio_avg_blocking_power_score_asof"), 0.0),
                "current_score": self._clamp_pct(current_row.get("portfolio_avg_blocking_power_score_asof")),
                "compare_score": self._clamp_pct(prior_row.get("portfolio_avg_blocking_power_score_asof")),
            },
            {
                "metric": "legal_durability",
                "label": "Legal Durability",
                "current_value": self._to_float(current_row.get("portfolio_legal_durability_index_asof"), 0.0),
                "compare_value": self._to_float(prior_row.get("portfolio_legal_durability_index_asof"), 0.0),
                "current_score": self._clamp_pct(current_row.get("portfolio_legal_durability_index_asof"), 100.0),
                "compare_score": self._clamp_pct(prior_row.get("portfolio_legal_durability_index_asof"), 100.0),
            },
            {
                "metric": "field_breadth",
                "label": "Field Breadth",
                "current_value": self._to_float(current_row.get("portfolio_field_breadth_asof"), 0.0),
                "compare_value": self._to_float(prior_row.get("portfolio_field_breadth_asof"), 0.0),
                "current_score": self._clamp_pct(current_row.get("portfolio_field_breadth_asof"), 10.0),
                "compare_score": self._clamp_pct(prior_row.get("portfolio_field_breadth_asof"), 10.0),
            },
            {
                "metric": "concentration_balance",
                "label": "Concentration Balance",
                "current_value": 1.0 - self._to_float(current_row.get("portfolio_field_concentration_hhi_asof"), 1.0),
                "compare_value": 1.0 - self._to_float(prior_row.get("portfolio_field_concentration_hhi_asof"), 1.0),
                "current_score": self._clamp_pct(1.0 - self._to_float(current_row.get("portfolio_field_concentration_hhi_asof"), 1.0), 100.0),
                "compare_score": self._clamp_pct(1.0 - self._to_float(prior_row.get("portfolio_field_concentration_hhi_asof"), 1.0), 100.0),
            },
            {
                "metric": "data_completeness",
                "label": "Data Completeness",
                "current_value": self._to_float(current_row.get("portfolio_data_completeness_pct_asof"), 0.0),
                "compare_value": self._to_float(prior_row.get("portfolio_data_completeness_pct_asof"), 0.0),
                "current_score": self._clamp_pct(current_row.get("portfolio_data_completeness_pct_asof"), 100.0),
                "compare_score": self._clamp_pct(prior_row.get("portfolio_data_completeness_pct_asof"), 100.0),
            },
        ]
        compare_rows = [
            {
                **metric,
                "current_year": current_year,
                "compare_year": prior_year,
                "delta": self._to_float(metric["current_value"], 0.0) - self._to_float(metric["compare_value"], 0.0),
            }
            for metric in metrics
        ]
        return PortfolioSectionResponse(
            owner_id=owner_id,
            rows=compare_rows,
            meta=ResponseMeta(
                page="portfolio.compare_timeslice",
                artifact_sources=[str(path) for path in self.repository.artifacts()],
                caveats=[
                    Caveat(
                        code="current_owner_replay",
                        title="Current-owner replay",
                        detail="Historical comparison is currently computed from PIT family state replayed through current owner membership where owner-history truth is unavailable.",
                    ),
                    Caveat(
                        code="normalized_axes",
                        title="Normalized compare axes",
                        detail="Compare scores are normalized to 0-100 for shape comparison; exact raw values remain the evidence columns.",
                    ),
                ],
            ),
        )

    def get_pending_grants(
        self,
        owner_id: str,
        horizon: str = "24m",
        branch_jurisdiction_code: str | None = None,
        branch_wipo_field: str | None = None,
        branch_limit: int = 25,
    ) -> PortfolioSectionResponse:
        payload = self.repository.get_owner_pending_grant_sections(
            owner_id,
            horizon=horizon,
            branch_jurisdiction_code=branch_jurisdiction_code,
            branch_wipo_field=branch_wipo_field,
            branch_limit=branch_limit,
        )
        metrics = payload.get("metrics", {}) if isinstance(payload, dict) else {}
        summary = payload.get("summary", {}) if isinstance(payload, dict) else {}
        jurisdiction_rows = payload.get("jurisdictions", []) if isinstance(payload, dict) else []
        field_rows = payload.get("fields", []) if isinstance(payload, dict) else []
        branch_rows = payload.get("branches", []) if isinstance(payload, dict) else []
        serving_ready = bool(payload.get("serving_ready")) if isinstance(payload, dict) else False
        reason = self._to_str(
            payload.get("reason") if isinstance(payload, dict) else None,
            "Pending-grant current serving slice is unavailable.",
        )

        selected_percentile = self._to_float(summary.get("pending_pipeline_percentile"), 0.0)
        if selected_percentile >= 95.0:
            priority_tier = "top"
        elif selected_percentile >= 80.0:
            priority_tier = "high"
        elif selected_percentile >= 50.0:
            priority_tier = "watch"
        else:
            priority_tier = "monitor"

        support_level = self._support_from_status(summary.get("pending_pipeline_support_level"))
        pending_pipeline_branch_count = self._to_int(summary.get("pending_pipeline_branch_count"), 0)
        pending_pipeline_family_count = self._to_int(summary.get("pending_pipeline_family_count"), 0)
        current_pending_branch_count = self._to_int(summary.get("current_pending_branch_count"), 0)
        current_pending_family_count = self._to_int(summary.get("current_pending_family_count"), 0)
        branch_coverage_pct = (
            pending_pipeline_branch_count / current_pending_branch_count if current_pending_branch_count > 0 else 0.0
        )
        family_coverage_pct = (
            pending_pipeline_family_count / current_pending_family_count if current_pending_family_count > 0 else 0.0
        )
        rows: list[dict[str, object]] = [
            {
                "kind": "summary",
                "feature_status": "candidate_only",
                "serving_ready": serving_ready,
                "horizon": horizon,
                "recommended_output": "rank_percentile_first",
                "probability_headline_allowed": False,
                "reason": reason,
                "observed_roc_auc": self._to_float(metrics.get("roc_auc"), 0.0),
                "observed_pr_auc": self._to_float(metrics.get("pr_auc"), 0.0),
                "pending_pipeline_branch_count": pending_pipeline_branch_count,
                "pending_pipeline_family_count": pending_pipeline_family_count,
                "current_pending_branch_count": current_pending_branch_count,
                "current_pending_family_count": current_pending_family_count,
                "pending_pipeline_branch_coverage_pct": branch_coverage_pct,
                "pending_pipeline_family_coverage_pct": family_coverage_pct,
                "pending_pipeline_expected_likely_grants_12m": self._to_float(
                    summary.get("pending_pipeline_expected_likely_grants_12m"),
                    0.0,
                ),
                "pending_pipeline_expected_likely_grants_24m": self._to_float(
                    summary.get("pending_pipeline_expected_likely_grants_24m"),
                    0.0,
                ),
                "pending_pipeline_avg_probability_12m": self._to_float(
                    summary.get("pending_pipeline_avg_probability_12m"),
                    0.0,
                ),
                "pending_pipeline_avg_probability_24m": self._to_float(
                    summary.get("pending_pipeline_avg_probability_24m"),
                    0.0,
                ),
                "pending_pipeline_percentile": selected_percentile,
                "pending_pipeline_priority_tier": priority_tier,
                "pending_pipeline_support_level": str(summary.get("pending_pipeline_support_level") or "limited"),
                "pending_pipeline_top_jurisdiction": self._to_str(summary.get("pending_pipeline_top_jurisdiction"), ""),
                "pending_pipeline_top_field": self._to_str(summary.get("pending_pipeline_top_field"), ""),
                "top_branch_family_id": self._to_str(summary.get("top_branch_family_id"), ""),
                "top_branch_jurisdiction": self._to_str(summary.get("top_branch_jurisdiction"), ""),
                "top_branch_field": self._to_str(summary.get("top_branch_field"), ""),
                "top_branch_probability": self._to_float(summary.get("top_branch_probability"), 0.0),
                "top_branch_percentile": self._to_float(summary.get("top_branch_percentile"), 0.0),
            }
        ]
        rows.extend(
            {
                "kind": "jurisdiction",
                "jurisdiction_code": self._to_str(row.get("jurisdiction_code"), ""),
                "office_support_level": self._to_str(row.get("office_support_level"), "limited"),
                "branch_count": self._to_int(row.get("branch_count"), 0),
                "family_count": self._to_int(row.get("family_count"), 0),
                "avg_probability_12m": self._to_float(row.get("avg_probability_12m"), 0.0),
                "avg_probability_24m": self._to_float(row.get("avg_probability_24m"), 0.0),
                "expected_likely_grants_12m": self._to_float(row.get("expected_likely_grants_12m"), 0.0),
                "expected_likely_grants_24m": self._to_float(row.get("expected_likely_grants_24m"), 0.0),
                "avg_percentile": self._to_float(row.get("avg_percentile"), 0.0),
            }
            for row in jurisdiction_rows
        )
        rows.extend(
            {
                "kind": "field",
                "wipo_field": self._to_str(row.get("primary_wipo_field"), ""),
                "branch_count": self._to_int(row.get("branch_count"), 0),
                "family_count": self._to_int(row.get("family_count"), 0),
                "avg_probability_12m": self._to_float(row.get("avg_probability_12m"), 0.0),
                "avg_probability_24m": self._to_float(row.get("avg_probability_24m"), 0.0),
                "expected_likely_grants_12m": self._to_float(row.get("expected_likely_grants_12m"), 0.0),
                "expected_likely_grants_24m": self._to_float(row.get("expected_likely_grants_24m"), 0.0),
                "avg_percentile": self._to_float(row.get("avg_percentile"), 0.0),
            }
            for row in field_rows
        )
        rows.extend(
            {
                "kind": "branch",
                "docdb_family_id": self._to_str(row.get("docdb_family_id"), ""),
                "jurisdiction_code": self._to_str(row.get("jurisdiction_code"), ""),
                "primary_wipo_field": self._to_str(row.get("primary_wipo_field"), ""),
                "pending_age_years": self._to_float(row.get("pending_age_years"), 0.0),
                "family_age_years": self._to_float(row.get("family_age_years"), 0.0),
                "family_blocking_power_score_asof": self._to_float(row.get("family_blocking_power_score_asof"), 0.0),
                "family_enforceability_score_asof": self._to_float(row.get("family_enforceability_score_asof"), 0.0),
                "family_rcf_score_asof": self._to_float(row.get("family_rcf_score_asof"), 0.0),
                "data_completeness_pct_asof": self._to_float(row.get("data_completeness_pct_asof"), 0.0),
                "probability_12m": self._to_float(row.get("probability_12m"), 0.0),
                "probability_24m": self._to_float(row.get("probability_24m"), 0.0),
                "selected_probability": self._to_float(row.get("selected_probability"), 0.0),
                "rank_within_office_horizon": self._to_int(row.get("rank_within_office_horizon"), 0),
                "percentile_within_office_horizon": self._to_float(row.get("percentile_within_office_horizon"), 0.0),
                "office_support_level": self._to_str(row.get("office_support_level"), "limited"),
                "priority_tier": self._to_str(row.get("priority_tier"), "monitor"),
            }
            for row in branch_rows
        )
        return PortfolioSectionResponse(
            owner_id=owner_id,
            rows=rows,
            meta=ResponseMeta(
                page="portfolio.pending_grants",
                artifact_sources=[str(path) for path in self.repository.artifacts()],
                support_level=support_level if serving_ready else SupportLevel.candidate_only,
                caveats=[
                    Caveat(
                        code="candidate_only",
                        title="Pending-grant remains candidate-only",
                        detail="Pending-grant is not part of the sealed public portfolio forecast layer and should be presented, if at all, as rank/percentile-first rather than exact probability truth.",
                    ),
                    Caveat(
                        code="office_rank_first",
                        title="Office-relative ranking",
                        detail="Branch percentiles and ranks are computed within jurisdiction-level pending slices, so they are useful for prioritization but not direct cross-office probability truth.",
                    ),
                    Caveat(
                        code="expected_grants_are_directional",
                        title="Expected grants are directional",
                        detail="Summed expected likely-grant counts are directional portfolio planning aids and should not be presented as promised realized grant totals.",
                    ),
                ],
            ),
        )

    def get_forecast(self, owner_id: str, horizon: str = "3y", as_of_year: int | None = None) -> PortfolioForecastResponse:
        selected = str(horizon).strip().lower()
        forecast_row = self.repository.get_owner_forecast_summary(owner_id, as_of_year=as_of_year)
        forecast_sections = self.repository.get_owner_forecast_sections(owner_id, as_of_year=as_of_year)
        risk12m = self.repository.get_owner_risk_distribution(owner_id, horizon="12m", as_of_year=as_of_year)
        risk24m = self.repository.get_owner_risk_distribution(owner_id, horizon="24m", as_of_year=as_of_year)
        has_forecast = bool(forecast_row) or bool(forecast_sections) or bool(risk12m) or bool(risk24m)

        selected_horizons = {"3y", "5y"}
        if selected in {"3y", "5y"}:
            selected_horizons = {selected}

        sections: list[dict[str, object]] = []
        for selected in sorted(selected_horizons):
            if not has_forecast:
                continue
            if selected == "3y":
                total = self._to_float(forecast_row.get("portfolio_expected_future_citations_total_3y"), 0)
                low = self._to_float(forecast_row.get("portfolio_expected_future_citations_lower_3y"), 0)
                high = self._to_float(forecast_row.get("portfolio_expected_future_citations_upper_3y"), 0)
                per_family = self._to_float(forecast_row.get("portfolio_expected_future_citations_per_effective_family_3y"), 0)
                concentration = self._to_float(forecast_row.get("portfolio_top_contributor_dependence_pct_3y"), 0)
                coverage = self._to_float(forecast_row.get("portfolio_phase03_feature_completeness_pct_3y"), 0)
            else:
                total = self._to_float(forecast_row.get("portfolio_expected_future_citations_total_5y"), 0)
                low = self._to_float(forecast_row.get("portfolio_expected_future_citations_lower_5y"), 0)
                high = self._to_float(forecast_row.get("portfolio_expected_future_citations_upper_5y"), 0)
                per_family = self._to_float(forecast_row.get("portfolio_expected_future_citations_per_effective_family_5y"), 0)
                concentration = self._to_float(forecast_row.get("portfolio_top_contributor_dependence_pct_5y"), 0)
                coverage = self._to_float(forecast_row.get("portfolio_phase03_feature_completeness_pct_5y"), 0)

            top_segments = [
                {
                    "field": str(segment.get("wipo_field", "unknown")),
                    "active_families": self._to_int(segment.get("portfolio_active_family_count_in_field"), 0),
                    "active_share": 0.0,
                    "hotspot_direction": str(segment.get("predicted_direction_band", "stable")),
                    "change_12m": self._to_float(segment.get("predicted_growth_rate_reference"), 0),
                    "confidence": self._support_from_status(segment.get("support_level")),
                }
                for segment in forecast_sections
                if str(segment.get("horizon", "")) == selected
                and self._to_int(segment.get("portfolio_active_family_count_in_field"), 0) > 0
            ]
            top_segments_sorted = sorted(
                top_segments,
                key=lambda row: row["active_families"],
                reverse=True,
            )[:10]
            total_active = sum(row["active_families"] for row in top_segments_sorted)
            for segment in top_segments_sorted:
                if total_active:
                    segment["active_share"] = self._to_float(segment["active_families"], 0) / total_active

            section = {
                "horizon": selected,
                "total": total,
                "low": low,
                "high": high,
                "per_effective_family": per_family,
                "top_contributor_dependence_pct": concentration,
                "coverage_pct": coverage,
                "top_segments": top_segments_sorted,
            }
            section["risk12m"] = risk12m if selected == "3y" else risk24m
            section["risk24m"] = risk24m
            sections.append(section)

        return PortfolioForecastResponse(
            owner_id=owner_id,
            coverage=CoverageMetadata(
                status=str(forecast_row.get("portfolio_prediction_coverage_status", "unknown")),
                pct=self._forecast_family_coverage_pct(forecast_row),
                covered_count=self._to_int(forecast_row.get("phase03_family_covered_count")),
                denominator_count=self._to_int(forecast_row.get("phase03_family_denominator_count")),
                caveat_text=str(forecast_row.get("coverage_caveat_text", "")).strip() or None,
            ),
            sections=sections,
            meta=ResponseMeta(
                page="portfolio.forecast",
                artifact_sources=[str(path) for path in self.repository.artifacts()],
                support_level=self._forecast_status_support(forecast_row),
                caveats=[
                    Caveat(
                        code="phase03_interval_first",
                        title="Phase 03 is interval-first",
                        detail="Model output is published as confidence intervals first; exact counts are not shown as single-point forecasts.",
                    ),
                    Caveat(
                        code="phase04_band_first",
                        title="Phase 04 is risk-band-first",
                        detail="Lapse risk is surfaced by bands first; single-family branch-level probabilities are secondary.",
                    ),
                ],
            ),
        )
