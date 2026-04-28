from __future__ import annotations

from datetime import date
import json
from pathlib import Path
import re
import subprocess

from config.settings import get_settings
from infrastructure.artifacts import ArtifactLocator
from infrastructure.duckdb import DuckDbProvider


PLACEHOLDER_OWNER_VALUES = {"", "_", "UNKNOWN", "UNKNOWN_OWNER", "UNASSIGNED"}


class PortfolioRepository:
    def __init__(self) -> None:
        settings = get_settings()
        self.settings = settings
        self.summary_path = settings.etl_data_root / "gold" / "gold_portfolio_summary.parquet"
        self.forecast_summary_path = settings.etl_data_root / "gold" / "gold_portfolio_forecast_summary.parquet"
        self.forecast_segments_path = settings.etl_data_root / "gold" / "gold_portfolio_forecast_segments.parquet"
        self.forecast_contributors_path = settings.etl_data_root / "gold" / "gold_portfolio_forecast_contributors.parquet"
        self.classification_mix_path = settings.etl_data_root / "gold" / "gold_portfolio_classification_mix_pit.parquet"
        self.family_classification_mix_path = settings.etl_data_root / "gold" / "gold_family_classification_mix_pit.parquet"
        self.threat_path = settings.etl_data_root / "gold" / "gold_portfolio_threat_matrix.parquet"
        self.field_timeseries_path = settings.etl_data_root / "gold" / "gold_portfolio_field_timeseries.parquet"
        self.compare_pit_path = settings.etl_data_root / "gold" / "gold_portfolio_compare_pit.parquet"
        self.family_compare_path = settings.etl_data_root / "gold" / "gold_family_compare_pit.parquet"
        self.family_citation_summary_path = settings.etl_data_root / "gold" / "gold_family_citation_summary.parquet"
        self.family_citation_timeseries_path = settings.etl_data_root / "gold" / "gold_family_citation_timeseries_pit.parquet"
        self.portfolio_citation_summary_path = settings.etl_data_root / "gold" / "gold_portfolio_citation_summary.parquet"
        self.portfolio_citation_timeseries_path = settings.etl_data_root / "gold" / "gold_portfolio_citation_timeseries.parquet"
        self.portfolio_citation_family_leaderboard_path = settings.etl_data_root / "gold" / "gold_portfolio_citation_family_leaderboard.parquet"
        self.portfolio_citation_attacker_path = settings.etl_data_root / "gold" / "gold_portfolio_attacker_momentum.parquet"
        self.portfolio_citation_field_path = settings.etl_data_root / "gold" / "gold_portfolio_citation_pressure_by_field.parquet"
        self.portfolio_citation_jurisdiction_path = settings.etl_data_root / "gold" / "gold_portfolio_citation_pressure_by_jurisdiction.parquet"
        self.portfolio_filing_timeseries_path = settings.etl_data_root / "gold" / "gold_portfolio_filing_timeseries.parquet"
        self.family_summary_path = settings.etl_data_root / "gold" / "gold_family_summary.parquet"
        self.family_blocking_path = settings.etl_data_root / "gold" / "gold_family_blocking_power.parquet"
        self.owner_bridge_path = settings.etl_data_root / "silver" / "silver_family_owner_bridge.parquet"
        self.branch_history_dense_path = settings.etl_data_root / "silver" / "silver_branch_status_history_dense.parquet"
        self.family_citation_metrics_path = settings.etl_data_root / "silver" / "silver_family_citation_metrics.parquet"
        self.family_feature_snapshot_pit_path = settings.etl_data_root / "silver" / "silver_family_feature_snapshot_pit.parquet"
        self.enriched_citation_network_path = settings.etl_data_root / "silver" / "silver_enriched_citation_network.parquet"
        self.phase04_prediction_path = settings.etl_data_root / "ml" / "ml_prediction_family_jurisdiction_lapse_risk.parquet"
        self.pending_grant_prediction_path = settings.etl_data_root / "ml" / "ml_prediction_pending_grant_pipeline.parquet"
        self.pending_grant_model_card_path = settings.etl_data_root / "ml" / "model_card_pending_grant_pipeline.json"
        self.pending_grant_calibration_path = settings.etl_data_root / "ml" / "pending_grant_pipeline_calibration.json"
        self.pending_grant_model_12m_path = settings.etl_data_root / "ml" / "pending_grant_pipeline_12m_model.txt"
        self.pending_grant_model_24m_path = settings.etl_data_root / "ml" / "pending_grant_pipeline_24m_model.txt"
        self.pending_grant_cache_dir = settings.pending_grant_cache_dir
        self.artifact_locator = ArtifactLocator(settings=settings)
        self.duckdb_provider = DuckDbProvider()
        self._core_path_map: dict[Path, str] = {
            self.summary_path: "portfolio_summary",
            self.forecast_summary_path: "portfolio_forecast_summary",
            self.forecast_segments_path: "portfolio_forecast_segments",
            self.forecast_contributors_path: "portfolio_forecast_contributors",
            self.threat_path: "portfolio_threat_matrix",
            self.portfolio_citation_family_leaderboard_path: "portfolio_citation_family_leaderboard",
            self.portfolio_filing_timeseries_path: "portfolio_filing_timeseries",
            self.family_summary_path: "family_summary",
            self.family_blocking_path: "family_blocking_power",
            self.owner_bridge_path: "family_owner_bridge",
        }
        self._analytics_path_map: dict[Path, str] = {
            self.summary_path: "portfolio_summary",
            self.forecast_summary_path: "portfolio_forecast_summary",
            self.forecast_segments_path: "portfolio_forecast_segments",
            self.forecast_contributors_path: "portfolio_forecast_contributors",
            self.classification_mix_path: "portfolio_classification_mix_pit",
            self.family_classification_mix_path: "family_classification_mix_pit",
            self.threat_path: "portfolio_threat_matrix",
            self.field_timeseries_path: "portfolio_field_timeseries",
            self.compare_pit_path: "portfolio_compare_pit",
            self.family_compare_path: "family_compare_pit",
            self.family_citation_summary_path: "family_citation_summary",
            self.family_citation_timeseries_path: "family_citation_timeseries_pit",
            self.portfolio_citation_summary_path: "portfolio_citation_summary",
            self.portfolio_citation_timeseries_path: "portfolio_citation_timeseries",
            self.portfolio_citation_family_leaderboard_path: "portfolio_citation_family_leaderboard",
            self.portfolio_citation_attacker_path: "portfolio_attacker_momentum",
            self.portfolio_citation_field_path: "portfolio_citation_pressure_by_field",
            self.portfolio_citation_jurisdiction_path: "portfolio_citation_pressure_by_jurisdiction",
            self.portfolio_filing_timeseries_path: "portfolio_filing_timeseries",
            self.family_summary_path: "family_summary",
            self.family_blocking_path: "family_blocking_power",
            self.owner_bridge_path: "family_owner_bridge",
            self.branch_history_dense_path: "branch_status_history_dense",
            self.family_citation_metrics_path: "family_citation_metrics",
            self.family_feature_snapshot_pit_path: "family_feature_snapshot_pit",
            self.enriched_citation_network_path: "enriched_citation_network",
            self.phase04_prediction_path: "family_lapse_risk_predictions",
            self.pending_grant_prediction_path: "pending_grant_prediction_pipeline",
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
            serving_artifacts.extend(
                [
                    self.pending_grant_model_card_path,
                    self.pending_grant_calibration_path,
                    self.pending_grant_model_12m_path,
                    self.pending_grant_model_24m_path,
                ]
            )
            return serving_artifacts
        artifacts = [
            self.summary_path,
            self.forecast_summary_path,
            self.forecast_segments_path,
            self.forecast_contributors_path,
            self.classification_mix_path,
            self.family_classification_mix_path,
            self.threat_path,
            self.field_timeseries_path,
            self.compare_pit_path,
            self.family_compare_path,
            self.family_citation_summary_path,
            self.family_citation_timeseries_path,
            self.portfolio_citation_summary_path,
            self.portfolio_citation_timeseries_path,
            self.portfolio_citation_family_leaderboard_path,
            self.portfolio_citation_attacker_path,
            self.portfolio_citation_field_path,
            self.portfolio_citation_jurisdiction_path,
            self.portfolio_filing_timeseries_path,
            self.family_summary_path,
            self.family_blocking_path,
            self.owner_bridge_path,
            self.branch_history_dense_path,
            self.family_citation_metrics_path,
            self.family_feature_snapshot_pit_path,
            self.enriched_citation_network_path,
            self.phase04_prediction_path,
            self.pending_grant_prediction_path,
            self.pending_grant_model_card_path,
            self.pending_grant_calibration_path,
            self.pending_grant_model_12m_path,
            self.pending_grant_model_24m_path,
        ]
        if analytics_serving_path is not None:
            artifacts.insert(0, analytics_serving_path)
        return artifacts

    def _attach_core_serving(self, con: "DuckDbProvider", core_serving_path: Path) -> None:
        attached = con.execute("pragma database_list").fetchall()
        if any(str(row[1]) == "core_db" for row in attached):
            return
        con.execute(f"ATTACH '{core_serving_path}' AS core_db (READ_ONLY)")

    def _core_table_exists(self, con: "DuckDbProvider", table_name: str) -> bool:
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

    def _attach_analytics_serving(self, con: "DuckDbProvider", analytics_serving_path: Path) -> None:
        attached = con.execute("pragma database_list").fetchall()
        if any(str(row[1]) == "analytics_db" for row in attached):
            return
        con.execute(f"ATTACH '{analytics_serving_path}' AS analytics_db (READ_ONLY)")

    def _analytics_table_exists(self, con: "DuckDbProvider", table_name: str) -> bool:
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

    def _analytics_relation(self, con: "DuckDbProvider", path: Path) -> str:
        core_table_name = self._core_path_map.get(path)
        core_serving_path = self.artifact_locator.resolve_core_serving_duckdb()
        if core_table_name and core_serving_path is not None and core_serving_path.exists():
            self._attach_core_serving(con, core_serving_path)
            if self._core_table_exists(con, core_table_name):
                return f"core_db.{core_table_name}"
        table_name = self._analytics_path_map.get(path)
        analytics_serving_path = self.artifact_locator.resolve_analytics_serving_duckdb()
        if table_name and analytics_serving_path is not None and analytics_serving_path.exists():
            self._attach_analytics_serving(con, analytics_serving_path)
            if self._analytics_table_exists(con, table_name):
                return f"analytics_db.{table_name}"
        if (core_table_name or table_name) and not self.settings.raw_parquet_fallback_enabled:
            expected_tables = [table_name_ref for table_name_ref in [core_table_name, table_name] if table_name_ref]
            raise RuntimeError(
                f"Serving table for '{path.name}' is required because raw parquet fallback is disabled. "
                f"Expected one of: {', '.join(expected_tables)}."
            )
        return f"read_parquet('{path}')"

    def _analytics_source_available(self, path: Path) -> bool:
        if path.exists():
            return True
        table_name = self._analytics_path_map.get(path)
        if table_name is None:
            return False
        manifest = self.artifact_locator.resolve_serving_manifest()
        if manifest is None:
            return False
        snapshot = manifest.snapshots.get("analytics")
        if snapshot is None or table_name not in snapshot.tables:
            return False
        analytics_serving_path = self.artifact_locator.resolve_analytics_serving_duckdb()
        return analytics_serving_path is not None and analytics_serving_path.exists()

    def _snapshot_year_filter(self, as_of_year: int | None) -> str:
        if as_of_year is None:
            return ""
        return f" and extract(year from snapshot_date) = {int(as_of_year)}"

    def _classification_year_filter(self, as_of_year: int | None, column_name: str = "as_of_year") -> str:
        if as_of_year is None:
            return ""
        return f" and {column_name} = {int(as_of_year)}"

    def _query_rows(self, con: "DuckDbProvider", query: str, parameters: list[object] | tuple[object, ...]) -> list[dict[str, object]]:
        rows = con.execute(query, parameters).fetchall()
        if not rows:
            return []
        columns = [name for name, *_ in con.description]
        return [dict(zip(columns, row)) for row in rows]

    def _owner_variants(self, owner_id: str) -> list[str]:
        raw = (owner_id or "").strip()
        variants = {
            raw,
            raw.upper(),
            raw.replace("-", "_"),
            raw.replace(" ", "_"),
            raw.upper().replace("-", "_"),
            raw.upper().replace(" ", "_"),
        }
        return [candidate for candidate in variants if candidate]

    def _normalize_owner_token(self, owner_name: str | None) -> str:
        normalized = re.sub(r"[^A-Z0-9]+", "_", (owner_name or "").strip().upper())
        return normalized.strip("_")

    def _is_placeholder_owner(self, owner_name: str | None) -> bool:
        return self._normalize_owner_token(owner_name) in PLACEHOLDER_OWNER_VALUES

    def _non_placeholder_owner_sql(self, column_name: str = "owner_name_harmonized") -> str:
        return f"trim(upper(coalesce({column_name}, ''))) not in ('', '_', 'UNKNOWN', 'UNKNOWN_OWNER', 'UNASSIGNED')"

    def _portfolio_peer_bucket_sql(self, column_name: str = "portfolio_family_count_within_mega_cluster") -> str:
        return f"""
            case
                when coalesce({column_name}, 0) <= 1 then '1'
                when {column_name} between 2 and 5 then '2_5'
                when {column_name} between 6 and 20 then '6_20'
                when {column_name} between 21 and 100 then '21_100'
                when {column_name} between 101 and 500 then '101_500'
                else '501_plus'
            end
        """

    def _citation_family_sort_column(self, sort: str | None) -> str:
        normalized = (sort or "").strip().lower()
        return {
            "forward_clean": "forward_citations_clean",
            "forward_weighted": "forward_citations_weighted",
            "early_5y": "early_citations_5y",
            "early_7y": "early_citations_7y",
            "blocking": "blocking_score",
        }.get(normalized, "forward_citations_clean")

    def _parquet_has_column(self, con: "DuckDbProvider", path: Path, column_name: str) -> bool:
        relation = self._analytics_relation(con, path)
        rows = con.execute(
            f"""
            describe select *
            from {relation}
            """,
        ).fetchall()
        return any(candidate[0] == column_name for candidate in rows)

    def _parquet_has_columns(self, con: "DuckDbProvider", path: Path, column_names: list[str]) -> bool:
        relation = self._analytics_relation(con, path)
        rows = con.execute(
            f"""
            describe select *
            from {relation}
            """,
        ).fetchall()
        available_columns = {candidate[0] for candidate in rows}
        return all(column_name in available_columns for column_name in column_names)

    def _citation_pit_path(self) -> Path:
        if self._analytics_source_available(self.family_citation_timeseries_path):
            return self.family_citation_timeseries_path
        return self.family_feature_snapshot_pit_path

    def _citation_pit_observed_filter(self, alias: str = "fs") -> str:
        if self._analytics_source_available(self.family_citation_timeseries_path):
            return ""
        return f"and coalesce({alias}.is_observed_as_of_snapshot, false)"

    def _resolve_owner(self, con: "DuckDbProvider", path: Path, owner_id: str) -> str | None:
        relation = self._analytics_relation(con, path)
        for candidate in self._owner_variants(owner_id):
            if self._is_placeholder_owner(candidate):
                continue
            row = con.execute(
                f"""
                select owner_name_harmonized
                from {relation}
                where owner_name_harmonized = ?
                  and {self._non_placeholder_owner_sql('owner_name_harmonized')}
                limit 1
                """,
                [candidate],
            ).fetchone()
            if row:
                return row[0]
        display_candidate = (owner_id or "").strip().upper()
        has_owner_display = self._parquet_has_column(con, path, "owner_name_display")
        if display_candidate and has_owner_display and not self._is_placeholder_owner(display_candidate):
            row = con.execute(
                f"""
                select owner_name_harmonized
                from {relation}
                where upper(coalesce(owner_name_display, '')) = ?
                  and {self._non_placeholder_owner_sql('owner_name_harmonized')}
                limit 1
                """,
                [display_candidate],
            ).fetchone()
            if row:
                return row[0]
        return None

    def _resolve_owner_from_table(self, con: "DuckDbProvider", table_name: str, owner_id: str) -> str | None:
        for candidate in self._owner_variants(owner_id):
            if self._is_placeholder_owner(candidate):
                continue
            row = con.execute(
                f"""
                select owner_name_harmonized
                from core_db.{table_name}
                where owner_name_harmonized = ?
                  and {self._non_placeholder_owner_sql('owner_name_harmonized')}
                limit 1
                """,
                [candidate],
            ).fetchone()
            if row:
                return row[0]
        has_owner_display = con.execute(
            "select 1 from pragma_table_info(?) where name = 'owner_name_display' limit 1",
            [f"core_db.{table_name}"],
        ).fetchone()
        if not has_owner_display:
            return None
        display_candidate = (owner_id or "").strip().upper()
        if display_candidate and not self._is_placeholder_owner(display_candidate):
            row = con.execute(
                f"""
                select owner_name_harmonized
                from core_db.{table_name}
                where upper(coalesce(owner_name_display, '')) = ?
                  and {self._non_placeholder_owner_sql('owner_name_harmonized')}
                limit 1
                """,
                [display_candidate],
            ).fetchone()
            if row:
                return row[0]
        return None

    def _resolve_owner_in_parquet(
        self,
        con: "DuckDbProvider",
        path: Path,
        owner_id: str,
        harmonized_column: str,
        display_column: str | None = None,
    ) -> str | None:
        relation = self._analytics_relation(con, path)
        for candidate in self._owner_variants(owner_id):
            if self._is_placeholder_owner(candidate):
                continue
            row = con.execute(
                f"""
                select {harmonized_column}
                from {relation}
                where {harmonized_column} = ?
                  and {self._non_placeholder_owner_sql(harmonized_column)}
                limit 1
                """,
                [candidate],
            ).fetchone()
            if row:
                return row[0]
        if display_column and self._parquet_has_column(con, path, display_column):
            display_candidate = (owner_id or "").strip().upper()
            if display_candidate and not self._is_placeholder_owner(display_candidate):
                row = con.execute(
                    f"""
                    select {harmonized_column}
                    from {relation}
                    where upper(coalesce({display_column}, '')) = ?
                      and {self._non_placeholder_owner_sql(harmonized_column)}
                    limit 1
                    """,
                    [display_candidate],
                ).fetchone()
                if row:
                    return row[0]
        return None

    def _owner_search_sql(
        self,
        source_sql: str,
        coverage_sql: str,
        normalized: str,
        term_upper: str,
        limit: int,
    ) -> tuple[str, list[object]]:
        like_display = f"%{term_upper}%"
        like_harmonized = f"%{normalized}%"
        prefix_normalized = f"{normalized}%"
        query_length = max(len(normalized), 1)
        exact_short_alias_family_threshold = 50

        query_sql = f"""
        with primary_owner_coverage as (
            select
                owner_name_harmonized,
                count(distinct docdb_family_id) as primary_owner_family_count
            from {coverage_sql}
            where owner_name_harmonized is not null
              and {self._non_placeholder_owner_sql('owner_name_harmonized')}
              and coalesce(is_primary_owner, false) = true
            group by owner_name_harmonized
        ),
        scoped as (
            select
                s.owner_name_harmonized,
                s.owner_name_display,
                cast(coalesce(p.primary_owner_family_count, s.portfolio_family_count_within_mega_cluster, 0) as integer) as family_count,
                regexp_replace(upper(coalesce(s.owner_name_display, '')), '[^A-Z0-9]+', '_', 'g') as normalized_display,
                upper(coalesce(s.owner_name_harmonized, '')) as normalized_harmonized,
                row_number() over (
                    partition by s.owner_name_harmonized
                    order by s.snapshot_date desc
                ) as row_num
            from {source_sql} s
            join primary_owner_coverage p
              on s.owner_name_harmonized = p.owner_name_harmonized
            where s.owner_name_harmonized is not null
              and {self._non_placeholder_owner_sql('s.owner_name_harmonized')}
              and coalesce(p.primary_owner_family_count, 0) > 0
              and (
                upper(coalesce(s.owner_name_display, '')) like ?
                or upper(s.owner_name_harmonized) like ?
              )
        )
        select
            owner_name_harmonized,
            coalesce(owner_name_display, owner_name_harmonized) as owner_name_display,
            family_count
        from scoped
        where row_num = 1
        order by
            case
                when (
                    (normalized_harmonized = ? or normalized_display = ?)
                    and ({query_length} > 3 or family_count >= {exact_short_alias_family_threshold})
                ) then 0
                when (
                    (normalized_display like ? and coalesce(substr(normalized_display, {query_length + 1}, 1), '') not in ('', '_'))
                    or (normalized_harmonized like ? and coalesce(substr(normalized_harmonized, {query_length + 1}, 1), '') not in ('', '_'))
                ) then 1
                when normalized_harmonized = ? or normalized_display = ? then 2
                when (
                    (normalized_display like ? and coalesce(substr(normalized_display, {query_length + 1}, 1), '') = '_')
                    or (normalized_harmonized like ? and coalesce(substr(normalized_harmonized, {query_length + 1}, 1), '') = '_')
                ) then 3
                when upper(coalesce(owner_name_display, '')) like ? then 4
                when normalized_harmonized like ? then 5
                else 6
            end,
            family_count desc,
            length(normalized_harmonized) asc,
            owner_name_display asc
        limit ?
        """
        parameters: list[object] = [
            like_display,
            like_harmonized,
            normalized,
            normalized,
            prefix_normalized,
            prefix_normalized,
            normalized,
            normalized,
            prefix_normalized,
            prefix_normalized,
            like_display,
            like_harmonized,
            int(limit),
        ]
        return query_sql, parameters

    def get_owner_summary(self, owner_id: str, as_of_year: int | None = None) -> dict[str, object]:
        core_serving_path = self.artifact_locator.resolve_core_serving_duckdb()
        if core_serving_path is not None:
            with self.duckdb_provider.connect() as con:
                self._attach_core_serving(con, core_serving_path)
                if self._core_table_exists(con, "portfolio_summary"):
                    resolved_owner = self._resolve_owner_from_table(con, "portfolio_summary", owner_id)
                    if resolved_owner:
                        query = f"""
                        select *
                        from core_db.portfolio_summary
                        where owner_name_harmonized = ?
                        {self._snapshot_year_filter(as_of_year)}
                        order by snapshot_date desc
                        limit 1
                        """
                        rows = self._query_rows(con, query, [resolved_owner])
                        if rows:
                            return rows[0]

        with self.duckdb_provider.connect() as con:
            resolved_owner = self._resolve_owner(con, self.summary_path, owner_id)
            if not resolved_owner:
                return {}
            summary_ref = self._analytics_relation(con, self.summary_path)
            query = f"""
            select *
            from {summary_ref}
            where owner_name_harmonized = ?
            {self._snapshot_year_filter(as_of_year)}
            order by snapshot_date desc
            limit 1
            """
            rows = self._query_rows(con, query, [resolved_owner])
            return rows[0] if rows else {}

    def get_owner_summary_peer_context(self, owner_id: str, as_of_year: int | None = None) -> dict[str, object]:
        core_serving_path = self.artifact_locator.resolve_core_serving_duckdb()
        if core_serving_path is not None:
            with self.duckdb_provider.connect() as con:
                self._attach_core_serving(con, core_serving_path)
                if self._core_table_exists(con, "portfolio_compare_current_serving"):
                    resolved_owner = self._resolve_owner_from_table(con, "portfolio_compare_current_serving", owner_id)
                    if resolved_owner:
                        query = """
                        select *
                        from core_db.portfolio_compare_current_serving
                        where owner_name_harmonized = ?
                        limit 1
                        """
                        rows = self._query_rows(con, query, [resolved_owner])
                        if rows:
                            if as_of_year is None:
                                return rows[0]
                            snapshot_date = rows[0].get("snapshot_date")
                            snapshot_year = int(str(snapshot_date)[:4]) if snapshot_date is not None else None
                            if snapshot_year == int(as_of_year):
                                return rows[0]
                if self._core_table_exists(con, "portfolio_summary"):
                    resolved_owner = self._resolve_owner_from_table(con, "portfolio_summary", owner_id)
                    if resolved_owner:
                        peer_bucket_sql = self._portfolio_peer_bucket_sql()
                        query = f"""
                        with latest_snapshot as (
                            select max(snapshot_date) as snapshot_date
                            from core_db.portfolio_summary
                            where {self._non_placeholder_owner_sql('owner_name_harmonized')}
                            {self._snapshot_year_filter(as_of_year)}
                        ),
                        scoped as (
                            select
                                owner_name_harmonized,
                                {peer_bucket_sql} as peer_bucket,
                                cast(coalesce(portfolio_total_mass_score, 0.0) as double) as portfolio_total_mass_score,
                                cast(coalesce(portfolio_current_threat_score, 0.0) as double) as portfolio_current_threat_score,
                                cast(coalesce(portfolio_heritage_score, 0.0) as double) as portfolio_heritage_score,
                                cast(coalesce(portfolio_avg_blocking_power_within_mega_cluster, 0.0) as double) as portfolio_avg_blocking_power_within_mega_cluster,
                                cast(coalesce(portfolio_hit_rate_top_decile, 0.0) as double) as portfolio_hit_rate_top_decile,
                                cast(coalesce(portfolio_crown_jewel_index, 0.0) as double) as portfolio_crown_jewel_index
                            from core_db.portfolio_summary
                            where snapshot_date = (select snapshot_date from latest_snapshot)
                              and {self._non_placeholder_owner_sql('owner_name_harmonized')}
                        ),
                        ranked as (
                            select
                                *,
                                count(*) over (partition by peer_bucket) as peer_bucket_size,
                                percent_rank() over (partition by peer_bucket order by portfolio_total_mass_score) * 100.0 as portfolio_total_mass_score_percentile,
                                percent_rank() over (partition by peer_bucket order by portfolio_current_threat_score) * 100.0 as portfolio_current_threat_score_percentile,
                                percent_rank() over (partition by peer_bucket order by portfolio_heritage_score) * 100.0 as portfolio_heritage_score_percentile,
                                percent_rank() over (partition by peer_bucket order by portfolio_avg_blocking_power_within_mega_cluster) * 100.0 as portfolio_avg_blocking_power_percentile,
                                percent_rank() over (partition by peer_bucket order by portfolio_hit_rate_top_decile) * 100.0 as portfolio_hit_rate_top_decile_percentile,
                                percent_rank() over (partition by peer_bucket order by portfolio_crown_jewel_index) * 100.0 as portfolio_crown_jewel_index_percentile
                            from scoped
                        )
                        select *
                        from ranked
                        where owner_name_harmonized = ?
                        limit 1
                        """
                        rows = self._query_rows(con, query, [resolved_owner])
                        if rows:
                            return rows[0]

        with self.duckdb_provider.connect() as con:
            resolved_owner = self._resolve_owner(con, self.summary_path, owner_id)
            if not resolved_owner:
                return {}
            summary_ref = self._analytics_relation(con, self.summary_path)
            peer_bucket_sql = self._portfolio_peer_bucket_sql()
            query = f"""
            with latest_snapshot as (
                select max(snapshot_date) as snapshot_date
                from {summary_ref}
                where {self._non_placeholder_owner_sql('owner_name_harmonized')}
                {self._snapshot_year_filter(as_of_year)}
            ),
            scoped as (
                select
                    owner_name_harmonized,
                    {peer_bucket_sql} as peer_bucket,
                    cast(coalesce(portfolio_total_mass_score, 0.0) as double) as portfolio_total_mass_score,
                    cast(coalesce(portfolio_current_threat_score, 0.0) as double) as portfolio_current_threat_score,
                    cast(coalesce(portfolio_heritage_score, 0.0) as double) as portfolio_heritage_score,
                    cast(coalesce(portfolio_avg_blocking_power_within_mega_cluster, 0.0) as double) as portfolio_avg_blocking_power_within_mega_cluster,
                    cast(coalesce(portfolio_hit_rate_top_decile, 0.0) as double) as portfolio_hit_rate_top_decile,
                    cast(coalesce(portfolio_crown_jewel_index, 0.0) as double) as portfolio_crown_jewel_index
                from {summary_ref}
                where snapshot_date = (select snapshot_date from latest_snapshot)
                  and {self._non_placeholder_owner_sql('owner_name_harmonized')}
            ),
            ranked as (
                select
                    *,
                    count(*) over (partition by peer_bucket) as peer_bucket_size,
                    percent_rank() over (partition by peer_bucket order by portfolio_total_mass_score) * 100.0 as portfolio_total_mass_score_percentile,
                    percent_rank() over (partition by peer_bucket order by portfolio_current_threat_score) * 100.0 as portfolio_current_threat_score_percentile,
                    percent_rank() over (partition by peer_bucket order by portfolio_heritage_score) * 100.0 as portfolio_heritage_score_percentile,
                    percent_rank() over (partition by peer_bucket order by portfolio_avg_blocking_power_within_mega_cluster) * 100.0 as portfolio_avg_blocking_power_percentile,
                    percent_rank() over (partition by peer_bucket order by portfolio_hit_rate_top_decile) * 100.0 as portfolio_hit_rate_top_decile_percentile,
                    percent_rank() over (partition by peer_bucket order by portfolio_crown_jewel_index) * 100.0 as portfolio_crown_jewel_index_percentile
                from scoped
            )
            select *
            from ranked
            where owner_name_harmonized = ?
            limit 1
            """
            rows = self._query_rows(con, query, [resolved_owner])
            return rows[0] if rows else {}

    def search_owners(self, query: str, limit: int = 8) -> list[dict[str, object]]:
        term = (query or "").strip()
        if len(term) < 2:
            return []
        normalized = term.upper().replace("-", "_").replace(" ", "_")
        query_sql, parameters = self._owner_search_sql(
            source_sql="core_db.portfolio_summary",
            coverage_sql="core_db.family_owner_bridge",
            normalized=normalized,
            term_upper=term.upper(),
            limit=limit,
        )

        core_serving_path = self.artifact_locator.resolve_core_serving_duckdb()
        if core_serving_path is not None:
            with self.duckdb_provider.connect() as con:
                self._attach_core_serving(con, core_serving_path)
                if self._core_table_exists(con, "portfolio_summary") and self._core_table_exists(con, "family_owner_bridge"):
                    rows = self._query_rows(con, query_sql, parameters)
                    if rows:
                        return rows

        with self.duckdb_provider.connect() as con:
            summary_ref = self._analytics_relation(con, self.summary_path)
            owner_bridge_ref = self._analytics_relation(con, self.owner_bridge_path)
            raw_query_sql, raw_parameters = self._owner_search_sql(
                source_sql=summary_ref,
                coverage_sql=owner_bridge_ref,
                normalized=normalized,
                term_upper=term.upper(),
                limit=limit,
            )
            return self._query_rows(con, raw_query_sql, raw_parameters)

    def get_owner_forecast_summary(self, owner_id: str, as_of_year: int | None = None) -> dict[str, object]:
        core_serving_path = self.artifact_locator.resolve_core_serving_duckdb()
        if core_serving_path is not None:
            with self.duckdb_provider.connect() as con:
                self._attach_core_serving(con, core_serving_path)
                if self._core_table_exists(con, "portfolio_forecast_summary"):
                    resolved_owner = self._resolve_owner_from_table(con, "portfolio_forecast_summary", owner_id)
                    if resolved_owner:
                        query = f"""
                        select *
                        from core_db.portfolio_forecast_summary
                        where owner_name_harmonized = ?
                        {self._snapshot_year_filter(as_of_year)}
                        order by snapshot_date desc
                        limit 1
                        """
                        rows = self._query_rows(con, query, [resolved_owner])
                        if rows:
                            return rows[0]

        with self.duckdb_provider.connect() as con:
            resolved_owner = self._resolve_owner(con, self.forecast_summary_path, owner_id)
            if not resolved_owner:
                return {}
            forecast_summary_ref = self._analytics_relation(con, self.forecast_summary_path)
            query = f"""
            select *
            from {forecast_summary_ref}
            where owner_name_harmonized = ?
            {self._snapshot_year_filter(as_of_year)}
            order by snapshot_date desc
            limit 1
            """
            rows = self._query_rows(con, query, [resolved_owner])
            return rows[0] if rows else {}

    def get_owner_family_status_counts(self, owner_id: str) -> dict[str, object]:
        core_serving_path = self.artifact_locator.resolve_core_serving_duckdb()
        if core_serving_path is not None:
            with self.duckdb_provider.connect() as con:
                self._attach_core_serving(con, core_serving_path)
                if self._core_table_exists(con, "family_owner_bridge") and self._core_table_exists(con, "family_summary"):
                    resolved_owner = self._resolve_owner_from_table(con, "family_owner_bridge", owner_id)
                    if resolved_owner:
                        query = """
                        with owner_families as (
                            select distinct docdb_family_id
                            from core_db.family_owner_bridge
                            where owner_name_harmonized = ?
                              and coalesce(is_primary_owner, false) = true
                        )
                        select
                            count(distinct of.docdb_family_id) as family_count,
                            count(distinct case when gs.family_composite_status = 'fully_active' then of.docdb_family_id end) as active_family_count,
                            count(distinct case when gs.family_composite_status = 'pending_emerging' then of.docdb_family_id end) as pending_family_count,
                            count(distinct case when gs.family_composite_status = 'under_fire' then of.docdb_family_id end) as under_fire_family_count,
                            count(distinct case when gs.family_composite_status = 'partially_lapsed' then of.docdb_family_id end) as partially_lapsed_family_count,
                            count(distinct case when gs.family_composite_status = 'dead' then of.docdb_family_id end) as dead_family_count,
                            count(distinct case when gs.family_composite_status in ('dead', 'partially_lapsed') then of.docdb_family_id end) as abandoned_family_count
                        from owner_families of
                        left join core_db.family_summary gs using (docdb_family_id)
                        """
                        rows = self._query_rows(con, query, [resolved_owner])
                        if rows:
                            return rows[0]

        with self.duckdb_provider.connect() as con:
            resolved_owner = self._resolve_owner(con, self.owner_bridge_path, owner_id)
            if not resolved_owner:
                return {}
            owner_bridge_ref = self._analytics_relation(con, self.owner_bridge_path)
            family_summary_ref = self._analytics_relation(con, self.family_summary_path)
            query = f"""
            with owner_families as (
                select distinct docdb_family_id
                from {owner_bridge_ref}
                where owner_name_harmonized = ?
                  and coalesce(is_primary_owner, false) = true
            )
            select
                count(distinct of.docdb_family_id) as family_count,
                count(distinct case when gs.family_composite_status = 'fully_active' then of.docdb_family_id end) as active_family_count,
                count(distinct case when gs.family_composite_status = 'pending_emerging' then of.docdb_family_id end) as pending_family_count,
                count(distinct case when gs.family_composite_status = 'under_fire' then of.docdb_family_id end) as under_fire_family_count,
                count(distinct case when gs.family_composite_status = 'partially_lapsed' then of.docdb_family_id end) as partially_lapsed_family_count,
                count(distinct case when gs.family_composite_status = 'dead' then of.docdb_family_id end) as dead_family_count,
                count(distinct case when gs.family_composite_status in ('dead', 'partially_lapsed') then of.docdb_family_id end) as abandoned_family_count
            from owner_families of
            left join {family_summary_ref} gs using (docdb_family_id)
            """
            rows = self._query_rows(con, query, [resolved_owner])
            return rows[0] if rows else {}

    def get_owner_in_scope_family_status_counts(self, owner_id: str) -> dict[str, object]:
        core_serving_path = self.artifact_locator.resolve_core_serving_duckdb()
        if core_serving_path is not None:
            with self.duckdb_provider.connect() as con:
                self._attach_core_serving(con, core_serving_path)
                required_tables = ["family_owner_bridge", "family_summary", "family_blocking_power"]
                if all(self._core_table_exists(con, table_name) for table_name in required_tables):
                    resolved_owner = self._resolve_owner_from_table(con, "family_owner_bridge", owner_id)
                    if resolved_owner:
                        query = """
                        with owner_families as (
                            select distinct docdb_family_id
                            from core_db.family_owner_bridge
                            where owner_name_harmonized = ?
                        ),
                        family_current as (
                            select s.docdb_family_id
                            from core_db.family_summary s
                            join core_db.family_blocking_power b using (docdb_family_id)
                        )
                        select
                            count(distinct of.docdb_family_id) as family_count,
                            count(distinct case when gs.family_composite_status = 'pending_emerging' then of.docdb_family_id end) as pending_family_count,
                            count(distinct case when gs.family_composite_status = 'fully_active' then of.docdb_family_id end) as active_family_count,
                            count(distinct case when gs.family_composite_status = 'under_fire' then of.docdb_family_id end) as under_fire_family_count,
                            count(distinct case when gs.family_composite_status = 'partially_lapsed' then of.docdb_family_id end) as partially_lapsed_family_count,
                            count(distinct case when gs.family_composite_status = 'dead' then of.docdb_family_id end) as dead_family_count
                        from owner_families of
                        join family_current fc using (docdb_family_id)
                        left join core_db.family_summary gs using (docdb_family_id)
                        """
                        rows = self._query_rows(con, query, [resolved_owner])
                        if rows:
                            return rows[0]

        with self.duckdb_provider.connect() as con:
            resolved_owner = self._resolve_owner(con, self.owner_bridge_path, owner_id)
            if not resolved_owner:
                return {}
            owner_bridge_ref = self._analytics_relation(con, self.owner_bridge_path)
            family_summary_ref = self._analytics_relation(con, self.family_summary_path)
            family_blocking_ref = self._analytics_relation(con, self.family_blocking_path)
            query = f"""
            with owner_families as (
                select distinct docdb_family_id
                from {owner_bridge_ref}
                where owner_name_harmonized = ?
            ),
            family_current as (
                select s.docdb_family_id
                from {family_summary_ref} s
                join {family_blocking_ref} b using (docdb_family_id)
            )
            select
                count(distinct of.docdb_family_id) as family_count,
                count(distinct case when gs.family_composite_status = 'pending_emerging' then of.docdb_family_id end) as pending_family_count,
                count(distinct case when gs.family_composite_status = 'fully_active' then of.docdb_family_id end) as active_family_count,
                count(distinct case when gs.family_composite_status = 'under_fire' then of.docdb_family_id end) as under_fire_family_count,
                count(distinct case when gs.family_composite_status = 'partially_lapsed' then of.docdb_family_id end) as partially_lapsed_family_count,
                count(distinct case when gs.family_composite_status = 'dead' then of.docdb_family_id end) as dead_family_count
            from owner_families of
            join family_current fc using (docdb_family_id)
            left join {family_summary_ref} gs using (docdb_family_id)
            """
            rows = self._query_rows(con, query, [resolved_owner])
            return rows[0] if rows else {}

    def get_owner_forecast_sections(self, owner_id: str, as_of_year: int | None = None) -> list[dict[str, object]]:
        core_serving_path = self.artifact_locator.resolve_core_serving_duckdb()
        if core_serving_path is not None:
            with self.duckdb_provider.connect() as con:
                self._attach_core_serving(con, core_serving_path)
                if self._core_table_exists(con, "portfolio_forecast_segments"):
                    resolved_owner = self._resolve_owner_from_table(con, "portfolio_forecast_segments", owner_id)
                    if resolved_owner:
                        query = f"""
                        select *
                        from core_db.portfolio_forecast_segments
                        where owner_name_harmonized = ?
                        {self._snapshot_year_filter(as_of_year)}
                        order by horizon, wipo_field
                        """
                        rows = self._query_rows(con, query, [resolved_owner])
                        if rows:
                            return rows

        with self.duckdb_provider.connect() as con:
            resolved_owner = self._resolve_owner(con, self.forecast_segments_path, owner_id)
            if not resolved_owner:
                return []
            forecast_segments_ref = self._analytics_relation(con, self.forecast_segments_path)
            query = f"""
            select *
            from {forecast_segments_ref}
            where owner_name_harmonized = ?
            {self._snapshot_year_filter(as_of_year)}
            order by horizon, wipo_field
            """
            return self._query_rows(con, query, [resolved_owner])

    def get_owner_families(
        self,
        owner_id: str,
        as_of_year: int | None = None,
        limit: int = 10,
        offset: int = 0,
        q: str | None = None,
        status: str | None = None,
        primary_field: str | None = None,
        sort: str | None = None,
        exclude_inactive: bool = False,
    ) -> list[dict[str, object]]:
        normalized_sort = (sort or "blocking").strip().lower()
        order_clause = (
            "forecast_contributor desc nulls last, blocking_score desc, family_id asc"
            if normalized_sort in {"forecast", "forecast_contributor"}
            else "priority_year desc nulls last, blocking_score desc nulls last, family_id asc"
            if normalized_sort in {"priority_year", "priority"}
            else "blocking_score desc nulls last, forecast_contributor desc nulls last, family_id asc"
        )
        filters = ""
        normalized_query = (q or "").strip().upper()
        if normalized_query:
            like_query = f"%{normalized_query}%"
            filters += """
              and (
                upper(cast(ob.docdb_family_id as varchar)) like ?
                or upper(coalesce(gs.primary_wipo_field, '')) like ?
                or upper(coalesce(gs.family_composite_status, '')) like ?
              )
            """
        else:
            like_query = None

        normalized_status = (status or "").strip().upper()
        if normalized_status:
            filters += " and upper(coalesce(gs.family_composite_status, '')) = ?"

        normalized_primary_field = (primary_field or "").strip().upper()
        if normalized_primary_field:
            filters += " and upper(coalesce(gs.primary_wipo_field, '')) = ?"

        if exclude_inactive:
            filters += " and coalesce(gs.family_composite_status, 'unknown') in ('fully_active', 'pending_emerging', 'under_fire', 'partially_lapsed')"

        core_serving_path = self.artifact_locator.resolve_core_serving_duckdb()
        if core_serving_path is not None:
            with self.duckdb_provider.connect() as con:
                self._attach_core_serving(con, core_serving_path)
                required_tables = [
                    "family_owner_bridge",
                    "portfolio_forecast_contributors",
                    "family_blocking_power",
                    "family_summary",
                ]
                if all(self._core_table_exists(con, table_name) for table_name in required_tables):
                    resolved_owner = self._resolve_owner_from_table(con, "family_owner_bridge", owner_id)
                    if resolved_owner:
                        parameters: list[object] = [resolved_owner, resolved_owner]
                        if like_query is not None:
                            parameters.extend([like_query, like_query, like_query])
                        if normalized_status:
                            parameters.append(normalized_status)
                        if normalized_primary_field:
                            parameters.append(normalized_primary_field)
                        parameters.extend([int(limit), int(offset)])
                        query = """
                        with contributions as (
                            select
                                contributor_entity_id as family_id,
                                coalesce(contribution_share, 0.0) as owner_weight,
                                coalesce(contribution_value, 0.0) as forecast_contributor
                            from core_db.portfolio_forecast_contributors
                            where owner_name_harmonized = ?
                              and contributor_scope = 'phase03_future_citations'
                              and horizon = '3y'
                        ),
                        base as (
                            select
                                cast(ob.docdb_family_id as varchar) as family_id,
                                coalesce(c.owner_weight, 0.0) as owner_weight,
                                coalesce(fb.family_ui_blocking_power_score, 0.0) as blocking_score,
                                coalesce(gs.family_composite_status, 'unknown') as status,
                                cast(gs.family_priority_year as integer) as priority_year,
                                coalesce(cast(gs.family_priority_year as varchar), 'unknown') as heritage,
                                coalesce(gs.primary_wipo_field, 'unknown') as primary_field,
                                c.forecast_contributor
                            from core_db.family_owner_bridge ob
                                left join contributions c
                                    on c.family_id = cast(ob.docdb_family_id as varchar)
                                left join core_db.family_blocking_power fb using (docdb_family_id)
                                left join core_db.family_summary gs using (docdb_family_id)
                                where ob.owner_name_harmonized = ?
                                  and coalesce(ob.is_primary_owner, false) = true
                                  """ + filters + """
                        )
                        select
                            *,
                            count(*) over () as total_count
                        from base
                        order by """ + order_clause + """
                        limit ?
                        offset ?
                        """
                        rows = self._query_rows(con, query, parameters)
                        if rows:
                            return rows

        with self.duckdb_provider.connect() as con:
            resolved_owner = self._resolve_owner(con, self.owner_bridge_path, owner_id)
            if not resolved_owner:
                return []
            forecast_contributors_ref = self._analytics_relation(con, self.forecast_contributors_path)
            owner_bridge_ref = self._analytics_relation(con, self.owner_bridge_path)
            family_blocking_ref = self._analytics_relation(con, self.family_blocking_path)
            family_summary_ref = self._analytics_relation(con, self.family_summary_path)
            parameters = [resolved_owner, resolved_owner]
            if like_query is not None:
                parameters.extend([like_query, like_query, like_query])
            if normalized_status:
                parameters.append(normalized_status)
            if normalized_primary_field:
                parameters.append(normalized_primary_field)
            parameters.extend([int(limit), int(offset)])
            query = f"""
            with contributions as (
                select
                    contributor_entity_id as family_id,
                    coalesce(contribution_share, 0.0) as owner_weight,
                    coalesce(contribution_value, 0.0) as forecast_contributor
                from {forecast_contributors_ref}
                where owner_name_harmonized = ?
                  and contributor_scope = 'phase03_future_citations'
                  and horizon = '3y'
            ),
            base as (
                select
                    cast(ob.docdb_family_id as varchar) as family_id,
                    coalesce(c.owner_weight, 0.0) as owner_weight,
                    coalesce(fb.family_ui_blocking_power_score, 0.0) as blocking_score,
                    coalesce(gs.family_composite_status, 'unknown') as status,
                    cast(gs.family_priority_year as integer) as priority_year,
                    coalesce(cast(gs.family_priority_year as varchar), 'unknown') as heritage,
                    coalesce(gs.primary_wipo_field, 'unknown') as primary_field,
                    c.forecast_contributor
                from {owner_bridge_ref} ob
                left join contributions c
                    on c.family_id = cast(ob.docdb_family_id as varchar)
                left join {family_blocking_ref} fb using (docdb_family_id)
                left join {family_summary_ref} gs using (docdb_family_id)
                where ob.owner_name_harmonized = ?
                  and coalesce(ob.is_primary_owner, false) = true
                  {filters}
            )
            select
                *,
                count(*) over () as total_count
            from base
            order by {order_clause}
            limit ?
            offset ?
            """
            return self._query_rows(con, query, parameters)

    def get_owner_fields(self, owner_id: str, as_of_year: int | None = None, limit: int = 30) -> list[dict[str, object]]:
        core_serving_path = self.artifact_locator.resolve_core_serving_duckdb()
        if core_serving_path is not None:
            with self.duckdb_provider.connect() as con:
                self._attach_core_serving(con, core_serving_path)
                if self._core_table_exists(con, "portfolio_forecast_segments"):
                    resolved_owner = self._resolve_owner_from_table(con, "portfolio_forecast_segments", owner_id)
                    if resolved_owner:
                        query = f"""
                        select
                            wipo_field as field,
                            portfolio_active_family_count_in_field as active_families,
                            portfolio_active_family_count_in_field / nullif(sum(portfolio_active_family_count_in_field) over (), 0.0) as active_share,
                            case
                                when predicted_direction_band = 'heating' then 'gains'
                                when predicted_direction_band = 'cooling' then 'losses'
                                else 'stable'
                            end as hotspot_direction,
                            coalesce(predicted_growth_rate_reference, 0.0) as change_12m,
                            support_level as confidence
                        from core_db.portfolio_forecast_segments
                        where owner_name_harmonized = ?
                          and horizon = '3y'
                          {self._snapshot_year_filter(as_of_year)}
                          and wipo_field is not null
                          and coalesce(portfolio_active_family_count_in_field, 0) > 0
                        qualify row_number() over (
                            partition by horizon
                            order by portfolio_active_family_count_in_field desc
                        ) <= {int(limit)}
                        order by portfolio_active_family_count_in_field desc
                        """
                        rows = self._query_rows(con, query, [resolved_owner])
                        if rows:
                            return rows

        with self.duckdb_provider.connect() as con:
            resolved_owner = self._resolve_owner(con, self.forecast_segments_path, owner_id)
            if not resolved_owner:
                return []
            forecast_segments_ref = self._analytics_relation(con, self.forecast_segments_path)
            field_timeseries_ref = self._analytics_relation(con, self.field_timeseries_path)
            query = f"""
            select
                wipo_field as field,
                portfolio_active_family_count_in_field as active_families,
                portfolio_active_family_count_in_field / nullif(sum(portfolio_active_family_count_in_field) over (), 0.0) as active_share,
                case
                    when predicted_direction_band = 'heating' then 'gains'
                    when predicted_direction_band = 'cooling' then 'losses'
                    else 'stable'
                end as hotspot_direction,
                coalesce(predicted_growth_rate_reference, 0.0) as change_12m,
                support_level as confidence
            from {forecast_segments_ref}
            where owner_name_harmonized = ?
              and horizon = '3y'
              {self._snapshot_year_filter(as_of_year)}
              and wipo_field is not null
              and coalesce(portfolio_active_family_count_in_field, 0) > 0
            qualify row_number() over (
                partition by horizon
                order by portfolio_active_family_count_in_field desc
            ) <= {int(limit)}
            order by portfolio_active_family_count_in_field desc
            """
            rows = self._query_rows(con, query, [resolved_owner])
            if rows:
                return rows

            fallback_query = f"""
            select
                wipo_field as field,
                active_family_count as active_families,
                active_family_count / nullif(sum(active_family_count) over (), 0.0) as active_share,
                'stable' as hotspot_direction,
                0.0 as change_12m,
                'moderate' as confidence
            from {field_timeseries_ref}
            where owner_name_harmonized = ?
              and wipo_field is not null
              and coalesce(active_family_count, 0) > 0
              {self._snapshot_year_filter(as_of_year)}
            qualify row_number() over (
                partition by wipo_field
                order by snapshot_date desc
            ) = 1
            order by active_family_count desc
            limit ?
            """
            return self._query_rows(con, fallback_query, [resolved_owner, int(limit)])

    def get_owner_field_timeseries(
        self,
        owner_id: str,
        as_of_year: int | None = None,
        limit_fields: int = 8,
    ) -> list[dict[str, object]]:
        with DuckDbProvider().connect() as con:
            resolved_owner = self._resolve_owner(con, self.field_timeseries_path, owner_id)
            if not resolved_owner:
                return []
            field_timeseries_ref = self._analytics_relation(con, self.field_timeseries_path)
            query = f"""
            with scoped as (
                select *
                from {field_timeseries_ref}
                where owner_name_harmonized = ?
                  and wipo_field is not null
                  {self._snapshot_year_filter(as_of_year)}
            ),
            latest_snapshot as (
                select max(snapshot_date) as snapshot_date
                from scoped
            ),
            top_fields as (
                select wipo_field
                from scoped
                where snapshot_date = (select snapshot_date from latest_snapshot)
                qualify row_number() over (
                    order by active_family_count desc nulls last, wipo_field asc
                ) <= {int(limit_fields)}
            ),
            with_totals as (
                select
                    s.snapshot_date,
                    s.wipo_field,
                    cast(coalesce(s.active_family_count, 0) as bigint) as active_family_count,
                    cast(coalesce(s.enforceability_score, 0.0) as double) as enforceability_score,
                    cast(coalesce(s.heritage_score, 0.0) as double) as heritage_score,
                    cast(coalesce(s.active_family_count, 0) as double)
                      / nullif(sum(coalesce(s.active_family_count, 0)) over (partition by s.snapshot_date), 0.0) as active_share
                from scoped s
                join top_fields tf on s.wipo_field = tf.wipo_field
            )
            select *
            from with_totals
            order by wipo_field asc, snapshot_date asc
            """
            return self._query_rows(con, query, [resolved_owner])

    def get_owner_citation_summary(
        self,
        owner_id: str,
        as_of_year: int | None = None,
    ) -> dict[str, object]:
        with DuckDbProvider().connect() as con:
            resolved_owner = self._resolve_owner(con, self.owner_bridge_path, owner_id)
            if not resolved_owner:
                return {}
            citation_pit_path = self._citation_pit_path()
            citation_pit_observed_filter = self._citation_pit_observed_filter("fs")
            summary_fast_path_ready = self._analytics_source_available(self.portfolio_citation_summary_path) and self._parquet_has_columns(
                con,
                self.portfolio_citation_summary_path,
                [
                    "distinct_citing_family_count",
                    "distinct_cited_family_count",
                    "avg_out_of_bounds_citation_share",
                ],
            )
            owner_bridge_ref = self._analytics_relation(con, self.owner_bridge_path)
            citation_pit_ref = self._analytics_relation(con, citation_pit_path)
            citation_summary_ref = self._analytics_relation(con, self.portfolio_citation_summary_path)
            citation_network_ref = self._analytics_relation(con, self.enriched_citation_network_path)
            family_citation_metrics_ref = self._analytics_relation(con, self.family_citation_metrics_path)
            family_summary_ref = self._analytics_relation(con, self.family_summary_path)
            if summary_fast_path_ready:
                query = f"""
                with base as (
                    select *
                    from {citation_summary_ref}
                    where owner_name_harmonized = ?
                ),
                selected_year as (
                    select cast(coalesce(?, (select max(as_of_year) from base)) as integer) as as_of_year
                )
                select *
                from base
                where as_of_year = (select as_of_year from selected_year)
                order by current_snapshot_date desc
                limit 1
                """
                rows = self._query_rows(con, query, [resolved_owner, as_of_year])
                return rows[0] if rows else {}
            query = f"""
            with owner_families as (
                select distinct docdb_family_id
                from {owner_bridge_ref}
                where owner_name_harmonized = ?
                  and coalesce(is_primary_owner, false) = true
            ),
            latest_year as (
                select max(as_of_year) as as_of_year
                from {citation_pit_ref} fs
                join owner_families of using (docdb_family_id)
                where true
                  {citation_pit_observed_filter}
            ),
            selected_year as (
                select cast(coalesce(?, (select as_of_year from latest_year)) as integer) as as_of_year
            ),
            scope_families as (
                select distinct fs.docdb_family_id
                from {citation_pit_ref} fs
                join owner_families of using (docdb_family_id)
                where fs.as_of_year = (select as_of_year from selected_year)
                  {citation_pit_observed_filter}
            ),
            pit as (
                select
                    fs.docdb_family_id,
                    cast(coalesce(fs.pre_asof_unique_citing_family_count, 0.0) as double) as pre_asof_unique_citing_family_count,
                    cast(coalesce(fs.pre_asof_citing_assignee_diversity, 0.0) as double) as pre_asof_citing_assignee_diversity,
                    cast(coalesce(fs.pre_asof_attacker_density_score, 0.0) as double) as pre_asof_attacker_density_score
                from {citation_pit_ref} fs
                join scope_families sf using (docdb_family_id)
                where fs.as_of_year = (select as_of_year from selected_year)
            ),
            exact_forward as (
                select
                    count(*)::bigint as forward_citations_clean_total,
                    cast(coalesce(sum(n.clean_edge_weight), 0.0) as double) as forward_citations_weighted_total,
                    count(distinct n.source_docdb_family_id)::bigint as distinct_citing_family_count
                from {citation_network_ref} n
                join scope_families sf
                  on n.cited_docdb_family_id = sf.docdb_family_id
                where not coalesce(n.is_out_of_bounds, false)
                  and not coalesce(n.is_intra_family_citation, false)
                  and not coalesce(n.is_self_citation, false)
                  and cast(coalesce(n.citation_year, 0) as integer) <= (select as_of_year from selected_year)
            ),
            exact_backward as (
                select
                    count(*)::bigint as backward_citations_clean_total,
                    count(distinct n.cited_docdb_family_id)::bigint as distinct_cited_family_count
                from {citation_network_ref} n
                join scope_families sf
                  on n.source_docdb_family_id = sf.docdb_family_id
                where n.cited_docdb_family_id is not null
                  and not coalesce(n.is_out_of_bounds, false)
                  and not coalesce(n.is_intra_family_citation, false)
                  and not coalesce(n.is_self_citation, false)
                  and cast(coalesce(n.citation_year, 0) as integer) <= (select as_of_year from selected_year)
            ),
            current_agg as (
                select
                    cast(coalesce(sum(cm.family_backward_npl_citation_count), 0.0) as double) as backward_npl_citation_total,
                    cast(coalesce(avg(cm.family_science_grounding_score), 0.0) as double) as avg_science_grounding_score,
                    cast(coalesce(avg(gs.family_generality_percentile), 0.0) as double) as avg_generality_percentile,
                    cast(coalesce(avg(gs.family_originality_percentile), 0.0) as double) as avg_originality_percentile,
                    cast(coalesce(avg(cm.out_of_bounds_citation_share), 0.0) as double) as avg_out_of_bounds_citation_share
                from scope_families sf
                left join {family_citation_metrics_ref} cm using (docdb_family_id)
                left join {family_summary_ref} gs using (docdb_family_id)
            )
            select
                (select as_of_year from selected_year) as as_of_year,
                count(distinct sf.docdb_family_id) as family_count,
                cast(coalesce((select forward_citations_clean_total from exact_forward), 0) as double) as forward_citations_clean_total,
                cast(coalesce((select forward_citations_weighted_total from exact_forward), 0.0) as double) as forward_citations_weighted_total,
                cast(coalesce((select backward_citations_clean_total from exact_backward), 0) as double) as backward_citations_clean_total,
                cast(coalesce((select backward_npl_citation_total from current_agg), 0.0) as double) as backward_npl_citation_total,
                cast(coalesce((select distinct_citing_family_count from exact_forward), 0) as bigint) as distinct_citing_family_count,
                cast(coalesce((select distinct_cited_family_count from exact_backward), 0) as bigint) as distinct_cited_family_count,
                cast(coalesce((select avg_science_grounding_score from current_agg), 0.0) as double) as avg_science_grounding_score,
                cast(coalesce((select avg_generality_percentile from current_agg), 0.0) as double) as avg_generality_percentile,
                cast(coalesce((select avg_originality_percentile from current_agg), 0.0) as double) as avg_originality_percentile,
                cast(coalesce(avg(pit.pre_asof_unique_citing_family_count), 0.0) as double) as avg_unique_citing_family_count,
                cast(coalesce(avg(pit.pre_asof_citing_assignee_diversity), 0.0) as double) as avg_citing_assignee_diversity,
                cast(coalesce(avg(pit.pre_asof_attacker_density_score), 0.0) as double) as avg_attacker_density_score,
                cast(coalesce((select avg_out_of_bounds_citation_share from current_agg), 0.0) as double) as avg_out_of_bounds_citation_share
            from scope_families sf
            left join pit using (docdb_family_id)
            """
            rows = self._query_rows(con, query, [resolved_owner, as_of_year])
            return rows[0] if rows else {}

    def get_owner_citation_timeseries(
        self,
        owner_id: str,
        year_from: int | None = None,
        year_to: int | None = None,
    ) -> list[dict[str, object]]:
        with DuckDbProvider().connect() as con:
            resolved_owner = self._resolve_owner(con, self.owner_bridge_path, owner_id)
            if not resolved_owner:
                return []
            citation_pit_path = self._citation_pit_path()
            citation_pit_observed_filter = self._citation_pit_observed_filter("fs")
            timeseries_fast_path_ready = self._analytics_source_available(self.portfolio_citation_timeseries_path) and self._parquet_has_columns(
                con,
                self.portfolio_citation_timeseries_path,
                [
                    "distinct_citing_family_count",
                    "backward_citations_clean_total",
                    "distinct_cited_family_count",
                    "avg_citation_data_completeness_pct",
                    "citation_support_level",
                ],
            )
            owner_bridge_ref = self._analytics_relation(con, self.owner_bridge_path)
            citation_pit_ref = self._analytics_relation(con, citation_pit_path)
            citation_timeseries_ref = self._analytics_relation(con, self.portfolio_citation_timeseries_path)
            citation_network_ref = self._analytics_relation(con, self.enriched_citation_network_path)
            if timeseries_fast_path_ready:
                filters = ""
                parameters: list[object] = [resolved_owner]
                if year_from is not None:
                    filters += " and as_of_year >= ?"
                    parameters.append(int(year_from))
                if year_to is not None:
                    filters += " and as_of_year <= ?"
                    parameters.append(int(year_to))
                query = f"""
                select *
                from {citation_timeseries_ref}
                where owner_name_harmonized = ?
                {filters}
                order by as_of_year asc
                """
                return self._query_rows(con, query, parameters)
            filters = ""
            parameters: list[object] = [resolved_owner]
            if year_from is not None:
                filters += " and fs.as_of_year >= ?"
                parameters.append(int(year_from))
            if year_to is not None:
                filters += " and fs.as_of_year <= ?"
                parameters.append(int(year_to))
            query = f"""
            with owner_families as (
                select distinct docdb_family_id
                from {owner_bridge_ref}
                where owner_name_harmonized = ?
                  and coalesce(is_primary_owner, false) = true
            ),
            pit as (
                select
                    cast(fs.as_of_year as integer) as as_of_year,
                    fs.docdb_family_id,
                    cast(coalesce(fs.pre_asof_forward_citations_weighted, 0.0) as double) as pre_asof_forward_citations_weighted,
                    cast(coalesce(fs.pre_asof_unique_citing_family_count, 0.0) as double) as pre_asof_unique_citing_family_count,
                    cast(coalesce(fs.pre_asof_citing_assignee_diversity, 0.0) as double) as pre_asof_citing_assignee_diversity,
                    cast(coalesce(fs.pre_asof_attacker_density_score, 0.0) as double) as pre_asof_attacker_density_score
                from {citation_pit_ref} fs
                join owner_families of using (docdb_family_id)
                where true
                  {citation_pit_observed_filter}
                  {filters}
            ),
            pit_agg as (
                select
                    as_of_year,
                    count(distinct docdb_family_id) as family_count,
                    cast(coalesce(sum(pre_asof_forward_citations_weighted), 0.0) as double) as forward_citations_weighted_total,
                    cast(coalesce(avg(pre_asof_unique_citing_family_count), 0.0) as double) as avg_unique_citing_family_count,
                    cast(coalesce(avg(pre_asof_citing_assignee_diversity), 0.0) as double) as avg_citing_assignee_diversity,
                    cast(coalesce(avg(pre_asof_attacker_density_score), 0.0) as double) as avg_attacker_density_score
                from pit
                group by as_of_year
            ),
            exact_forward as (
                select
                    p.as_of_year,
                    count(*)::bigint as forward_citations_clean_total
                from pit p
                join {citation_network_ref} n
                  on n.cited_docdb_family_id = p.docdb_family_id
                where not coalesce(n.is_out_of_bounds, false)
                  and not coalesce(n.is_intra_family_citation, false)
                  and not coalesce(n.is_self_citation, false)
                  and cast(coalesce(n.citation_year, 0) as integer) <= p.as_of_year
                group by p.as_of_year
            )
            select
                pit_agg.as_of_year,
                pit_agg.family_count,
                cast(coalesce(exact_forward.forward_citations_clean_total, 0) as double) as forward_citations_clean_total,
                pit_agg.forward_citations_weighted_total,
                pit_agg.avg_unique_citing_family_count,
                pit_agg.avg_citing_assignee_diversity,
                pit_agg.avg_attacker_density_score
            from pit_agg
            left join exact_forward using (as_of_year)
            order by pit_agg.as_of_year asc
            """
            return self._query_rows(con, query, parameters)

    def get_owner_citation_families(
        self,
        owner_id: str,
        limit: int = 10,
        offset: int = 0,
        wipo_field: str | None = None,
        status: str | None = None,
        sort: str | None = None,
    ) -> list[dict[str, object]]:
        sort_column = self._citation_family_sort_column(sort)
        with DuckDbProvider().connect() as con:
            resolved_owner = self._resolve_owner(con, self.owner_bridge_path, owner_id)
            if not resolved_owner:
                return []
            filters = ""
            parameters: list[object] = [resolved_owner]
            normalized_wipo_field = (wipo_field or "").strip().upper()
            if normalized_wipo_field:
                filters += " and upper(coalesce(primary_field, '')) = ?"
                parameters.append(normalized_wipo_field)
            normalized_status = (status or "").strip().upper()
            if normalized_status:
                filters += " and upper(coalesce(status, '')) = ?"
                parameters.append(normalized_status)
            parameters.extend([int(limit), int(offset)])
            core_serving_path = self.artifact_locator.resolve_core_serving_duckdb()
            if core_serving_path is not None and core_serving_path.exists():
                self._attach_core_serving(con, core_serving_path)
                if self._core_table_exists(con, "portfolio_citation_family_leaderboard"):
                    query = f"""
                    with base as (
                        select
                            cast(docdb_family_id as varchar) as family_id,
                            cast(coalesce(family_priority_year, 0) as integer) as family_priority_year,
                            coalesce(primary_wipo_field, 'unknown') as primary_field,
                            coalesce(family_composite_status, 'unknown') as status,
                            cast(coalesce(family_forward_citations_clean, 0.0) as double) as forward_citations_clean,
                            cast(coalesce(family_forward_citations_weighted_raw, 0.0) as double) as forward_citations_weighted,
                            cast(coalesce(family_fwd_cits5, 0.0) as double) as early_citations_5y,
                            cast(coalesce(family_fwd_cits7, 0.0) as double) as early_citations_7y,
                            cast(coalesce(unique_citing_family_count, 0.0) as double) as unique_citing_family_count,
                            cast(coalesce(citing_assignee_diversity, 0.0) as double) as citing_assignee_diversity,
                            cast(coalesce(family_ui_blocking_power_score, 0.0) as double) as blocking_score
                        from core_db.portfolio_citation_family_leaderboard
                        where owner_name_harmonized = ?
                    )
                    select
                        *,
                        count(*) over () as total_count
                    from base
                    where true
                    {filters}
                    order by {sort_column} desc nulls last, forward_citations_clean desc nulls last, family_id asc
                    limit ?
                    offset ?
                    """
                    rows = self._query_rows(con, query, parameters)
                    if rows:
                        return rows
            citation_family_ref = self._analytics_relation(con, self.portfolio_citation_family_leaderboard_path)
            family_owner_bridge_ref = self._analytics_relation(con, self.owner_bridge_path)
            family_citation_summary_ref = self._analytics_relation(con, self.family_citation_summary_path)
            family_citation_metrics_ref = self._analytics_relation(con, self.family_citation_metrics_path)
            family_summary_ref = self._analytics_relation(con, self.family_summary_path)
            family_blocking_ref = self._analytics_relation(con, self.family_blocking_path)
            if self._analytics_source_available(self.portfolio_citation_family_leaderboard_path):
                query = f"""
                with base as (
                    select
                        cast(docdb_family_id as varchar) as family_id,
                        cast(coalesce(family_priority_year, 0) as integer) as family_priority_year,
                        coalesce(primary_wipo_field, 'unknown') as primary_field,
                        coalesce(family_composite_status, 'unknown') as status,
                        cast(coalesce(family_forward_citations_clean, 0.0) as double) as forward_citations_clean,
                        cast(coalesce(family_forward_citations_weighted_raw, 0.0) as double) as forward_citations_weighted,
                        cast(coalesce(family_fwd_cits5, 0.0) as double) as early_citations_5y,
                        cast(coalesce(family_fwd_cits7, 0.0) as double) as early_citations_7y,
                        cast(coalesce(unique_citing_family_count, 0.0) as double) as unique_citing_family_count,
                        cast(coalesce(citing_assignee_diversity, 0.0) as double) as citing_assignee_diversity,
                        cast(coalesce(family_ui_blocking_power_score, 0.0) as double) as blocking_score
                    from {citation_family_ref}
                    where owner_name_harmonized = ?
                )
                select
                    *,
                    count(*) over () as total_count
                from base
                where true
                {filters}
                order by {sort_column} desc nulls last, forward_citations_clean desc nulls last, family_id asc
                limit ?
                offset ?
                """
                rows = self._query_rows(con, query, parameters)
                if rows:
                    return rows
            query = f"""
            with owner_families as (
                select distinct docdb_family_id
                from {family_owner_bridge_ref}
                where owner_name_harmonized = ?
                  and coalesce(is_primary_owner, false) = true
            ),
            base as (
                select
                    cast(of.docdb_family_id as varchar) as family_id,
                    cast(coalesce(gs.family_priority_year, 0) as integer) as family_priority_year,
                    coalesce(gs.primary_wipo_field, 'unknown') as primary_field,
                    coalesce(gs.family_composite_status, 'unknown') as status,
                    cast(coalesce(fcs.family_forward_citations_clean, cm.family_forward_citations_clean, 0.0) as double) as forward_citations_clean,
                    cast(coalesce(fcs.family_forward_citations_weighted_raw, cm.family_forward_citations_weighted, 0.0) as double) as forward_citations_weighted,
                    cast(coalesce(cm.family_fwd_cits5, 0.0) as double) as early_citations_5y,
                    cast(coalesce(cm.family_fwd_cits7, 0.0) as double) as early_citations_7y,
                    cast(0.0 as double) as unique_citing_family_count,
                    cast(coalesce(fcs.citing_assignee_diversity, 0.0) as double) as citing_assignee_diversity,
                    cast(coalesce(fb.family_ui_blocking_power_score, 0.0) as double) as blocking_score
                from owner_families of
                left join {family_citation_summary_ref} fcs using (docdb_family_id)
                left join {family_citation_metrics_ref} cm using (docdb_family_id)
                left join {family_summary_ref} gs using (docdb_family_id)
                left join {family_blocking_ref} fb using (docdb_family_id)
            )
            select
                *,
                count(*) over () as total_count
            from base
            where true
            {filters}
            order by {sort_column} desc nulls last, forward_citations_clean desc nulls last, family_id asc
            limit ?
            offset ?
            """
            return self._query_rows(con, query, parameters)

    def get_owner_filing_timeseries(
        self,
        owner_id: str,
        year_from: int | None = None,
        year_to: int | None = None,
    ) -> list[dict[str, object]]:
        with DuckDbProvider().connect() as con:
            filters = ""
            core_serving_path = self.artifact_locator.resolve_core_serving_duckdb()
            if core_serving_path is not None and core_serving_path.exists():
                self._attach_core_serving(con, core_serving_path)
                if self._core_table_exists(con, "portfolio_filing_timeseries"):
                    resolved_owner = self._resolve_owner_from_table(con, "portfolio_filing_timeseries", owner_id)
                    if resolved_owner:
                        parameters: list[object] = [resolved_owner]
                        if year_from is not None:
                            filters += " and filing_year >= ?"
                            parameters.append(int(year_from))
                        if year_to is not None:
                            filters += " and filing_year <= ?"
                            parameters.append(int(year_to))
                        query = f"""
                        select
                            cast(filing_year as integer) as filing_year,
                            cast(family_filing_count as bigint) as family_filing_count,
                            cast(cumulative_family_count as bigint) as cumulative_family_count,
                            cast(rolling_3y_family_filing_count as bigint) as rolling_3y_family_filing_count,
                            cast(coalesce(prior_3y_family_filing_count, 0) as bigint) as prior_3y_family_filing_count,
                            cast(coalesce(rolling_3y_change_pct, 0.0) as double) as rolling_3y_change_pct,
                            cast(momentum_direction as varchar) as momentum_direction
                        from core_db.portfolio_filing_timeseries
                        where owner_name_harmonized = ?
                        {filters}
                        order by filing_year asc
                        """
                        rows = self._query_rows(con, query, parameters)
                        if rows:
                            return rows
                        filters = ""
                required_tables = ["family_owner_bridge", "family_summary", "family_blocking_power"]
                if all(self._core_table_exists(con, table_name) for table_name in required_tables):
                    resolved_owner = self._resolve_owner_from_table(con, "family_owner_bridge", owner_id)
                    if not resolved_owner:
                        return []
                    parameters: list[object] = [resolved_owner]
                    if year_from is not None:
                        filters += " and filing_year >= ?"
                        parameters.append(int(year_from))
                    if year_to is not None:
                        filters += " and filing_year <= ?"
                        parameters.append(int(year_to))
                    query = f"""
                    with owner_families as (
                        select distinct docdb_family_id
                        from core_db.family_owner_bridge
                        where owner_name_harmonized = ?
                    ),
                    family_current as (
                        select s.docdb_family_id
                        from core_db.family_summary s
                        join core_db.family_blocking_power b using (docdb_family_id)
                    ),
                    yearly as (
                        select
                            cast(gs.family_priority_year as integer) as filing_year,
                            count(distinct of.docdb_family_id) as family_filing_count
                        from owner_families of
                        join family_current fc using (docdb_family_id)
                        join core_db.family_summary gs using (docdb_family_id)
                        where cast(coalesce(gs.family_priority_year, 0) as integer) > 0
                        group by cast(gs.family_priority_year as integer)
                    ),
                    windows as (
                        select
                            filing_year,
                            family_filing_count,
                            sum(family_filing_count) over (
                                order by filing_year
                                rows between unbounded preceding and current row
                            ) as cumulative_family_count,
                            sum(family_filing_count) over (
                                order by filing_year
                                rows between 2 preceding and current row
                            ) as rolling_3y_family_filing_count,
                            sum(family_filing_count) over (
                                order by filing_year
                                rows between 5 preceding and 3 preceding
                            ) as prior_3y_family_filing_count
                        from yearly
                    )
                    select
                        cast(filing_year as integer) as filing_year,
                        cast(family_filing_count as bigint) as family_filing_count,
                        cast(cumulative_family_count as bigint) as cumulative_family_count,
                        cast(rolling_3y_family_filing_count as bigint) as rolling_3y_family_filing_count,
                        cast(coalesce(prior_3y_family_filing_count, 0) as bigint) as prior_3y_family_filing_count,
                        cast(
                            case
                                when coalesce(prior_3y_family_filing_count, 0) <= 0 and rolling_3y_family_filing_count > 0 then 1.0
                                when coalesce(prior_3y_family_filing_count, 0) <= 0 then 0.0
                                else (rolling_3y_family_filing_count - prior_3y_family_filing_count) / cast(prior_3y_family_filing_count as double)
                            end
                        as double) as rolling_3y_change_pct,
                        case
                            when coalesce(prior_3y_family_filing_count, 0) <= 0 and rolling_3y_family_filing_count > 0 then 'accelerating'
                            when (
                                case
                                    when coalesce(prior_3y_family_filing_count, 0) <= 0 then 0.0
                                    else (rolling_3y_family_filing_count - prior_3y_family_filing_count) / cast(prior_3y_family_filing_count as double)
                                end
                            ) >= 0.20 then 'accelerating'
                            when (
                                case
                                    when coalesce(prior_3y_family_filing_count, 0) <= 0 then 0.0
                                    else (rolling_3y_family_filing_count - prior_3y_family_filing_count) / cast(prior_3y_family_filing_count as double)
                                end
                            ) <= -0.20 then 'cooling'
                            else 'stable'
                        end as momentum_direction
                    from windows
                    where true
                    {filters}
                    order by filing_year asc
                    """
                    rows = self._query_rows(con, query, parameters)
                    if rows:
                        return rows
            resolved_owner = self._resolve_owner(con, self.owner_bridge_path, owner_id)
            if not resolved_owner:
                return []
            owner_bridge_ref = self._analytics_relation(con, self.owner_bridge_path)
            family_summary_ref = self._analytics_relation(con, self.family_summary_path)
            family_blocking_ref = self._analytics_relation(con, self.family_blocking_path)
            filters = ""
            parameters = [resolved_owner]
            if year_from is not None:
                filters += " and filing_year >= ?"
                parameters.append(int(year_from))
            if year_to is not None:
                filters += " and filing_year <= ?"
                parameters.append(int(year_to))
            query = f"""
            with owner_families as (
                select distinct docdb_family_id
                from {owner_bridge_ref}
                where owner_name_harmonized = ?
            ),
            family_current as (
                select s.docdb_family_id
                from {family_summary_ref} s
                join {family_blocking_ref} b using (docdb_family_id)
            ),
            yearly as (
                select
                    cast(gs.family_priority_year as integer) as filing_year,
                    count(distinct of.docdb_family_id) as family_filing_count
                from owner_families of
                join family_current fc using (docdb_family_id)
                join {family_summary_ref} gs using (docdb_family_id)
                where cast(coalesce(gs.family_priority_year, 0) as integer) > 0
                group by cast(gs.family_priority_year as integer)
            ),
            windows as (
                select
                    filing_year,
                    family_filing_count,
                    sum(family_filing_count) over (
                        order by filing_year
                        rows between unbounded preceding and current row
                    ) as cumulative_family_count,
                    sum(family_filing_count) over (
                        order by filing_year
                        rows between 2 preceding and current row
                    ) as rolling_3y_family_filing_count,
                    sum(family_filing_count) over (
                        order by filing_year
                        rows between 5 preceding and 3 preceding
                    ) as prior_3y_family_filing_count
                from yearly
            )
            select
                cast(filing_year as integer) as filing_year,
                cast(family_filing_count as bigint) as family_filing_count,
                cast(cumulative_family_count as bigint) as cumulative_family_count,
                cast(rolling_3y_family_filing_count as bigint) as rolling_3y_family_filing_count,
                cast(coalesce(prior_3y_family_filing_count, 0) as bigint) as prior_3y_family_filing_count,
                cast(
                    case
                        when coalesce(prior_3y_family_filing_count, 0) <= 0 and rolling_3y_family_filing_count > 0 then 1.0
                        when coalesce(prior_3y_family_filing_count, 0) <= 0 then 0.0
                        else (rolling_3y_family_filing_count - prior_3y_family_filing_count) / cast(prior_3y_family_filing_count as double)
                    end
                as double) as rolling_3y_change_pct,
                case
                    when coalesce(prior_3y_family_filing_count, 0) <= 0 and rolling_3y_family_filing_count > 0 then 'accelerating'
                    when (
                        case
                            when coalesce(prior_3y_family_filing_count, 0) <= 0 then 0.0
                            else (rolling_3y_family_filing_count - prior_3y_family_filing_count) / cast(prior_3y_family_filing_count as double)
                        end
                    ) >= 0.20 then 'accelerating'
                    when (
                        case
                            when coalesce(prior_3y_family_filing_count, 0) <= 0 then 0.0
                            else (rolling_3y_family_filing_count - prior_3y_family_filing_count) / cast(prior_3y_family_filing_count as double)
                        end
                    ) <= -0.20 then 'cooling'
                    else 'stable'
                end as momentum_direction
            from windows
            where true
            {filters}
            order by filing_year asc
            """
            return self._query_rows(con, query, parameters)

    def get_owner_status_timeseries(
        self,
        owner_id: str,
        year_from: int | None = None,
        year_to: int | None = None,
    ) -> list[dict[str, object]]:
        required_paths = [
            self.family_compare_path,
            self.owner_bridge_path,
            self.family_summary_path,
            self.family_blocking_path,
        ]
        if any(not self._analytics_source_available(path) for path in required_paths):
            return []
        with DuckDbProvider().connect() as con:
            resolved_owner = self._resolve_owner(con, self.owner_bridge_path, owner_id)
            if not resolved_owner:
                return []
            owner_bridge_ref = self._analytics_relation(con, self.owner_bridge_path)
            family_summary_ref = self._analytics_relation(con, self.family_summary_path)
            family_blocking_ref = self._analytics_relation(con, self.family_blocking_path)
            family_compare_ref = self._analytics_relation(con, self.family_compare_path)
            filters = ""
            parameters: list[object] = [resolved_owner]
            if year_from is not None:
                filters += " and as_of_year >= ?"
                parameters.append(int(year_from))
            if year_to is not None:
                filters += " and as_of_year <= ?"
                parameters.append(int(year_to))
            query = f"""
            with owner_families as (
                select distinct docdb_family_id
                from {owner_bridge_ref}
                where owner_name_harmonized = ?
            ),
            family_current as (
                select s.docdb_family_id
                from {family_summary_ref} s
                join {family_blocking_ref} b using (docdb_family_id)
            ),
            scoped as (
                select fc.*
                from {family_compare_ref} fc
                join owner_families of using (docdb_family_id)
                join family_current using (docdb_family_id)
                where true
                  and coalesce(historical_compare_safe, false) = true
                  {filters}
            )
            select
                cast(as_of_year as integer) as as_of_year,
                max(current_snapshot_date) as current_snapshot_date,
                count(*) as family_count,
                sum(case when family_composite_status_asof = 'pending_emerging' then 1 else 0 end) as pending_family_count,
                sum(case when family_composite_status_asof = 'fully_active' then 1 else 0 end) as fully_active_family_count,
                sum(case when family_composite_status_asof = 'under_fire' then 1 else 0 end) as under_fire_family_count,
                sum(case when family_composite_status_asof = 'partially_lapsed' then 1 else 0 end) as partially_lapsed_family_count,
                sum(case when family_composite_status_asof = 'dead' then 1 else 0 end) as dead_family_count,
                cast(round(avg(case when family_composite_status_asof is not null then 1.0 else 0.0 end), 6) as double) as status_coverage_pct,
                cast(
                    round(
                        avg(
                            case
                                when trim(coalesce(owner_name_harmonized_current, '')) not in ('', '_', 'UNKNOWN', 'UNKNOWN_OWNER', 'UNASSIGNED') then 1.0
                                else 0.0
                            end
                        ),
                        6
                    ) as double
                ) as owner_identity_coverage_pct,
                cast(round(avg(case when coalesce(historical_owner_truth_supported, false) then 1.0 else 0.0 end), 6) as double) as historical_owner_truth_supported_pct,
                cast(round(avg(case when coalesce(current_owner_metadata_only, false) then 1.0 else 0.0 end), 6) as double) as current_owner_metadata_only_pct,
                cast(round(avg(coalesce(data_completeness_pct_asof, 0.0)), 6) as double) as avg_data_completeness_pct_asof
            from scoped
            group by as_of_year
            order by as_of_year asc
            """
            return self._query_rows(con, query, parameters)

    def get_owner_jurisdiction_unlock_history(
        self,
        owner_id: str,
        year_from: int | None = None,
        year_to: int | None = None,
        jurisdiction_limit: int = 20,
    ) -> dict[str, object]:
        empty_payload: dict[str, object] = {
            "summary": {},
            "years": [],
            "jurisdictions": [],
        }
        required_paths = [
            self.owner_bridge_path,
            self.family_summary_path,
            self.family_blocking_path,
            self.branch_history_dense_path,
        ]
        if any(not self._analytics_source_available(path) for path in required_paths):
            return empty_payload

        with DuckDbProvider().connect() as con:
            resolved_owner = self._resolve_owner(con, self.owner_bridge_path, owner_id)
            if not resolved_owner:
                return empty_payload
            owner_bridge_ref = self._analytics_relation(con, self.owner_bridge_path)
            family_summary_ref = self._analytics_relation(con, self.family_summary_path)
            family_blocking_ref = self._analytics_relation(con, self.family_blocking_path)
            branch_history_ref = self._analytics_relation(con, self.branch_history_dense_path)

            year_filter = ""
            year_parameters: list[object] = []
            if year_from is not None:
                year_filter += " and first_unlock_year >= ?"
                year_parameters.append(int(year_from))
            if year_to is not None:
                year_filter += " and first_unlock_year <= ?"
                year_parameters.append(int(year_to))

            latest_presence_filters = ""
            latest_presence_parameters: list[object] = []
            if year_from is not None:
                latest_presence_filters += " and snapshot_year >= ?"
                latest_presence_parameters.append(int(year_from))
            if year_to is not None:
                latest_presence_filters += " and snapshot_year <= ?"
                latest_presence_parameters.append(int(year_to))

            owner_cte = f"""
            with owner_families as (
                select distinct docdb_family_id
                from {owner_bridge_ref}
                where owner_name_harmonized = ?
            ),
            in_scope_families as (
                select distinct of.docdb_family_id
                from owner_families of
                join {family_summary_ref} gs using (docdb_family_id)
                join {family_blocking_ref} fb using (docdb_family_id)
            ),
            scoped as (
                select
                    cast(b.snapshot_year as integer) as snapshot_year,
                    upper(trim(coalesce(b.jurisdiction_code, ''))) as jurisdiction_code,
                    cast(b.docdb_family_id as bigint) as docdb_family_id,
                    coalesce(b.active_branch_flag, false) as active_branch_flag,
                    coalesce(b.pending_branch_flag, false) as pending_branch_flag,
                    coalesce(b.lapsed_or_expired_flag, false) as lapsed_or_expired_flag,
                    coalesce(b.opposed_branch_flag, false) as opposed_branch_flag
                from {branch_history_ref} b
                join in_scope_families using (docdb_family_id)
                where trim(coalesce(b.jurisdiction_code, '')) not in ('', '_', 'UNKNOWN', 'UNKNOWN_OWNER', 'UNASSIGNED')
                  and cast(coalesce(b.snapshot_year, 0) as integer) > 0
                  and (
                    coalesce(b.active_branch_flag, false)
                    or coalesce(b.pending_branch_flag, false)
                    or coalesce(b.lapsed_or_expired_flag, false)
                    or coalesce(b.opposed_branch_flag, false)
                  )
            ),
            first_unlocks as (
                select
                    jurisdiction_code,
                    min(snapshot_year) as first_unlock_year,
                    min(snapshot_year) filter (where active_branch_flag) as first_active_year,
                    min(snapshot_year) filter (where pending_branch_flag) as first_pending_year,
                    min(snapshot_year) filter (where lapsed_or_expired_flag) as first_lapsed_year,
                    count(distinct docdb_family_id) as tracked_family_count,
                    count(distinct case when active_branch_flag then docdb_family_id end) as active_family_count,
                    count(distinct case when pending_branch_flag then docdb_family_id end) as pending_family_count,
                    count(distinct case when lapsed_or_expired_flag then docdb_family_id end) as lapsed_family_count
                from scoped
                group by jurisdiction_code
            ),
            jurisdiction_year_presence as (
                select
                    snapshot_year as as_of_year,
                    jurisdiction_code,
                    bool_or(active_branch_flag) as any_active,
                    bool_or(pending_branch_flag) as any_pending,
                    bool_or(lapsed_or_expired_flag) as any_lapsed,
                    bool_or(opposed_branch_flag) as any_opposed
                from scoped
                where true
                {latest_presence_filters}
                group by snapshot_year, jurisdiction_code
            ),
            filtered_unlocks as (
                select *
                from first_unlocks
                where true
                {year_filter}
            ),
            yearly_presence as (
                select
                    as_of_year,
                    count(*) filter (where any_active) as active_jurisdiction_count,
                    count(*) filter (where not any_active and any_pending) as pending_jurisdiction_count,
                    count(*) filter (where not any_active and not any_pending and any_lapsed) as lapsed_jurisdiction_count,
                    count(*) filter (where not any_active and not any_pending and not any_lapsed and any_opposed) as tracked_jurisdiction_count
                from jurisdiction_year_presence
                group by as_of_year
            ),
            yearly_unlocks as (
                select
                    first_unlock_year as as_of_year,
                    count(*) as unlocked_jurisdiction_count,
                    sum(
                        case
                            when first_active_year = first_unlock_year then 1
                            else 0
                        end
                    ) as active_unlock_count,
                    sum(
                        case
                            when (first_active_year is null or first_active_year != first_unlock_year)
                             and first_pending_year = first_unlock_year then 1
                            else 0
                        end
                    ) as pending_unlock_count,
                    sum(
                        case
                            when first_active_year is null
                             and first_pending_year is null
                             and first_lapsed_year = first_unlock_year then 1
                            else 0
                        end
                    ) as lapsed_only_unlock_count,
                    array_agg(jurisdiction_code order by jurisdiction_code) as unlocked_jurisdictions
                from filtered_unlocks
                group by first_unlock_year
            ),
            timeline_years as (
                select as_of_year from yearly_unlocks
                union
                select as_of_year from yearly_presence
            )
            """

            summary_query = owner_cte + """
            select
                count(*) as unlocked_jurisdiction_count,
                min(first_unlock_year) as first_unlock_year,
                max(first_unlock_year) as latest_unlock_year,
                sum(active_family_count) as active_family_observations,
                sum(pending_family_count) as pending_family_observations,
                sum(lapsed_family_count) as lapsed_family_observations,
                count(distinct case when first_active_year is not null then jurisdiction_code end) as ever_active_jurisdiction_count
            from filtered_unlocks
            """
            year_rows_query = owner_cte + """
            select
                timeline_years.as_of_year,
                coalesce(yearly_unlocks.unlocked_jurisdiction_count, 0) as unlocked_jurisdiction_count,
                sum(coalesce(yearly_unlocks.unlocked_jurisdiction_count, 0)) over (
                    order by timeline_years.as_of_year
                    rows between unbounded preceding and current row
                ) as cumulative_unlocked_jurisdiction_count,
                coalesce(yearly_unlocks.active_unlock_count, 0) as active_unlock_count,
                coalesce(yearly_unlocks.pending_unlock_count, 0) as pending_unlock_count,
                coalesce(yearly_unlocks.lapsed_only_unlock_count, 0) as lapsed_only_unlock_count,
                coalesce(yearly_presence.active_jurisdiction_count, 0) as active_jurisdiction_count,
                coalesce(yearly_presence.pending_jurisdiction_count, 0) as pending_jurisdiction_count,
                coalesce(yearly_presence.lapsed_jurisdiction_count, 0) as lapsed_jurisdiction_count,
                yearly_unlocks.unlocked_jurisdictions
            from timeline_years
            left join yearly_unlocks
              on yearly_unlocks.as_of_year = timeline_years.as_of_year
            left join yearly_presence
              on yearly_presence.as_of_year = timeline_years.as_of_year
            order by timeline_years.as_of_year asc
            """
            jurisdiction_rows_query = owner_cte + """
            select
                jurisdiction_code,
                first_unlock_year,
                case
                    when first_active_year = first_unlock_year then 'active'
                    when first_pending_year = first_unlock_year then 'pending'
                    when first_lapsed_year = first_unlock_year then 'lapsed_only'
                    else 'tracked'
                end as first_unlock_basis,
                first_active_year,
                first_pending_year,
                first_lapsed_year,
                tracked_family_count,
                active_family_count,
                pending_family_count,
                lapsed_family_count
            from filtered_unlocks
            order by first_unlock_year asc, tracked_family_count desc, jurisdiction_code asc
            limit ?
            """
            latest_presence_query = owner_cte + """
            select
                as_of_year,
                active_jurisdiction_count,
                pending_jurisdiction_count,
                lapsed_jurisdiction_count
            from yearly_presence
            order by as_of_year desc
            limit 1
            """

            summary_parameters: list[object] = [resolved_owner, *year_parameters, *latest_presence_parameters]
            # owner_cte is shared; parameter order is owner + filtered year params + presence year params.
            summary_row = self._query_rows(con, summary_query, summary_parameters)
            year_rows = self._query_rows(con, year_rows_query, summary_parameters)
            jurisdiction_rows = self._query_rows(
                con,
                jurisdiction_rows_query,
                [resolved_owner, *year_parameters, *latest_presence_parameters, int(jurisdiction_limit)],
            )
            latest_presence_rows = self._query_rows(con, latest_presence_query, summary_parameters)

        summary = summary_row[0] if summary_row else {}
        latest_presence = latest_presence_rows[0] if latest_presence_rows else {}
        return {
            "summary": {
                **summary,
                "latest_presence_year": latest_presence.get("as_of_year"),
                "latest_active_jurisdiction_count": latest_presence.get("active_jurisdiction_count"),
                "latest_pending_jurisdiction_count": latest_presence.get("pending_jurisdiction_count"),
                "latest_lapsed_jurisdiction_count": latest_presence.get("lapsed_jurisdiction_count"),
            },
            "years": year_rows,
            "jurisdictions": jurisdiction_rows,
        }

    def get_owner_citation_attackers(
        self,
        owner_id: str,
        limit: int = 10,
        offset: int = 0,
        wipo_field: str | None = None,
        jurisdiction_code: str | None = None,
        year_from: int | None = None,
        year_to: int | None = None,
    ) -> list[dict[str, object]]:
        with DuckDbProvider().connect() as con:
            resolved_owner = self._resolve_owner(con, self.owner_bridge_path, owner_id)
            if not resolved_owner:
                return []
            citation_attacker_ref = self._analytics_relation(con, self.portfolio_citation_attacker_path)
            owner_bridge_ref = self._analytics_relation(con, self.owner_bridge_path)
            citation_network_ref = self._analytics_relation(con, self.enriched_citation_network_path)
            if self._analytics_source_available(self.portfolio_citation_attacker_path):
                parameters: list[object] = [resolved_owner, resolved_owner]
                filters = """
                  and trim(coalesce(citing_assignee_name, '')) not in ('', '_', 'UNKNOWN', 'UNKNOWN_OWNER', 'UNASSIGNED')
                  and upper(coalesce(citing_assignee_name, '')) <> upper(?)
                """
                if wipo_field:
                    filters += " and wipo_field = ?"
                    parameters.append(wipo_field)
                if jurisdiction_code:
                    filters += " and jurisdiction_code = ?"
                    parameters.append(jurisdiction_code.upper())
                if year_from is not None:
                    filters += " and year >= ?"
                    parameters.append(int(year_from))
                if year_to is not None:
                    filters += " and year <= ?"
                    parameters.append(int(year_to))
                query = f"""
                with base as (
                    select
                        citing_assignee_name,
                        wipo_field,
                        jurisdiction_code,
                        cast(coalesce(year, 0) as integer) as citation_year,
                        cast(coalesce(citation_event_count, 0) as bigint) as citation_event_count,
                        cast(coalesce(clean_citation_count, 0.0) as double) as clean_citation_count,
                        cast(coalesce(citation_lethality_sum_raw, 0.0) as double) as citation_lethality_sum
                    from {citation_attacker_ref}
                    where owner_name_harmonized = ?
                    {filters}
                ),
                ranked as (
                    select
                        citing_assignee_name,
                        wipo_field,
                        jurisdiction_code,
                        max(citation_year) as latest_citation_year,
                        sum(citation_event_count) as citation_event_count,
                        cast(coalesce(sum(clean_citation_count), 0.0) as double) as clean_citation_count,
                        cast(coalesce(sum(citation_lethality_sum), 0.0) as double) as citation_lethality_sum
                    from base
                    group by citing_assignee_name, wipo_field, jurisdiction_code
                )
                select
                    *,
                    count(*) over () as total_count
                from ranked
                order by citation_lethality_sum desc, citation_event_count desc, citing_assignee_name asc
                limit ?
                offset ?
                """
                parameters.extend([int(limit), int(offset)])
                return self._query_rows(con, query, parameters)
            parameters: list[object] = [resolved_owner]
            filters = """
              and not coalesce(n.is_intra_family_citation, false)
              and not coalesce(n.is_self_citation, false)
              and trim(coalesce(n.citing_assignee_name, '')) not in ('', '_', 'UNKNOWN', 'UNASSIGNED')
            """
            if wipo_field:
                filters += " and n.citing_primary_wipo_field = ?"
                parameters.append(wipo_field)
            if jurisdiction_code:
                filters += " and n.citing_jurisdiction_code = ?"
                parameters.append(jurisdiction_code.upper())
            if year_from is not None:
                filters += " and n.citation_year >= ?"
                parameters.append(int(year_from))
            if year_to is not None:
                filters += " and n.citation_year <= ?"
                parameters.append(int(year_to))
            query = f"""
            with owner_families as (
                select distinct docdb_family_id
                from {owner_bridge_ref}
                where owner_name_harmonized = ?
                  and coalesce(is_primary_owner, false) = true
            ),
            base as (
                select
                    coalesce(n.citing_assignee_name, '') as citing_assignee_name,
                    coalesce(n.citing_primary_wipo_field, '') as wipo_field,
                    coalesce(n.citing_jurisdiction_code, '') as jurisdiction_code,
                    cast(coalesce(n.citation_year, 0) as integer) as latest_citation_year,
                    cast(coalesce(n.clean_edge_weight, 0.0) as double) as clean_edge_weight,
                    cast(coalesce(n.citation_lethality_score, 0.0) as double) as citation_lethality_score
                from {citation_network_ref} n
                join owner_families of
                  on n.cited_docdb_family_id = of.docdb_family_id
                where true
                  {filters}
            ),
            ranked as (
                select
                    citing_assignee_name,
                    wipo_field,
                    jurisdiction_code,
                    max(latest_citation_year) as latest_citation_year,
                    count(*) as citation_event_count,
                    cast(coalesce(sum(clean_edge_weight), 0.0) as double) as clean_citation_count,
                    cast(coalesce(sum(citation_lethality_score), 0.0) as double) as citation_lethality_sum
                from base
                group by citing_assignee_name, wipo_field, jurisdiction_code
            )
            select
                *,
                count(*) over () as total_count
            from ranked
            order by citation_lethality_sum desc, citation_event_count desc, citing_assignee_name asc
            limit ?
            offset ?
            """
            parameters.extend([int(limit), int(offset)])
            return self._query_rows(con, query, parameters)

    def get_owner_citation_fields(
        self,
        owner_id: str,
        limit: int = 10,
        offset: int = 0,
        jurisdiction_code: str | None = None,
        year_from: int | None = None,
        year_to: int | None = None,
    ) -> list[dict[str, object]]:
        with DuckDbProvider().connect() as con:
            resolved_owner = self._resolve_owner(con, self.owner_bridge_path, owner_id)
            if not resolved_owner:
                return []
            citation_field_ref = self._analytics_relation(con, self.portfolio_citation_field_path)
            citation_attacker_ref = self._analytics_relation(con, self.portfolio_citation_attacker_path)
            owner_bridge_ref = self._analytics_relation(con, self.owner_bridge_path)
            citation_network_ref = self._analytics_relation(con, self.enriched_citation_network_path)
            if (
                self._analytics_source_available(self.portfolio_citation_field_path)
                and year_from is not None
                and year_to is not None
                and int(year_from) == int(year_to)
                and jurisdiction_code is None
            ):
                parameters: list[object] = [resolved_owner]
                filters = """
                  and trim(coalesce(wipo_field, '')) not in ('', '_', 'UNKNOWN', 'UNKNOWN_OWNER', 'UNASSIGNED')
                """
                if year_from is not None:
                    filters += " and year >= ?"
                    parameters.append(int(year_from))
                if year_to is not None:
                    filters += " and year <= ?"
                    parameters.append(int(year_to))
                query = f"""
                with ranked as (
                    select
                        wipo_field,
                        max(cast(coalesce(year, 0) as integer)) as latest_citation_year,
                        cast(coalesce(sum(citation_event_count), 0.0) as double) as citation_event_count,
                        cast(coalesce(sum(citing_assignee_count), 0.0) as bigint) as citing_assignee_count,
                        cast(coalesce(sum(clean_citation_count), 0.0) as double) as clean_citation_count,
                        cast(coalesce(sum(citation_lethality_sum_raw), 0.0) as double) as citation_lethality_sum
                    from {citation_field_ref}
                    where owner_name_harmonized = ?
                    {filters}
                    group by wipo_field
                )
                select
                    *,
                    count(*) over () as total_count
                from ranked
                order by citation_lethality_sum desc, citation_event_count desc, wipo_field asc
                limit ?
                offset ?
                """
                parameters.extend([int(limit), int(offset)])
                return self._query_rows(con, query, parameters)
            if self._analytics_source_available(self.portfolio_citation_attacker_path):
                parameters = [resolved_owner]
                filters = """
                  and trim(coalesce(wipo_field, '')) not in ('', '_', 'UNKNOWN', 'UNKNOWN_OWNER', 'UNASSIGNED')
                """
                if jurisdiction_code:
                    filters += " and jurisdiction_code = ?"
                    parameters.append(jurisdiction_code.upper())
                if year_from is not None:
                    filters += " and year >= ?"
                    parameters.append(int(year_from))
                if year_to is not None:
                    filters += " and year <= ?"
                    parameters.append(int(year_to))
                query = f"""
                with base as (
                    select
                        wipo_field,
                        citing_assignee_name,
                        cast(coalesce(year, 0) as integer) as citation_year,
                        cast(coalesce(citation_event_count, 0) as bigint) as citation_event_count,
                        cast(coalesce(clean_citation_count, 0.0) as double) as clean_citation_count,
                        cast(coalesce(citation_lethality_sum_raw, 0.0) as double) as citation_lethality_sum
                    from {citation_attacker_ref}
                    where owner_name_harmonized = ?
                    {filters}
                ),
                ranked as (
                    select
                        wipo_field,
                        max(citation_year) as latest_citation_year,
                        sum(citation_event_count) as citation_event_count,
                        count(distinct citing_assignee_name) as citing_assignee_count,
                        cast(coalesce(sum(clean_citation_count), 0.0) as double) as clean_citation_count,
                        cast(coalesce(sum(citation_lethality_sum), 0.0) as double) as citation_lethality_sum
                    from base
                    group by wipo_field
                )
                select
                    *,
                    count(*) over () as total_count
                from ranked
                order by citation_lethality_sum desc, citation_event_count desc, wipo_field asc
                limit ?
                offset ?
                """
                parameters.extend([int(limit), int(offset)])
                return self._query_rows(con, query, parameters)
            parameters: list[object] = [resolved_owner]
            filters = """
              and not coalesce(n.is_intra_family_citation, false)
              and not coalesce(n.is_self_citation, false)
              and trim(coalesce(n.citing_assignee_name, '')) not in ('', '_', 'UNKNOWN', 'UNASSIGNED')
              and trim(coalesce(n.citing_primary_wipo_field, '')) not in ('', '_', 'UNKNOWN', 'UNASSIGNED')
            """
            if jurisdiction_code:
                filters += " and n.citing_jurisdiction_code = ?"
                parameters.append(jurisdiction_code.upper())
            if year_from is not None:
                filters += " and n.citation_year >= ?"
                parameters.append(int(year_from))
            if year_to is not None:
                filters += " and n.citation_year <= ?"
                parameters.append(int(year_to))
            query = f"""
            with owner_families as (
                select distinct docdb_family_id
                from {owner_bridge_ref}
                where owner_name_harmonized = ?
                  and coalesce(is_primary_owner, false) = true
            ),
            base as (
                select
                    coalesce(n.citing_primary_wipo_field, '') as wipo_field,
                    coalesce(n.citing_assignee_name, '') as citing_assignee_name,
                    cast(coalesce(n.citation_year, 0) as integer) as citation_year,
                    cast(coalesce(n.clean_edge_weight, 0.0) as double) as clean_edge_weight,
                    cast(coalesce(n.citation_lethality_score, 0.0) as double) as citation_lethality_score
                from {citation_network_ref} n
                join owner_families of
                  on n.cited_docdb_family_id = of.docdb_family_id
                where true
                  {filters}
            ),
            ranked as (
                select
                    wipo_field,
                    max(citation_year) as latest_citation_year,
                    count(*) as citation_event_count,
                    count(distinct citing_assignee_name) as citing_assignee_count,
                    cast(coalesce(sum(clean_edge_weight), 0.0) as double) as clean_citation_count,
                    cast(coalesce(sum(citation_lethality_score), 0.0) as double) as citation_lethality_sum
                from base
                group by wipo_field
            )
            select
                *,
                count(*) over () as total_count
            from ranked
            order by citation_lethality_sum desc, citation_event_count desc, wipo_field asc
            limit ?
            offset ?
            """
            parameters.extend([int(limit), int(offset)])
            return self._query_rows(con, query, parameters)

    def get_owner_citation_jurisdictions(
        self,
        owner_id: str,
        limit: int = 10,
        offset: int = 0,
        wipo_field: str | None = None,
        year_from: int | None = None,
        year_to: int | None = None,
    ) -> list[dict[str, object]]:
        with DuckDbProvider().connect() as con:
            resolved_owner = self._resolve_owner(con, self.owner_bridge_path, owner_id)
            if not resolved_owner:
                return []
            citation_jurisdiction_ref = self._analytics_relation(con, self.portfolio_citation_jurisdiction_path)
            citation_attacker_ref = self._analytics_relation(con, self.portfolio_citation_attacker_path)
            owner_bridge_ref = self._analytics_relation(con, self.owner_bridge_path)
            citation_network_ref = self._analytics_relation(con, self.enriched_citation_network_path)
            if (
                self._analytics_source_available(self.portfolio_citation_jurisdiction_path)
                and year_from is not None
                and year_to is not None
                and int(year_from) == int(year_to)
                and wipo_field is None
            ):
                parameters: list[object] = [resolved_owner]
                filters = """
                  and trim(coalesce(jurisdiction_code, '')) not in ('', '_', 'UNKNOWN', 'UNKNOWN_OWNER', 'UNASSIGNED')
                """
                if year_from is not None:
                    filters += " and year >= ?"
                    parameters.append(int(year_from))
                if year_to is not None:
                    filters += " and year <= ?"
                    parameters.append(int(year_to))
                query = f"""
                with ranked as (
                    select
                        jurisdiction_code,
                        max(cast(coalesce(year, 0) as integer)) as latest_citation_year,
                        cast(coalesce(sum(citation_event_count), 0.0) as double) as citation_event_count,
                        cast(coalesce(sum(citing_assignee_count), 0.0) as bigint) as citing_assignee_count,
                        cast(coalesce(sum(wipo_field_count), 0.0) as bigint) as wipo_field_count,
                        cast(coalesce(sum(clean_citation_count), 0.0) as double) as clean_citation_count,
                        cast(coalesce(sum(citation_lethality_sum_raw), 0.0) as double) as citation_lethality_sum
                    from {citation_jurisdiction_ref}
                    where owner_name_harmonized = ?
                    {filters}
                    group by jurisdiction_code
                )
                select
                    *,
                    count(*) over () as total_count
                from ranked
                order by citation_lethality_sum desc, citation_event_count desc, jurisdiction_code asc
                limit ?
                offset ?
                """
                parameters.extend([int(limit), int(offset)])
                return self._query_rows(con, query, parameters)
            if self._analytics_source_available(self.portfolio_citation_attacker_path):
                parameters = [resolved_owner]
                filters = """
                  and trim(coalesce(jurisdiction_code, '')) not in ('', '_', 'UNKNOWN', 'UNKNOWN_OWNER', 'UNASSIGNED')
                """
                if wipo_field:
                    filters += " and wipo_field = ?"
                    parameters.append(wipo_field)
                if year_from is not None:
                    filters += " and year >= ?"
                    parameters.append(int(year_from))
                if year_to is not None:
                    filters += " and year <= ?"
                    parameters.append(int(year_to))
                query = f"""
                with base as (
                    select
                        jurisdiction_code,
                        citing_assignee_name,
                        wipo_field,
                        cast(coalesce(year, 0) as integer) as citation_year,
                        cast(coalesce(citation_event_count, 0) as bigint) as citation_event_count,
                        cast(coalesce(clean_citation_count, 0.0) as double) as clean_citation_count,
                        cast(coalesce(citation_lethality_sum_raw, 0.0) as double) as citation_lethality_sum
                    from {citation_attacker_ref}
                    where owner_name_harmonized = ?
                    {filters}
                ),
                ranked as (
                    select
                        jurisdiction_code,
                        max(citation_year) as latest_citation_year,
                        sum(citation_event_count) as citation_event_count,
                        count(distinct citing_assignee_name) as citing_assignee_count,
                        count(distinct wipo_field) as wipo_field_count,
                        cast(coalesce(sum(clean_citation_count), 0.0) as double) as clean_citation_count,
                        cast(coalesce(sum(citation_lethality_sum), 0.0) as double) as citation_lethality_sum
                    from base
                    group by jurisdiction_code
                )
                select
                    *,
                    count(*) over () as total_count
                from ranked
                order by citation_lethality_sum desc, citation_event_count desc, jurisdiction_code asc
                limit ?
                offset ?
                """
                parameters.extend([int(limit), int(offset)])
                return self._query_rows(con, query, parameters)
            parameters: list[object] = [resolved_owner]
            filters = """
              and not coalesce(n.is_intra_family_citation, false)
              and not coalesce(n.is_self_citation, false)
              and trim(coalesce(n.citing_assignee_name, '')) not in ('', '_', 'UNKNOWN', 'UNASSIGNED')
              and trim(coalesce(n.citing_jurisdiction_code, '')) not in ('', '_', 'UNKNOWN', 'UNASSIGNED')
            """
            if wipo_field:
                filters += " and n.citing_primary_wipo_field = ?"
                parameters.append(wipo_field)
            if year_from is not None:
                filters += " and n.citation_year >= ?"
                parameters.append(int(year_from))
            if year_to is not None:
                filters += " and n.citation_year <= ?"
                parameters.append(int(year_to))
            query = f"""
            with owner_families as (
                select distinct docdb_family_id
                from {owner_bridge_ref}
                where owner_name_harmonized = ?
                  and coalesce(is_primary_owner, false) = true
            ),
            base as (
                select
                    coalesce(n.citing_jurisdiction_code, '') as jurisdiction_code,
                    coalesce(n.citing_assignee_name, '') as citing_assignee_name,
                    coalesce(n.citing_primary_wipo_field, '') as wipo_field,
                    cast(coalesce(n.citation_year, 0) as integer) as citation_year,
                    cast(coalesce(n.clean_edge_weight, 0.0) as double) as clean_edge_weight,
                    cast(coalesce(n.citation_lethality_score, 0.0) as double) as citation_lethality_score
                from {citation_network_ref} n
                join owner_families of
                  on n.cited_docdb_family_id = of.docdb_family_id
                where true
                  {filters}
            ),
            ranked as (
                select
                    jurisdiction_code,
                    max(citation_year) as latest_citation_year,
                    count(*) as citation_event_count,
                    count(distinct citing_assignee_name) as citing_assignee_count,
                    count(distinct wipo_field) as wipo_field_count,
                    cast(coalesce(sum(clean_edge_weight), 0.0) as double) as clean_citation_count,
                    cast(coalesce(sum(citation_lethality_score), 0.0) as double) as citation_lethality_sum
                from base
                group by jurisdiction_code
            )
            select
                *,
                count(*) over () as total_count
            from ranked
            order by citation_lethality_sum desc, citation_event_count desc, jurisdiction_code asc
            limit ?
            offset ?
            """
            parameters.extend([int(limit), int(offset)])
            return self._query_rows(con, query, parameters)

    def get_owner_citation_cpc_groups(
        self,
        owner_id: str,
        limit: int = 10,
        offset: int = 0,
        wipo_field: str | None = None,
        jurisdiction_code: str | None = None,
        year_from: int | None = None,
        year_to: int | None = None,
    ) -> list[dict[str, object]]:
        with DuckDbProvider().connect() as con:
            resolved_owner = self._resolve_owner(con, self.owner_bridge_path, owner_id)
            if not resolved_owner:
                return []
            owner_bridge_ref = self._analytics_relation(con, self.owner_bridge_path)
            family_classification_ref = self._analytics_relation(con, self.family_classification_mix_path)
            citation_network_ref = self._analytics_relation(con, self.enriched_citation_network_path)

            parameters: list[object] = [resolved_owner]
            citation_filters = ""
            if wipo_field:
                citation_filters += " and coalesce(n.citing_primary_wipo_field, '') = ?"
                parameters.append(wipo_field)
            if jurisdiction_code:
                citation_filters += " and coalesce(n.citing_jurisdiction_code, '') = ?"
                parameters.append(jurisdiction_code.upper())
            if year_from is not None:
                citation_filters += " and n.citation_year >= ?"
                parameters.append(int(year_from))
            if year_to is not None:
                citation_filters += " and n.citation_year <= ?"
                parameters.append(int(year_to))

            query = f"""
            with owner_families as (
                select distinct ob.docdb_family_id
                from {owner_bridge_ref} ob
                where ob.owner_name_harmonized = ?
                  and coalesce(ob.is_primary_owner, false) = true
                  and {self._non_placeholder_owner_sql('ob.owner_name_harmonized')}
            ),
            latest_family_classification as (
                select
                    fc.docdb_family_id,
                    fc.cpc_main_groups_asof
                from (
                    select
                        fc.*,
                        row_number() over (
                            partition by fc.docdb_family_id
                            order by fc.as_of_year desc, fc.as_of_date desc
                        ) as row_number
                    from {family_classification_ref} fc
                    join owner_families of using (docdb_family_id)
                ) fc
                where row_number = 1
            ),
            family_cpc as (
                select
                    lfc.docdb_family_id,
                    c.cpc_main_group as cpc_main_group
                from latest_family_classification lfc
                cross join unnest(lfc.cpc_main_groups_asof) as c(cpc_main_group)
                where c.cpc_main_group is not null
                  and c.cpc_main_group <> ''
            ),
            ranked as (
                select
                    fc.cpc_main_group,
                    max(cast(coalesce(n.citation_year, 0) as integer)) as latest_citation_year,
                    count(*) as citation_event_count,
                    cast(coalesce(sum(n.clean_edge_weight), 0.0) as double) as clean_citation_count,
                    cast(coalesce(sum(n.citation_lethality_score), 0.0) as double) as citation_lethality_sum,
                    count(distinct n.cited_docdb_family_id) as cited_family_count
                from {citation_network_ref} n
                join family_cpc fc
                  on n.cited_docdb_family_id = fc.docdb_family_id
                where not coalesce(n.is_out_of_bounds, false)
                  and not coalesce(n.is_intra_family_citation, false)
                  and not coalesce(n.is_self_citation, false)
                  {citation_filters}
                group by fc.cpc_main_group
            )
            select
                *,
                count(*) over () as total_count
            from ranked
            order by citation_lethality_sum desc, clean_citation_count desc, cpc_main_group asc
            limit ?
            offset ?
            """
            parameters.extend([int(limit), int(offset)])
            return self._query_rows(con, query, parameters)

    def get_owner_threats(
        self,
        owner_id: str,
        limit: int = 10,
        offset: int = 0,
        wipo_field: str | None = None,
        exclude_self: bool = True,
        exclude_unknown: bool = True,
    ) -> list[dict[str, object]]:
        core_serving_path = self.artifact_locator.resolve_core_serving_duckdb()
        if core_serving_path is not None:
            with self.duckdb_provider.connect() as con:
                self._attach_core_serving(con, core_serving_path)
                if self._core_table_exists(con, "portfolio_threat_matrix"):
                    resolved_owner = self._resolve_owner_from_table(con, "portfolio_threat_matrix", owner_id)
                    if resolved_owner:
                        parameters: list[object] = [resolved_owner]
                        filters = ""
                        if exclude_self:
                            filters += " and coalesce(citing_assignee_name, '') <> ?"
                            parameters.append(resolved_owner)
                        if exclude_unknown:
                            filters += " and trim(coalesce(citing_assignee_name, '')) not in ('', '_', 'UNKNOWN', 'UNASSIGNED')"
                            filters += " and trim(coalesce(wipo_field, '')) not in ('', '_', 'UNKNOWN', 'UNASSIGNED')"
                        if wipo_field:
                            filters += " and wipo_field = ?"
                            parameters.append(wipo_field)
                        query = f"""
                        with base as (
                            select
                                citing_assignee_name,
                                wipo_field,
                                coalesce(citation_lethality_sum, 0.0) as citation_lethality_sum,
                                coalesce(collided_family_count, 0) as collided_family_count
                            from core_db.portfolio_threat_matrix
                            where owner_name_harmonized = ?
                            {filters}
                        )
                        select
                            *,
                            count(*) over () as total_count
                        from base
                        order by citation_lethality_sum desc nulls last, collided_family_count desc, citing_assignee_name asc
                        limit ?
                        offset ?
                        """
                        rows = self._query_rows(con, query, [*parameters, int(limit), int(offset)])
                        if rows:
                            return rows

        with self.duckdb_provider.connect() as con:
            resolved_owner = self._resolve_owner(con, self.threat_path, owner_id)
            if not resolved_owner:
                return []
            threat_ref = self._analytics_relation(con, self.threat_path)
            parameters: list[object] = [resolved_owner]
            filters = ""
            if exclude_self:
                filters += " and coalesce(citing_assignee_name, '') <> ?"
                parameters.append(resolved_owner)
            if exclude_unknown:
                filters += " and trim(coalesce(citing_assignee_name, '')) not in ('', '_', 'UNKNOWN', 'UNASSIGNED')"
                filters += " and trim(coalesce(wipo_field, '')) not in ('', '_', 'UNKNOWN', 'UNASSIGNED')"
            if wipo_field:
                filters += " and wipo_field = ?"
                parameters.append(wipo_field)
            query = f"""
            with base as (
                select
                    citing_assignee_name,
                    wipo_field,
                    coalesce(citation_lethality_sum, 0.0) as citation_lethality_sum,
                    coalesce(collided_family_count, 0) as collided_family_count
                from {threat_ref}
                where owner_name_harmonized = ?
                {filters}
            )
            select
                *,
                count(*) over () as total_count
            from base
            order by citation_lethality_sum desc nulls last, collided_family_count desc, citing_assignee_name asc
            limit ?
            offset ?
            """
            parameters.extend([int(limit), int(offset)])
            return self._query_rows(con, query, parameters)

    def get_owner_classification(
        self,
        owner_id: str,
        as_of_year: int | None = None,
        limit: int = 10,
        offset: int = 0,
        classification_type: str = "CPC_MAIN_GROUP",
        wipo_field: str | None = None,
    ) -> list[dict[str, object]]:
        selected_type = classification_type.strip().upper() if classification_type else "CPC_MAIN_GROUP"
        selected_wipo_field = (wipo_field or "").strip()
        core_serving_path = self.artifact_locator.resolve_core_serving_duckdb()

        if as_of_year is None and core_serving_path is not None:
            with self.duckdb_provider.connect() as con:
                self._attach_core_serving(con, core_serving_path)
                if not (selected_type == "CPC_MAIN_GROUP" and selected_wipo_field) and self._core_table_exists(
                    con, "portfolio_classification_current_serving"
                ):
                    resolved_owner = self._resolve_owner_from_table(
                        con,
                        "portfolio_classification_current_serving",
                        owner_id,
                    )
                    if resolved_owner:
                        type_filter = " and classification_type in ('WIPO_FIELD', 'CPC_MAIN_GROUP')"
                        parameters: list[object] = [resolved_owner]
                        if selected_type in {"WIPO_FIELD", "CPC_MAIN_GROUP"}:
                            type_filter = " and classification_type = ?"
                            parameters.append(selected_type)
                        query = f"""
                        select
                            segment,
                            classification_label,
                            classification_type,
                            rank,
                            family_share,
                            active_family_count,
                            trajectory,
                            count(*) over () as total_count
                        from core_db.portfolio_classification_current_serving
                        where owner_name_harmonized = ?
                          {type_filter}
                        order by classification_type, rank
                        limit ?
                        offset ?
                        """
                        rows = self._query_rows(con, query, parameters + [int(limit), int(offset)])
                        if rows:
                            return rows
                        return []

        with self.duckdb_provider.connect() as con:
            resolved_owner = self._resolve_owner(con, self.classification_mix_path, owner_id)
            if not resolved_owner:
                return []
            family_classification_ref = self._analytics_relation(con, self.family_classification_mix_path)
            owner_bridge_ref = self._analytics_relation(con, self.owner_bridge_path)
            classification_ref = self._analytics_relation(con, self.classification_mix_path)
            if selected_type == "CPC_MAIN_GROUP" and selected_wipo_field:
                query = f"""
                with base as (
                    select
                        fc.docdb_family_id,
                        fc.as_of_year,
                        fc.cpc_main_groups_asof
                    from {family_classification_ref} fc
                    join {owner_bridge_ref} ob using (docdb_family_id)
                    where ob.owner_name_harmonized = ?
                      and fc.primary_wipo_field_asof = ?
                      and {self._non_placeholder_owner_sql('ob.owner_name_harmonized')}
                ),
                selected_year as (
                    select cast(coalesce(?, max(as_of_year)) as integer) as as_of_year
                    from base
                ),
                previous_year as (
                    select max(as_of_year)::integer as as_of_year
                    from base
                    where as_of_year < (select as_of_year from selected_year)
                ),
                filtered_base as (
                    select
                        *
                    from base
                    where as_of_year in (
                        (select as_of_year from selected_year),
                        (select as_of_year from previous_year)
                    )
                ),
                field_totals as (
                    select
                        as_of_year,
                        count(distinct docdb_family_id) as field_family_count
                    from filtered_base
                    group by as_of_year
                ),
                aggregated as (
                    select
                        b.as_of_year,
                        c.cpc_main_group as classification_code,
                        count(distinct b.docdb_family_id) as family_count
                    from filtered_base b
                    cross join unnest(b.cpc_main_groups_asof) as c(cpc_main_group)
                    where c.cpc_main_group is not null
                      and c.cpc_main_group <> ''
                    group by b.as_of_year, c.cpc_main_group
                ),
                scored as (
                    select
                        a.as_of_year,
                        a.classification_code as segment,
                        a.family_count,
                        case
                            when coalesce(t.field_family_count, 0) = 0 then null
                            else cast(a.family_count as double) / cast(t.field_family_count as double)
                        end as family_share
                    from aggregated a
                    join field_totals t using (as_of_year)
                ),
                current_rows as (
                    select
                        s.as_of_year,
                        s.segment,
                        ? as classification_label,
                        'CPC_MAIN_GROUP' as classification_type,
                        row_number() over (
                            order by s.family_count desc, s.segment asc
                        ) as rank,
                        s.family_share
                    from scored s
                    where s.as_of_year = (select as_of_year from selected_year)
                ),
                previous_rows as (
                    select
                        segment,
                        family_share as previous_family_share
                    from scored
                    where as_of_year = (select as_of_year from previous_year)
                )
                select
                    c.*,
                    case
                        when p.previous_family_share is null then null
                        else c.family_share - p.previous_family_share
                    end as trajectory,
                    count(*) over () as total_count
                from current_rows c
                left join previous_rows p using (segment)
                order by rank
                limit ?
                offset ?
                """
                return self._query_rows(
                    con,
                    query,
                    [resolved_owner, selected_wipo_field, as_of_year, selected_wipo_field, int(limit), int(offset)],
                )
            type_filter = " and classification_type in ('WIPO_FIELD', 'CPC_MAIN_GROUP')"
            parameters: list[object] = [resolved_owner]
            if selected_type in {"WIPO_FIELD", "CPC_MAIN_GROUP"}:
                type_filter = " and classification_type = ?"
                parameters.append(selected_type)
            query = f"""
            with base as (
                select *
                from {classification_ref}
                where owner_name_harmonized = ?
                  {type_filter}
            ),
            selected_year as (
                select cast(coalesce(?, max(as_of_year)) as integer) as as_of_year
                from base
            ),
            previous_year as (
                select max(as_of_year)::integer as as_of_year
                from base
                where as_of_year < (select as_of_year from selected_year)
            ),
            current_rows as (
                select
                    classification_code as segment,
                    classification_label,
                    classification_type,
                    classification_rank_within_owner_year as rank,
                    portfolio_family_share_asof as family_share,
                    portfolio_family_count_in_classification_asof as active_family_count
                from base
                where as_of_year = (select as_of_year from selected_year)
            ),
            previous_rows as (
                select
                    classification_type,
                    classification_code as segment,
                    portfolio_family_share_asof as previous_family_share
                from base
                where as_of_year = (select as_of_year from previous_year)
            )
            select
                c.*,
                case
                    when p.previous_family_share is null then null
                    else c.family_share - p.previous_family_share
                end as trajectory,
                count(*) over () as total_count
            from current_rows c
            left join previous_rows p using (classification_type, segment)
            order by classification_type, rank
            limit ?
            offset ?
            """
            return self._query_rows(con, query, parameters + [as_of_year, int(limit), int(offset)])

    def get_owner_classification_timeseries(
        self,
        owner_id: str,
        as_of_year: int | None = None,
        limit_fields: int = 6,
    ) -> list[dict[str, object]]:
        with DuckDbProvider().connect() as con:
            resolved_owner = self._resolve_owner(con, self.classification_mix_path, owner_id)
            if not resolved_owner:
                return []
            classification_ref = self._analytics_relation(con, self.classification_mix_path)
            query = f"""
            with latest_year as (
                select
                    max(as_of_year) as as_of_year
                from {classification_ref}
                where owner_name_harmonized = ?
                  and classification_type = 'WIPO_FIELD'
            ),
            selected_year as (
                select
                    cast(coalesce(?, (select as_of_year from latest_year)) as integer) as as_of_year
            ),
            top_fields as (
                select
                    classification_code as wipo_field
                from {classification_ref}
                where owner_name_harmonized = ?
                  and classification_type = 'WIPO_FIELD'
                  and as_of_year = (select as_of_year from selected_year)
                qualify row_number() over (
                    order by portfolio_family_count_in_classification_asof desc nulls last,
                             portfolio_active_family_count_in_classification_asof desc nulls last,
                             classification_code asc
                ) <= {int(limit_fields)}
            )
            select
                c.classification_code as wipo_field,
                cast(c.as_of_year as integer) as year,
                cast(coalesce(c.portfolio_active_family_share_asof, 0.0) as double) as share,
                cast(coalesce(c.portfolio_family_share_asof, 0.0) as double) as portfolio
            from {classification_ref} c
            join top_fields tf
              on c.classification_code = tf.wipo_field
            where c.owner_name_harmonized = ?
                and c.classification_type = 'WIPO_FIELD'
                and c.as_of_year <= (select as_of_year from selected_year)
            order by c.classification_code, c.as_of_year
            """
            rows = self._query_rows(
                con,
                query,
                [resolved_owner, as_of_year, resolved_owner, resolved_owner],
            )
            return rows

    def get_owner_forecast_contributors(
        self,
        owner_id: str,
        horizon: str = "3y",
        contributor_scope: str = "phase03_future_citations",
        limit: int = 10,
        offset: int = 0,
        current_state_only: bool = False,
    ) -> list[dict[str, object]]:
        with DuckDbProvider().connect() as con:
            resolved_owner = self._resolve_owner(con, self.forecast_contributors_path, owner_id)
            if not resolved_owner:
                return []
            forecast_contributors_ref = self._analytics_relation(con, self.forecast_contributors_path)
            family_summary_ref = self._analytics_relation(con, self.family_summary_path)
            if current_state_only:
                core_serving_path = self.artifact_locator.resolve_core_serving_duckdb()
                if core_serving_path is not None and core_serving_path.exists():
                    self._attach_core_serving(con, core_serving_path)
                    if self._core_table_exists(con, "family_summary"):
                        query = f"""
                        with base as (
                            select
                                c.contributor_scope,
                                c.horizon,
                                c.contributor_entity_id,
                                c.jurisdiction_code,
                                cast(coalesce(c.contribution_value, 0.0) as double) as contribution_value,
                                cast(coalesce(c.contribution_share, 0.0) as double) as contribution_share,
                                cast(coalesce(c.contributor_rank, 0) as integer) as contributor_rank,
                                coalesce(gs.family_composite_status, 'unknown') as status
                            from {forecast_contributors_ref} c
                            left join core_db.family_summary gs
                              on cast(gs.docdb_family_id as varchar) = c.contributor_entity_id
                            where c.owner_name_harmonized = ?
                              and c.horizon = ?
                              and c.contributor_scope = ?
                              and coalesce(gs.family_composite_status, 'unknown') in ('fully_active', 'pending_emerging', 'under_fire', 'partially_lapsed')
                        )
                        select
                            *,
                            count(*) over () as total_count
                        from base
                        order by contributor_rank asc, contribution_value desc, contributor_entity_id asc
                        limit ?
                        offset ?
                        """
                        rows = self._query_rows(
                            con,
                            query,
                            [resolved_owner, horizon, contributor_scope, int(limit), int(offset)],
                        )
                        return rows
                query = f"""
                with base as (
                    select
                        c.contributor_scope,
                        c.horizon,
                        c.contributor_entity_id,
                        c.jurisdiction_code,
                        cast(coalesce(c.contribution_value, 0.0) as double) as contribution_value,
                        cast(coalesce(c.contribution_share, 0.0) as double) as contribution_share,
                        cast(coalesce(c.contributor_rank, 0) as integer) as contributor_rank,
                        coalesce(gs.family_composite_status, 'unknown') as status
                    from {forecast_contributors_ref} c
                    left join {family_summary_ref} gs
                      on cast(gs.docdb_family_id as varchar) = c.contributor_entity_id
                    where c.owner_name_harmonized = ?
                      and c.horizon = ?
                      and c.contributor_scope = ?
                      and coalesce(gs.family_composite_status, 'unknown') in ('fully_active', 'pending_emerging', 'under_fire', 'partially_lapsed')
                )
                select
                    *,
                    count(*) over () as total_count
                from base
                order by contributor_rank asc, contribution_value desc, contributor_entity_id asc
                limit ?
                offset ?
                """
                return self._query_rows(
                    con,
                    query,
                    [resolved_owner, horizon, contributor_scope, int(limit), int(offset)],
                )
            query = f"""
            select
                contributor_scope,
                horizon,
                contributor_entity_id,
                jurisdiction_code,
                cast(coalesce(contribution_value, 0.0) as double) as contribution_value,
                cast(coalesce(contribution_share, 0.0) as double) as contribution_share,
                cast(coalesce(contributor_rank, 0) as integer) as contributor_rank,
                count(*) over () as total_count
            from {forecast_contributors_ref}
            where owner_name_harmonized = ?
              and horizon = ?
              and contributor_scope = ?
            order by contributor_rank asc, contribution_value desc, contributor_entity_id asc
            limit ?
            offset ?
            """
            return self._query_rows(
                con,
                query,
                [resolved_owner, horizon, contributor_scope, int(limit), int(offset)],
            )

    def get_owner_market_context(
        self,
        owner_id: str,
        horizon: str = "3y",
        as_of_year: int | None = None,
        limit_segments: int = 10,
    ) -> tuple[dict[str, object], list[dict[str, object]]]:
        with DuckDbProvider().connect() as con:
            resolved_summary_owner = self._resolve_owner(con, self.forecast_summary_path, owner_id)
            resolved_segment_owner = self._resolve_owner(con, self.forecast_segments_path, owner_id)
            if not resolved_summary_owner or not resolved_segment_owner:
                return {}, []
            forecast_summary_ref = self._analytics_relation(con, self.forecast_summary_path)
            forecast_segments_ref = self._analytics_relation(con, self.forecast_segments_path)
            summary_query = f"""
            select *
            from {forecast_summary_ref}
            where owner_name_harmonized = ?
            {self._snapshot_year_filter(as_of_year)}
            order by snapshot_date desc
            limit 1
            """
            summary_rows = self._query_rows(con, summary_query, [resolved_summary_owner])
            segment_query = f"""
            select
                horizon,
                wipo_field,
                predicted_direction_band,
                support_level,
                cast(coalesce(predicted_growth_rate_reference, 0.0) as double) as predicted_growth_rate_reference,
                cast(coalesce(predicted_count_reference, 0.0) as double) as predicted_count_reference,
                cast(coalesce(portfolio_active_family_count_in_field, 0) as bigint) as portfolio_active_family_count_in_field
            from {forecast_segments_ref}
            where owner_name_harmonized = ?
              and horizon = ?
              {self._snapshot_year_filter(as_of_year)}
            order by portfolio_active_family_count_in_field desc, wipo_field asc
            limit ?
            """
            segment_rows = self._query_rows(con, segment_query, [resolved_segment_owner, horizon, int(limit_segments)])
            return (summary_rows[0] if summary_rows else {}), segment_rows

    def get_owner_compare_timeslice(
        self,
        owner_id: str,
        base_year: int | None = None,
        compare_year: int | None = None,
    ) -> list[dict[str, object]]:
        with DuckDbProvider().connect() as con:
            resolved_owner = self._resolve_owner(con, self.compare_pit_path, owner_id)
            if not resolved_owner:
                return []
            compare_ref = self._analytics_relation(con, self.compare_pit_path)
            if base_year is None:
                latest_row = con.execute(
                    f"""
                    select max(as_of_year)
                    from {compare_ref}
                    where owner_name_harmonized = ?
                    """,
                    [resolved_owner],
                ).fetchone()
                base_year = int(latest_row[0]) if latest_row and latest_row[0] is not None else None
            if compare_year is None and base_year is not None:
                prior_row = con.execute(
                    f"""
                    select max(as_of_year)
                    from {compare_ref}
                    where owner_name_harmonized = ?
                      and as_of_year < ?
                      and coalesce(historical_compare_safe, false) = true
                      and not (
                        as_of_year = 2025
                        and coalesce(portfolio_avg_enforceability_score_asof, 0.0) = 0.0
                      )
                    """,
                    [resolved_owner, int(base_year)],
                ).fetchone()
                compare_year = int(prior_row[0]) if prior_row and prior_row[0] is not None else None
            if base_year is None or compare_year is None:
                return []
            query = f"""
            select *
            from {compare_ref}
            where owner_name_harmonized = ?
              and as_of_year in (?, ?)
            order by as_of_year desc
            """
            return self._query_rows(con, query, [resolved_owner, int(base_year), int(compare_year)])

    def get_owner_compare_timeslice_options(self, owner_id: str) -> dict[str, object]:
        with DuckDbProvider().connect() as con:
            resolved_owner = self._resolve_owner(con, self.compare_pit_path, owner_id)
            if not resolved_owner:
                return {
                    "entity_id": str(owner_id),
                    "available_years": [],
                    "compare_safe_years": [],
                    "default_base_year": None,
                    "default_compare_year": None,
                }

            compare_ref = self._analytics_relation(con, self.compare_pit_path)
            rows = self._query_rows(
                con,
                f"""
                select
                    as_of_year,
                    coalesce(historical_compare_safe, false) as historical_compare_safe,
                    not (
                        as_of_year = 2025
                        and coalesce(portfolio_avg_enforceability_score_asof, 0.0) = 0.0
                    ) as year_allowed
                from {compare_ref}
                where owner_name_harmonized = ?
                order by as_of_year desc
                """,
                [resolved_owner],
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
            "entity_id": str(resolved_owner),
            "available_years": available_years,
            "compare_safe_years": compare_safe_years,
            "default_base_year": default_base_year,
            "default_compare_year": default_compare_year,
        }

    def get_pending_grant_contract(self) -> dict[str, object]:
        if not self.pending_grant_model_card_path.exists():
            return {}
        try:
            return json.loads(self.pending_grant_model_card_path.read_text())
        except (OSError, json.JSONDecodeError):
            return {}

    def _pending_grant_probability_columns(self, horizon: str) -> tuple[str, str, str]:
        selected = "12m" if str(horizon).strip().lower() == "12m" else "24m"
        return (
            f"grant_probability_calibrated_{selected}",
            f"pending_grant_rank_within_office_{selected}",
            f"pending_grant_percentile_within_office_{selected}",
        )

    def _pending_grant_priority_tier_sql(self, percentile_sql: str) -> str:
        return f"""
            case
                when coalesce({percentile_sql}, 0.0) >= 95.0 then 'top'
                when coalesce({percentile_sql}, 0.0) >= 80.0 then 'high'
                when coalesce({percentile_sql}, 0.0) >= 50.0 then 'watch'
                else 'monitor'
            end
        """

    def _pending_grant_support_sort_sql(self, column_name: str = "office_support_level") -> str:
        return f"""
            case
                when {column_name} = 'strong' then 3
                when {column_name} = 'moderate' then 2
                when {column_name} = 'limited' then 1
                else 0
            end
        """

    def _pending_grant_metrics(self, horizon: str) -> dict[str, object]:
        model_card = self.get_pending_grant_contract()
        if not isinstance(model_card, dict):
            return {}
        baseline_results = model_card.get("baseline_results", {})
        if isinstance(baseline_results, dict):
            horizon_metrics = baseline_results.get(horizon, {})
            if isinstance(horizon_metrics, dict):
                test_metrics = horizon_metrics.get("test_metrics", {})
                if isinstance(test_metrics, dict):
                    return test_metrics
        metrics = model_card.get("metrics", {})
        if isinstance(metrics, dict):
            horizon_metrics = metrics.get(horizon, {})
            if isinstance(horizon_metrics, dict):
                return horizon_metrics
        return {}

    def _pending_grant_owner_cache_path(self, resolved_owner: str) -> Path:
        return self.pending_grant_cache_dir / f"{self._normalize_owner_token(resolved_owner)}.parquet"

    def _pending_grant_scorer_python(self) -> Path | None:
        configured = (self.settings.pending_grant_scorer_python or "").strip()
        if configured:
            candidate = Path(configured)
            if candidate.exists():
                return candidate
        for candidate in (
            self.settings.repo_root / "etl" / ".venv-seed-backfill" / "bin" / "python",
            self.settings.repo_root / "etl" / ".venv" / "bin" / "python",
            self.settings.repo_root / "backend" / ".venv" / "bin" / "python",
        ):
            if candidate.exists():
                return candidate
        return None

    def _pending_grant_cache_is_fresh(self, cache_path: Path) -> bool:
        if not cache_path.exists():
            return False
        try:
            cache_mtime = cache_path.stat().st_mtime
        except OSError:
            return False
        source_paths = [
            self.owner_bridge_path,
            self.branch_history_dense_path,
            self.settings.repo_root / "etl" / "scripts" / "build_pending_grant_owner_cache.py",
            self.pending_grant_model_card_path,
            self.pending_grant_calibration_path,
            self.pending_grant_model_12m_path,
            self.pending_grant_model_24m_path,
            self.settings.etl_data_root / "ml" / "ml_feature_pending_grant_pipeline.parquet",
        ]
        for path in source_paths:
            if not path.exists():
                return False
            try:
                if path.stat().st_mtime > cache_mtime:
                    return False
            except OSError:
                return False
        return True

    def _ensure_pending_grant_owner_cache(self, resolved_owner: str) -> Path | None:
        cache_path = self._pending_grant_owner_cache_path(resolved_owner)
        if self._pending_grant_cache_is_fresh(cache_path):
            return cache_path

        scorer_python = self._pending_grant_scorer_python()
        script_path = self.settings.repo_root / "etl" / "scripts" / "build_pending_grant_owner_cache.py"
        if scorer_python is None or not script_path.exists():
            return cache_path if cache_path.exists() else None

        self.pending_grant_cache_dir.mkdir(parents=True, exist_ok=True)
        command = [
            str(scorer_python),
            str(script_path),
            "--owner-harmonized",
            resolved_owner,
            "--output-path",
            str(cache_path),
        ]
        result = subprocess.run(
            command,
            cwd=str(self.settings.repo_root),
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return cache_path if cache_path.exists() else None
        return cache_path if cache_path.exists() else None

    def get_owner_pending_grant_sections(
        self,
        owner_id: str,
        horizon: str = "24m",
        branch_jurisdiction_code: str | None = None,
        branch_wipo_field: str | None = None,
        branch_limit: int = 25,
    ) -> dict[str, object]:
        metrics = self._pending_grant_metrics(horizon)

        probability_col, rank_col, percentile_col = self._pending_grant_probability_columns(horizon)
        priority_sql = self._pending_grant_priority_tier_sql(percentile_col)
        support_sort_sql = self._pending_grant_support_sort_sql("office_support_level")

        safe_branch_limit = max(10, min(int(branch_limit), 100))

        with DuckDbProvider().connect() as con:
            resolved_owner = self._resolve_owner(con, self.owner_bridge_path, owner_id)
            if not resolved_owner:
                return {
                    "serving_ready": False,
                    "metrics": metrics,
                    "summary": {},
                    "jurisdictions": [],
                    "fields": [],
                    "branches": [],
                    "reason": "No harmonized owner match was found for this pending-grant slice.",
                }

            source_path = self.pending_grant_prediction_path
            if not self._analytics_source_available(source_path) and not source_path.exists():
                cache_path = self._ensure_pending_grant_owner_cache(resolved_owner)
                if cache_path is None or not cache_path.exists():
                    return {
                        "serving_ready": False,
                        "metrics": metrics,
                        "summary": {},
                        "jurisdictions": [],
                        "fields": [],
                        "branches": [],
                        "reason": "Pending-grant prediction artifact is not materialized and owner-scoped scoring fallback is unavailable.",
                    }
                source_path = cache_path
            owner_bridge_ref = self._analytics_relation(con, self.owner_bridge_path)
            branch_history_ref = self._analytics_relation(con, self.branch_history_dense_path)
            source_ref = self._analytics_relation(con, source_path)

            owner_cte = f"""
            with owner_families as (
                select distinct cast(docdb_family_id as varchar) as docdb_family_id
                from {owner_bridge_ref}
                where owner_name_harmonized = ?
                  and coalesce(is_primary_owner, false) = true
            ),
            owner_current_pending_pairs as (
                select docdb_family_id, jurisdiction_code, snapshot_date
                from (
                    select
                        cast(b.docdb_family_id as varchar) as docdb_family_id,
                        b.jurisdiction_code,
                        cast(b.snapshot_date as date) as snapshot_date,
                        coalesce(b.pending_branch_flag, false) as pending_branch_flag,
                        row_number() over (
                            partition by cast(b.docdb_family_id as varchar), b.jurisdiction_code
                            order by b.snapshot_year desc, b.snapshot_date desc
                        ) as rn
                    from {branch_history_ref} b
                    join owner_families f
                      on cast(b.docdb_family_id as varchar) = f.docdb_family_id
                ) ranked
                where rn = 1
                  and pending_branch_flag
            ),
            owner_pending as (
                select p.*
                from {source_ref} p
                join owner_current_pending_pairs c
                  on cast(p.docdb_family_id as varchar) = c.docdb_family_id
                 and p.jurisdiction_code = c.jurisdiction_code
                 and cast(p.as_of_date as date) = c.snapshot_date
            )
            """
            owner_parameters: list[object] = [resolved_owner]

            summary_query = owner_cte + f"""
            select
                count(*) as pending_pipeline_branch_count,
                count(distinct cast(docdb_family_id as varchar)) as pending_pipeline_family_count,
                (
                    select count(*)
                    from owner_current_pending_pairs
                ) as current_pending_branch_count,
                (
                    select count(distinct docdb_family_id)
                    from owner_current_pending_pairs
                ) as current_pending_family_count,
                cast(avg(grant_probability_calibrated_12m) as double) as pending_pipeline_avg_probability_12m,
                cast(avg(grant_probability_calibrated_24m) as double) as pending_pipeline_avg_probability_24m,
                cast(sum(grant_probability_calibrated_12m) as double) as pending_pipeline_expected_likely_grants_12m,
                cast(sum(grant_probability_calibrated_24m) as double) as pending_pipeline_expected_likely_grants_24m,
                cast(avg({percentile_col}) as double) as pending_pipeline_percentile,
                (
                    select office_support_level
                    from owner_pending
                    group by office_support_level
                    order by count(*) desc, {support_sort_sql} desc, office_support_level asc
                    limit 1
                ) as pending_pipeline_support_level,
                (
                    select jurisdiction_code
                    from owner_pending
                    group by jurisdiction_code
                    order by sum({probability_col}) desc, count(*) desc, jurisdiction_code asc
                    limit 1
                ) as pending_pipeline_top_jurisdiction,
                (
                    select primary_wipo_field
                    from owner_pending
                    group by primary_wipo_field
                    order by sum({probability_col}) desc, count(*) desc, primary_wipo_field asc
                    limit 1
                ) as pending_pipeline_top_field,
                (
                    select cast(docdb_family_id as varchar)
                    from owner_pending
                    order by {probability_col} desc, {percentile_col} desc, cast(docdb_family_id as varchar) asc
                    limit 1
                ) as top_branch_family_id,
                (
                    select jurisdiction_code
                    from owner_pending
                    order by {probability_col} desc, {percentile_col} desc, cast(docdb_family_id as varchar) asc
                    limit 1
                ) as top_branch_jurisdiction,
                (
                    select primary_wipo_field
                    from owner_pending
                    order by {probability_col} desc, {percentile_col} desc, cast(docdb_family_id as varchar) asc
                    limit 1
                ) as top_branch_field,
                (
                    select cast({probability_col} as double)
                    from owner_pending
                    order by {probability_col} desc, {percentile_col} desc, cast(docdb_family_id as varchar) asc
                    limit 1
                ) as top_branch_probability,
                (
                    select cast({percentile_col} as double)
                    from owner_pending
                    order by {probability_col} desc, {percentile_col} desc, cast(docdb_family_id as varchar) asc
                    limit 1
                ) as top_branch_percentile
            from owner_pending
            """
            summary_rows = self._query_rows(con, summary_query, owner_parameters)
            summary = summary_rows[0] if summary_rows else {}

            if not summary:
                return {
                    "serving_ready": False,
                    "metrics": metrics,
                    "summary": summary,
                    "jurisdictions": [],
                    "fields": [],
                    "branches": [],
                    "reason": "Pending-grant summary could not be computed for this owner.",
                }

            current_pending_branch_count = int(summary.get("current_pending_branch_count") or 0)
            pending_pipeline_branch_count = int(summary.get("pending_pipeline_branch_count") or 0)

            if current_pending_branch_count == 0:
                return {
                    "serving_ready": False,
                    "metrics": metrics,
                    "summary": summary,
                    "jurisdictions": [],
                    "fields": [],
                    "branches": [],
                    "reason": "This owner has no current pending family-jurisdiction branches in the branch-status ledger.",
                }

            if pending_pipeline_branch_count == 0:
                return {
                    "serving_ready": False,
                    "metrics": metrics,
                    "summary": summary,
                    "jurisdictions": [],
                    "fields": [],
                    "branches": [],
                    "reason": "This owner has current pending family-jurisdiction branches in the branch-status ledger, but none are in the scored pending-grant feature slice yet.",
                }

            jurisdictions_query = owner_cte + f"""
            select
                jurisdiction_code,
                office_support_level,
                count(*) as branch_count,
                count(distinct cast(docdb_family_id as varchar)) as family_count,
                cast(avg(grant_probability_calibrated_12m) as double) as avg_probability_12m,
                cast(avg(grant_probability_calibrated_24m) as double) as avg_probability_24m,
                cast(sum(grant_probability_calibrated_12m) as double) as expected_likely_grants_12m,
                cast(sum(grant_probability_calibrated_24m) as double) as expected_likely_grants_24m,
                cast(avg({percentile_col}) as double) as avg_percentile
            from owner_pending
            group by jurisdiction_code, office_support_level
            order by sum({probability_col}) desc, branch_count desc, jurisdiction_code asc
            limit 10
            """
            fields_query = owner_cte + f"""
            select
                primary_wipo_field,
                count(*) as branch_count,
                count(distinct cast(docdb_family_id as varchar)) as family_count,
                cast(avg(grant_probability_calibrated_12m) as double) as avg_probability_12m,
                cast(avg(grant_probability_calibrated_24m) as double) as avg_probability_24m,
                cast(sum(grant_probability_calibrated_12m) as double) as expected_likely_grants_12m,
                cast(sum(grant_probability_calibrated_24m) as double) as expected_likely_grants_24m,
                cast(avg({percentile_col}) as double) as avg_percentile
            from owner_pending
            group by primary_wipo_field
            order by sum({probability_col}) desc, branch_count desc, primary_wipo_field asc
            limit 10
            """
            branch_filters: list[str] = []
            branch_parameters = list(owner_parameters)
            if branch_jurisdiction_code:
                branch_filters.append("jurisdiction_code = ?")
                branch_parameters.append(str(branch_jurisdiction_code))
            if branch_wipo_field:
                branch_filters.append("primary_wipo_field = ?")
                branch_parameters.append(str(branch_wipo_field))
            branch_where_sql = ""
            if branch_filters:
                branch_where_sql = "where " + " and ".join(branch_filters)

            branches_query = owner_cte + f"""
            select
                cast(docdb_family_id as varchar) as docdb_family_id,
                jurisdiction_code,
                primary_wipo_field,
                cast(coalesce(pending_age_years, 0.0) as double) as pending_age_years,
                cast(coalesce(family_age_years, 0.0) as double) as family_age_years,
                cast(coalesce(family_blocking_power_score_asof, 0.0) as double) as family_blocking_power_score_asof,
                cast(coalesce(family_enforceability_score_asof, 0.0) as double) as family_enforceability_score_asof,
                cast(coalesce(family_rcf_score_asof, 0.0) as double) as family_rcf_score_asof,
                cast(coalesce(data_completeness_pct_asof, 0.0) as double) as data_completeness_pct_asof,
                cast(coalesce(grant_probability_calibrated_12m, 0.0) as double) as probability_12m,
                cast(coalesce(grant_probability_calibrated_24m, 0.0) as double) as probability_24m,
                cast(coalesce({probability_col}, 0.0) as double) as selected_probability,
                cast(coalesce({rank_col}, 0) as bigint) as rank_within_office_horizon,
                cast(coalesce({percentile_col}, 0.0) as double) as percentile_within_office_horizon,
                office_support_level,
                {priority_sql} as priority_tier
            from owner_pending
            {branch_where_sql}
            order by {probability_col} desc, {percentile_col} desc, cast(docdb_family_id as varchar) asc
            limit ?
            """
            branch_parameters.append(safe_branch_limit)
            return {
                "serving_ready": True,
                "metrics": metrics,
                "summary": summary,
                "jurisdictions": self._query_rows(con, jurisdictions_query, owner_parameters),
                "fields": self._query_rows(con, fields_query, owner_parameters),
                "branches": self._query_rows(con, branches_query, branch_parameters),
                "reason": "Pending-grant is served from current scored pending branches and should remain rank/percentile-first in the UI.",
            }

    def get_owner_risk_distribution(self, owner_id: str, horizon: str, as_of_year: int | None = None) -> list[dict[str, object]]:
        with DuckDbProvider().connect() as con:
            resolved_owner = self._resolve_owner(con, self.owner_bridge_path, owner_id)
            if not resolved_owner:
                return []
            owner_bridge_ref = self._analytics_relation(con, self.owner_bridge_path)
            phase04_ref = self._analytics_relation(con, self.phase04_prediction_path)
            year_filter = f" and extract(year from as_of_date) = {int(as_of_year)}" if as_of_year is not None else ""
            query = f"""
            with owner_families as (
                select cast(docdb_family_id as varchar) as docdb_family_id
                from {owner_bridge_ref}
                where owner_name_harmonized = ?
                  and coalesce(is_primary_owner, false) = true
            ),
            banded as (
                select
                    cast(risk_probability_calibrated as double) as risk_probability_calibrated,
                    cast(docdb_family_id as varchar) as docdb_family_id
                from {phase04_ref}
                where model_scope = 'family_jurisdiction_lapse_risk'
                  and horizon = ?
                  and isfinite(cast(risk_probability_calibrated as double))
                  {year_filter}
            )
            select
                case
                    when risk_probability_calibrated < 0.33 then 'low'
                    when risk_probability_calibrated < 0.66 then 'medium'
                    else 'high'
                end as risk_band,
                count(distinct b.docdb_family_id) as family_count,
                cast(count(distinct b.docdb_family_id) as double) / nullif((
                    select count(distinct b2.docdb_family_id)
                    from banded b2
                    join owner_families f2 on b2.docdb_family_id = f2.docdb_family_id
                ), 0) as share
            from banded b
            join owner_families f on b.docdb_family_id = f.docdb_family_id
            group by risk_band
            order by
              case risk_band when 'low' then 1 when 'medium' then 2 else 3 end
            """
            return self._query_rows(con, query, [resolved_owner, horizon])

    def get_latest_snapshot_year(self) -> int:
        core_serving_path = self.artifact_locator.resolve_core_serving_duckdb()
        if core_serving_path is not None:
            with self.duckdb_provider.connect() as con:
                self._attach_core_serving(con, core_serving_path)
                if self._core_table_exists(con, "portfolio_summary"):
                    row = con.execute("select extract(year from max(snapshot_date)) from core_db.portfolio_summary").fetchone()
                    if row and row[0] is not None:
                        return int(row[0])

        with self.duckdb_provider.connect() as con:
            summary_ref = self._analytics_relation(con, self.summary_path)
            row = con.execute(f"select extract(year from max(snapshot_date)) from {summary_ref}").fetchone()
            if row and row[0] is not None:
                return int(row[0])
            return date.today().year
