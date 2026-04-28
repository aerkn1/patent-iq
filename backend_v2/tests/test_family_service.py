from application.services.families import FamilyService


class FakeFamilyRepository:
    def __init__(self) -> None:
        self.last_citing_families_owner_filter: str | None = None

    def artifacts(self) -> list:
        return []

    def get_family_overview_context(self, family_id: str):
        if family_id != "123":
            return {}
        return {
            "docdb_family_id": 123,
            "owner_name_display": "Apple",
            "primary_wipo_field": "Computer technology",
            "primary_wipo_field_current": "Computer technology",
            "family_composite_status": "fully_active",
            "family_composite_status_asof": "fully_active",
            "family_earliest_priority_date": "2018-04-12",
            "family_priority_year": 2018,
            "family_size_docdb": 4,
            "active_jurisdiction_count": 3,
            "active_grant_branch_count": 2,
            "lapsed_jurisdiction_count": 1,
            "opposed_branch_count": 0,
            "family_coverage_stability_score": 0.84,
            "family_ui_blocking_power_score": 91.0,
            "family_overall_legal_enforceability_score": 4.2,
            "family_heritage_score": 13.5,
            "family_quality_index_6_score": 0.72,
            "oecd_quality_percentile": 74.0,
            "family_generality_percentile": 67.0,
            "family_originality_percentile": 71.0,
            "family_radicalness_percentile": 63.0,
            "family_science_grounding_score": 0.44,
            "family_science_grounding_percentile": 58.0,
            "raw_family_citation_count": 12,
            "pre_asof_forward_citations_weighted": 16.5,
            "data_completeness_pct_asof": 0.94,
            "current_owner_metadata_only": True,
            "historical_compare_safe": True,
            "historical_oecd_supported": False,
            "legal_durability_percentile": 88.0,
            "citation_heritage_percentile": 83.0,
            "scope_type": "mega_cluster_bounded",
            "is_main_window_family": True,
            "is_heritage_backfill_family": False,
            "is_semantic_candidate": True,
            "is_in_vector_sample": False,
            "covered_wipo_fields": ["Computer technology"],
            "family_tech_breadth_wipo_count": 1,
        }

    def get_family_compare_context(self, family_id: str):
        return self.get_family_overview_context(family_id)

    def get_family_suggestions(self, query: str, limit: int = 8):
        return [
            {
                "family_id": "123",
                "label": "123",
                "owner_name_display": "Apple",
                "primary_field": "Computer technology",
                "status": "fully_active",
            }
        ][:limit]

    def get_family_field_rows(self, family_id: str, as_of_year: int | None = None):
        return [
            {
                "wipo_industry_code": "Computer technology",
                "base_fraction": 0.8,
                "field_share_asof": 0.72,
                "field_share_method": "appln_weighted_field_share",
            }
        ]

    def get_family_field_timeseries(self, family_id: str):
        return [
            {
                "snapshot_year": 2024,
                "wipo_industry_code": "Computer technology",
                "base_fraction": 0.7,
                "field_share_asof": 0.72,
                "field_share_method": "appln_weighted_field_share",
            }
        ]

    def get_family_blocking_timeseries(self, family_id: str):
        return [{"snapshot_year": 2024, "ui_blocking_power_score": 88.0}]

    def get_family_member_publications(self, family_id: str, limit: int = 10, offset: int = 0):
        return ([{"appln_id": 101, "publication_number_full": "US123A", "is_application_stage": True}], 1)

    def get_family_member_publication_summary(self, family_id: str):
        return {"publication_count": 1, "application_stage_count": 1, "grant_stage_count": 0, "modifier_stage_count": 0}

    def get_family_citation_metrics(self, family_id: str):
        return {
            "family_forward_citations_raw": 11,
            "family_forward_citations_clean": 8,
            "family_forward_citations_weighted": 16.5,
            "family_fwd_cits5": 4,
            "family_fwd_cits7": 7,
            "family_backward_patent_citation_count": 5,
            "family_backward_citations_clean": 3,
            "family_backward_npl_citation_count": 2,
            "family_science_grounding_score": 0.44,
            "out_of_bounds_citation_count": 1,
            "out_of_bounds_citation_share": 0.09,
            "family_rcf_score": 0.28,
            "family_adjusted_citation_score_raw": 3.7,
        }

    def get_family_citation_event_summary(self, family_id: str):
        return {
            "forward_citing_owner_count": 5,
            "backward_cited_owner_count": 2,
        }

    def get_family_citation_chronology(self, family_id: str):
        return [
            {
                "as_of_date": "2024-12-31",
                "as_of_year": 2024,
                "is_observed_as_of_snapshot": True,
                "forward_citation_event_count_year": 3,
                "pre_asof_forward_citation_event_count": 12,
                "pre_asof_forward_clean_citation_event_count": 9,
                "pre_asof_forward_citations_weighted": 16.5,
                "pre_asof_unique_citing_family_count": 6,
                "pre_asof_unique_citing_owner_count": 5,
                "backward_citation_event_count_year": 1,
                "pre_asof_backward_citation_event_count": 5,
                "pre_asof_backward_clean_citation_event_count": 4,
                "pre_asof_distinct_cited_family_count": 3,
                "pre_asof_citing_assignee_diversity": 0.52,
                "pre_asof_attacker_density_score": 0.33,
                "first_forward_citation_date_asof": "2021-02-18",
                "latest_forward_citation_date_asof": "2024-10-22",
                "window_5y_closed": True,
                "window_7y_closed": False,
                "pre_asof_forward_clean_5y": 4,
                "pre_asof_forward_clean_7y": 6,
                "data_completeness_pct_asof": 0.94,
                "historical_citation_safe": True,
                "chronology_support_level": "high",
                "method_version": "gold_family_citation_chronology_v1",
            }
        ]

    def get_family_citing_families(
        self,
        family_id: str,
        limit: int = 50,
        offset: int = 0,
        owner_filter: str | None = None,
    ):
        self.last_citing_families_owner_filter = owner_filter
        return (
            [
                {
                    "citing_docdb_family_id": 456,
                    "citing_assignee_name": "Samsung",
                    "distinct_cited_member_count": 2,
                    "distinct_citing_publication_count": 2,
                    "first_citation_date": "2020-02-01",
                    "latest_citation_date": "2024-01-10",
                }
            ],
            1,
        )

    def get_family_top_cited_members(self, family_id: str, limit: int = 10):
        return [
            {
                "publication_number_full": "US123A",
                "focal_publication_office": "US",
                "focal_publication_kind": "A1",
                "focal_publication_date": "2019-03-01",
                "is_application_stage": True,
                "is_grant_stage": False,
                "citation_event_count": 7,
                "clean_citation_event_count": 5,
                "citing_family_count": 4,
                "citing_owner_count": 3,
                "first_citation_date": "2020-02-01",
                "latest_citation_date": "2024-01-10",
            }
        ]

    def get_family_top_citing_owners(self, family_id: str, limit: int = 10):
        return [
            {
                "citing_owner_name": "Samsung",
                "citation_event_count": 6,
                "clean_citation_event_count": 4,
                "citing_family_count": 2,
                "citing_publication_count": 3,
                "cited_member_count": 1,
                "citation_lethality_sum": 5.6,
                "first_citation_date": "2020-02-01",
                "latest_citation_date": "2024-01-10",
            }
        ]

    def get_family_feature_timeseries(self, family_id: str):
        return [
            {
                "as_of_date": "2024-12-31",
                "as_of_year": 2024,
                "is_observed_as_of_snapshot": True,
                "family_blocking_power_score_asof": 88.0,
                "family_enforceability_score_asof": 4.1,
                "family_rcf_score_asof": 0.31,
                "pre_asof_forward_citations_clean": 8,
                "pre_asof_forward_citations_weighted": 16.5,
                "pre_asof_unique_citing_family_count": 6,
                "pre_asof_citing_assignee_diversity": 0.52,
                "pre_asof_attacker_density_score": 0.33,
                "data_completeness_pct_asof": 0.94,
            }
        ]

    def get_family_classification_snapshot(self, family_id: str, as_of_year: int | None = None):
        return {"top_cpc_main_group_asof": "G06F", "classification_breadth_band_asof": "focused"}

    def get_family_classification_timeseries(self, family_id: str):
        return [{"as_of_year": 2024, "top_cpc_main_group_asof": "G06F"}]

    def get_family_forecasts(self, family_id: str):
        return []

    def get_family_lapse_risk_rows(self, family_id: str):
        return [{"horizon": "12m", "jurisdiction_code": "US", "office_support_level": "moderate"}]

    def get_family_jurisdiction_legal_rows(self, family_id: str, as_of_year: int | None = None):
        return [
            {
                "jurisdiction_code": "US",
                "branch_state_label": "ACTIVE_GRANT",
                "representative_branch_stage": "STANDARD_GRANT",
                "branch_coefficient_mode": "localized",
                "jurisdiction_enforceability_contribution_raw": 2.5,
                "jurisdiction_enforceability_share_of_family": 0.625,
                "jurisdiction_relative_enforceability_pct": 1.0,
                "jurisdiction_relative_enforceability_band": "dominant",
                "final_market_multiplier": 1.5,
                "last_event_date": "2024-06-01",
                "last_event_type": "GRANT",
            },
            {
                "jurisdiction_code": "EP",
                "branch_state_label": "PENDING_ONLY",
                "representative_branch_stage": "PENDING_APPLICATION",
                "branch_coefficient_mode": "global_fallback",
                "jurisdiction_enforceability_contribution_raw": 1.5,
                "jurisdiction_enforceability_share_of_family": 0.375,
                "jurisdiction_relative_enforceability_pct": 0.6,
                "jurisdiction_relative_enforceability_band": "strong",
                "final_market_multiplier": 1.0,
                "last_event_date": "2023-09-10",
                "last_event_type": "PENDING_APPLICATION",
            },
        ]

    def get_family_status_history(self, family_id: str):
        return [
            {
                "snapshot_year": 2023,
                "family_composite_status": "pending_emerging",
                "active_jurisdiction_count": 0,
                "active_grant_branch_count": 0,
                "lapsed_jurisdiction_count": 0,
                "opposed_branch_count": 0,
            },
            {
                "snapshot_year": 2024,
                "family_composite_status": "fully_active",
                "active_jurisdiction_count": 2,
                "active_grant_branch_count": 1,
                "lapsed_jurisdiction_count": 0,
                "opposed_branch_count": 0,
            },
        ]


class FakePublicationRepository:
    def get_title_for_application(self, appln_id: int):
        return {
            "title_text": "Adaptive communication system for secure signal routing",
            "language_code": "en",
        }


def build_service() -> FamilyService:
    return FamilyService(
        repository=FakeFamilyRepository(),
        publication_repository=FakePublicationRepository(),
    )


def test_family_service_overview_exposes_summary_cards_and_caveats() -> None:
    service = build_service()

    response = service.get_overview("123")

    assert response.identity.id == "123"
    assert len(response.summary_cards) == 4
    assert [card["label"] for card in response.summary_cards] == [
        "Blocking Power",
        "DOCDB family size",
        "Active Reach",
        "Heritage",
    ]
    assert response.summary_cards[0]["band_label"] == "Leading"
    assert response.summary_cards[3]["key"] == "heritage"
    assert response.summary_cards[3]["value"] == 83.0
    assert response.summary_cards[3]["peer_percentile"] == 83.0
    assert response.summary_cards[3]["peer_cohort_label"] == "2018 / Computer technology"
    legal_metrics = [metric for metric in response.overview_metrics if metric["group"] == "legal"]
    assert any(metric["label"] == "Raw legal enforceability proxy" and metric["value"] == 4.2 for metric in legal_metrics)
    identity_metrics = [metric for metric in response.overview_metrics if metric["group"] == "identity"]
    innovation_metrics = [metric for metric in response.overview_metrics if metric["group"] == "innovation"]
    assert any(
        metric["label"] == "Representative publication title"
        and metric["value"] == "Adaptive communication system for secure signal routing"
        for metric in identity_metrics
    )
    assert any(metric["label"] == "Earliest priority date" and metric["value"] == "2018-04-12" for metric in identity_metrics)
    assert any(metric["label"] == "Originality percentile" and metric["value"] == 71.0 for metric in innovation_metrics)
    assert any(metric["label"] == "Radicalness percentile" and metric["value"] == 63.0 for metric in innovation_metrics)
    assert any(metric["label"] == "Science grounding percentile" and metric["value"] == 58.0 for metric in innovation_metrics)
    caveat_codes = [c.code for c in response.meta.caveats]
    assert "current_owner_metadata_only" in caveat_codes
    assert response.meta.coverage is not None
    assert response.meta.coverage.pct == 0.94


def test_family_service_suggestions_return_serving_rows() -> None:
    service = build_service()

    response = service.get_family_suggestions("12", limit=5)

    assert response.query == "12"
    assert len(response.rows) == 1
    assert response.rows[0].family_id == "123"
    assert response.rows[0].owner_label == "Apple"
    assert response.rows[0].primary_field == "Computer technology"


def test_family_service_forecasts_section_is_gated_when_forecast_rows_are_missing() -> None:
    service = build_service()

    response = service.get_section("123", "forecasts")

    assert response.summary is not None
    assert response.summary["forecast_available"] is False
    assert response.summary["lapse_available"] is True
    caveat_codes = [c.code for c in response.meta.caveats]
    assert "forecast_unavailable" in caveat_codes


def test_family_service_members_section_has_pagination() -> None:
    service = build_service()

    response = service.get_section("123", "members", limit=10, offset=0)

    assert response.meta.pagination is not None
    assert response.meta.pagination.returned_count == 1
    assert response.meta.pagination.total_count == 1


def test_family_service_legal_section_exposes_jurisdiction_rows_and_status_history() -> None:
    service = build_service()

    response = service.get_section("123", "legal")

    assert response.summary is not None
    assert response.summary["jurisdiction_footprint_count"] == 2
    assert response.summary["last_event_type"] == "GRANT"
    assert len(response.rows) == 2
    assert response.rows[0]["jurisdiction_code"] == "US"
    assert response.rows[0]["jurisdiction_relative_enforceability_band"] == "dominant"
    assert response.rows[0]["branch_coefficient_mode"] == "localized"
    status_history_rows = [row for row in response.series if row.get("series_kind") == "status_history"]
    assert len(status_history_rows) == 2
    caveat_codes = [c.code for c in response.meta.caveats]
    assert "jurisdiction_legal_contribution" in caveat_codes


def test_family_service_citations_section_hides_raw_intermediates() -> None:
    service = build_service()

    response = service.get_section("123", "citations")

    assert response.summary is not None
    assert response.summary["forward_citations_clean"] == 8
    assert response.summary["forward_citing_owner_count"] == 5
    assert response.summary["forward_citations_7y"] == 7
    assert response.summary["backward_citations_clean"] == 3
    assert response.summary["backward_cited_owner_count"] == 2
    assert response.summary["backward_npl_citation_count"] == 2
    assert "family_adjusted_citation_score_raw" not in response.summary
    assert "family_rcf_score" not in response.summary
    assert "forward_citation_event_count" not in response.summary
    assert "forward_clean_citation_event_count" not in response.summary
    assert "forward_citations_weighted" not in response.summary
    assert "backward_citation_event_count" not in response.summary
    assert "science_grounding_score" not in response.summary
    assert response.rows[0]["pre_asof_forward_citation_event_count"] == 12
    assert response.rows[0]["forward_citation_event_count_year"] == 3
    assert response.rows[0]["pre_asof_forward_citations_weighted"] == 16.5
    assert response.rows[0]["pre_asof_unique_citing_owner_count"] == 5
    assert response.rows[0]["pre_asof_distinct_cited_family_count"] == 3
    assert response.rows[0]["first_forward_citation_date_asof"] == "2021-02-18"
    assert response.rows[0]["window_5y_closed"] is True
    assert response.rows[0]["chronology_support_level"] == "high"
    assert "method_version" not in response.rows[0]
    series_kinds = [row["series_kind"] for row in response.series]
    assert "top_cited_member" in series_kinds
    assert "top_citing_owner" in series_kinds
    assert "citing_family" in series_kinds
    top_member = next(row for row in response.series if row["series_kind"] == "top_cited_member")
    top_owner = next(row for row in response.series if row["series_kind"] == "top_citing_owner")
    citing_family_row = next(row for row in response.series if row["series_kind"] == "citing_family")
    assert top_member["publication_number_full"] == "US123A"
    assert top_member["clean_citation_event_count"] == 5
    assert top_owner["citing_owner_name"] == "Samsung"
    assert top_owner["cited_member_count"] == 1
    assert top_owner["citation_lethality_sum"] == 5.6
    assert citing_family_row["distinct_cited_member_count"] == 2
    assert citing_family_row["distinct_citing_publication_count"] == 2
    assert response.meta.pagination is not None
    assert response.meta.pagination.limit == 10
    assert response.meta.pagination.total_count == 1
    assert response.meta.pagination.returned_count == 1
    caveat_codes = [c.code for c in response.meta.caveats]
    assert "citation_summary_curated_proxy" in caveat_codes
    assert "citing_family_list_clean_grain" in caveat_codes
    assert "citation_owner_ranking_excludes_unknown" in caveat_codes


def test_family_service_citations_section_forwards_owner_filter_to_citing_family_list() -> None:
    repository = FakeFamilyRepository()
    service = FamilyService(
        repository=repository,
        publication_repository=FakePublicationRepository(),
    )

    response = service.get_section("123", "citations", owner_filter="Samsung")

    assert response.meta.pagination is not None
    assert repository.last_citing_families_owner_filter == "Samsung"


def test_family_service_timeseries_section_exposes_only_trajectory_series() -> None:
    service = build_service()

    response = service.get_section("123", "timeseries")

    assert response.summary is not None
    assert response.summary["blocking_history_points"] == 1
    assert response.summary["field_history_rows"] == 1
    assert response.rows == []
    assert len(response.series) == 2
    series_kinds = {row["series_kind"] for row in response.series}
    assert series_kinds == {"blocking_history", "field_history"}
    field_history_row = next(row for row in response.series if row["series_kind"] == "field_history")
    assert field_history_row["field_share_asof"] == 0.72
    assert field_history_row["field_share_method"] == "appln_weighted_field_share"
