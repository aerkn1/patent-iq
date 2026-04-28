from __future__ import annotations

from datetime import date, datetime
from statistics import median
from typing import Any

from domain.schemas.common import Caveat, PageIdentity, PaginationMetadata, ResponseMeta, SupportLevel
from domain.schemas.market_intelligence import MarketOverviewResponse, MarketSectionResponse, MarketWorkspaceResponse
from infrastructure.repositories.market_intelligence_repository import MarketIntelligenceRepository


class MarketIntelligenceService:
    def __init__(self, repository: MarketIntelligenceRepository | None = None) -> None:
        self.repository = repository or MarketIntelligenceRepository()

    def get_overview(self, as_of_year: int | None = None) -> MarketOverviewResponse:
        scope = self.repository.get_scope_summary()
        overview = self.repository.get_overview_snapshot()
        segments = self.repository.get_segments(as_of_year=as_of_year)
        return MarketOverviewResponse(
            identity=PageIdentity(
                id="market-intelligence",
                label="Market Intelligence",
                page_kind="market_intelligence",
                selected_year=as_of_year,
            ),
            summary_cards=[
                {
                    "key": "segment_count",
                    "label": "Segments in scope",
                    "value": self._to_int(overview.get("segment_count"), 0),
                },
                {
                    "key": "rising_segment_count",
                    "label": "Rising segments",
                    "value": self._to_int(overview.get("rising_segment_count"), 0),
                },
                {
                    "key": "cooling_segment_count",
                    "label": "Cooling segments",
                    "value": self._to_int(overview.get("cooling_segment_count"), 0),
                },
                {
                    "key": "covered_field_count",
                    "label": "Covered fields",
                    "value": self._to_int(scope.get("covered_field_count"), 0),
                },
                {
                    "key": "latest_market_year",
                    "label": "Latest supported year",
                    "value": self._to_int(scope.get("latest_market_year"), 0),
                },
                {
                    "key": "latest_comparable_market_year",
                    "label": "Latest comparable year",
                    "value": self._to_int(scope.get("latest_comparable_market_year"), 0),
                },
            ],
            featured_segments=[
                {
                    "segment_id": self._to_text(segment.get("segment_id")),
                    "wipo_field": self._to_text(segment.get("wipo_industry_code")),
                    "market_state": self._to_text(segment.get("market_state"), "stable"),
                    "total_family_count": self._to_int(segment.get("total_family_count"), 0),
                    "blocking_density": self._to_float(segment.get("segment_blocking_density_asof"), 0.0),
                }
                for segment in segments[:5]
            ],
            meta=ResponseMeta(
                page="market_intelligence.overview",
                artifact_sources=[str(path) for path in self.repository.artifacts()],
                support_level=SupportLevel.moderate,
                caveats=[
                    Caveat(
                        code="no_jurisdiction_slice",
                        title="No jurisdiction slice yet",
                        detail="Current CPC trend marts are field-year based and are not yet jurisdiction-sliced.",
                    )
                ],
            ),
        )

    def get_section(self, section: str, segment_id: str | None = None) -> MarketSectionResponse:
        rows: list[dict[str, Any]]
        caveats: list[Caveat] = []

        if section == "segments":
            rows = [
                self._map_segment_row(row, sparkline=[])
                for row in self.repository.get_segments()
            ]
        elif section == "segment_detail" and segment_id:
            matches = [
                self._map_segment_row(row, sparkline=[])
                for row in self.repository.get_segments()
                if self._to_text(row.get("wipo_industry_code")) == segment_id
            ]
            rows = matches[:1]
        elif section == "segment_timeseries" and segment_id:
            rows = self._map_timeseries_rows(self.repository.get_timeseries(segment_id=segment_id))
        elif section == "segment_owners" and segment_id:
            rows = self._map_owner_rows(self.repository.get_segment_owners(segment_id=segment_id))
        elif section == "segment_jurisdictions" and segment_id:
            latest_year = self._to_int(self.repository.get_scope_summary().get("latest_market_year"), 0) or None
            rows = self._map_citation_jurisdiction_rows(
                self.repository.get_citation_jurisdictions(segment_id=segment_id, as_of_year=latest_year, limit=20, offset=0)
            )
        elif section == "cpc_trends":
            rows = self._map_cpc_trend_rows(self.repository.get_cpc_trends(segment_id=segment_id))
            caveats.append(
                Caveat(
                    code="cpc_trend_scope",
                    title="Latest-year CPC emphasis",
                    detail="CPC trend rows are ranked within the bounded segment frame and should be read as directional composition, not literal whole-world CPC dominance.",
                )
            )
        else:
            rows = []

        return MarketSectionResponse(
            segment_id=segment_id,
            rows=rows,
            meta=ResponseMeta(
                page=f"market_intelligence.{section}",
                artifact_sources=[str(path) for path in self.repository.artifacts()],
                support_level=SupportLevel.moderate,
                caveats=caveats,
            ),
        )

    def get_workspace(
        self,
        market_state: str = "all",
        segment_id: str | None = None,
        as_of_year: int | None = None,
    ) -> MarketWorkspaceResponse:
        normalized_state = self._normalize_market_state(market_state)
        scope = self.repository.get_scope_summary()
        overview = self.repository.get_overview_snapshot()
        raw_segments = self.repository.get_segments(as_of_year=as_of_year)
        timeseries_rows = self.repository.get_timeseries()
        sparkline_map = self._group_timeseries(timeseries_rows)
        segments = [self._map_segment_row(row, sparkline_map.get(self._to_text(row.get("wipo_industry_code")), [])) for row in raw_segments]
        filtered_segments = segments if normalized_state == "all" else [
            row for row in segments if self._to_text(row.get("market_state"), "stable") == normalized_state
        ]

        selected_segment_id = segment_id if segment_id and any(row["wipo_industry_code"] == segment_id for row in filtered_segments) else None
        if selected_segment_id is None and filtered_segments:
            selected_segment_id = self._to_text(filtered_segments[0].get("wipo_industry_code"))

        latest_market_year = self._to_int(scope.get("latest_market_year"), 0) or None
        latest_comparable_market_year = self._to_int(scope.get("latest_comparable_market_year"), 0) or latest_market_year
        effective_market_year = as_of_year or latest_market_year or latest_comparable_market_year
        if effective_market_year is not None and latest_market_year is not None:
            effective_market_year = min(int(effective_market_year), int(latest_market_year))
        selected_segment = None
        if selected_segment_id:
            segment_row = next(
                (row for row in filtered_segments if self._to_text(row.get("wipo_industry_code")) == selected_segment_id),
                None,
            )
            if segment_row:
                selected_segment = {
                    "segment_id": self._to_text(segment_row.get("segment_id")),
                    "wipo_industry_code": self._to_text(segment_row.get("wipo_industry_code")),
                    "market_state": self._to_text(segment_row.get("market_state"), "stable"),
                    "summary": {
                        key: value
                        for key, value in segment_row.items()
                        if key not in {"sparkline"}
                    },
                    "timeseries": sparkline_map.get(selected_segment_id, []),
                    "top_owners": self._map_owner_rows(
                        self.repository.get_segment_owners(segment_id=selected_segment_id, as_of_year=effective_market_year, limit=8, offset=0)
                    ),
                    "top_families": self._map_family_rows(
                        self.repository.get_segment_families(
                            segment_id=selected_segment_id,
                            as_of_year=effective_market_year,
                            limit=8,
                            offset=0,
                        )
                    ),
                    "top_jurisdictions": self._map_citation_jurisdiction_rows(
                        self.repository.get_citation_jurisdictions(
                            segment_id=selected_segment_id,
                            as_of_year=effective_market_year,
                            limit=8,
                            offset=0,
                        )
                    ),
                    "citation_trend": self._map_citation_trend_rows(
                        self.repository.get_citation_trends(segment_id=selected_segment_id, limit=32, offset=0)
                    ),
                    "top_attackers": self._map_citation_attacker_rows(
                        self.repository.get_citation_attackers(
                            segment_id=selected_segment_id,
                            as_of_year=effective_market_year,
                            limit=8,
                            offset=0,
                        )
                    ),
                    "top_cpcs": self._map_cpc_trend_rows(
                        self.repository.get_cpc_trends(segment_id=selected_segment_id, limit=10, offset=0)
                    ),
                    "field_jurisdictions": self._map_field_jurisdiction_rows(
                        self.repository.get_segment_field_jurisdictions(
                            segment_id=selected_segment_id,
                            as_of_year=effective_market_year,
                            limit=12,
                            offset=0,
                        )
                    ),
                    "cpc_jurisdictions": self._map_cpc_jurisdiction_rows(
                        self.repository.get_segment_cpc_jurisdictions(
                            segment_id=selected_segment_id,
                            as_of_year=effective_market_year,
                            limit=12,
                            offset=0,
                        )
                    ),
                }

        return MarketWorkspaceResponse(
            identity=PageIdentity(
                id="market-intelligence",
                label="Market Intelligence",
                page_kind="market_intelligence",
                selected_year=effective_market_year,
            ),
            scope={
                "scope_type": "mega_cluster_bounded",
                "covered_field_count": self._to_int(scope.get("covered_field_count"), 0),
                "coverage_year_range": {
                    "start_year": self._to_int(scope.get("start_year"), 0),
                    "end_year": self._to_int(scope.get("end_year"), 0),
                },
                "snapshot_date": self._to_iso(scope.get("snapshot_date")),
                "latest_market_year": self._to_int(scope.get("latest_market_year"), 0),
                "latest_comparable_market_year": self._to_int(scope.get("latest_comparable_market_year"), 0),
                "latest_cpc_year": self._to_int(scope.get("latest_cpc_year"), 0),
            },
            overview={
                "segment_count": self._to_int(overview.get("segment_count"), 0),
                "rising_segment_count": self._to_int(overview.get("rising_segment_count"), 0),
                "cooling_segment_count": self._to_int(overview.get("cooling_segment_count"), 0),
                "total_family_count": self._to_int(overview.get("total_family_count"), 0),
                "avg_segment_family_count": round(self._to_float(overview.get("avg_segment_family_count"), 0.0), 1),
            },
            filters={
                "market_state": normalized_state,
                "state_options": [
                    {"value": "all", "label": "All segments", "count": len(segments)},
                    {"value": "rising", "label": "Rising", "count": len([row for row in segments if row["market_state"] == "rising"])},
                    {"value": "cooling", "label": "Cooling", "count": len([row for row in segments if row["market_state"] == "cooling"])},
                    {"value": "stable", "label": "Stable", "count": len([row for row in segments if row["market_state"] == "stable"])},
                ],
                "segment_options": [
                    {
                        "value": row["wipo_industry_code"],
                        "label": row["wipo_industry_code"],
                        "market_state": row["market_state"],
                        "total_family_count": row["total_family_count"],
                    }
                    for row in filtered_segments
                ],
                "selected_segment": selected_segment_id,
            },
            segments=filtered_segments,
            selected_segment=selected_segment,
            methodology=[
                {
                    "code": "bounded_scope",
                    "title": "Bounded mega-cluster scope",
                    "detail": "All market surfaces are restricted to the approved PatentIQ mega-cluster family universe rather than whole-world patent totals.",
                },
                {
                    "code": "pit_current_state",
                    "title": "Current-state PIT serving",
                    "detail": "Density, ownership, and CPC panels use latest point-in-time slices. Historical trend lines remain separate from current-state overlays.",
                },
                {
                    "code": "owner_truth_limit",
                    "title": "Historical owner truth is limited",
                    "detail": "Ownership leaderboards emphasize latest PIT concentration. Historical owner truth support remains partial and should not be overstated.",
                },
            ],
            meta=ResponseMeta(
                page="market_intelligence.workspace",
                artifact_sources=[str(path) for path in self.repository.artifacts()],
                support_level=SupportLevel.moderate,
                caveats=[
                    Caveat(
                        code="state_vs_history",
                        title="Current state versus replay",
                        detail="Current-state market labels should not be collapsed into historical chronology. Use the trend panels to inspect replay and the state labels to read the latest bounded surface.",
                    ),
                    Caveat(
                        code="classification_replay",
                        title="Stable field replay",
                        detail="Field and CPC slices are anchored to stable classification replay rather than dated code-mutation truth.",
                    ),
                ],
            ),
        )

    def get_market_overview_history(self) -> MarketSectionResponse:
        rows = self._map_market_overview_rows(self.repository.get_market_overview_history())
        return MarketSectionResponse(
            segment_id=None,
            rows=rows,
            meta=ResponseMeta(
                page="market_intelligence.market_overview_history",
                artifact_sources=[str(path) for path in self.repository.artifacts()],
                support_level=SupportLevel.moderate,
                caveats=[
                    Caveat(
                        code="market_primary_field_universe",
                        title="Primary-field market universe",
                        detail="Market-wide yearly rollups use the bounded 10-field primary WIPO assignment so the workspace can serve a unique family universe without overlapping segment totals.",
                    )
                ],
            ),
        )

    def get_leading_jurisdictions(
        self,
        as_of_year: int | None = None,
        limit_per_field: int = 5,
    ) -> MarketSectionResponse:
        rows = self._map_leading_jurisdiction_rows(
            self.repository.get_leading_jurisdictions(as_of_year=as_of_year, limit_per_field=limit_per_field)
        )
        return self._build_section_response(
            page="market_intelligence.leading_jurisdictions",
            rows=rows,
            section_key="leading_jurisdictions",
            metric_basis="Unique DOCDB families",
            scope_basis="Served market fields with primary-field replay",
            sum_safe=False,
            overlap_policy="Jurisdiction rows are deduplicated within each field, but families can still appear in multiple jurisdictions.",
            caveats=[
                Caveat(
                    code="office_coded_geography",
                    title="Office-coded geography",
                    detail="Jurisdiction rows reflect office-coded protection footprint, so EP and WO may appear alongside country codes unless filtered in the UI.",
                )
            ],
        )

    def get_segment_applications_grants(
        self,
        segment_id: str,
        year_from: int | None = None,
        year_to: int | None = None,
        jurisdiction_limit: int = 12,
    ) -> MarketSectionResponse:
        rows = self._map_application_grant_rows(
            self.repository.get_segment_applications_grants(
                segment_id=segment_id,
                year_from=year_from,
                year_to=year_to,
                jurisdiction_limit=jurisdiction_limit,
            )
        )
        return self._build_section_response(
            page="market_intelligence.segment_applications_grants",
            rows=rows,
            section_key="applications_grants",
            segment_id=segment_id,
            metric_basis="Distinct appln_id publication events",
            scope_basis="Selected field using primary-field family replay",
            sum_safe=False,
            overlap_policy="Application and grant rows are event flows by office and year, not a unique-family stock view.",
            caveats=[
                Caveat(
                    code="event_flow_not_stock",
                    title="Event flow, not stock",
                    detail="Application and grant counts represent office-level publication events. They should not be read as the same metric as unique family stock or active-family counts.",
                )
            ],
        )

    def get_segment_grant_mix(
        self,
        segment_id: str,
        as_of_year: int | None = None,
        limit: int = 12,
        offset: int = 0,
    ) -> MarketSectionResponse:
        rows = self.repository.get_segment_grant_mix(
            segment_id=segment_id,
            as_of_year=as_of_year,
            limit=limit,
            offset=offset,
        )
        total_count = self._extract_total_count(rows)
        return self._build_section_response(
            page="market_intelligence.segment_grant_mix",
            rows=self._map_grant_mix_rows(rows),
            section_key="grant_mix",
            segment_id=segment_id,
            metric_basis="Distinct appln_id publication events",
            scope_basis="Selected field using primary-field family replay",
            sum_safe=False,
            overlap_policy="Application and grant counts can coexist for the same office-year slice and should be read as complementary event streams.",
            pagination=PaginationMetadata(limit=limit, offset=offset, returned_count=len(rows), total_count=total_count),
            caveats=[
                Caveat(
                    code="grant_mix_office_view",
                    title="Office-level mix",
                    detail="Rows summarize office-level application and grant publications for the selected year rather than legal family status.",
                )
            ],
        )

    def get_segment_unitary_patent_summary(
        self,
        segment_id: str,
        jurisdiction_limit: int = 18,
    ) -> MarketSectionResponse:
        rows = self._map_unitary_patent_rows(
            self.repository.get_segment_unitary_patent_summary(
                segment_id=segment_id,
                jurisdiction_limit=jurisdiction_limit,
            )
        )
        return self._build_section_response(
            page="market_intelligence.segment_unitary_patent",
            rows=rows,
            section_key="unitary_patent",
            segment_id=segment_id,
            metric_basis="Register-confirmed UP families plus heuristic UP family coverage",
            scope_basis="Selected field using primary-field family replay",
            sum_safe=False,
            overlap_policy="Register-confirmed yearly rows and heuristic member-state coverage rows answer different questions and should not be summed together.",
            caveats=[
                Caveat(
                    code="unitary_signal_split",
                    title="Register-confirmed versus heuristic UP signal",
                    detail="The yearly register stream is authoritative but sparse in the current snapshot. Jurisdiction coverage rows come from heuristic UP detection expanded to member states.",
                )
            ],
        )

    def get_cpc_trends(
        self,
        segment_id: str | None = None,
        as_of_year: int | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> MarketSectionResponse:
        rows = self.repository.get_cpc_trends(
            segment_id=segment_id,
            as_of_year=as_of_year,
            limit=limit,
            offset=offset,
        )
        total_count = self._extract_total_count(rows)
        return self._build_section_response(
            page="market_intelligence.cpc_trends",
            rows=self._map_cpc_trend_rows(rows),
            section_key="cpc_trends",
            segment_id=segment_id,
            metric_basis="Overlapping CPC family slices",
            scope_basis="Selected field using replayed CPC membership history",
            sum_safe=False,
            overlap_policy="Families can contribute to multiple CPC main groups, so CPC rows should not be summed back to one field total.",
            caveats=[
                Caveat(
                    code="cpc_trend_scope",
                    title="Latest-year CPC emphasis",
                    detail="CPC trend rows are ranked within the bounded segment frame and should be read as directional composition, not literal whole-world CPC dominance.",
                ),
                Caveat(
                    code="cpc_trend_history",
                    title="Historical-safe but replayed CPC history",
                    detail="Year filtering is stable for comparison, but CPC membership is replayed to history rather than sourced from dated code-mutation truth.",
                ),
            ],
            pagination=PaginationMetadata(limit=limit, offset=offset, returned_count=len(rows), total_count=total_count),
        )

    def get_segment_cpc_jurisdictions(
        self,
        segment_id: str,
        as_of_year: int | None = None,
        cpc_main_group: str | None = None,
        jurisdiction_code: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> MarketSectionResponse:
        rows = self.repository.get_segment_cpc_jurisdictions(
            segment_id=segment_id,
            as_of_year=as_of_year,
            cpc_main_group=cpc_main_group,
            jurisdiction_code=jurisdiction_code,
            limit=limit,
            offset=offset,
        )
        total_count = self._extract_total_count(rows)
        return self._build_section_response(
            page="market_intelligence.segment_cpc_jurisdictions",
            rows=self._map_cpc_jurisdiction_rows(rows),
            section_key="cpc_jurisdictions",
            segment_id=segment_id,
            metric_basis="Overlapping CPC-by-jurisdiction family slices",
            scope_basis="Selected field using replayed CPC membership history",
            sum_safe=False,
            overlap_policy="Rows are non-additive across CPC groups and jurisdictions because one family can appear in multiple CPC slices and multiple jurisdictions.",
            caveats=[
                Caveat(
                    code="classification_jurisdiction_support",
                    title="Mixed support levels across CPC geography",
                    detail="CPC-by-jurisdiction rows are available across the served market frame, but support strength varies by slice and should be interpreted with the support-level caveat in mind.",
                )
            ],
            pagination=PaginationMetadata(limit=limit, offset=offset, returned_count=len(rows), total_count=total_count),
        )

    def get_segment_cpc_owners(
        self,
        segment_id: str,
        cpc_main_group: str,
        as_of_year: int | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> MarketSectionResponse:
        rows = self.repository.get_segment_cpc_owners(
            segment_id=segment_id,
            cpc_main_group=cpc_main_group,
            as_of_year=as_of_year,
            limit=limit,
            offset=offset,
        )
        total_count = self._extract_total_count(rows)
        return self._build_section_response(
            page="market_intelligence.segment_cpc_owners",
            rows=self._map_cpc_owner_rows(rows),
            section_key="cpc_owners",
            segment_id=segment_id,
            metric_basis="Unique families within the selected CPC slice",
            scope_basis="Selected field and one CPC main group using current-owner replay",
            sum_safe=False,
            overlap_policy="Owner rows are additive only within the selected CPC slice. CPC slices remain non-additive across different CPC groups.",
            caveats=[
                Caveat(
                    code="current_owner_replay",
                    title="Current-owner replay",
                    detail="Owner names reflect the current harmonized owner basis carried by the family compare PIT, not true historical owner-at-year reconstruction.",
                )
            ],
            pagination=PaginationMetadata(limit=limit, offset=offset, returned_count=len(rows), total_count=total_count),
        )

    def get_segment_cpc_citing_owners(
        self,
        segment_id: str,
        cpc_main_group: str,
        as_of_year: int | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> MarketSectionResponse:
        rows = self.repository.get_segment_cpc_citing_owners(
            segment_id=segment_id,
            cpc_main_group=cpc_main_group,
            as_of_year=as_of_year,
            limit=limit,
            offset=offset,
        )
        total_count = self._extract_total_count(rows)
        return self._build_section_response(
            page="market_intelligence.segment_cpc_citing_owners",
            rows=self._map_cpc_citing_owner_rows(rows),
            section_key="cpc_citing_owners",
            segment_id=segment_id,
            metric_basis="External citation events into the selected CPC slice",
            scope_basis="Selected field and one CPC main group using replayed CPC membership history",
            sum_safe=False,
            overlap_policy="Rows rank named external citing owners inside the selected CPC slice. Placeholder owners are excluded, so the table is directional rather than a full event-total ledger.",
            caveats=[
                Caveat(
                    code="classification_replay",
                    title="Replayed CPC membership",
                    detail="The cited-family CPC slice follows the current classification replay carried by the classification PIT, not a fully dated CPC-mutation history.",
                ),
                Caveat(
                    code="named_citing_owner_only",
                    title="Named citing owners only",
                    detail="Rows exclude placeholder citing-owner names, and raw self-citation flags may not remove every same-owner edge after harmonization.",
                ),
            ],
            pagination=PaginationMetadata(limit=limit, offset=offset, returned_count=len(rows), total_count=total_count),
        )

    def get_citation_trends(
        self,
        segment_id: str | None = None,
        as_of_year: int | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> MarketSectionResponse:
        rows = self.repository.get_citation_trends(
            segment_id=segment_id,
            as_of_year=as_of_year,
            limit=limit,
            offset=offset,
        )
        total_count = self._extract_total_count(rows)
        return MarketSectionResponse(
            segment_id=segment_id,
            rows=[
                {
                    "as_of_year": self._to_int(row.get("as_of_year"), 0),
                    "wipo_field": self._to_text(row.get("wipo_industry_code")),
                    "citation_event_count": self._to_int(row.get("citation_event_count"), 0),
                    "citation_count": self._to_float(row.get("citation_count"), 0.0),
                    "citation_lethality_sum": self._to_float(row.get("citation_lethality_sum_raw"), 0.0),
                    "distinct_citing_assignee_count": self._to_int(row.get("distinct_citing_assignee_count"), 0),
                    "distinct_citing_jurisdiction_count": self._to_int(row.get("distinct_citing_jurisdiction_count"), 0),
                    "citation_pressure_index": self._to_float(row.get("citation_pressure_index"), 0.0),
                    "market_citation_state": self._to_text(row.get("market_citation_state"), "stable"),
                    "market_state_reference": self._to_text(row.get("market_state_reference"), "stable"),
                }
                for row in rows
            ],
            meta=ResponseMeta(
                page="market_intelligence.citation_trends",
                artifact_sources=[str(path) for path in self.repository.artifacts()],
                support_level=SupportLevel.moderate,
                caveats=[
                    Caveat(
                        code="classification_replay",
                        title="Stable field replay",
                        detail="Market citation field slices are anchored to stable family-to-field membership rather than dated code-mutation truth.",
                    )
                ],
                pagination=PaginationMetadata(limit=limit, offset=offset, returned_count=len(rows), total_count=total_count),
            ),
        )

    def get_citation_jurisdictions(
        self,
        segment_id: str | None = None,
        as_of_year: int | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> MarketSectionResponse:
        rows = self.repository.get_citation_jurisdictions(
            segment_id=segment_id,
            as_of_year=as_of_year,
            limit=limit,
            offset=offset,
        )
        total_count = self._extract_total_count(rows)
        return MarketSectionResponse(
            segment_id=segment_id,
            rows=[
                {
                    "as_of_year": self._to_int(row.get("as_of_year"), 0),
                    "wipo_field": self._to_text(row.get("wipo_industry_code")),
                    "jurisdiction_code": self._to_text(row.get("jurisdiction_code")),
                    "citation_event_count": self._to_int(row.get("citation_event_count"), 0),
                    "distinct_citing_assignee_count": self._to_int(row.get("distinct_citing_assignee_count"), 0),
                    "citation_count": self._to_float(row.get("citation_count"), 0.0),
                    "citation_lethality_sum": self._to_float(row.get("citation_lethality_sum_raw"), 0.0),
                    "citation_pressure_index": self._to_float(row.get("citation_pressure_index"), 0.0),
                }
                for row in rows
            ],
            meta=ResponseMeta(
                page="market_intelligence.citation_jurisdictions",
                artifact_sources=[str(path) for path in self.repository.artifacts()],
                support_level=SupportLevel.moderate,
                caveats=[
                    Caveat(
                        code="citation_geography",
                        title="Citing geography",
                        detail="Jurisdiction rows reflect the citing-side publication geography in the clean citation ledger.",
                    )
                ],
                pagination=PaginationMetadata(limit=limit, offset=offset, returned_count=len(rows), total_count=total_count),
            ),
        )

    def get_citation_attackers(
        self,
        segment_id: str | None = None,
        as_of_year: int | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> MarketSectionResponse:
        rows = self.repository.get_citation_attackers(
            segment_id=segment_id,
            as_of_year=as_of_year,
            limit=limit,
            offset=offset,
        )
        total_count = self._extract_total_count(rows)
        return MarketSectionResponse(
            segment_id=segment_id,
            rows=[
                {
                    "as_of_year": self._to_int(row.get("as_of_year"), 0),
                    "wipo_field": self._to_text(row.get("wipo_industry_code")),
                    "citing_assignee": self._to_text(row.get("citing_assignee_name")),
                    "citation_event_count": self._to_int(row.get("citation_event_count"), 0),
                    "distinct_citing_jurisdiction_count": self._to_int(row.get("distinct_citing_jurisdiction_count"), 0),
                    "citation_count": self._to_float(row.get("citation_count"), 0.0),
                    "citation_lethality_sum": self._to_float(row.get("citation_lethality_sum_raw"), 0.0),
                    "attacker_pressure_index": self._to_float(row.get("attacker_pressure_index"), 0.0),
                }
                for row in rows
            ],
            meta=ResponseMeta(
                page="market_intelligence.citation_attackers",
                artifact_sources=[str(path) for path in self.repository.artifacts()],
                support_level=SupportLevel.moderate,
                pagination=PaginationMetadata(limit=limit, offset=offset, returned_count=len(rows), total_count=total_count),
            ),
        )

    def _normalize_market_state(self, value: str) -> str:
        normalized = (value or "all").strip().lower()
        if normalized not in {"all", "rising", "cooling", "stable"}:
            return "all"
        return normalized

    def _group_timeseries(self, rows: list[dict[str, object]]) -> dict[str, list[dict[str, object]]]:
        year_medians: dict[int, int] = {}
        year_buckets: dict[int, list[int]] = {}
        for row in rows:
            year = self._to_int(row.get("family_priority_year"), 0)
            if year <= 0:
                continue
            year_buckets.setdefault(year, []).append(self._to_int(row.get("family_count"), 0))
        for year, counts in year_buckets.items():
            year_medians[year] = int(round(median(counts))) if counts else 0

        grouped: dict[str, list[dict[str, object]]] = {}
        for row in rows:
            segment = self._to_text(row.get("wipo_industry_code"))
            year = self._to_int(row.get("family_priority_year"), 0)
            current_count = self._to_int(row.get("family_count"), 0)
            prior_count = self._to_int(row.get("prior_family_count"), 0)
            market_median_count = year_medians.get(year, 0)
            growth_rate = 0.0
            if prior_count > 0:
                growth_rate = (current_count - prior_count) / prior_count
            grouped.setdefault(segment, []).append(
                {
                    "year": year,
                    "family_count": current_count,
                    "prior_family_count": prior_count,
                    "market_state": self._to_text(
                        row.get("market_state") if self._to_bool(row.get("market_state_ui_safe")) else "provisional",
                        "stable",
                    ),
                    "market_state_ui_safe": self._to_bool(row.get("market_state_ui_safe")),
                    "is_recent_priority_year_incomplete": self._to_bool(row.get("is_recent_priority_year_incomplete")),
                    "latest_comparable_year": self._to_int(row.get("latest_comparable_year"), 0),
                    "growth_rate": round(growth_rate, 4),
                    "year_over_year_delta_pct": round(growth_rate, 4),
                    "market_median_family_count": market_median_count,
                    "delta_from_market_median": current_count - market_median_count,
                }
            )
        return grouped

    def _map_segment_row(self, row: dict[str, object], sparkline: list[dict[str, object]]) -> dict[str, object]:
        owner_count = self._to_int(row.get("segment_owner_count_hist_proxy_asof"), 0)
        top_owner_share = self._to_float(row.get("segment_top_owner_share_hist_proxy"), 0.0)
        current_count = self._to_int(row.get("segment_priority_year_family_count_asof"), 0)
        prior_count = self._to_int(row.get("segment_prior_priority_year_family_count_asof"), 0)
        market_state_ui_safe = self._to_bool(row.get("segment_market_state_ui_safe_asof"))
        priority_year_incomplete = self._to_bool(row.get("segment_priority_year_incomplete_asof"))
        heat_state = self._to_text(row.get("segment_heat_state_asof"), "stable") if market_state_ui_safe else "provisional"
        momentum_delta = 0.0
        if prior_count > 0:
            momentum_delta = (current_count - prior_count) / prior_count
        return {
            "segment_id": self._to_text(row.get("segment_id")),
            "wipo_industry_code": self._to_text(row.get("wipo_industry_code")),
            "market_state": self._to_text(row.get("market_state"), "stable"),
            "total_family_count": self._to_int(row.get("total_family_count"), 0),
            "latest_year": self._to_int(row.get("latest_year"), 0),
            "latest_comparable_year": self._to_int(row.get("latest_comparable_year"), 0),
            "latest_year_incomplete": self._to_bool(row.get("latest_year_incomplete")),
            "latest_market_year": self._to_int(row.get("latest_market_year"), 0),
            "snapshot_date": self._to_iso(row.get("snapshot_date")),
            "segment_heat_state_asof": heat_state,
            "segment_market_state_ui_safe_asof": market_state_ui_safe,
            "segment_priority_year_incomplete_asof": priority_year_incomplete,
            "segment_latest_comparable_year": self._to_int(row.get("segment_latest_comparable_year"), 0),
            "segment_family_count_stock_asof": self._to_int(row.get("segment_family_count_stock_asof"), 0),
            "segment_priority_year_family_count_asof": current_count,
            "segment_prior_priority_year_family_count_asof": prior_count,
            "segment_growth_index_asof": round(self._to_float(row.get("segment_growth_index_asof"), 0.0), 4),
            "segment_owner_count_hist_proxy_asof": owner_count,
            "segment_blocking_density_asof": round(self._to_float(row.get("segment_blocking_density_asof"), 0.0), 2),
            "segment_field_balance_asof": round(self._to_float(row.get("segment_field_balance_asof"), 0.0), 3),
            "segment_active_family_count_asof": self._to_int(row.get("segment_active_family_count_asof"), 0),
            "segment_active_weight_asof": round(self._to_float(row.get("segment_active_weight_asof"), 0.0), 4),
            "segment_active_jurisdiction_share_asof": round(
                self._to_float(row.get("segment_active_jurisdiction_share_asof"), 0.0), 4
            ),
            "segment_enforceability_density_asof": round(
                self._to_float(row.get("segment_enforceability_density_asof"), 0.0), 2
            ),
            "segment_top_owner_share_hist_proxy": round(top_owner_share, 4),
            "historical_compare_safe": self._to_bool(row.get("historical_compare_safe")),
            "historical_owner_truth_supported": self._to_bool(row.get("historical_owner_truth_supported")),
            "current_owner_bridge_replayed_to_history": self._to_bool(
                row.get("current_owner_bridge_replayed_to_history")
            ),
            "historical_oecd_supported": self._to_bool(row.get("historical_oecd_supported")),
            "momentum_delta_pct": round(momentum_delta, 4),
            "crowding_label": self._crowding_label(owner_count, top_owner_share),
            "sparkline": sparkline[-8:],
        }

    def _map_market_overview_rows(self, rows: list[dict[str, object]]) -> list[dict[str, object]]:
        mapped: list[dict[str, object]] = []
        for row in rows:
            owner_count = self._to_int(row.get("owner_count_asof"), 0)
            top_owner_share = self._to_float(row.get("top_owner_share_asof"), 0.0)
            mapped.append(
                {
                    "as_of_year": self._to_int(row.get("as_of_year"), 0),
                    "current_snapshot_date": self._to_iso(row.get("current_snapshot_date")),
                    "market_family_count_asof": self._to_int(row.get("market_family_count_asof"), 0),
                    "pending_family_count_asof": self._to_int(row.get("pending_family_count_asof"), 0),
                    "fully_active_family_count_asof": self._to_int(row.get("fully_active_family_count_asof"), 0),
                    "partially_lapsed_family_count_asof": self._to_int(row.get("partially_lapsed_family_count_asof"), 0),
                    "dead_family_count_asof": self._to_int(row.get("dead_family_count_asof"), 0),
                    "owner_count_asof": owner_count,
                    "avg_blocking_power_score_asof": round(
                        self._to_float(row.get("avg_blocking_power_score_asof"), 0.0), 2
                    ),
                    "avg_enforceability_score_asof": round(
                        self._to_float(row.get("avg_enforceability_score_asof"), 0.0), 2
                    ),
                    "avg_forward_citations_clean_asof": round(
                        self._to_float(row.get("avg_forward_citations_clean_asof"), 0.0), 2
                    ),
                    "total_forward_citations_clean_asof": round(
                        self._to_float(row.get("total_forward_citations_clean_asof"), 0.0), 0
                    ),
                    "top_owner_share_asof": round(top_owner_share, 4),
                    "crowding_label": self._crowding_label(owner_count, top_owner_share),
                }
            )
        return mapped

    def _map_timeseries_rows(self, rows: list[dict[str, object]]) -> list[dict[str, object]]:
        return self._group_timeseries(rows).get(self._to_text(rows[0].get("wipo_industry_code")), []) if rows else []

    def _map_owner_rows(self, rows: list[dict[str, object]]) -> list[dict[str, object]]:
        return [
            {
                "as_of_year": self._to_int(row.get("as_of_year"), 0),
                "leaderboard_rank": self._to_int(row.get("leaderboard_rank"), 0),
                "owner_name": self._owner_name(row),
                "owner_id": self._to_text(row.get("owner_name_harmonized")) or None,
                "in_segment_family_count_hist_proxy": self._to_int(row.get("in_segment_family_count_hist_proxy"), 0),
                "in_segment_family_share_hist_proxy": round(
                    self._to_float(row.get("in_segment_family_share_hist_proxy"), 0.0), 4
                ),
                "avg_blocking_score_asof": round(self._to_float(row.get("avg_blocking_score_asof"), 0.0), 2),
                "total_blocking_score_asof": round(self._to_float(row.get("total_blocking_score_asof"), 0.0), 2),
                "field_presence_weight_asof": round(self._to_float(row.get("field_presence_weight_asof"), 0.0), 3),
                "family_composite_status_asof": self._to_text(row.get("family_composite_status_asof"), "n/a"),
            }
            for row in rows
        ]

    def _map_family_rows(self, rows: list[dict[str, object]]) -> list[dict[str, object]]:
        return [
            {
                "as_of_year": self._to_int(row.get("as_of_year"), 0),
                "leaderboard_rank": self._to_int(row.get("leaderboard_rank"), 0),
                "docdb_family_id": self._to_int(row.get("docdb_family_id"), 0),
                "owner_name": self._owner_name_from_identifier(row.get("owner_name_harmonized_current")),
                "owner_id": self._to_text(row.get("owner_name_harmonized_current")) or None,
                "avg_blocking_score_asof": round(self._to_float(row.get("avg_blocking_score_asof"), 0.0), 2),
                "total_blocking_score_asof": round(self._to_float(row.get("total_blocking_score_asof"), 0.0), 2),
                "field_presence_weight_asof": round(self._to_float(row.get("field_presence_weight_asof"), 0.0), 3),
                "family_composite_status_asof": self._to_text(row.get("family_composite_status_asof"), "n/a"),
            }
            for row in rows
        ]

    def _map_cpc_trend_rows(self, rows: list[dict[str, object]]) -> list[dict[str, object]]:
        return [
            {
                "as_of_year": self._to_int(row.get("as_of_year"), 0),
                "current_snapshot_date": self._to_iso(row.get("current_snapshot_date")),
                "wipo_field": self._to_text(row.get("wipo_industry_code")),
                "cpc_main_group": self._to_text(row.get("cpc_main_group")),
                "cpc_main_group_label": self._to_text(row.get("cpc_main_group_label")),
                "cpc_family_count_asof": self._to_int(row.get("cpc_family_count_asof"), 0),
                "cpc_active_family_count_asof": self._to_int(row.get("cpc_active_family_count_asof"), 0),
                "cpc_family_share_within_segment_asof": round(
                    self._to_float(row.get("cpc_family_share_within_segment_asof"), 0.0), 4
                ),
                "cpc_active_family_share_within_segment_asof": round(
                    self._to_float(row.get("cpc_active_family_share_within_segment_asof"), 0.0), 4
                ),
                "cpc_blocking_density_asof": round(self._to_float(row.get("cpc_blocking_density_asof"), 0.0), 2),
                "cpc_enforceability_density_asof": round(
                    self._to_float(row.get("cpc_enforceability_density_asof"), 0.0), 2
                ),
                "cpc_pre_asof_forward_citations_clean_avg_asof": round(
                    self._to_float(row.get("cpc_pre_asof_forward_citations_clean_avg_asof"), 0.0), 2
                ),
                "cpc_avg_rcf_score_asof": round(self._to_float(row.get("cpc_avg_rcf_score_asof"), 0.0), 2),
                "cpc_prior_family_count_asof": self._to_int(row.get("cpc_prior_family_count_asof"), 0),
                "cpc_growth_index_asof": round(self._to_float(row.get("cpc_growth_index_asof"), 0.0), 4),
                "cpc_heat_state_asof": self._to_text(row.get("cpc_heat_state_asof"), "stable"),
                "cpc_rank_within_segment_year": self._to_int(row.get("cpc_rank_within_segment_year"), 0),
            }
            for row in rows
        ]

    def _map_field_jurisdiction_rows(self, rows: list[dict[str, object]]) -> list[dict[str, object]]:
        return [
            {
                "as_of_year": self._to_int(row.get("as_of_year"), 0),
                "wipo_field": self._to_text(row.get("wipo_field")),
                "jurisdiction_code": self._to_text(row.get("jurisdiction_code")),
                "jurisdiction_family_count_asof": self._to_int(row.get("jurisdiction_family_count_asof"), 0),
                "jurisdiction_active_family_count_asof": self._to_int(
                    row.get("jurisdiction_active_family_count_asof"), 0
                ),
                "jurisdiction_family_share_within_segment_asof": round(
                    self._to_float(row.get("jurisdiction_family_share_within_segment_asof"), 0.0), 4
                ),
                "jurisdiction_active_family_share_within_segment_asof": round(
                    self._to_float(row.get("jurisdiction_active_family_share_within_segment_asof"), 0.0), 4
                ),
                "cpc_group_count": self._to_int(row.get("cpc_group_count"), 0),
            }
            for row in rows
        ]

    def _map_cpc_jurisdiction_rows(self, rows: list[dict[str, object]]) -> list[dict[str, object]]:
        return [
            {
                "as_of_year": self._to_int(row.get("as_of_year"), 0),
                "current_snapshot_date": self._to_iso(row.get("current_snapshot_date")),
                "wipo_field": self._to_text(row.get("wipo_field")),
                "cpc_main_group": self._to_text(row.get("cpc_main_group")),
                "jurisdiction_code": self._to_text(row.get("jurisdiction_code")),
                "family_count_asof": self._to_int(row.get("family_count_asof"), 0),
                "active_family_count_asof": self._to_int(row.get("active_family_count_asof"), 0),
                "family_share_within_slice_asof": round(
                    self._to_float(row.get("family_share_within_slice_asof"), 0.0), 4
                ),
                "citation_pressure_index_asof": round(
                    self._to_float(row.get("citation_pressure_index_asof"), 0.0), 4
                ),
                "growth_index_asof": round(self._to_float(row.get("growth_index_asof"), 0.0), 4),
                "blocking_density_asof": round(self._to_float(row.get("blocking_density_asof"), 0.0), 2),
                "enforceability_density_asof": round(
                    self._to_float(row.get("enforceability_density_asof"), 0.0), 2
                ),
                "slice_rank_within_year": self._to_int(row.get("slice_rank_within_year"), 0),
            }
            for row in rows
        ]

    def _map_cpc_owner_rows(self, rows: list[dict[str, object]]) -> list[dict[str, object]]:
        return [
            {
                "as_of_year": self._to_int(row.get("as_of_year"), 0),
                "wipo_field": self._to_text(row.get("wipo_field")),
                "cpc_main_group": self._to_text(row.get("cpc_main_group")),
                "leaderboard_rank": self._to_int(row.get("leaderboard_rank"), 0),
                "owner_name": self._to_text(row.get("owner_name_display_current"))
                or self._owner_name_from_identifier(row.get("owner_name_harmonized")),
                "owner_id": self._to_text(row.get("owner_name_harmonized")) or None,
                "owner_family_count_in_cpc_asof": self._to_int(row.get("owner_family_count_in_cpc_asof"), 0),
                "owner_active_family_count_in_cpc_asof": self._to_int(row.get("owner_active_family_count_in_cpc_asof"), 0),
                "owner_family_share_within_cpc_asof": round(
                    self._to_float(row.get("owner_family_share_within_cpc_asof"), 0.0), 4
                ),
                "owner_active_family_share_within_cpc_asof": round(
                    self._to_float(row.get("owner_active_family_share_within_cpc_asof"), 0.0), 4
                ),
                "avg_blocking_score_asof": round(self._to_float(row.get("avg_blocking_score_asof"), 0.0), 2),
                "avg_enforceability_score_asof": round(self._to_float(row.get("avg_enforceability_score_asof"), 0.0), 2),
            }
            for row in rows
        ]

    def _map_citation_trend_rows(self, rows: list[dict[str, object]]) -> list[dict[str, object]]:
        mapped = [
            {
                "as_of_year": self._to_int(row.get("as_of_year"), 0),
                "wipo_field": self._to_text(row.get("wipo_industry_code")),
                "citation_event_count": self._to_int(row.get("citation_event_count"), 0),
                "citation_count": self._to_float(row.get("citation_count"), 0.0),
                "citation_lethality_sum": self._to_float(row.get("citation_lethality_sum_raw"), 0.0),
                "distinct_citing_assignee_count": self._to_int(row.get("distinct_citing_assignee_count"), 0),
                "distinct_citing_jurisdiction_count": self._to_int(row.get("distinct_citing_jurisdiction_count"), 0),
                "citation_pressure_index": self._to_float(row.get("citation_pressure_index"), 0.0),
                "market_citation_state": self._to_text(row.get("market_citation_state"), "stable"),
                "market_state_reference": self._to_text(row.get("market_state_reference"), "stable"),
            }
            for row in rows
        ]
        mapped.sort(key=lambda row: (self._to_int(row.get("as_of_year"), 0), self._to_text(row.get("wipo_field"))))
        return mapped

    def _map_citation_jurisdiction_rows(self, rows: list[dict[str, object]]) -> list[dict[str, object]]:
        return [
            {
                "as_of_year": self._to_int(row.get("as_of_year"), 0),
                "wipo_field": self._to_text(row.get("wipo_industry_code")),
                "jurisdiction_code": self._to_text(row.get("jurisdiction_code")),
                "citation_event_count": self._to_int(row.get("citation_event_count"), 0),
                "distinct_citing_assignee_count": self._to_int(row.get("distinct_citing_assignee_count"), 0),
                "citation_count": self._to_float(row.get("citation_count"), 0.0),
                "citation_lethality_sum": self._to_float(row.get("citation_lethality_sum_raw"), 0.0),
                "citation_pressure_index": self._to_float(row.get("citation_pressure_index"), 0.0),
            }
            for row in rows
        ]

    def _map_citation_attacker_rows(self, rows: list[dict[str, object]]) -> list[dict[str, object]]:
        return [
            {
                "as_of_year": self._to_int(row.get("as_of_year"), 0),
                "wipo_field": self._to_text(row.get("wipo_industry_code")),
                "citing_assignee": self._to_text(row.get("citing_assignee_name")),
                "citation_event_count": self._to_int(row.get("citation_event_count"), 0),
                "distinct_citing_jurisdiction_count": self._to_int(row.get("distinct_citing_jurisdiction_count"), 0),
                "citation_count": self._to_float(row.get("citation_count"), 0.0),
                "citation_lethality_sum": self._to_float(row.get("citation_lethality_sum_raw"), 0.0),
                "attacker_pressure_index": self._to_float(row.get("attacker_pressure_index"), 0.0),
            }
            for row in rows
        ]

    def _map_leading_jurisdiction_rows(self, rows: list[dict[str, object]]) -> list[dict[str, object]]:
        return [
            {
                "as_of_year": self._to_int(row.get("as_of_year"), 0),
                "wipo_field": self._to_text(row.get("wipo_field")),
                "field_rank_within_year": self._to_int(row.get("field_rank_within_year"), 0),
                "jurisdiction_code": self._to_text(row.get("jurisdiction_code")),
                "jurisdiction_family_count_asof": self._to_int(row.get("jurisdiction_family_count_asof"), 0),
                "jurisdiction_active_family_count_asof": self._to_int(
                    row.get("jurisdiction_active_family_count_asof"), 0
                ),
                "jurisdiction_family_share_within_field_asof": round(
                    self._to_float(row.get("jurisdiction_family_share_within_field_asof"), 0.0), 4
                ),
            }
            for row in rows
        ]

    def _map_cpc_citing_owner_rows(self, rows: list[dict[str, object]]) -> list[dict[str, object]]:
        return [
            {
                "as_of_year": self._to_int(row.get("as_of_year"), 0),
                "wipo_field": self._to_text(row.get("wipo_field")),
                "cpc_main_group": self._to_text(row.get("cpc_main_group")),
                "leaderboard_rank": self._to_int(row.get("leaderboard_rank"), 0),
                "citing_owner_name": self._owner_name_from_identifier(row.get("citing_assignee_name")),
                "citing_owner_id": self._to_text(row.get("citing_assignee_name")) or None,
                "latest_citation_year": self._to_int(row.get("latest_citation_year"), 0),
                "citation_event_count": self._to_int(row.get("citation_event_count"), 0),
                "clean_citation_count": round(self._to_float(row.get("clean_citation_count"), 0.0), 2),
                "citation_lethality_sum": round(self._to_float(row.get("citation_lethality_sum"), 0.0), 2),
                "distinct_citing_jurisdiction_count": self._to_int(row.get("distinct_citing_jurisdiction_count"), 0),
                "cited_family_count": self._to_int(row.get("cited_family_count"), 0),
                "citation_event_share_within_cpc_asof": round(
                    self._to_float(row.get("citation_event_share_within_cpc_asof"), 0.0), 4
                ),
            }
            for row in rows
        ]

    def _map_application_grant_rows(self, rows: list[dict[str, object]]) -> list[dict[str, object]]:
        return [
            {
                "as_of_year": self._to_int(row.get("as_of_year"), 0),
                "wipo_field": self._to_text(row.get("wipo_field")),
                "jurisdiction_code": self._to_text(row.get("jurisdiction_code")),
                "application_count": self._to_int(row.get("application_count"), 0),
                "grant_count": self._to_int(row.get("grant_count"), 0),
                "total_event_count": self._to_int(row.get("total_event_count"), 0),
            }
            for row in rows
        ]

    def _map_grant_mix_rows(self, rows: list[dict[str, object]]) -> list[dict[str, object]]:
        return [
            {
                "as_of_year": self._to_int(row.get("as_of_year"), 0),
                "wipo_field": self._to_text(row.get("wipo_field")),
                "jurisdiction_code": self._to_text(row.get("jurisdiction_code")),
                "application_count": self._to_int(row.get("application_count"), 0),
                "grant_count": self._to_int(row.get("grant_count"), 0),
                "total_event_count": self._to_int(row.get("total_event_count"), 0),
                "grant_share_of_events": round(self._to_float(row.get("grant_share_of_events"), 0.0), 4),
            }
            for row in rows
        ]

    def _map_unitary_patent_rows(self, rows: list[dict[str, object]]) -> list[dict[str, object]]:
        return [
            {
                "row_kind": self._to_text(row.get("row_kind")),
                "wipo_field": self._to_text(row.get("wipo_field")),
                "as_of_year": self._to_int(row.get("as_of_year"), 0),
                "jurisdiction_code": self._to_text(row.get("jurisdiction_code")) or None,
                "register_confirmed_family_count": self._to_int(row.get("register_confirmed_family_count"), 0),
                "heuristic_family_count": self._to_int(row.get("heuristic_family_count"), 0),
                "unrolled_member_state_count": self._to_int(row.get("unrolled_member_state_count"), 0),
                "jurisdiction_family_count": self._to_int(row.get("jurisdiction_family_count"), 0),
                "ep_grant_event_count": self._to_int(row.get("ep_grant_event_count"), 0),
                "ep_grant_event_count_on_heuristic_up": self._to_int(row.get("ep_grant_event_count_on_heuristic_up"), 0),
            }
            for row in rows
        ]

    def _owner_name(self, row: dict[str, object]) -> str:
        display = self._to_text(row.get("owner_name_display_current"))
        if display:
            return display
        harmonized = self._to_text(row.get("owner_name_harmonized"))
        return self._owner_name_from_identifier(harmonized)

    def _owner_name_from_identifier(self, value: object) -> str:
        harmonized = self._to_text(value)
        return harmonized.replace("_", " ") if harmonized else "Metadata-only owner"

    def _crowding_label(self, owner_count: int, top_owner_share: float) -> str:
        if owner_count >= 200000 and top_owner_share <= 0.02:
            return "crowded"
        if top_owner_share >= 0.04:
            return "concentrated"
        if owner_count <= 80000:
            return "open"
        return "balanced"

    def _extract_total_count(self, rows: list[dict[str, object]]) -> int | None:
        if not rows:
            return 0
        total_count = rows[0].get("total_count")
        return self._to_int(total_count, 0) if total_count is not None else None

    def _build_section_response(
        self,
        *,
        page: str,
        rows: list[dict[str, object]],
        section_key: str,
        metric_basis: str,
        scope_basis: str,
        sum_safe: bool,
        overlap_policy: str,
        segment_id: str | None = None,
        caveats: list[Caveat] | None = None,
        pagination: PaginationMetadata | None = None,
        support_level: SupportLevel = SupportLevel.moderate,
    ) -> MarketSectionResponse:
        return MarketSectionResponse(
            segment_id=segment_id,
            section_key=section_key,
            metric_basis=metric_basis,
            scope_basis=scope_basis,
            sum_safe=sum_safe,
            overlap_policy=overlap_policy,
            rows=rows,
            meta=ResponseMeta(
                page=page,
                artifact_sources=[str(path) for path in self.repository.artifacts()],
                support_level=support_level,
                caveats=caveats or [],
                pagination=pagination,
            ),
        )

    def _to_int(self, value: object, default: int) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    def _to_float(self, value: object, default: float) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    def _to_text(self, value: object, default: str = "") -> str:
        if value is None:
            return default
        text = str(value)
        return text if text else default

    def _to_bool(self, value: object) -> bool:
        return bool(value)

    def _to_iso(self, value: object) -> str | None:
        if value is None:
            return None
        if isinstance(value, (date, datetime)):
            return value.isoformat()
        text = str(value)
        return text if text else None
