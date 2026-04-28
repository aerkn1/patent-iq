from __future__ import annotations

from pathlib import Path
from typing import Any

import duckdb

from config.settings import get_settings
from infrastructure.artifacts import ArtifactLocator
from infrastructure.duckdb import DuckDbProvider


class FamilyRepository:
    def __init__(self) -> None:
        settings = get_settings()
        self.settings = settings
        self.summary_path = settings.etl_data_root / "gold" / "gold_family_summary.parquet"
        self.blocking_power_path = settings.etl_data_root / "gold" / "gold_family_blocking_power.parquet"
        self.blocking_timeseries_path = settings.etl_data_root / "gold" / "gold_family_blocking_power_timeseries.parquet"
        self.field_contributions_path = settings.etl_data_root / "gold" / "gold_family_field_contributions.parquet"
        self.field_contributions_timeseries_path = settings.etl_data_root / "gold" / "gold_family_field_contributions_timeseries.parquet"
        self.heritage_summary_path = settings.etl_data_root / "gold" / "gold_family_heritage_summary.parquet"
        self.citation_chronology_path = settings.etl_data_root / "gold" / "gold_family_citation_chronology.parquet"
        self.compare_pit_path = settings.etl_data_root / "gold" / "gold_family_compare_pit.parquet"
        self.classification_mix_path = settings.etl_data_root / "gold" / "gold_family_classification_mix_pit.parquet"
        self.member_publications_path = settings.etl_data_root / "silver" / "silver_family_member_publications.parquet"
        self.owner_bridge_path = settings.etl_data_root / "silver" / "silver_family_owner_bridge.parquet"
        self.citation_metrics_path = settings.etl_data_root / "silver" / "silver_family_citation_metrics.parquet"
        self.oecd_quality_path = settings.etl_data_root / "silver" / "silver_family_oecd_quality.parquet"
        self.feature_snapshot_path = settings.etl_data_root / "silver" / "silver_family_feature_snapshot_pit.parquet"
        self.enriched_citation_network_path = settings.etl_data_root / "silver" / "silver_enriched_citation_network.parquet"
        self.enforceability_branches_path = settings.etl_data_root / "silver" / "silver_family_enforceability_branches.parquet"
        self.status_history_path = settings.etl_data_root / "silver" / "silver_family_status_history.parquet"
        self.branch_status_history_dense_path = settings.etl_data_root / "silver" / "silver_branch_status_history_dense.parquet"
        self.legal_event_ledger_path = settings.etl_data_root / "silver" / "silver_legal_status_event_ledger.parquet"
        self.forecast_path = settings.etl_data_root / "ml" / "ml_prediction_family_future_citations.parquet"
        self.lapse_risk_path = settings.etl_data_root / "ml" / "ml_prediction_family_jurisdiction_lapse_risk.parquet"
        self.artifact_locator = ArtifactLocator(settings=settings)
        self.duckdb_provider = DuckDbProvider()
        self._column_cache: dict[Path, list[str]] = {}
        self._analytics_path_map: dict[Path, str] = {
            self.summary_path: "family_summary",
            self.blocking_power_path: "family_blocking_power",
            self.heritage_summary_path: "family_heritage_summary",
            self.blocking_timeseries_path: "family_blocking_power_timeseries",
            self.field_contributions_path: "family_field_contributions",
            self.field_contributions_timeseries_path: "family_field_contributions_timeseries",
            self.citation_chronology_path: "family_citation_chronology",
            self.compare_pit_path: "family_compare_pit",
            self.classification_mix_path: "family_classification_mix_pit",
            self.member_publications_path: "family_member_publications",
            self.owner_bridge_path: "family_owner_bridge",
            self.citation_metrics_path: "family_citation_metrics",
            self.oecd_quality_path: "family_oecd_quality",
            self.feature_snapshot_path: "family_feature_snapshot_pit",
            self.enriched_citation_network_path: "enriched_citation_network",
            self.enforceability_branches_path: "family_enforceability_branches",
            self.status_history_path: "family_status_history",
            self.branch_status_history_dense_path: "branch_status_history_dense",
            self.legal_event_ledger_path: "legal_status_event_ledger",
            self.forecast_path: "family_forecast_predictions",
            self.lapse_risk_path: "family_lapse_risk_predictions",
        }

    def artifacts(self) -> list[Path]:
        core_serving_path = self.artifact_locator.resolve_core_serving_duckdb()
        analytics_serving_path = self.artifact_locator.resolve_analytics_serving_duckdb()
        serving_artifacts: list[Path] = []
        if core_serving_path is not None:
            serving_artifacts.append(core_serving_path)
        if analytics_serving_path is not None:
            serving_artifacts.append(analytics_serving_path)
        if serving_artifacts:
            return serving_artifacts
        artifacts = [
            self.summary_path,
            self.blocking_power_path,
            self.blocking_timeseries_path,
            self.field_contributions_path,
            self.field_contributions_timeseries_path,
            self.citation_chronology_path,
            self.heritage_summary_path,
            self.compare_pit_path,
            self.classification_mix_path,
            self.member_publications_path,
            self.owner_bridge_path,
            self.citation_metrics_path,
            self.oecd_quality_path,
            self.feature_snapshot_path,
            self.enriched_citation_network_path,
            self.enforceability_branches_path,
            self.status_history_path,
            self.branch_status_history_dense_path,
            self.legal_event_ledger_path,
            self.forecast_path,
            self.lapse_risk_path,
        ]
        if analytics_serving_path is not None:
            artifacts.insert(0, analytics_serving_path)
        return artifacts

    def _to_dict(self, columns: list[str], row: Any) -> dict[str, object]:
        if row is None:
            return {}
        return dict(zip(columns, row, strict=False))

    def _normalize_family_id(self, family_id: str | int | None) -> int | None:
        if family_id is None:
            return None
        try:
            return int(str(family_id).strip())
        except (TypeError, ValueError):
            return None

    def _attach_core_serving(self, con: duckdb.DuckDBPyConnection, core_serving_path: Path) -> None:
        attached = con.execute("pragma database_list").fetchall()
        if any(str(row[1]) == "core_db" for row in attached):
            return
        con.execute(f"ATTACH '{core_serving_path}' AS core_db (READ_ONLY)")

    def _core_table_exists(self, con: duckdb.DuckDBPyConnection, table_name: str) -> bool:
        row = con.execute(
            """
            select 1
            from information_schema.tables
            where table_catalog = 'core_db'
              and table_schema = 'main'
              and table_name = ?
            limit 1
            """,
            [table_name],
        ).fetchone()
        return row is not None

    def _attach_analytics_serving(self, con: duckdb.DuckDBPyConnection, analytics_serving_path: Path) -> None:
        attached = con.execute("pragma database_list").fetchall()
        if any(str(row[1]) == "analytics_db" for row in attached):
            return
        con.execute(f"ATTACH '{analytics_serving_path}' AS analytics_db (READ_ONLY)")

    def _analytics_table_exists(self, con: duckdb.DuckDBPyConnection, table_name: str) -> bool:
        row = con.execute(
            """
            select 1
            from information_schema.tables
            where table_catalog = 'analytics_db'
              and table_schema = 'main'
              and table_name = ?
            limit 1
            """,
            [table_name],
        ).fetchone()
        return row is not None

    def _analytics_relation(self, con: duckdb.DuckDBPyConnection, path: Path) -> str:
        table_name = self._analytics_path_map.get(path)
        analytics_serving_path = self.artifact_locator.resolve_analytics_serving_duckdb()
        if table_name and analytics_serving_path is not None and analytics_serving_path.exists():
            self._attach_analytics_serving(con, analytics_serving_path)
            if self._analytics_table_exists(con, table_name):
                return f"analytics_db.{table_name}"
        if table_name and not self.settings.raw_parquet_fallback_enabled:
            raise RuntimeError(
                f"Analytics serving table '{table_name}' is required for '{path.name}' because raw parquet fallback is disabled."
            )
        return f"read_parquet('{path}')"

    def _columns(self, path: Path) -> list[str]:
        table_name = self._analytics_path_map.get(path)
        analytics_serving_path = self.artifact_locator.resolve_analytics_serving_duckdb()
        if not path.exists() and (analytics_serving_path is None or table_name is None):
            return []
        cached = self._column_cache.get(path)
        if cached is not None:
            return cached
        with self.duckdb_provider.connect() as con:
            relation = self._analytics_relation(con, path)
            rows = con.execute(f"describe select * from {relation}").fetchall()
        columns = [row[0] for row in rows]
        self._column_cache[path] = columns
        return columns

    def _latest_year(
        self,
        con: duckdb.DuckDBPyConnection,
        path: Path,
        family_id: int,
        column_name: str,
    ) -> int | None:
        relation = self._analytics_relation(con, path)
        row = con.execute(
            f"select max({column_name}) from {relation} where docdb_family_id = ?",
            [family_id],
        ).fetchone()
        if row is None or row[0] is None:
            return None
        return int(row[0])

    def _latest_rows_by_year(
        self,
        con: duckdb.DuckDBPyConnection,
        path: Path,
        family_id: int,
        year_column: str,
        order_clause: str,
        as_of_year: int | None = None,
    ) -> list[dict[str, object]]:
        target_year = as_of_year if as_of_year is not None else self._latest_year(con, path, family_id, year_column)
        if target_year is None:
            return []
        relation = self._analytics_relation(con, path)
        cursor = con.execute(
            f"""
            select *
            from {relation}
            where docdb_family_id = ?
              and {year_column} = ?
            order by {order_clause}
            """,
            [family_id, target_year],
        )
        columns = [col[0] for col in cursor.description]
        return [self._to_dict(columns, row) for row in cursor.fetchall()]

    def _query_single_row(
        self,
        con: duckdb.DuckDBPyConnection,
        query: str,
        parameters: list[object] | tuple[object, ...],
    ) -> dict[str, object]:
        cursor = con.execute(query, parameters)
        row = cursor.fetchone()
        if row is None:
            return {}
        columns = [col[0] for col in cursor.description]
        return self._to_dict(columns, row)

    def _query_rows(
        self,
        con: duckdb.DuckDBPyConnection,
        query: str,
        parameters: list[object] | tuple[object, ...],
    ) -> list[dict[str, object]]:
        cursor = con.execute(query, parameters)
        columns = [col[0] for col in cursor.description]
        return [self._to_dict(columns, row) for row in cursor.fetchall()]

    def get_family_heritage_percentile(self, family_id: str | int) -> float | None:
        normalized_family_id = self._normalize_family_id(family_id)
        if normalized_family_id is None:
            return None

        core_serving_path = self.artifact_locator.resolve_core_serving_duckdb()
        if core_serving_path is not None:
            with self.duckdb_provider.connect() as con:
                self._attach_core_serving(con, core_serving_path)
                if self._core_table_exists(con, "family_compare_current_serving"):
                    row = con.execute(
                        """
                        select citation_heritage_percentile
                        from core_db.family_compare_current_serving
                        where docdb_family_id = ?
                        limit 1
                        """,
                        [normalized_family_id],
                    ).fetchone()
                    if row is not None and row[0] is not None:
                        return float(row[0])

        percentile_sql = """
            with heritage_ranked as (
                select
                    s.docdb_family_id,
                    100.0 * percent_rank() over (
                        partition by
                            coalesce(s.primary_wipo_field, 'unknown'),
                            coalesce(s.family_priority_year, -1)
                        order by coalesce(h.family_heritage_score, 0.0)
                    ) as citation_heritage_percentile
                from {summary_ref} s
                left join {heritage_ref} h using (docdb_family_id)
            )
            select citation_heritage_percentile
            from heritage_ranked
            where docdb_family_id = ?
            limit 1
        """

        if core_serving_path is not None:
            with self.duckdb_provider.connect() as con:
                self._attach_core_serving(con, core_serving_path)
                if self._core_table_exists(con, "family_summary") and self._core_table_exists(con, "family_heritage_summary"):
                    row = con.execute(
                        percentile_sql.format(
                            summary_ref="core_db.family_summary",
                            heritage_ref="core_db.family_heritage_summary",
                        ),
                        [normalized_family_id],
                    ).fetchone()
                    if row is not None and row[0] is not None:
                        return float(row[0])

        if not self.settings.raw_parquet_fallback_enabled:
            return None

        with self.duckdb_provider.connect() as con:
            summary_ref = self._analytics_relation(con, self.summary_path)
            heritage_ref = self._analytics_relation(con, self.heritage_summary_path)
            row = con.execute(
                percentile_sql.format(
                    summary_ref=summary_ref,
                    heritage_ref=heritage_ref,
                ),
                [normalized_family_id],
            ).fetchone()
        if row is None or row[0] is None:
            return None
        return float(row[0])

    def get_family_overview_context(self, family_id: str | int) -> dict[str, object]:
        normalized_family_id = self._normalize_family_id(family_id)
        if normalized_family_id is None:
            return {}

        core_serving_path = self.artifact_locator.resolve_core_serving_duckdb()
        base_context: dict[str, object] = {}
        if core_serving_path is not None:
            with self.duckdb_provider.connect() as con:
                self._attach_core_serving(con, core_serving_path)
                citation_metrics_ref = self._analytics_relation(con, self.citation_metrics_path)
                oecd_quality_ref = self._analytics_relation(con, self.oecd_quality_path)
                if all(
                    self._core_table_exists(con, table_name)
                    for table_name in [
                        "family_summary",
                        "family_blocking_power",
                        "family_heritage_summary",
                        "family_compare_current_serving",
                    ]
                ):
                    base_context = self._query_single_row(
                        con,
                        f"""
                        select
                            s.*,
                            b.family_market_threat_score_raw,
                            b.family_adjusted_citation_score_raw,
                            b.family_overall_legal_enforceability_score,
                            b.family_raw_absolute_blocking_power,
                            b.family_ui_blocking_power_score,
                            h.family_heritage_score,
                            h.raw_family_citation_count,
                            h.out_of_bounds_citation_share,
                            c.primary_wipo_field_current,
                            c.family_composite_status_asof,
                            c.family_enforceability_score_asof,
                            c.family_active_jurisdiction_share_asof,
                            c.family_jurisdiction_count_asof,
                            c.pre_asof_forward_citations_weighted,
                            c.data_completeness_pct_asof,
                            c.historical_compare_safe,
                            c.historical_oecd_supported,
                            c.current_owner_metadata_only,
                            cm.family_science_grounding_score,
                            oq.family_science_grounding_percentile
                        from core_db.family_summary s
                        left join core_db.family_blocking_power b using (docdb_family_id)
                        left join core_db.family_heritage_summary h using (docdb_family_id)
                        left join core_db.family_compare_current_serving c using (docdb_family_id)
                        left join {citation_metrics_ref} cm using (docdb_family_id)
                        left join {oecd_quality_ref} oq using (docdb_family_id)
                        where s.docdb_family_id = ?
                        limit 1
                        """,
                        [normalized_family_id],
                    )

        if not base_context and self.settings.raw_parquet_fallback_enabled:
            with self.duckdb_provider.connect() as con:
                compare_ref = self._analytics_relation(con, self.compare_pit_path)
                summary_ref = self._analytics_relation(con, self.summary_path)
                blocking_ref = self._analytics_relation(con, self.blocking_power_path)
                heritage_ref = self._analytics_relation(con, self.heritage_summary_path)
                citation_metrics_ref = self._analytics_relation(con, self.citation_metrics_path)
                oecd_quality_ref = self._analytics_relation(con, self.oecd_quality_path)
                base_context = self._query_single_row(
                    con,
                    f"""
                    with latest_compare as (
                        select *
                        from {compare_ref}
                        where docdb_family_id = ?
                          and is_latest_observed_year
                    )
                    select
                        s.*,
                        b.family_market_threat_score_raw,
                        b.family_adjusted_citation_score_raw,
                        b.family_overall_legal_enforceability_score,
                        b.family_raw_absolute_blocking_power,
                        b.family_ui_blocking_power_score,
                        h.family_heritage_score,
                        h.raw_family_citation_count,
                        h.out_of_bounds_citation_share,
                        c.primary_wipo_field_current,
                        c.family_composite_status_asof,
                        c.family_enforceability_score_asof,
                        c.family_active_jurisdiction_share_asof,
                        c.family_jurisdiction_count_asof,
                        c.pre_asof_forward_citations_weighted,
                        c.data_completeness_pct_asof,
                        c.historical_compare_safe,
                        c.historical_oecd_supported,
                        c.current_owner_metadata_only,
                        cm.family_science_grounding_score,
                        oq.family_science_grounding_percentile
                    from {summary_ref} s
                    left join {blocking_ref} b using (docdb_family_id)
                    left join {heritage_ref} h using (docdb_family_id)
                    left join latest_compare c using (docdb_family_id)
                    left join {citation_metrics_ref} cm using (docdb_family_id)
                    left join {oecd_quality_ref} oq using (docdb_family_id)
                    where s.docdb_family_id = ?
                    limit 1
                    """,
                    [normalized_family_id, normalized_family_id],
                )

        if not base_context and self.settings.raw_parquet_fallback_enabled:
            with self.duckdb_provider.connect() as con:
                blocking_ref = self._analytics_relation(con, self.blocking_power_path)
                blocking_overlay = self._query_single_row(
                    con,
                    f"""
                    select
                        family_market_threat_score_raw,
                        family_adjusted_citation_score_raw,
                        family_overall_legal_enforceability_score,
                        family_raw_absolute_blocking_power,
                        family_ui_blocking_power_score
                    from {blocking_ref}
                    where docdb_family_id = ?
                    limit 1
                    """,
                    [normalized_family_id],
                )
            if blocking_overlay:
                base_context.update(blocking_overlay)

        compare_context = self.get_family_compare_context(normalized_family_id)
        if compare_context:
            for key, value in compare_context.items():
                if key not in base_context or base_context.get(key) is None:
                    base_context[key] = value
        return base_context

    def get_family_field_rows(self, family_id: str | int, as_of_year: int | None = None) -> list[dict[str, object]]:
        normalized_family_id = self._normalize_family_id(family_id)
        if normalized_family_id is None:
            return []
        field_columns = set(self._columns(self.field_contributions_path))
        order_clause = (
            "coalesce(field_share_asof, base_fraction) desc, heritage_contribution_score desc, enforceability_contribution_score desc"
            if "field_share_asof" in field_columns
            else "base_fraction desc, heritage_contribution_score desc, enforceability_contribution_score desc"
        )
        with self.duckdb_provider.connect() as con:
            return self._latest_rows_by_year(
                con,
                self.field_contributions_path,
                normalized_family_id,
                "snapshot_year",
                order_clause,
                as_of_year=as_of_year,
            )

    def get_family_field_timeseries(self, family_id: str | int) -> list[dict[str, object]]:
        normalized_family_id = self._normalize_family_id(family_id)
        if normalized_family_id is None:
            return []
        field_columns = set(self._columns(self.field_contributions_timeseries_path))
        optional_numeric_fields = [
            "field_share_asof",
            "field_evidence_weight_asof",
            "field_application_count_asof",
            "family_application_count_asof",
        ]
        select_fields = [
            "snapshot_year",
            "wipo_industry_code",
            "max(snapshot_date) as snapshot_date",
            "avg(base_fraction) as base_fraction",
        ]
        for field_name in optional_numeric_fields:
            if field_name in field_columns:
                select_fields.append(f"avg({field_name}) as {field_name}")
        if "field_share_method" in field_columns:
            select_fields.append("max(field_share_method) as field_share_method")
        select_fields.extend(
            [
                "avg(enforceability_contribution_score) as enforceability_contribution_score",
                "avg(heritage_contribution_score) as heritage_contribution_score",
                "avg(active_market_weight) as active_market_weight",
                "max(max_active_stage) as max_active_stage",
                "bool_or(is_active_on_snapshot) as is_active_on_snapshot",
            ]
        )
        order_clause = (
            "coalesce(field_share_asof, base_fraction) desc, wipo_industry_code asc"
            if "field_share_asof" in field_columns
            else "base_fraction desc, wipo_industry_code asc"
        )
        with self.duckdb_provider.connect() as con:
            field_ref = self._analytics_relation(con, self.field_contributions_timeseries_path)
            return self._query_rows(
                con,
                f"""
                with aggregated as (
                    select
                        {", ".join(select_fields)}
                    from {field_ref}
                    where docdb_family_id = ?
                    group by 1, 2
                )
                select *
                from aggregated
                order by snapshot_year asc, {order_clause}
                """,
                [normalized_family_id],
            )

    def get_family_blocking_timeseries(self, family_id: str | int) -> list[dict[str, object]]:
        normalized_family_id = self._normalize_family_id(family_id)
        if normalized_family_id is None:
            return []
        blocking_columns = set(self._columns(self.blocking_timeseries_path))
        select_fields = [
            "extract(year from snapshot_date) as snapshot_year",
            "snapshot_date",
            "ui_blocking_power_score",
            "overall_legal_enforceability_score",
            "adjusted_citation_score_raw",
        ]
        if "blocking_citation_score_raw" in blocking_columns:
            select_fields.append("blocking_citation_score_raw")
        with self.duckdb_provider.connect() as con:
            blocking_ref = self._analytics_relation(con, self.blocking_timeseries_path)
            return self._query_rows(
                con,
                f"""
                select
                    {", ".join(select_fields)}
                from {blocking_ref}
                where docdb_family_id = ?
                order by snapshot_date asc
                """,
                [normalized_family_id],
            )

    def get_family_member_publications(
        self,
        family_id: str | int,
        limit: int = 10,
        offset: int = 0,
    ) -> tuple[list[dict[str, object]], int]:
        normalized_family_id = self._normalize_family_id(family_id)
        if normalized_family_id is None:
            return [], 0
        safe_limit = max(1, min(int(limit), 1000))
        safe_offset = max(0, int(offset))
        with self.duckdb_provider.connect() as con:
            member_ref = self._analytics_relation(con, self.member_publications_path)
            total_row = con.execute(
                f"select count(*) from {member_ref} where docdb_family_id = ?",
                [normalized_family_id],
            ).fetchone()
            total_count = int(total_row[0]) if total_row is not None else 0
            rows = self._query_rows(
                con,
                f"""
                select *
                from {member_ref}
                where docdb_family_id = ?
                order by publn_date desc nulls last, publication_number_full asc
                limit ? offset ?
                """,
                [normalized_family_id, safe_limit, safe_offset],
            )
        return rows, total_count

    def get_family_member_publication_summary(self, family_id: str | int) -> dict[str, object]:
        normalized_family_id = self._normalize_family_id(family_id)
        if normalized_family_id is None:
            return {}
        with self.duckdb_provider.connect() as con:
            member_ref = self._analytics_relation(con, self.member_publications_path)
            return self._query_single_row(
                con,
                f"""
                select
                    count(*) as publication_count,
                    sum(case when is_application_stage then 1 else 0 end) as application_stage_count,
                    sum(case when is_grant_stage then 1 else 0 end) as grant_stage_count,
                    sum(case when is_modifier_stage then 1 else 0 end) as modifier_stage_count,
                    count(distinct publn_auth) as office_count
                from {member_ref}
                where docdb_family_id = ?
                """,
                [normalized_family_id],
            )

    def get_family_citation_metrics(self, family_id: str | int) -> dict[str, object]:
        normalized_family_id = self._normalize_family_id(family_id)
        if normalized_family_id is None:
            return {}
        with self.duckdb_provider.connect() as con:
            citation_metrics_ref = self._analytics_relation(con, self.citation_metrics_path)
            return self._query_single_row(
                con,
                f"""
                select *
                from {citation_metrics_ref}
                where docdb_family_id = ?
                limit 1
                """,
                [normalized_family_id],
            )

    def get_family_citation_event_summary(self, family_id: str | int) -> dict[str, object]:
        normalized_family_id = self._normalize_family_id(family_id)
        if normalized_family_id is None:
            return {}
        with self.duckdb_provider.connect() as con:
            citation_network_ref = self._analytics_relation(con, self.enriched_citation_network_path)
            owner_bridge_ref = self._analytics_relation(con, self.owner_bridge_path)
            return self._query_single_row(
                con,
                f"""
                with scoped_network as (
                    select *
                    from {citation_network_ref}
                    where source_docdb_family_id = ?
                       or cited_docdb_family_id = ?
                ),
                primary_owner_bridge as (
                    select distinct
                        docdb_family_id,
                        owner_name_harmonized
                    from {owner_bridge_ref}
                    where coalesce(is_primary_owner, false)
                )
                select
                    cast(
                        coalesce(
                            count(
                                distinct case
                                    when n.cited_docdb_family_id = ?
                                     and not coalesce(is_out_of_bounds, false)
                                     and not coalesce(is_intra_family_citation, false)
                                     and not coalesce(is_self_citation, false)
                                     and trim(upper(coalesce(citing_assignee_name, ''))) not in ('', '_', 'UNKNOWN', 'UNKNOWN_OWNER', 'UNASSIGNED')
                                    then trim(cast(citing_assignee_name as varchar))
                                end
                            ),
                            0
                        ) as bigint
                    ) as forward_citing_owner_count,
                    cast(
                        coalesce(
                            count(
                                distinct case
                                    when n.source_docdb_family_id = ?
                                     and not coalesce(n.is_out_of_bounds, false)
                                     and not coalesce(n.is_intra_family_citation, false)
                                     and not coalesce(n.is_self_citation, false)
                                     and trim(upper(coalesce(ob.owner_name_harmonized, ''))) not in ('', '_', 'UNKNOWN', 'UNKNOWN_OWNER', 'UNASSIGNED')
                                    then trim(cast(ob.owner_name_harmonized as varchar))
                                end
                            ),
                            0
                        ) as bigint
                    ) as backward_cited_owner_count
                from scoped_network n
                left join primary_owner_bridge ob
                  on n.cited_docdb_family_id = ob.docdb_family_id
                """,
                [
                    normalized_family_id,
                    normalized_family_id,
                    normalized_family_id,
                    normalized_family_id,
                ],
            )

    def get_family_feature_timeseries(self, family_id: str | int) -> list[dict[str, object]]:
        normalized_family_id = self._normalize_family_id(family_id)
        if normalized_family_id is None:
            return []
        with self.duckdb_provider.connect() as con:
            feature_ref = self._analytics_relation(con, self.feature_snapshot_path)
            return self._query_rows(
                con,
                f"""
                select *
                from {feature_ref}
                where docdb_family_id = ?
                order by as_of_year asc
                """,
                [normalized_family_id],
            )

    def get_family_citation_chronology(self, family_id: str | int) -> list[dict[str, object]]:
        normalized_family_id = self._normalize_family_id(family_id)
        if normalized_family_id is None:
            return []
        with self.duckdb_provider.connect() as con:
            chronology_ref = self._analytics_relation(con, self.citation_chronology_path)
            feature_ref = self._analytics_relation(con, self.feature_snapshot_path)
            citation_network_ref = self._analytics_relation(con, self.enriched_citation_network_path)
            if self.citation_chronology_path.exists() or chronology_ref.startswith("analytics_db."):
                return self._query_rows(
                    con,
                    f"""
                    select *
                    from {chronology_ref}
                    where docdb_family_id = ?
                    order by as_of_year asc
                    """,
                    [normalized_family_id],
                )
            return self._query_rows(
                con,
                f"""
                with anchors as (
                    select
                        cast(as_of_year as integer) as as_of_year,
                        cast(as_of_date as date) as as_of_date,
                        coalesce(is_observed_as_of_snapshot, false) as is_observed_as_of_snapshot,
                        cast(coalesce(pre_asof_forward_citations_weighted, 0.0) as double) as pre_asof_forward_citations_weighted,
                        cast(coalesce(pre_asof_unique_citing_family_count, 0.0) as double) as pre_asof_unique_citing_family_count,
                        cast(coalesce(pre_asof_citing_assignee_diversity, 0.0) as double) as pre_asof_citing_assignee_diversity,
                        cast(coalesce(pre_asof_attacker_density_score, 0.0) as double) as pre_asof_attacker_density_score,
                        cast(coalesce(data_completeness_pct_asof, 0.0) as double) as data_completeness_pct_asof
                    from {feature_ref}
                    where docdb_family_id = ?
                    order by as_of_year asc
                ),
                forward_events as (
                    select
                        a.as_of_year,
                        cast(
                            coalesce(
                                count(*) filter (
                                    where cast(n.citation_date as date) <= a.as_of_date
                                ),
                                0
                            ) as bigint
                        ) as pre_asof_forward_citation_event_count,
                        cast(
                            coalesce(
                                count(*) filter (
                                    where cast(n.citation_date as date) <= a.as_of_date
                                      and not coalesce(n.is_out_of_bounds, false)
                                      and not coalesce(n.is_intra_family_citation, false)
                                      and not coalesce(n.is_self_citation, false)
                                ),
                                0
                            ) as bigint
                        ) as pre_asof_forward_clean_citation_event_count
                    from anchors a
                    left join {citation_network_ref} n
                      on n.cited_docdb_family_id = ?
                     and n.citation_date is not null
                    group by a.as_of_year, a.as_of_date
                ),
                backward_events as (
                    select
                        a.as_of_year,
                        cast(
                            coalesce(
                                count(*) filter (
                                    where cast(n.citation_date as date) <= a.as_of_date
                                ),
                                0
                            ) as bigint
                        ) as pre_asof_backward_citation_event_count,
                        cast(
                            coalesce(
                                count(*) filter (
                                    where cast(n.citation_date as date) <= a.as_of_date
                                      and not coalesce(n.is_out_of_bounds, false)
                                      and not coalesce(n.is_intra_family_citation, false)
                                      and not coalesce(n.is_self_citation, false)
                                ),
                                0
                            ) as bigint
                        ) as pre_asof_backward_clean_citation_event_count,
                        cast(
                            coalesce(
                                count(
                                    distinct case
                                        when cast(n.citation_date as date) <= a.as_of_date
                                         and n.cited_docdb_family_id is not null
                                         and not coalesce(n.is_out_of_bounds, false)
                                         and not coalesce(n.is_intra_family_citation, false)
                                         and not coalesce(n.is_self_citation, false)
                                        then n.cited_docdb_family_id
                                    end
                                ),
                                0
                            ) as bigint
                        ) as pre_asof_distinct_cited_family_count
                    from anchors a
                    left join {citation_network_ref} n
                      on n.source_docdb_family_id = ?
                     and n.citation_date is not null
                    group by a.as_of_year, a.as_of_date
                )
                select
                    a.as_of_year,
                    a.as_of_date,
                    a.is_observed_as_of_snapshot,
                    f.pre_asof_forward_citation_event_count,
                    f.pre_asof_forward_clean_citation_event_count,
                    a.pre_asof_forward_citations_weighted,
                    a.pre_asof_unique_citing_family_count,
                    b.pre_asof_backward_citation_event_count,
                    b.pre_asof_backward_clean_citation_event_count,
                    b.pre_asof_distinct_cited_family_count,
                    a.pre_asof_citing_assignee_diversity,
                    a.pre_asof_attacker_density_score,
                    a.data_completeness_pct_asof
                from anchors a
                left join forward_events f using (as_of_year)
                left join backward_events b using (as_of_year)
                order by a.as_of_year asc
                """,
                [normalized_family_id, normalized_family_id, normalized_family_id],
            )

    def get_family_citing_families(
        self,
        family_id: str | int,
        limit: int = 50,
        offset: int = 0,
        owner_filter: str | None = None,
    ) -> tuple[list[dict[str, object]], int]:
        normalized_family_id = self._normalize_family_id(family_id)
        if normalized_family_id is None:
            return [], 0
        safe_limit = max(1, min(int(limit), 1000))
        safe_offset = max(0, int(offset))
        normalized_owner_filter = str(owner_filter).strip() if owner_filter is not None else ""
        owner_filter_like = f"%{normalized_owner_filter.upper()}%" if normalized_owner_filter else None
        with self.duckdb_provider.connect() as con:
            member_ref = self._analytics_relation(con, self.member_publications_path)
            citation_network_ref = self._analytics_relation(con, self.enriched_citation_network_path)
            rows = self._query_rows(
                con,
                f"""
                with focal_publications as (
                    select
                        cast(pat_publn_id as bigint) as cited_pat_publn_id,
                        publication_number_full
                    from {member_ref}
                    where docdb_family_id = ?
                ),
                base as (
                    select
                        cast(n.source_docdb_family_id as bigint) as citing_docdb_family_id,
                        max_by(
                            coalesce(n.citing_assignee_name, 'UNKNOWN_OWNER'),
                            cast(n.citation_date as date)
                        ) as citing_assignee_name,
                        cast(coalesce(count(distinct fp.publication_number_full), 0) as bigint) as distinct_cited_member_count,
                        cast(coalesce(count(distinct n.citing_pat_publn_id), 0) as bigint) as distinct_citing_publication_count,
                        min(cast(n.citation_date as date)) as first_citation_date,
                        max(cast(n.citation_date as date)) as latest_citation_date
                    from {citation_network_ref} n
                    join focal_publications fp
                      on n.cited_pat_publn_id = fp.cited_pat_publn_id
                    where n.cited_docdb_family_id = ?
                      and n.source_docdb_family_id is not null
                      and not coalesce(n.is_out_of_bounds, false)
                      and not coalesce(n.is_intra_family_citation, false)
                      and not coalesce(n.is_self_citation, false)
                    group by
                        n.source_docdb_family_id
                ),
                filtered as (
                    select *
                    from base
                    where ? is null
                       or upper(coalesce(citing_assignee_name, '')) like ?
                )
                select
                    *,
                    count(*) over () as total_count
                from filtered
                order by
                    distinct_cited_member_count desc,
                    distinct_citing_publication_count desc,
                    latest_citation_date desc nulls last,
                    citing_docdb_family_id asc
                limit ?
                offset ?
                """,
                [normalized_family_id, normalized_family_id, owner_filter_like, owner_filter_like, safe_limit, safe_offset],
            )
        total_count = int(rows[0].get("total_count") or 0) if rows else 0
        cleaned_rows = [{key: value for key, value in row.items() if key != "total_count"} for row in rows]
        return cleaned_rows, total_count

    def get_family_top_cited_members(
        self,
        family_id: str | int,
        limit: int = 10,
    ) -> list[dict[str, object]]:
        normalized_family_id = self._normalize_family_id(family_id)
        if normalized_family_id is None:
            return []
        safe_limit = max(1, min(int(limit), 25))
        with self.duckdb_provider.connect() as con:
            member_ref = self._analytics_relation(con, self.member_publications_path)
            citation_network_ref = self._analytics_relation(con, self.enriched_citation_network_path)
            return self._query_rows(
                con,
                f"""
                with focal_publications as (
                    select
                        cast(pat_publn_id as bigint) as cited_pat_publn_id,
                        publication_number_full,
                        cast(publn_auth as varchar) as focal_publication_office,
                        trim(cast(publn_kind as varchar)) as focal_publication_kind,
                        cast(publn_date as date) as focal_publication_date,
                        coalesce(is_application_stage, false) as is_application_stage,
                        coalesce(is_grant_stage, false) as is_grant_stage
                    from {member_ref}
                    where docdb_family_id = ?
                )
                select
                    fp.publication_number_full,
                    fp.focal_publication_office,
                    fp.focal_publication_kind,
                    fp.focal_publication_date,
                    fp.is_application_stage,
                    fp.is_grant_stage,
                    cast(coalesce(count(*), 0) as bigint) as citation_event_count,
                    cast(
                        coalesce(
                            sum(
                                case
                                    when not coalesce(n.is_out_of_bounds, false)
                                     and not coalesce(n.is_intra_family_citation, false)
                                     and not coalesce(n.is_self_citation, false)
                                    then 1
                                    else 0
                                end
                            ),
                            0
                        ) as bigint
                    ) as clean_citation_event_count,
                    cast(
                        coalesce(
                            count(
                                distinct case
                                    when not coalesce(n.is_out_of_bounds, false)
                                     and not coalesce(n.is_intra_family_citation, false)
                                     and not coalesce(n.is_self_citation, false)
                                    then n.source_docdb_family_id
                                end
                            ),
                            0
                        ) as bigint
                    ) as citing_family_count,
                    cast(
                        coalesce(
                            count(
                                distinct case
                                    when not coalesce(n.is_out_of_bounds, false)
                                     and not coalesce(n.is_intra_family_citation, false)
                                     and not coalesce(n.is_self_citation, false)
                                     and trim(upper(coalesce(n.citing_assignee_name, ''))) not in ('', '_', 'UNKNOWN', 'UNKNOWN_OWNER', 'UNASSIGNED')
                                    then n.citing_assignee_name
                                end
                            ),
                            0
                        ) as bigint
                    ) as citing_owner_count,
                    min(cast(n.citation_date as date)) as first_citation_date,
                    max(cast(n.citation_date as date)) as latest_citation_date
                from {citation_network_ref} n
                join focal_publications fp
                  on n.cited_pat_publn_id = fp.cited_pat_publn_id
                where n.cited_docdb_family_id = ?
                group by
                    fp.publication_number_full,
                    fp.focal_publication_office,
                    fp.focal_publication_kind,
                    fp.focal_publication_date,
                    fp.is_application_stage,
                    fp.is_grant_stage
                order by clean_citation_event_count desc, citation_event_count desc, latest_citation_date desc nulls last, publication_number_full asc
                limit ?
                """,
                [normalized_family_id, normalized_family_id, safe_limit],
            )

    def get_family_top_citing_owners(
        self,
        family_id: str | int,
        limit: int = 10,
    ) -> list[dict[str, object]]:
        normalized_family_id = self._normalize_family_id(family_id)
        if normalized_family_id is None:
            return []
        safe_limit = max(1, min(int(limit), 100))
        with self.duckdb_provider.connect() as con:
            citation_network_ref = self._analytics_relation(con, self.enriched_citation_network_path)
            return self._query_rows(
                con,
                f"""
                select
                    trim(cast(n.citing_assignee_name as varchar)) as citing_owner_name,
                    cast(coalesce(count(*), 0) as bigint) as citation_event_count,
                    cast(coalesce(count(*), 0) as bigint) as clean_citation_event_count,
                    cast(coalesce(count(distinct n.source_docdb_family_id), 0) as bigint) as citing_family_count,
                    cast(coalesce(count(distinct n.citing_pat_publn_id), 0) as bigint) as citing_publication_count,
                    cast(coalesce(count(distinct n.cited_pat_publn_id), 0) as bigint) as cited_member_count,
                    cast(coalesce(sum(n.citation_lethality_score), 0.0) as double) as citation_lethality_sum,
                    min(cast(n.citation_date as date)) as first_citation_date,
                    max(cast(n.citation_date as date)) as latest_citation_date
                from {citation_network_ref} n
                where n.cited_docdb_family_id = ?
                  and not coalesce(n.is_out_of_bounds, false)
                  and not coalesce(n.is_intra_family_citation, false)
                  and not coalesce(n.is_self_citation, false)
                  and trim(upper(coalesce(n.citing_assignee_name, ''))) not in ('', '_', 'UNKNOWN', 'UNKNOWN_OWNER', 'UNASSIGNED')
                group by trim(cast(n.citing_assignee_name as varchar))
                order by citation_lethality_sum desc, clean_citation_event_count desc, citation_event_count desc, latest_citation_date desc nulls last, citing_owner_name asc
                limit ?
                """,
                [normalized_family_id, safe_limit],
            )

    def get_family_classification_snapshot(
        self,
        family_id: str | int,
        as_of_year: int | None = None,
    ) -> dict[str, object]:
        normalized_family_id = self._normalize_family_id(family_id)
        if normalized_family_id is None:
            return {}
        with self.duckdb_provider.connect() as con:
            rows = self._latest_rows_by_year(
                con,
                self.classification_mix_path,
                normalized_family_id,
                "as_of_year",
                "as_of_date desc",
                as_of_year=as_of_year,
            )
        return rows[0] if rows else {}

    def get_family_classification_timeseries(self, family_id: str | int) -> list[dict[str, object]]:
        normalized_family_id = self._normalize_family_id(family_id)
        if normalized_family_id is None:
            return []
        with self.duckdb_provider.connect() as con:
            classification_ref = self._analytics_relation(con, self.classification_mix_path)
            return self._query_rows(
                con,
                f"""
                select *
                from {classification_ref}
                where docdb_family_id = ?
                order by as_of_year asc, as_of_date asc
                """,
                [normalized_family_id],
            )

    def get_family_forecasts(self, family_id: str | int) -> list[dict[str, object]]:
        normalized_family_id = self._normalize_family_id(family_id)
        if normalized_family_id is None:
            return []
        with self.duckdb_provider.connect() as con:
            forecast_ref = self._analytics_relation(con, self.forecast_path)
            latest_year = self._latest_year(con, self.forecast_path, normalized_family_id, "as_of_year")
            if latest_year is None:
                return []
            return self._query_rows(
                con,
                f"""
                select *
                from {forecast_ref}
                where docdb_family_id = ?
                  and as_of_year = ?
                order by horizon asc
                """,
                [normalized_family_id, latest_year],
            )

    def get_family_lapse_risk_rows(self, family_id: str | int) -> list[dict[str, object]]:
        normalized_family_id = self._normalize_family_id(family_id)
        if normalized_family_id is None:
            return []
        with self.duckdb_provider.connect() as con:
            lapse_risk_ref = self._analytics_relation(con, self.lapse_risk_path)
            latest_year = self._latest_year(con, self.lapse_risk_path, normalized_family_id, "as_of_year")
            if latest_year is None:
                return []
            return self._query_rows(
                con,
                f"""
                select *
                from {lapse_risk_ref}
                where docdb_family_id = ?
                  and as_of_year = ?
                order by horizon asc, risk_probability_calibrated desc nulls last, jurisdiction_code asc
                """,
                [normalized_family_id, latest_year],
            )

    def get_family_jurisdiction_legal_rows(
        self,
        family_id: str | int,
        as_of_year: int | None = None,
    ) -> list[dict[str, object]]:
        normalized_family_id = self._normalize_family_id(family_id)
        if normalized_family_id is None:
            return []
        with self.duckdb_provider.connect() as con:
            enforceability_ref = self._analytics_relation(con, self.enforceability_branches_path)
            branch_history_ref = self._analytics_relation(con, self.branch_status_history_dense_path)
            legal_event_ref = self._analytics_relation(con, self.legal_event_ledger_path)
            target_year = as_of_year if as_of_year is not None else self._latest_year(
                con,
                self.enforceability_branches_path,
                normalized_family_id,
                "extract(year from snapshot_date)",
            )
            if target_year is None:
                return []
            return self._query_rows(
                con,
                f"""
                with branch_rows as (
                    select
                        docdb_family_id,
                        jurisdiction_code,
                        max(snapshot_date) as snapshot_date,
                        sum(coalesce(branch_enforceability_contribution_raw, 0.0)) as jurisdiction_enforceability_contribution_raw,
                        bool_or(coalesce(active_branch_flag, false)) as active_branch_flag,
                        max_by(coalesce(branch_state_label, 'unknown'), coalesce(branch_enforceability_contribution_raw, 0.0)) as branch_state_label,
                        max_by(coalesce(representative_branch_stage, 'unknown'), coalesce(branch_enforceability_contribution_raw, 0.0)) as representative_branch_stage,
                        max_by(coalesce(branch_coefficient_mode, 'unknown'), coalesce(branch_enforceability_contribution_raw, 0.0)) as branch_coefficient_mode,
                        max(coalesce(final_market_multiplier, 0.0)) as final_market_multiplier,
                        count(distinct wipo_industry_code) as field_count,
                        max_by(coalesce(wipo_industry_code, 'unknown'), coalesce(branch_enforceability_contribution_raw, 0.0)) as dominant_wipo_field
                    from {enforceability_ref}
                    where docdb_family_id = ?
                      and extract(year from snapshot_date) = ?
                    group by 1, 2
                ),
                history_rows as (
                    select
                        docdb_family_id,
                        jurisdiction_code,
                        max(last_grant_event_date) as last_grant_event_date,
                        max(last_lapse_event_date) as last_lapse_event_date,
                        max(last_expiry_event_date) as last_expiry_event_date,
                        max(last_negative_event_date) as last_negative_event_date,
                        max(last_opposition_event_date) as last_opposition_event_date,
                        max(last_pending_event_date) as last_pending_event_date,
                        max_by(coalesce(replay_branch_state, 'unknown'), snapshot_date) as replay_branch_state
                    from {branch_history_ref}
                    where docdb_family_id = ?
                      and snapshot_year = ?
                    group by 1, 2
                ),
                latest_event_rows as (
                    select
                        docdb_family_id,
                        jurisdiction_code,
                        max(event_date) as last_event_date,
                        max_by(coalesce(event_type, 'unknown'), event_date) as last_event_type,
                        max_by(coalesce(event_code, 'unknown'), event_date) as last_event_code
                    from {legal_event_ref}
                    where docdb_family_id = ?
                    group by 1, 2
                )
                select
                    b.*,
                    case
                        when sum(b.jurisdiction_enforceability_contribution_raw) over () > 0
                            then b.jurisdiction_enforceability_contribution_raw
                                 / sum(b.jurisdiction_enforceability_contribution_raw) over ()
                        else 0.0
                    end as jurisdiction_enforceability_share_of_family,
                    case
                        when max(b.jurisdiction_enforceability_contribution_raw) over () > 0
                            then b.jurisdiction_enforceability_contribution_raw
                                 / max(b.jurisdiction_enforceability_contribution_raw) over ()
                        else 0.0
                    end as jurisdiction_relative_enforceability_pct,
                    case
                        when max(b.jurisdiction_enforceability_contribution_raw) over () <= 0 then 'inactive'
                        when (
                            b.jurisdiction_enforceability_contribution_raw
                            / nullif(max(b.jurisdiction_enforceability_contribution_raw) over (), 0.0)
                        ) >= 0.85 then 'dominant'
                        when (
                            b.jurisdiction_enforceability_contribution_raw
                            / nullif(max(b.jurisdiction_enforceability_contribution_raw) over (), 0.0)
                        ) >= 0.60 then 'strong'
                        when (
                            b.jurisdiction_enforceability_contribution_raw
                            / nullif(max(b.jurisdiction_enforceability_contribution_raw) over (), 0.0)
                        ) >= 0.30 then 'supporting'
                        when b.jurisdiction_enforceability_contribution_raw > 0 then 'light'
                        else 'inactive'
                    end as jurisdiction_relative_enforceability_band,
                    h.last_grant_event_date,
                    h.last_lapse_event_date,
                    h.last_expiry_event_date,
                    h.last_negative_event_date,
                    h.last_opposition_event_date,
                    h.last_pending_event_date,
                    h.replay_branch_state,
                    e.last_event_date,
                    e.last_event_type,
                    e.last_event_code
                from branch_rows b
                left join history_rows h using (docdb_family_id, jurisdiction_code)
                left join latest_event_rows e using (docdb_family_id, jurisdiction_code)
                order by
                    b.active_branch_flag desc,
                    b.jurisdiction_enforceability_contribution_raw desc,
                    b.jurisdiction_code asc
                """,
                [normalized_family_id, int(target_year), normalized_family_id, int(target_year), normalized_family_id],
            )

    def get_family_status_history(self, family_id: str | int) -> list[dict[str, object]]:
        normalized_family_id = self._normalize_family_id(family_id)
        if normalized_family_id is None:
            return []
        with self.duckdb_provider.connect() as con:
            status_history_ref = self._analytics_relation(con, self.status_history_path)
            return self._query_rows(
                con,
                f"""
                select *
                from {status_history_ref}
                where docdb_family_id = ?
                order by snapshot_year asc, snapshot_date asc
                """,
                [normalized_family_id],
            )

    def get_family_compare_timeslice(
        self,
        family_id: str | int,
        base_year: int | None = None,
        compare_year: int | None = None,
    ) -> list[dict[str, object]]:
        normalized_family_id = self._normalize_family_id(family_id)
        if normalized_family_id is None:
            return []

        with self.duckdb_provider.connect() as con:
            compare_ref = self._analytics_relation(con, self.compare_pit_path)
            if base_year is None:
                latest_row = con.execute(
                    f"""
                    select max(as_of_year)
                    from {compare_ref}
                    where docdb_family_id = ?
                    """,
                    [normalized_family_id],
                ).fetchone()
                base_year = int(latest_row[0]) if latest_row and latest_row[0] is not None else None

            if compare_year is None and base_year is not None:
                prior_row = con.execute(
                    f"""
                    select max(as_of_year)
                    from {compare_ref}
                    where docdb_family_id = ?
                      and as_of_year < ?
                      and coalesce(historical_compare_safe, false) = true
                      and not (
                        as_of_year = 2025
                        and coalesce(family_enforceability_score_asof, 0.0) = 0.0
                      )
                    """,
                    [normalized_family_id, int(base_year)],
                ).fetchone()
                compare_year = int(prior_row[0]) if prior_row and prior_row[0] is not None else None

            if base_year is None or compare_year is None:
                return []

            return self._query_rows(
                con,
                f"""
                select *
                from {compare_ref}
                where docdb_family_id = ?
                  and as_of_year in (?, ?)
                order by as_of_year desc
                """,
                [normalized_family_id, int(base_year), int(compare_year)],
            )

    def get_family_compare_timeslice_options(self, family_id: str | int) -> dict[str, object]:
        normalized_family_id = self._normalize_family_id(family_id)
        if normalized_family_id is None:
            return {
                "entity_id": str(family_id),
                "available_years": [],
                "compare_safe_years": [],
                "default_base_year": None,
                "default_compare_year": None,
            }

        with self.duckdb_provider.connect() as con:
            compare_ref = self._analytics_relation(con, self.compare_pit_path)
            rows = self._query_rows(
                con,
                f"""
                select
                    as_of_year,
                    coalesce(historical_compare_safe, false) as historical_compare_safe,
                    not (
                        as_of_year = 2025
                        and coalesce(family_enforceability_score_asof, 0.0) = 0.0
                    ) as year_allowed
                from {compare_ref}
                where docdb_family_id = ?
                order by as_of_year desc
                """,
                [normalized_family_id],
            )

        available_years = [int(row["as_of_year"]) for row in rows if row.get("as_of_year") is not None]
        compare_safe_years = [
            int(row["as_of_year"])
            for row in rows
            if row.get("as_of_year") is not None
            and bool(row.get("historical_compare_safe"))
            and bool(row.get("year_allowed"))
        ]
        default_base_year = available_years[0] if available_years else None
        default_compare_year = next((year for year in compare_safe_years if default_base_year is not None and year < default_base_year), None)

        return {
            "entity_id": str(normalized_family_id),
            "available_years": available_years,
            "compare_safe_years": compare_safe_years,
            "default_base_year": default_base_year,
            "default_compare_year": default_compare_year,
        }

    def get_family_compare_contexts(self, family_ids: list[str | int | None]) -> dict[str, dict[str, object]]:
        normalized_family_ids = []
        for family_id in family_ids:
            normalized = self._normalize_family_id(family_id)
            if normalized is not None:
                normalized_family_ids.append(normalized)
        if not normalized_family_ids:
            return {}

        unique_family_ids = list(dict.fromkeys(normalized_family_ids))
        contexts: dict[str, dict[str, object]] = {}
        core_serving_path = self.artifact_locator.resolve_core_serving_duckdb()
        if core_serving_path is not None:
            contexts = self._get_family_compare_contexts_from_serving(core_serving_path, unique_family_ids)
        if self.settings.raw_parquet_fallback_enabled:
            missing_family_ids = [family_id for family_id in unique_family_ids if str(family_id) not in contexts]
            raw_contexts = self._get_family_compare_contexts_from_raw_parquet(missing_family_ids)
            for family_id, payload in raw_contexts.items():
                merged = dict(contexts.get(family_id, {}))
                merged.update(payload)
                contexts[family_id] = merged
        return contexts

    def _get_family_compare_contexts_from_serving(
        self,
        core_serving_path: Path,
        family_ids: list[int],
    ) -> dict[str, dict[str, object]]:
        placeholders = ", ".join("?" for _ in family_ids)
        with self.duckdb_provider.connect() as con:
            con.execute(f"ATTACH '{core_serving_path}' AS core_db (READ_ONLY)")
            table_exists = con.execute(
                """
                select 1
                from information_schema.tables
                where table_catalog = 'core_db'
                  and table_schema = 'main'
                  and table_name = 'family_compare_current_serving'
                limit 1
                """
            ).fetchone()
            if table_exists is None:
                return {}
            cursor = con.execute(
                f"""
                select *
                from core_db.family_compare_current_serving
                where docdb_family_id in ({placeholders})
                """,
                family_ids,
            )
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()
        contexts: dict[str, dict[str, object]] = {}
        for row in rows:
            payload = self._to_dict(columns, row)
            contexts[str(payload.get("docdb_family_id"))] = payload
        return contexts

    def _get_family_compare_contexts_from_raw_parquet(
        self,
        unique_family_ids: list[int],
    ) -> dict[str, dict[str, object]]:
        if not unique_family_ids:
            return {}
        placeholders = ", ".join("?" for _ in unique_family_ids)

        with self.duckdb_provider.connect() as con:
            compare_ref = self._analytics_relation(con, self.compare_pit_path)
            summary_ref = self._analytics_relation(con, self.summary_path)
            blocking_ref = self._analytics_relation(con, self.blocking_power_path)
            cursor = con.execute(
                f"""
                with latest_compare as (
                    select *
                    from {compare_ref}
                    where is_latest_observed_year
                ),
                legal_ranked as (
                    select
                        docdb_family_id,
                        100.0 * percent_rank() over (
                            partition by
                                coalesce(primary_wipo_field_current, 'unknown'),
                                coalesce(family_composite_status_asof, 'unknown')
                            order by coalesce(family_enforceability_score_asof, 0.0)
                        ) as legal_durability_percentile
                    from latest_compare
                ),
                citation_ranked as (
                    select
                        s.docdb_family_id,
                        100.0 * percent_rank() over (
                            partition by
                            coalesce(s.primary_wipo_field, 'unknown'),
                            coalesce(s.family_priority_year, -1)
                        order by coalesce(c.pre_asof_forward_citations_weighted, s.oecd_quality_proxy_score, 0.0)
                    ) as citation_heritage_percentile
                    from {summary_ref} s
                    left join latest_compare c using (docdb_family_id)
                )
                select
                    s.docdb_family_id,
                    s.owner_name_harmonized,
                    s.owner_name_display,
                    s.primary_wipo_field,
                    s.family_priority_year,
                    s.family_composite_status,
                    s.family_size_docdb,
                    s.family_tech_breadth_wipo_count,
                    s.active_jurisdiction_count,
                    s.family_fwd_cits7_percentile,
                    s.family_quality_index_6_score,
                    s.oecd_quality_percentile,
                    s.oecd_quality_proxy_score,
                    b.family_ui_blocking_power_score,
                    b.family_overall_legal_enforceability_score,
                    b.family_market_threat_score_raw,
                    c.primary_wipo_field_current,
                    c.family_composite_status_asof,
                    c.family_enforceability_score_asof,
                    c.family_active_jurisdiction_share_asof,
                    c.family_jurisdiction_count_asof,
                    c.pre_asof_forward_citations_weighted,
                    c.data_completeness_pct_asof,
                    c.historical_compare_safe,
                    c.historical_oecd_supported,
                    c.current_owner_metadata_only,
                    lr.legal_durability_percentile,
                    cr.citation_heritage_percentile
                from {summary_ref} s
                left join {blocking_ref} b using (docdb_family_id)
                left join latest_compare c using (docdb_family_id)
                left join legal_ranked lr using (docdb_family_id)
                left join citation_ranked cr using (docdb_family_id)
                where s.docdb_family_id in ({placeholders})
                """,
                unique_family_ids,
            )
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()

        contexts: dict[str, dict[str, object]] = {}
        for row in rows:
            payload = self._to_dict(columns, row)
            contexts[str(payload.get("docdb_family_id"))] = payload
        return contexts

    def get_family_compare_context(self, family_id: str | int) -> dict[str, object]:
        normalized_family_id = self._normalize_family_id(family_id)
        if normalized_family_id is None:
            return {}
        return self.get_family_compare_contexts([normalized_family_id]).get(str(normalized_family_id), {})

    def _get_core_family_suggestions(self, query: str, limit: int = 8) -> list[dict[str, object]] | None:
        normalized_query = str(query).strip()
        if len(normalized_query) < 1:
            return []

        safe_limit = max(1, min(int(limit), 20))
        upper_query = normalized_query.upper()
        id_prefix = f"{normalized_query}%"
        id_cluster_prefix = f"{normalized_query[:4]}%" if normalized_query.isdigit() and len(normalized_query) >= 6 else id_prefix
        text_like = f"%{upper_query}%"

        core_serving_path = self.artifact_locator.resolve_core_serving_duckdb()
        if core_serving_path is not None:
            with self.duckdb_provider.connect() as con:
                self._attach_core_serving(con, core_serving_path)
                if self._core_table_exists(con, "family_compare_current_serving") and self._core_table_exists(con, "family_summary"):
                    return self._query_rows(
                        con,
                        """
                        select
                            cast(c.docdb_family_id as varchar) as family_id,
                            cast(c.docdb_family_id as varchar) as label,
                            s.owner_name_display,
                            coalesce(c.primary_wipo_field_current, s.primary_wipo_field) as primary_field,
                            coalesce(c.family_composite_status_asof, s.family_composite_status) as status
                        from core_db.family_compare_current_serving c
                        left join core_db.family_summary s using (docdb_family_id)
                        where cast(c.docdb_family_id as varchar) like ?
                           or cast(c.docdb_family_id as varchar) like ?
                           or upper(coalesce(s.owner_name_display, '')) like ?
                           or upper(coalesce(c.primary_wipo_field_current, s.primary_wipo_field, '')) like ?
                        order by
                            case
                                when cast(c.docdb_family_id as varchar) = ? then 0
                                when cast(c.docdb_family_id as varchar) like ? then 1
                                when cast(c.docdb_family_id as varchar) like ? then 2
                                when upper(coalesce(s.owner_name_display, '')) like ? then 3
                                else 4
                            end,
                            cast(c.docdb_family_id as varchar) asc
                        limit ?
                        """,
                        [
                            id_prefix,
                            id_cluster_prefix,
                            text_like,
                            text_like,
                            normalized_query,
                            id_prefix,
                            id_cluster_prefix,
                            text_like,
                            safe_limit,
                        ],
                    )
        return None

    def get_family_suggestions(self, query: str, limit: int = 8) -> list[dict[str, object]]:
        core_rows = self._get_core_family_suggestions(query=query, limit=limit)
        return core_rows if core_rows is not None else []

    def get_family_compare_suggestions(self, query: str, limit: int = 8) -> list[dict[str, object]]:
        normalized_query = str(query).strip()
        if len(normalized_query) < 1:
            return []

        safe_limit = max(1, min(int(limit), 20))
        upper_query = normalized_query.upper()
        id_prefix = f"{normalized_query}%"
        id_cluster_prefix = f"{normalized_query[:4]}%" if normalized_query.isdigit() and len(normalized_query) >= 6 else id_prefix
        text_like = f"%{upper_query}%"

        core_rows = self._get_core_family_suggestions(query=normalized_query, limit=safe_limit)
        if core_rows is not None:
            return core_rows

        if not self.settings.raw_parquet_fallback_enabled:
            return []

        with self.duckdb_provider.connect() as con:
            compare_ref = self._analytics_relation(con, self.compare_pit_path)
            summary_ref = self._analytics_relation(con, self.summary_path)
            return self._query_rows(
                con,
                f"""
                with latest_compare as (
                    select *
                    from {compare_ref}
                    where is_latest_observed_year
                )
                select
                    cast(s.docdb_family_id as varchar) as family_id,
                    cast(s.docdb_family_id as varchar) as label,
                    s.owner_name_display,
                    coalesce(c.primary_wipo_field_current, s.primary_wipo_field) as primary_field,
                    coalesce(c.family_composite_status_asof, s.family_composite_status) as status
                from {summary_ref} s
                join latest_compare c using (docdb_family_id)
                where cast(s.docdb_family_id as varchar) like ?
                   or cast(s.docdb_family_id as varchar) like ?
                   or upper(coalesce(s.owner_name_display, '')) like ?
                   or upper(coalesce(c.primary_wipo_field_current, s.primary_wipo_field, '')) like ?
                order by
                    case
                        when cast(s.docdb_family_id as varchar) = ? then 0
                        when cast(s.docdb_family_id as varchar) like ? then 1
                        when cast(s.docdb_family_id as varchar) like ? then 2
                        when upper(coalesce(s.owner_name_display, '')) like ? then 3
                        else 4
                    end,
                    cast(s.docdb_family_id as varchar) asc
                limit ?
                """,
                [
                    id_prefix,
                    id_cluster_prefix,
                    text_like,
                    text_like,
                    normalized_query,
                    id_prefix,
                    id_cluster_prefix,
                    text_like,
                    safe_limit,
                ],
            )
