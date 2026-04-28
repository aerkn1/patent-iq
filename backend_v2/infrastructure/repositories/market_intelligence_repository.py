from __future__ import annotations

from pathlib import Path
from typing import Any

from config.settings import get_settings
from infrastructure.artifacts import ArtifactLocator
from infrastructure.duckdb import DuckDbProvider


class MarketIntelligenceRepository:
    SUPPORTED_YEAR_CAP = 2023

    def __init__(self) -> None:
        settings = get_settings()
        self.artifact_locator = ArtifactLocator(settings=settings)
        self.overview_path = settings.etl_data_root / "gold" / "gold_market_intelligence_overview.parquet"
        self.summary_path = settings.etl_data_root / "gold" / "gold_market_summary_pit.parquet"
        self.segment_path = settings.etl_data_root / "gold" / "gold_market_intelligence_segments.parquet"
        self.timeseries_path = settings.etl_data_root / "gold" / "gold_market_intelligence_timeseries.parquet"
        self.leaderboard_path = settings.etl_data_root / "gold" / "gold_market_leaderboard_pit.parquet"
        self.family_compare_path = settings.etl_data_root / "gold" / "gold_family_compare_pit.parquet"
        self.field_timeseries_path = settings.etl_data_root / "gold" / "gold_family_field_contributions_timeseries.parquet"
        self.market_overview_history_cache_path = (
            settings.cache_dir / f"market_overview_history_{self.SUPPORTED_YEAR_CAP}.parquet"
        )
        self.family_classification_mix_path = (
            settings.etl_data_root / "gold" / "gold_family_classification_mix_pit.parquet"
        )
        self.cpc_trend_path = settings.etl_data_root / "gold" / "gold_market_cpc_trend_pit.parquet"
        self.cpc_jurisdiction_path = settings.etl_data_root / "gold" / "gold_market_cpc_jurisdiction_trend_pit.parquet"
        self.citation_trend_path = settings.etl_data_root / "gold" / "gold_market_citation_trend_pit.parquet"
        self.citation_jurisdiction_path = (
            settings.etl_data_root / "gold" / "gold_market_citation_pressure_by_jurisdiction_pit.parquet"
        )
        self.citation_attacker_path = settings.etl_data_root / "gold" / "gold_market_attacker_leaderboard_pit.parquet"
        self.enriched_citation_network_path = settings.etl_data_root / "silver" / "silver_enriched_citation_network.parquet"
        self.family_classification_jurisdiction_path = (
            settings.etl_data_root / "gold" / "gold_family_classification_jurisdiction_pit.parquet"
        )
        self.member_publications_path = settings.etl_data_root / "silver" / "silver_family_member_publications.parquet"
        self.register_up_path = settings.etl_data_root / "silver" / "silver_ep_register_up_status.parquet"
        self.up_status_path = settings.etl_data_root / "silver" / "silver_up_status.parquet"
        self.family_jurisdiction_unrolled_path = (
            settings.etl_data_root / "silver" / "silver_family_jurisdiction_unrolled.parquet"
        )
        self._scope_summary_cache: dict[str, object] | None = None
        self._overview_snapshot_cache: dict[str, object] | None = None
        self._market_overview_history_cache: list[dict[str, object]] | None = None
        self._timeseries_cache: list[dict[str, object]] | None = None
        self._market_path_map: dict[Path, str] = {
            self.overview_path: "market_intelligence_overview",
            self.segment_path: "market_intelligence_segments",
            self.timeseries_path: "market_intelligence_timeseries",
        }
        self._analytics_path_map: dict[Path, str] = {
            self.summary_path: "market_summary_pit",
            self.leaderboard_path: "market_leaderboard_pit",
            self.family_compare_path: "family_compare_pit",
            self.field_timeseries_path: "family_field_contributions_timeseries",
            self.family_classification_mix_path: "family_classification_mix_pit",
            self.cpc_trend_path: "market_cpc_trend_pit",
            self.cpc_jurisdiction_path: "market_cpc_jurisdiction_trend_pit",
            self.citation_trend_path: "market_citation_trend_pit",
            self.citation_jurisdiction_path: "market_citation_pressure_by_jurisdiction_pit",
            self.citation_attacker_path: "market_attacker_leaderboard_pit",
            self.enriched_citation_network_path: "enriched_citation_network",
            self.family_classification_jurisdiction_path: "family_classification_jurisdiction_pit",
            self.member_publications_path: "family_member_publications",
            self.register_up_path: "ep_register_up_status",
            self.up_status_path: "up_status",
            self.family_jurisdiction_unrolled_path: "family_jurisdiction_unrolled",
        }

    def artifacts(self) -> list[Path]:
        market_serving_path = self.artifact_locator.resolve_market_serving_duckdb()
        analytics_serving_path = self.artifact_locator.resolve_analytics_serving_duckdb()
        serving_artifacts: list[Path] = []
        if market_serving_path is not None:
            serving_artifacts.append(market_serving_path)
        if analytics_serving_path is not None:
            serving_artifacts.append(analytics_serving_path)
        if serving_artifacts:
            return serving_artifacts
        return [
            self.overview_path,
            self.summary_path,
            self.segment_path,
            self.timeseries_path,
            self.leaderboard_path,
            self.family_classification_mix_path,
            self.cpc_trend_path,
            self.cpc_jurisdiction_path,
            self.citation_trend_path,
            self.citation_jurisdiction_path,
            self.citation_attacker_path,
            self.enriched_citation_network_path,
            self.family_classification_jurisdiction_path,
            self.member_publications_path,
            self.register_up_path,
            self.up_status_path,
            self.family_jurisdiction_unrolled_path,
        ]

    def _attach_market_serving(self, con: "DuckDbProvider", market_serving_path: Path) -> None:
        attached = con.execute("pragma database_list").fetchall()
        if any(str(row[1]) == "market_db" for row in attached):
            return
        con.execute(f"ATTACH '{market_serving_path}' AS market_db (READ_ONLY)")

    def _market_table_exists(self, con: "DuckDbProvider", table_name: str) -> bool:
        row = con.execute(
            """
            select 1
            from information_schema.tables
            where table_catalog = 'market_db'
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

    def _manifest_table_available(self, snapshot_key: str, table_name: str) -> bool:
        manifest = self.artifact_locator.resolve_serving_manifest()
        if manifest is None:
            return False
        snapshot = manifest.snapshots.get(snapshot_key)
        if snapshot is None:
            return False
        return table_name in snapshot.tables

    def _source_available(self, path: Path) -> bool:
        if path.exists():
            return True
        market_table = self._market_path_map.get(path)
        if market_table is not None and self._manifest_table_available("market", market_table):
            market_serving_path = self.artifact_locator.resolve_market_serving_duckdb()
            return market_serving_path is not None and market_serving_path.exists()
        analytics_table = self._analytics_path_map.get(path)
        if analytics_table is not None and self._manifest_table_available("analytics", analytics_table):
            analytics_serving_path = self.artifact_locator.resolve_analytics_serving_duckdb()
            return analytics_serving_path is not None and analytics_serving_path.exists()
        return False

    def _relation_for_path(self, con: "DuckDbProvider", path: Path) -> str:
        market_table = self._market_path_map.get(path)
        market_serving_path = self.artifact_locator.resolve_market_serving_duckdb()
        if market_table is not None and market_serving_path is not None and market_serving_path.exists():
            self._attach_market_serving(con, market_serving_path)
            if self._market_table_exists(con, market_table):
                return f"market_db.{market_table}"
        if market_table is not None and not self.artifact_locator.settings.raw_parquet_fallback_enabled:
            raise RuntimeError(
                f"Market serving table '{market_table}' is required for '{path.name}' because raw parquet fallback is disabled."
            )
        analytics_table = self._analytics_path_map.get(path)
        analytics_serving_path = self.artifact_locator.resolve_analytics_serving_duckdb()
        if analytics_table is not None and analytics_serving_path is not None and analytics_serving_path.exists():
            self._attach_analytics_serving(con, analytics_serving_path)
            if self._analytics_table_exists(con, analytics_table):
                return f"analytics_db.{analytics_table}"
        if analytics_table is not None and not self.artifact_locator.settings.raw_parquet_fallback_enabled:
            raise RuntimeError(
                f"Analytics serving table '{analytics_table}' is required for '{path.name}' because raw parquet fallback is disabled."
            )
        return f"read_parquet('{path}')"

    def _query_rows(
        self,
        con: "DuckDbProvider",
        query: str,
        parameters: list[object] | tuple[object, ...],
    ) -> list[dict[str, object]]:
        rows = con.execute(query, parameters).fetchall()
        if not rows:
            return []
        columns = [name for name, *_ in con.description]
        return [dict(zip(columns, row)) for row in rows]

    def _query_scalar(
        self,
        path: Path,
        query: str,
        parameters: list[object] | tuple[object, ...] = (),
        column: str = "value",
    ) -> Any:
        if not path.exists():
            return None
        with DuckDbProvider().connect() as con:
            rows = self._query_rows(con, query, parameters)
        if not rows:
            return None
        return rows[0].get(column)

    def _latest_year(self, path: Path, year_column: str = "as_of_year") -> int | None:
        if not self._source_available(path):
            return None
        with DuckDbProvider().connect() as con:
            relation = self._relation_for_path(con, path)
            rows = self._query_rows(con, f"select max({year_column}) as value from {relation}", ())
        if not rows:
            return None
        value = rows[0].get("value")
        return int(value) if value is not None else None

    def _supported_year(
        self,
        path: Path,
        requested_year: int | None = None,
        year_column: str = "as_of_year",
    ) -> int | None:
        if requested_year is not None:
            return min(int(requested_year), self.SUPPORTED_YEAR_CAP)
        latest_year = self._latest_year(path, year_column=year_column)
        if latest_year is None:
            return None
        return min(latest_year, self.SUPPORTED_YEAR_CAP)

    def _latest_publication_year(self) -> int | None:
        if not self._source_available(self.member_publications_path):
            return None
        with DuckDbProvider().connect() as con:
            member_ref = self._relation_for_path(con, self.member_publications_path)
            rows = self._query_rows(
                con,
                f"""
                select max(cast(year(publn_date) as integer)) as value
                from {member_ref}
                where cast(year(publn_date) as integer) between 1900 and 9998
                """,
                (),
            )
        if not rows:
            return None
        value = rows[0].get("value")
        return int(value) if value is not None else None

    def get_scope_summary(self) -> dict[str, object]:
        if self._scope_summary_cache is not None:
            return dict(self._scope_summary_cache)
        summary_snapshot_date = None
        latest_market_year = None
        latest_comparable_market_year = None
        latest_cpc_year = self._latest_year(self.cpc_trend_path) if self._source_available(self.cpc_trend_path) else None
        market_serving_path = self.artifact_locator.resolve_market_serving_duckdb()
        if market_serving_path is not None and market_serving_path.exists():
            with DuckDbProvider().connect() as con:
                self._attach_market_serving(con, market_serving_path)
                if self._market_table_exists(con, "market_intelligence_segments") and self._market_table_exists(
                    con,
                    "market_intelligence_timeseries",
                ):
                    segment_rows = self._query_rows(
                        con,
                        """
                        select
                            count(distinct wipo_industry_code) as covered_field_count,
                            max(latest_year) as latest_market_year,
                            max(latest_comparable_year) as latest_comparable_market_year,
                            max(snapshot_date) as snapshot_date
                        from market_db.market_intelligence_segments
                        """,
                        (),
                    )
                    timeseries_rows = self._query_rows(
                        con,
                        """
                        select
                            min(family_priority_year) as start_year,
                            max(family_priority_year) as end_year
                        from market_db.market_intelligence_timeseries
                        """,
                        (),
                    )
                    if segment_rows and timeseries_rows:
                        payload = dict(segment_rows[0])
                        payload.update(timeseries_rows[0])
                        payload["end_year"] = min(int(payload.get("end_year") or 0), self.SUPPORTED_YEAR_CAP)
                        payload["snapshot_date"] = payload.get("snapshot_date")
                        payload["latest_market_year"] = (
                            min(int(payload.get("latest_market_year")), self.SUPPORTED_YEAR_CAP)
                            if payload.get("latest_market_year") is not None
                            else None
                        )
                        comparable_year = payload.get("latest_comparable_market_year")
                        payload["latest_comparable_market_year"] = (
                            min(int(comparable_year), self.SUPPORTED_YEAR_CAP) if comparable_year is not None else None
                        )
                        payload["latest_cpc_year"] = (
                            min(int(latest_cpc_year), self.SUPPORTED_YEAR_CAP) if latest_cpc_year is not None else None
                        )
                        self._scope_summary_cache = dict(payload)
                        return dict(payload)
        if not self._source_available(self.timeseries_path):
            return {}
        with DuckDbProvider().connect() as con:
            if self._source_available(self.summary_path):
                latest_market_year = self._latest_year(self.summary_path)
                summary_ref = self._relation_for_path(con, self.summary_path)
                summary_rows = self._query_rows(
                    con,
                    f"select max(current_snapshot_date) as value from {summary_ref}",
                    (),
                )
                if summary_rows:
                    summary_snapshot_date = summary_rows[0].get("value")
            timeseries_ref = self._relation_for_path(con, self.timeseries_path)
            query = f"""
            select
                count(distinct wipo_industry_code) as covered_field_count,
                min(family_priority_year) as start_year,
                max(family_priority_year) as end_year,
                max(latest_comparable_year) as latest_comparable_market_year
            from {timeseries_ref}
            """
            rows = self._query_rows(con, query, ())
        if not rows:
            return {}
        payload = rows[0]
        payload["end_year"] = min(int(payload.get("end_year") or 0), self.SUPPORTED_YEAR_CAP)
        payload["snapshot_date"] = summary_snapshot_date
        payload["latest_market_year"] = (
            min(int(latest_market_year), self.SUPPORTED_YEAR_CAP) if latest_market_year is not None else None
        )
        comparable_year = payload.get("latest_comparable_market_year") or latest_comparable_market_year
        payload["latest_comparable_market_year"] = (
            min(int(comparable_year), self.SUPPORTED_YEAR_CAP) if comparable_year is not None else None
        )
        payload["latest_cpc_year"] = min(int(latest_cpc_year), self.SUPPORTED_YEAR_CAP) if latest_cpc_year is not None else None
        self._scope_summary_cache = dict(payload)
        return dict(payload)

    def get_market_overview_history(self) -> list[dict[str, object]]:
        if self._market_overview_history_cache is not None:
            return [dict(row) for row in self._market_overview_history_cache]
        if self.market_overview_history_cache_path.exists():
            try:
                with DuckDbProvider().connect() as con:
                    rows = self._query_rows(
                        con,
                        f"""
                        select *
                        from read_parquet('{self.market_overview_history_cache_path}')
                        order by as_of_year asc
                        """,
                        (),
                    )
                self._market_overview_history_cache = [dict(row) for row in rows]
                return [dict(row) for row in rows]
            except Exception:
                self.market_overview_history_cache_path.unlink(missing_ok=True)
        if not self._source_available(self.family_compare_path) or not self._source_available(self.segment_path):
            return []
        with DuckDbProvider().connect() as con:
            segment_ref = self._relation_for_path(con, self.segment_path)
            family_compare_ref = self._relation_for_path(con, self.family_compare_path)
            query = f"""
            with served_segments as (
                select distinct
                    wipo_industry_code
                from {segment_ref}
            ),
            family_base as (
                select
                    cast(fc.as_of_year as integer) as as_of_year,
                    fc.current_snapshot_date,
                    fc.docdb_family_id,
                    fc.family_composite_status_asof,
                    coalesce(fc.family_blocking_power_score_asof, 0.0) as family_blocking_power_score_asof,
                    coalesce(fc.family_enforceability_score_asof, 0.0) as family_enforceability_score_asof,
                    coalesce(fc.pre_asof_forward_citations_clean, 0.0) as pre_asof_forward_citations_clean,
                    fc.owner_name_harmonized_current
                from {family_compare_ref} fc
                where cast(fc.as_of_year as integer) <= {self.SUPPORTED_YEAR_CAP}
                  and fc.primary_wipo_field_current in (select wipo_industry_code from served_segments)
            ),
            owner_counts as (
                select
                    as_of_year,
                    owner_name_harmonized_current,
                    count(*) as owner_family_count
                from family_base
                where trim(coalesce(owner_name_harmonized_current, '')) not in ('', '_', 'UNKNOWN', 'UNKNOWN_OWNER', 'UNASSIGNED')
                group by as_of_year, owner_name_harmonized_current
            ),
            yearly_owner_stats as (
                select
                    as_of_year,
                    count(*) as owner_count_asof,
                    max(owner_family_count) as top_owner_family_count_asof
                from owner_counts
                group by as_of_year
            )
            select
                fb.as_of_year,
                max(fb.current_snapshot_date) as current_snapshot_date,
                count(*) as market_family_count_asof,
                sum(case when fb.family_composite_status_asof = 'pending_emerging' then 1 else 0 end) as pending_family_count_asof,
                sum(case when fb.family_composite_status_asof = 'fully_active' then 1 else 0 end) as fully_active_family_count_asof,
                sum(case when fb.family_composite_status_asof = 'partially_lapsed' then 1 else 0 end) as partially_lapsed_family_count_asof,
                sum(case when fb.family_composite_status_asof = 'dead' then 1 else 0 end) as dead_family_count_asof,
                coalesce(yos.owner_count_asof, 0) as owner_count_asof,
                avg(fb.family_blocking_power_score_asof) as avg_blocking_power_score_asof,
                avg(fb.family_enforceability_score_asof) as avg_enforceability_score_asof,
                avg(fb.pre_asof_forward_citations_clean) as avg_forward_citations_clean_asof,
                sum(fb.pre_asof_forward_citations_clean) as total_forward_citations_clean_asof,
                case
                    when count(*) = 0 then 0.0
                    else coalesce(yos.top_owner_family_count_asof, 0) / count(*)
                end as top_owner_share_asof
            from family_base fb
            left join yearly_owner_stats yos
              on fb.as_of_year = yos.as_of_year
            group by fb.as_of_year, yos.owner_count_asof, yos.top_owner_family_count_asof
            order by fb.as_of_year asc
            """
            cache_tmp_path = Path(f"{self.market_overview_history_cache_path}.tmp")
            cache_tmp_path.unlink(missing_ok=True)
            try:
                self.market_overview_history_cache_path.parent.mkdir(parents=True, exist_ok=True)
                con.execute(
                    f"""
                    copy (
                        {query}
                    ) to '{cache_tmp_path}' (format parquet, compression zstd)
                    """
                )
                cache_tmp_path.replace(self.market_overview_history_cache_path)
                rows = self._query_rows(
                    con,
                    f"""
                    select *
                    from read_parquet('{self.market_overview_history_cache_path}')
                    order by as_of_year asc
                    """,
                    (),
                )
            except Exception:
                cache_tmp_path.unlink(missing_ok=True)
                rows = self._query_rows(con, query, ())
        self._market_overview_history_cache = [dict(row) for row in rows]
        return [dict(row) for row in rows]

    def get_overview_snapshot(self) -> dict[str, object]:
        if self._overview_snapshot_cache is not None:
            return dict(self._overview_snapshot_cache)
        market_serving_path = self.artifact_locator.resolve_market_serving_duckdb()
        if market_serving_path is not None and market_serving_path.exists():
            with DuckDbProvider().connect() as con:
                self._attach_market_serving(con, market_serving_path)
                if self._market_table_exists(con, "market_intelligence_overview"):
                    rows = self._query_rows(
                        con,
                        """
                        select
                            segment_count,
                            rising_segment_count,
                            cooling_segment_count,
                            total_family_count,
                            avg_segment_family_count
                        from market_db.market_intelligence_overview
                        limit 1
                        """,
                        (),
                    )
                    payload = rows[0] if rows else {}
                    self._overview_snapshot_cache = dict(payload)
                    return dict(payload)
        if not self._source_available(self.overview_path):
            return {}
        with DuckDbProvider().connect() as con:
            overview_ref = self._relation_for_path(con, self.overview_path)
            rows = self._query_rows(
                con,
                f"""
                select
                    segment_count,
                    rising_segment_count,
                    cooling_segment_count,
                    total_family_count,
                    avg_segment_family_count
                from {overview_ref}
                limit 1
                """,
                (),
            )
        payload = rows[0] if rows else {}
        self._overview_snapshot_cache = dict(payload)
        return dict(payload)

    def get_segments(self, as_of_year: int | None = None) -> list[dict[str, object]]:
        market_serving_path = self.artifact_locator.resolve_market_serving_duckdb()
        scope = self.get_scope_summary()
        effective_year = self._supported_year(
            self.summary_path,
            requested_year=as_of_year or (
                int(scope.get("latest_market_year")) if scope.get("latest_market_year") is not None else None
            ),
        )
        if market_serving_path is not None and market_serving_path.exists():
            with DuckDbProvider().connect() as con:
                self._attach_market_serving(con, market_serving_path)
                if self._market_table_exists(con, "market_intelligence_segments"):
                    if self._source_available(self.summary_path) and effective_year is not None:
                        summary_ref = self._relation_for_path(con, self.summary_path)
                        query = f"""
                        with latest_summary as (
                            select
                                wipo_industry_code,
                                as_of_year,
                                current_snapshot_date,
                                segment_heat_state_asof,
                                segment_market_state_ui_safe_asof,
                                segment_priority_year_incomplete_asof,
                                segment_latest_comparable_year,
                                segment_family_count_stock_asof,
                                segment_priority_year_family_count_asof,
                                segment_prior_priority_year_family_count_asof,
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
                            from {summary_ref}
                            where as_of_year = ?
                        )
                        select
                            segments.segment_id,
                            segments.wipo_industry_code,
                            segments.market_state,
                            segments.total_family_count,
                            segments.latest_year,
                            segments.latest_comparable_year,
                            segments.latest_year_incomplete,
                            summary.as_of_year as latest_market_year,
                            coalesce(summary.current_snapshot_date, segments.snapshot_date) as snapshot_date,
                            summary.segment_heat_state_asof,
                            summary.segment_market_state_ui_safe_asof,
                            summary.segment_priority_year_incomplete_asof,
                            summary.segment_latest_comparable_year,
                            summary.segment_family_count_stock_asof,
                            summary.segment_priority_year_family_count_asof,
                            summary.segment_prior_priority_year_family_count_asof,
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
                        from market_db.market_intelligence_segments as segments
                        left join latest_summary as summary
                          on summary.wipo_industry_code = segments.wipo_industry_code
                        order by segments.total_family_count desc, segments.wipo_industry_code asc
                        """
                        return self._query_rows(con, query, [int(effective_year)])
                    query = """
                    select
                        segment_id,
                        wipo_industry_code,
                        market_state,
                        total_family_count,
                        latest_year,
                        latest_comparable_year,
                        latest_year_incomplete,
                        snapshot_date
                    from market_db.market_intelligence_segments
                    order by total_family_count desc, wipo_industry_code asc
                    """
                    return self._query_rows(con, query, ())
        if not self._source_available(self.segment_path):
            return []
        with DuckDbProvider().connect() as con:
            segment_ref = self._relation_for_path(con, self.segment_path)
            if self._source_available(self.summary_path) and effective_year is not None:
                summary_ref = self._relation_for_path(con, self.summary_path)
                query = f"""
                with latest_summary as (
                    select
                        wipo_industry_code,
                        as_of_year,
                        current_snapshot_date,
                        segment_heat_state_asof,
                        segment_market_state_ui_safe_asof,
                        segment_priority_year_incomplete_asof,
                        segment_latest_comparable_year,
                        segment_family_count_stock_asof,
                        segment_priority_year_family_count_asof,
                        segment_prior_priority_year_family_count_asof,
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
                    from {summary_ref}
                    where as_of_year = ?
                )
                select
                    segments.segment_id,
                    segments.wipo_industry_code,
                    segments.market_state,
                    segments.total_family_count,
                    segments.latest_year,
                    segments.latest_comparable_year,
                    segments.latest_year_incomplete,
                    summary.as_of_year as latest_market_year,
                    summary.current_snapshot_date as snapshot_date,
                    summary.segment_heat_state_asof,
                    summary.segment_market_state_ui_safe_asof,
                    summary.segment_priority_year_incomplete_asof,
                    summary.segment_latest_comparable_year,
                    summary.segment_family_count_stock_asof,
                    summary.segment_priority_year_family_count_asof,
                    summary.segment_prior_priority_year_family_count_asof,
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
                from {segment_ref} as segments
                left join latest_summary as summary
                  on summary.wipo_industry_code = segments.wipo_industry_code
                order by segments.total_family_count desc, segments.wipo_industry_code asc
                """
                return self._query_rows(con, query, [int(effective_year)])
            query = f"""
            select
                segment_id,
                wipo_industry_code,
                market_state,
                total_family_count,
                latest_year,
                latest_comparable_year,
                latest_year_incomplete
            from {segment_ref}
            order by total_family_count desc, wipo_industry_code asc
            """
            return self._query_rows(con, query, ())

    def get_timeseries(self, segment_id: str | None = None) -> list[dict[str, object]]:
        market_serving_path = self.artifact_locator.resolve_market_serving_duckdb()
        if segment_id is None and self._timeseries_cache is not None:
            return [dict(row) for row in self._timeseries_cache]
        if market_serving_path is not None and market_serving_path.exists():
            with DuckDbProvider().connect() as con:
                self._attach_market_serving(con, market_serving_path)
                if self._market_table_exists(con, "market_intelligence_timeseries"):
                    parameters: list[object] = []
                    filters = f" and cast(family_priority_year as integer) <= {self.SUPPORTED_YEAR_CAP}"
                    if segment_id:
                        filters += " and wipo_industry_code = ?"
                        parameters.append(segment_id)
                    query = f"""
                    select
                        family_priority_year,
                        wipo_industry_code,
                        family_count,
                        prior_family_count,
                        market_state,
                        market_state_ui_safe,
                        is_recent_priority_year_incomplete,
                        latest_comparable_year,
                        snapshot_date
                    from market_db.market_intelligence_timeseries
                    where true
                    {filters}
                    order by wipo_industry_code asc, family_priority_year asc
                    """
                    rows = self._query_rows(con, query, parameters)
                    if segment_id is None:
                        self._timeseries_cache = [dict(row) for row in rows]
                    return [dict(row) for row in rows]
        if not self._source_available(self.timeseries_path):
            return []
        with DuckDbProvider().connect() as con:
            timeseries_ref = self._relation_for_path(con, self.timeseries_path)
            parameters: list[object] = []
            filters = f" and cast(family_priority_year as integer) <= {self.SUPPORTED_YEAR_CAP}"
            if segment_id:
                filters += " and wipo_industry_code = ?"
                parameters.append(segment_id)
            query = f"""
            select
                family_priority_year,
                wipo_industry_code,
                family_count,
                prior_family_count,
                market_state,
                market_state_ui_safe,
                is_recent_priority_year_incomplete,
                latest_comparable_year
            from {timeseries_ref}
            where true
            {filters}
            order by wipo_industry_code asc, family_priority_year asc
            """
            rows = self._query_rows(con, query, parameters)
        if segment_id is None:
            self._timeseries_cache = [dict(row) for row in rows]
        return [dict(row) for row in rows]

    def get_segment_owners(
        self,
        segment_id: str,
        as_of_year: int | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict[str, object]]:
        if not self._source_available(self.leaderboard_path):
            return []
        effective_year = self._supported_year(self.leaderboard_path, requested_year=as_of_year)
        if effective_year is None:
            return []
        with DuckDbProvider().connect() as con:
            leaderboard_ref = self._relation_for_path(con, self.leaderboard_path)
            parameters: list[object] = [segment_id]
            filters = """
              and leaderboard_entity_type = 'owner'
              and trim(coalesce(owner_name_display_current, owner_name_harmonized, '')) not in ('', '_', 'UNKNOWN', 'UNKNOWN_OWNER', 'UNASSIGNED')
            """
            if effective_year is not None:
                filters += " and as_of_year = ?"
                parameters.append(int(effective_year))
            query = f"""
            select
                *,
                count(*) over () as total_count
            from {leaderboard_ref}
            where segment_key = ?
            {filters}
            order by as_of_year desc, leaderboard_rank asc, owner_name_display_current asc
            limit ?
            offset ?
            """
            parameters.extend([int(limit), int(offset)])
            return self._query_rows(con, query, parameters)

    def get_segment_families(
        self,
        segment_id: str,
        as_of_year: int | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict[str, object]]:
        if not self._source_available(self.leaderboard_path):
            return []
        effective_year = self._supported_year(self.leaderboard_path, requested_year=as_of_year)
        if effective_year is None:
            return []
        with DuckDbProvider().connect() as con:
            leaderboard_ref = self._relation_for_path(con, self.leaderboard_path)
            family_compare_ref = self._relation_for_path(con, self.family_compare_path)
            parameters: list[object] = [segment_id, int(effective_year), int(limit), int(offset), int(effective_year)]
            query = f"""
            with ranked_families as (
                select
                    as_of_year,
                    leaderboard_rank,
                    docdb_family_id,
                    avg_blocking_score_asof,
                    total_blocking_score_asof,
                    field_presence_weight_asof,
                    family_composite_status_asof,
                    count(*) over () as total_count
                from {leaderboard_ref}
                where segment_key = ?
                  and leaderboard_entity_type = 'family'
                  and as_of_year = ?
                order by leaderboard_rank asc, docdb_family_id asc
                limit ?
                offset ?
            ),
            family_owner as (
                select
                    docdb_family_id,
                    max(owner_name_harmonized_current) as owner_name_harmonized_current
                from {family_compare_ref}
                where as_of_year = ?
                  and docdb_family_id in (select docdb_family_id from ranked_families)
                group by docdb_family_id
            )
            select
                ranked_families.*,
                family_owner.owner_name_harmonized_current
            from ranked_families
            left join family_owner
              on family_owner.docdb_family_id = ranked_families.docdb_family_id
            order by ranked_families.leaderboard_rank asc, ranked_families.docdb_family_id asc
            """
            return self._query_rows(con, query, parameters)

    def get_segment_field_jurisdictions(
        self,
        segment_id: str,
        as_of_year: int | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict[str, object]]:
        if not self._source_available(self.cpc_jurisdiction_path) or not self._source_available(self.summary_path):
            return []
        effective_year = self._supported_year(self.cpc_jurisdiction_path, requested_year=as_of_year)
        if effective_year is None:
            return []
        with DuckDbProvider().connect() as con:
            summary_ref = self._relation_for_path(con, self.summary_path)
            cpc_jurisdiction_ref = self._relation_for_path(con, self.cpc_jurisdiction_path)
            parameters: list[object] = [int(effective_year), segment_id, int(effective_year), segment_id, int(limit), int(offset)]
            query = f"""
            with segment_basis as (
                select
                    wipo_industry_code,
                    as_of_year,
                    segment_family_count_stock_asof,
                    segment_active_family_count_asof
                from {summary_ref}
                where as_of_year = ?
                  and wipo_industry_code = ?
            ),
            jurisdiction_rollup as (
                select
                    as_of_year,
                    wipo_field,
                    jurisdiction_code,
                    max(segment_family_count_basis_asof) as jurisdiction_family_count_asof,
                    max(segment_active_family_count_basis_asof) as jurisdiction_active_family_count_asof,
                    count(distinct cpc_main_group) as cpc_group_count
                from {cpc_jurisdiction_ref}
                where as_of_year = ?
                  and wipo_field = ?
                group by as_of_year, wipo_field, jurisdiction_code
            )
            select
                jurisdiction_rollup.*,
                coalesce(segment_basis.segment_family_count_stock_asof, 0) as segment_family_count_stock_asof,
                coalesce(segment_basis.segment_active_family_count_asof, 0) as segment_active_family_count_asof,
                case
                    when coalesce(segment_basis.segment_family_count_stock_asof, 0) = 0 then 0.0
                    else jurisdiction_rollup.jurisdiction_family_count_asof / segment_basis.segment_family_count_stock_asof
                end as jurisdiction_family_share_within_segment_asof,
                case
                    when coalesce(segment_basis.segment_active_family_count_asof, 0) = 0 then 0.0
                    else jurisdiction_rollup.jurisdiction_active_family_count_asof / segment_basis.segment_active_family_count_asof
                end as jurisdiction_active_family_share_within_segment_asof,
                count(*) over () as total_count
            from jurisdiction_rollup
            left join segment_basis
              on segment_basis.wipo_industry_code = jurisdiction_rollup.wipo_field
             and segment_basis.as_of_year = jurisdiction_rollup.as_of_year
            order by
                jurisdiction_rollup.jurisdiction_family_count_asof desc,
                jurisdiction_rollup.jurisdiction_active_family_count_asof desc,
                jurisdiction_rollup.jurisdiction_code asc
            limit ?
            offset ?
            """
            return self._query_rows(con, query, parameters)

    def get_segment_cpc_jurisdictions(
        self,
        segment_id: str,
        as_of_year: int | None = None,
        cpc_main_group: str | None = None,
        jurisdiction_code: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict[str, object]]:
        if not self._source_available(self.cpc_jurisdiction_path):
            return []
        effective_year = self._supported_year(self.cpc_jurisdiction_path, requested_year=as_of_year)
        if effective_year is None:
            return []
        with DuckDbProvider().connect() as con:
            cpc_jurisdiction_ref = self._relation_for_path(con, self.cpc_jurisdiction_path)
            parameters: list[object] = [int(effective_year), segment_id]
            filters = ""
            if cpc_main_group:
                filters += " and cpc_main_group ilike ?"
                parameters.append(f"%{cpc_main_group.strip()}%")
            if jurisdiction_code:
                filters += " and jurisdiction_code ilike ?"
                parameters.append(f"%{jurisdiction_code.strip()}%")
            query = f"""
            select
                *,
                count(*) over () as total_count
            from {cpc_jurisdiction_ref}
            where as_of_year = ?
              and wipo_field = ?
            {filters}
            order by
                family_count_asof desc,
                citation_pressure_index_asof desc,
                cpc_main_group asc,
                jurisdiction_code asc
            limit ?
            offset ?
            """
            parameters.extend([int(limit), int(offset)])
            return self._query_rows(con, query, parameters)

    def get_segment_cpc_owners(
        self,
        segment_id: str,
        cpc_main_group: str,
        as_of_year: int | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict[str, object]]:
        if not self._source_available(self.family_compare_path) or not self._source_available(self.family_classification_mix_path):
            return []
        effective_year = self._supported_year(self.family_compare_path, requested_year=as_of_year)
        if effective_year is None:
            return []
        normalized_cpc = cpc_main_group.strip()
        if not normalized_cpc:
            return []
        with DuckDbProvider().connect() as con:
            family_compare_ref = self._relation_for_path(con, self.family_compare_path)
            family_classification_ref = self._relation_for_path(con, self.family_classification_mix_path)
            parameters: list[object] = [
                int(effective_year),
                segment_id,
                normalized_cpc,
                normalized_cpc,
                int(limit),
                int(offset),
            ]
            query = f"""
            with cpc_families as (
                select
                    fc.as_of_year,
                    fc.primary_wipo_field_current as wipo_field,
                    fc.owner_name_harmonized_current as owner_name_harmonized,
                    fc.owner_name_display_current as owner_name_display_current,
                    fc.docdb_family_id,
                    cast(coalesce(fc.active_jurisdiction_count_asof, 0.0) > 0 as boolean) as is_active_family_asof,
                    coalesce(fc.family_blocking_power_score_asof, 0.0) as family_blocking_power_score_asof,
                    coalesce(fc.family_enforceability_score_asof, 0.0) as family_enforceability_score_asof
                from {family_compare_ref} fc
                inner join {family_classification_ref} fcm
                  on fcm.docdb_family_id = fc.docdb_family_id
                 and fcm.as_of_year = fc.as_of_year
                where fc.as_of_year = ?
                  and fc.primary_wipo_field_current = ?
                  and list_contains(fcm.cpc_main_groups_asof, ?)
                  and trim(upper(coalesce(fc.owner_name_display_current, fc.owner_name_harmonized_current, ''))) not in (
                    '',
                    '_',
                    'UNKNOWN',
                    'UNKNOWN_OWNER',
                    'UNASSIGNED'
                  )
            ),
            cpc_totals as (
                select
                    count(distinct docdb_family_id) as cpc_family_count_asof,
                    count(distinct case when is_active_family_asof then docdb_family_id end) as cpc_active_family_count_asof
                from cpc_families
            ),
            owner_rollup as (
                select
                    as_of_year,
                    wipo_field,
                    owner_name_harmonized,
                    max(owner_name_display_current) as owner_name_display_current,
                    count(distinct docdb_family_id) as owner_family_count_in_cpc_asof,
                    count(distinct case when is_active_family_asof then docdb_family_id end) as owner_active_family_count_in_cpc_asof,
                    avg(family_blocking_power_score_asof) as avg_blocking_score_asof,
                    avg(family_enforceability_score_asof) as avg_enforceability_score_asof
                from cpc_families
                group by as_of_year, wipo_field, owner_name_harmonized
            ),
            ranked as (
                select
                    owner_rollup.*,
                    row_number() over (
                        order by owner_family_count_in_cpc_asof desc,
                                 owner_active_family_count_in_cpc_asof desc,
                                 avg_blocking_score_asof desc,
                                 owner_name_display_current asc
                    ) as leaderboard_rank
                from owner_rollup
            )
            select
                ranked.as_of_year,
                ranked.wipo_field,
                ? as cpc_main_group,
                ranked.leaderboard_rank,
                ranked.owner_name_harmonized,
                ranked.owner_name_display_current,
                ranked.owner_family_count_in_cpc_asof,
                ranked.owner_active_family_count_in_cpc_asof,
                case
                    when coalesce(cpc_totals.cpc_family_count_asof, 0) = 0 then 0.0
                    else ranked.owner_family_count_in_cpc_asof / cpc_totals.cpc_family_count_asof
                end as owner_family_share_within_cpc_asof,
                case
                    when coalesce(cpc_totals.cpc_active_family_count_asof, 0) = 0 then 0.0
                    else ranked.owner_active_family_count_in_cpc_asof / cpc_totals.cpc_active_family_count_asof
                end as owner_active_family_share_within_cpc_asof,
                ranked.avg_blocking_score_asof,
                ranked.avg_enforceability_score_asof,
                count(*) over () as total_count
            from ranked
            cross join cpc_totals
            order by ranked.leaderboard_rank asc, ranked.owner_name_display_current asc
            limit ?
            offset ?
            """
            return self._query_rows(con, query, parameters)

    def get_leading_jurisdictions(
        self,
        as_of_year: int | None = None,
        limit_per_field: int = 5,
    ) -> list[dict[str, object]]:
        if not self._source_available(self.family_classification_jurisdiction_path) or not self._source_available(self.summary_path):
            return []
        effective_year = self._supported_year(self.family_classification_jurisdiction_path, requested_year=as_of_year)
        if effective_year is None:
            return []
        with DuckDbProvider().connect() as con:
            segment_ref = self._relation_for_path(con, self.segment_path)
            summary_ref = self._relation_for_path(con, self.summary_path)
            family_classification_jurisdiction_ref = self._relation_for_path(con, self.family_classification_jurisdiction_path)
            parameters: list[object] = [int(effective_year), int(effective_year), int(limit_per_field)]
            query = f"""
            with served_segments as (
                select distinct
                    wipo_industry_code
                from {segment_ref}
            ),
            field_basis as (
                select
                    wipo_industry_code,
                    segment_family_count_stock_asof,
                    segment_active_family_count_asof
                from {summary_ref}
                where as_of_year = ?
                  and wipo_industry_code in (select wipo_industry_code from served_segments)
            ),
            field_jurisdictions as (
                select
                    as_of_year,
                    wipo_field,
                    jurisdiction_code,
                    count(distinct docdb_family_id) as jurisdiction_family_count_asof,
                    count(distinct case when is_active_asof then docdb_family_id end) as jurisdiction_active_family_count_asof
                from {family_classification_jurisdiction_ref}
                where as_of_year = ?
                  and wipo_field in (select wipo_industry_code from served_segments)
                group by as_of_year, wipo_field, jurisdiction_code
            ),
            ranked as (
                select
                    field_jurisdictions.*,
                    row_number() over (
                        partition by field_jurisdictions.wipo_field
                        order by
                            field_jurisdictions.jurisdiction_family_count_asof desc,
                            field_jurisdictions.jurisdiction_active_family_count_asof desc,
                            field_jurisdictions.jurisdiction_code asc
                    ) as field_rank_within_year
                from field_jurisdictions
            )
            select
                ranked.*,
                case
                    when coalesce(field_basis.segment_family_count_stock_asof, 0) = 0 then 0.0
                    else ranked.jurisdiction_family_count_asof / field_basis.segment_family_count_stock_asof
                end as jurisdiction_family_share_within_field_asof,
                count(*) over () as total_count
            from ranked
            left join field_basis
              on field_basis.wipo_industry_code = ranked.wipo_field
            where ranked.field_rank_within_year <= ?
            order by ranked.wipo_field asc, ranked.field_rank_within_year asc
            """
            return self._query_rows(con, query, parameters)

    def get_segment_applications_grants(
        self,
        segment_id: str,
        year_from: int | None = None,
        year_to: int | None = None,
        jurisdiction_limit: int = 12,
    ) -> list[dict[str, object]]:
        if not self._source_available(self.member_publications_path) or not self._source_available(self.family_compare_path):
            return []
        scope = self.get_scope_summary()
        latest_market_year = (
            int(scope.get("latest_market_year"))
            if scope.get("latest_market_year") is not None
            else self.SUPPORTED_YEAR_CAP
        )
        publication_end_year = year_to or latest_market_year
        publication_start_year = year_from or int(scope.get("start_year") or latest_market_year)
        if publication_start_year > publication_end_year:
            publication_start_year = publication_end_year
        family_basis_year = self._supported_year(self.family_compare_path, requested_year=publication_end_year)
        if family_basis_year is None:
            return []
        with DuckDbProvider().connect() as con:
            family_compare_ref = self._relation_for_path(con, self.family_compare_path)
            member_ref = self._relation_for_path(con, self.member_publications_path)
            parameters: list[object] = [
                int(family_basis_year),
                segment_id,
                int(publication_start_year),
                int(publication_end_year),
                int(jurisdiction_limit),
                segment_id,
            ]
            query = f"""
            with segment_families as (
                select distinct
                    docdb_family_id
                from {family_compare_ref}
                where as_of_year = ?
                  and primary_wipo_field_current = ?
            ),
            publication_events as (
                select
                    cast(year(publn_date) as integer) as as_of_year,
                    publn_auth as jurisdiction_code,
                    appln_id,
                    is_application_stage,
                    is_grant_stage
                from {member_ref}
                where docdb_family_id in (select docdb_family_id from segment_families)
                  and trim(coalesce(publn_auth, '')) <> ''
                  and cast(year(publn_date) as integer) between ? and ?
                  and (
                      coalesce(is_application_stage, false)
                      or coalesce(is_grant_stage, false)
                  )
            ),
            top_jurisdictions as (
                select
                    jurisdiction_code
                from (
                    select
                        jurisdiction_code,
                        count(distinct appln_id) filter (where is_application_stage) as application_count,
                        count(distinct appln_id) filter (where is_grant_stage) as grant_count
                    from publication_events
                    group by jurisdiction_code
                ) ranked_jurisdictions
                order by
                    (application_count + grant_count) desc,
                    grant_count desc,
                    jurisdiction_code asc
                limit ?
            )
            select
                publication_events.as_of_year,
                ? as wipo_field,
                publication_events.jurisdiction_code,
                count(distinct publication_events.appln_id) filter (where publication_events.is_application_stage) as application_count,
                count(distinct publication_events.appln_id) filter (where publication_events.is_grant_stage) as grant_count,
                count(distinct publication_events.appln_id) filter (
                    where publication_events.is_application_stage or publication_events.is_grant_stage
                ) as total_event_count,
                count(*) over () as total_count
            from publication_events
            where publication_events.jurisdiction_code in (select jurisdiction_code from top_jurisdictions)
            group by publication_events.as_of_year, publication_events.jurisdiction_code
            order by
                publication_events.as_of_year asc,
                total_event_count desc,
                publication_events.jurisdiction_code asc
            """
            return self._query_rows(con, query, parameters)

    def get_segment_grant_mix(
        self,
        segment_id: str,
        as_of_year: int | None = None,
        limit: int = 12,
        offset: int = 0,
    ) -> list[dict[str, object]]:
        if not self._source_available(self.member_publications_path) or not self._source_available(self.family_compare_path):
            return []
        scope = self.get_scope_summary()
        latest_market_year = (
            int(scope.get("latest_market_year"))
            if scope.get("latest_market_year") is not None
            else self.SUPPORTED_YEAR_CAP
        )
        effective_year = as_of_year or latest_market_year
        family_basis_year = self._supported_year(self.family_compare_path, requested_year=effective_year)
        if family_basis_year is None:
            return []
        with DuckDbProvider().connect() as con:
            family_compare_ref = self._relation_for_path(con, self.family_compare_path)
            member_ref = self._relation_for_path(con, self.member_publications_path)
            parameters: list[object] = [
                int(family_basis_year),
                segment_id,
                int(effective_year),
                int(effective_year),
                segment_id,
                int(limit),
                int(offset),
            ]
            query = f"""
            with segment_families as (
                select distinct
                    docdb_family_id
                from {family_compare_ref}
                where as_of_year = ?
                  and primary_wipo_field_current = ?
            ),
            publication_events as (
                select
                    publn_auth as jurisdiction_code,
                    appln_id,
                    is_application_stage,
                    is_grant_stage
                from {member_ref}
                where docdb_family_id in (select docdb_family_id from segment_families)
                  and trim(coalesce(publn_auth, '')) <> ''
                  and cast(year(publn_date) as integer) = ?
                  and (
                      coalesce(is_application_stage, false)
                      or coalesce(is_grant_stage, false)
                  )
            )
            select
                ? as as_of_year,
                ? as wipo_field,
                publication_events.jurisdiction_code,
                count(distinct publication_events.appln_id) filter (where publication_events.is_application_stage) as application_count,
                count(distinct publication_events.appln_id) filter (where publication_events.is_grant_stage) as grant_count,
                count(distinct publication_events.appln_id) filter (
                    where publication_events.is_application_stage or publication_events.is_grant_stage
                ) as total_event_count,
                case
                    when count(distinct publication_events.appln_id) filter (
                        where publication_events.is_application_stage or publication_events.is_grant_stage
                    ) = 0 then 0.0
                    else cast(
                        count(distinct publication_events.appln_id) filter (where publication_events.is_grant_stage) as double
                    ) / count(distinct publication_events.appln_id) filter (
                        where publication_events.is_application_stage or publication_events.is_grant_stage
                    )
                end as grant_share_of_events,
                count(*) over () as total_count
            from publication_events
            group by publication_events.jurisdiction_code
            order by
                grant_count desc,
                application_count desc,
                publication_events.jurisdiction_code asc
            limit ?
            offset ?
            """
            return self._query_rows(con, query, parameters)

    def get_segment_unitary_patent_summary(
        self,
        segment_id: str,
        jurisdiction_limit: int = 18,
    ) -> list[dict[str, object]]:
        if (
            not self._source_available(self.family_compare_path)
            or not self._source_available(self.up_status_path)
            or not self._source_available(self.family_jurisdiction_unrolled_path)
            or not self._source_available(self.member_publications_path)
            or not self._source_available(self.register_up_path)
        ):
            return []
        scope = self.get_scope_summary()
        latest_market_year = (
            int(scope.get("latest_market_year"))
            if scope.get("latest_market_year") is not None
            else self.SUPPORTED_YEAR_CAP
        )
        family_basis_year = self._supported_year(self.family_compare_path, requested_year=latest_market_year)
        if family_basis_year is None:
            return []
        with DuckDbProvider().connect() as con:
            family_compare_ref = self._relation_for_path(con, self.family_compare_path)
            register_up_ref = self._relation_for_path(con, self.register_up_path)
            member_ref = self._relation_for_path(con, self.member_publications_path)
            up_status_ref = self._relation_for_path(con, self.up_status_path)
            family_jurisdiction_unrolled_ref = self._relation_for_path(con, self.family_jurisdiction_unrolled_path)
            parameters: list[object] = [
                int(family_basis_year),
                segment_id,
                segment_id,
                int(latest_market_year),
                segment_id,
                segment_id,
                int(latest_market_year),
                int(jurisdiction_limit),
            ]
            query = f"""
            with segment_families as (
                select distinct
                    docdb_family_id
                from {family_compare_ref}
                where as_of_year = ?
                  and primary_wipo_field_current = ?
            ),
            register_families as (
                select distinct
                    publications.docdb_family_id,
                    cast(year(register_up.ep_register_up_event_latest_date) as integer) as as_of_year
                from {register_up_ref} register_up
                inner join {member_ref} publications
                  on publications.appln_id = register_up.appln_id
                where coalesce(register_up.ep_register_is_unitary_patent, false)
                  and cast(year(register_up.ep_register_up_event_latest_date) as integer) between 1900 and 9998
                  and publications.docdb_family_id in (select docdb_family_id from segment_families)
            ),
            heuristic_families as (
                select distinct
                    docdb_family_id
                from {up_status_ref}
                where coalesce(has_up_registration, false)
                  and docdb_family_id in (select docdb_family_id from segment_families)
            ),
            coverage_summary as (
                select
                    count(distinct heuristic_families.docdb_family_id) as heuristic_family_count,
                    count(distinct unrolled.jurisdiction_code) as unrolled_member_state_count
                from heuristic_families
                left join {family_jurisdiction_unrolled_ref} unrolled
                  on unrolled.docdb_family_id = heuristic_families.docdb_family_id
                 and coalesce(unrolled.is_up_unrolled, false)
            ),
            ep_grant_overlap as (
                select
                    count(distinct publications.appln_id) as ep_grant_event_count,
                    count(
                        distinct case
                            when publications.docdb_family_id in (select docdb_family_id from heuristic_families)
                                then publications.appln_id
                            else null
                        end
                    ) as ep_grant_event_count_on_heuristic_up
                from {member_ref} publications
                where coalesce(publications.is_grant_stage, false)
                  and publications.publn_auth = 'EP'
                  and publications.docdb_family_id in (select docdb_family_id from segment_families)
            ),
            yearly_rollup as (
                select
                    as_of_year,
                    count(distinct docdb_family_id) as register_confirmed_family_count
                from register_families
                group by as_of_year
            ),
            jurisdiction_rollup as (
                select
                    jurisdiction_code,
                    count(distinct docdb_family_id) as jurisdiction_family_count
                from {family_jurisdiction_unrolled_ref}
                where coalesce(is_up_unrolled, false)
                  and docdb_family_id in (select docdb_family_id from heuristic_families)
                group by jurisdiction_code
            ),
            ranked_jurisdictions as (
                select
                    jurisdiction_rollup.*,
                    row_number() over (
                        order by jurisdiction_rollup.jurisdiction_family_count desc, jurisdiction_rollup.jurisdiction_code asc
                    ) as jurisdiction_rank
                from jurisdiction_rollup
            ),
            combined_rows as (
                select
                    'summary' as row_kind,
                    ? as wipo_field,
                    cast(? as integer) as as_of_year,
                    cast(null as varchar) as jurisdiction_code,
                    coalesce((select count(distinct docdb_family_id) from register_families), 0) as register_confirmed_family_count,
                    coalesce((select heuristic_family_count from coverage_summary), 0) as heuristic_family_count,
                    coalesce((select unrolled_member_state_count from coverage_summary), 0) as unrolled_member_state_count,
                    cast(null as bigint) as jurisdiction_family_count,
                    coalesce((select ep_grant_event_count from ep_grant_overlap), 0) as ep_grant_event_count,
                    coalesce((select ep_grant_event_count_on_heuristic_up from ep_grant_overlap), 0) as ep_grant_event_count_on_heuristic_up,
                    0 as sort_bucket,
                    0 as sort_rank
                union all
                select
                    'year' as row_kind,
                    ? as wipo_field,
                    yearly_rollup.as_of_year,
                    cast(null as varchar) as jurisdiction_code,
                    yearly_rollup.register_confirmed_family_count,
                    coalesce((select heuristic_family_count from coverage_summary), 0) as heuristic_family_count,
                    coalesce((select unrolled_member_state_count from coverage_summary), 0) as unrolled_member_state_count,
                    cast(null as bigint) as jurisdiction_family_count,
                    cast(null as bigint) as ep_grant_event_count,
                    cast(null as bigint) as ep_grant_event_count_on_heuristic_up,
                    1 as sort_bucket,
                    yearly_rollup.as_of_year as sort_rank
                from yearly_rollup
                union all
                select
                    'jurisdiction' as row_kind,
                    ? as wipo_field,
                    cast(? as integer) as as_of_year,
                    ranked_jurisdictions.jurisdiction_code,
                    cast(null as bigint) as register_confirmed_family_count,
                    ranked_jurisdictions.jurisdiction_family_count as heuristic_family_count,
                    cast(null as bigint) as unrolled_member_state_count,
                    ranked_jurisdictions.jurisdiction_family_count,
                    cast(null as bigint) as ep_grant_event_count,
                    cast(null as bigint) as ep_grant_event_count_on_heuristic_up,
                    2 as sort_bucket,
                    ranked_jurisdictions.jurisdiction_rank as sort_rank
                from ranked_jurisdictions
                where ranked_jurisdictions.jurisdiction_rank <= ?
            )
            select
                row_kind,
                wipo_field,
                as_of_year,
                jurisdiction_code,
                register_confirmed_family_count,
                heuristic_family_count,
                unrolled_member_state_count,
                jurisdiction_family_count,
                ep_grant_event_count,
                ep_grant_event_count_on_heuristic_up
            from combined_rows
            order by sort_bucket asc, sort_rank asc, jurisdiction_code asc
            """
            return self._query_rows(con, query, parameters)

    def get_cpc_trends(
        self,
        segment_id: str | None = None,
        as_of_year: int | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict[str, object]]:
        if not self._source_available(self.cpc_trend_path):
            return []
        effective_year = self._supported_year(self.cpc_trend_path, requested_year=as_of_year)
        if effective_year is None:
            return []
        with DuckDbProvider().connect() as con:
            cpc_trend_ref = self._relation_for_path(con, self.cpc_trend_path)
            parameters: list[object] = [int(effective_year)]
            filters = " and as_of_year = ?"
            if segment_id:
                filters += " and wipo_industry_code = ?"
                parameters.append(segment_id)
            query = f"""
            select
                *,
                count(*) over () as total_count
            from {cpc_trend_ref}
            where true
            {filters}
            order by as_of_year desc, cpc_rank_within_segment_year asc, cpc_family_count_asof desc
            limit ?
            offset ?
            """
            parameters.extend([int(limit), int(offset)])
            return self._query_rows(con, query, parameters)

    def get_segment_cpc_citing_owners(
        self,
        segment_id: str,
        cpc_main_group: str,
        as_of_year: int | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict[str, object]]:
        if not self._source_available(self.family_classification_mix_path) or not self._source_available(self.enriched_citation_network_path):
            return []
        effective_year = self._supported_year(self.family_classification_mix_path, requested_year=as_of_year)
        if effective_year is None:
            return []
        normalized_cpc = cpc_main_group.strip()
        if not normalized_cpc:
            return []
        with DuckDbProvider().connect() as con:
            family_classification_ref = self._relation_for_path(con, self.family_classification_mix_path)
            citation_network_ref = self._relation_for_path(con, self.enriched_citation_network_path)
            parameters: list[object] = [
                int(effective_year),
                segment_id,
                normalized_cpc,
                int(effective_year),
                normalized_cpc,
                int(limit),
                int(offset),
            ]
            query = f"""
            with cpc_families as (
                select
                    fc.as_of_year,
                    fc.primary_wipo_field_asof as wipo_field,
                    fc.docdb_family_id
                from {family_classification_ref} fc
                where fc.as_of_year = ?
                  and fc.primary_wipo_field_asof = ?
                  and list_contains(fc.cpc_main_groups_asof, ?)
            ),
            cpc_citation_events as (
                select
                    cf.as_of_year,
                    cf.wipo_field,
                    trim(coalesce(n.citing_assignee_name, '')) as citing_assignee_name,
                    upper(trim(coalesce(n.citing_jurisdiction_code, ''))) as citing_jurisdiction_code,
                    cast(year(n.citation_date) as integer) as citation_year,
                    coalesce(n.clean_edge_weight, 0.0) as clean_edge_weight,
                    coalesce(n.citation_lethality_score, 0.0) as citation_lethality_score,
                    n.cited_docdb_family_id
                from {citation_network_ref} n
                inner join cpc_families cf
                  on cf.docdb_family_id = n.cited_docdb_family_id
                where not coalesce(n.is_out_of_bounds, false)
                  and not coalesce(n.is_intra_family_citation, false)
                  and not coalesce(n.is_self_citation, false)
                  and n.citation_date is not null
                  and cast(year(n.citation_date) as integer) between 1900 and ?
                  and trim(upper(coalesce(n.citing_assignee_name, ''))) not in (
                    '',
                    '_',
                    'UNKNOWN',
                    'UNKNOWN_OWNER',
                    'UNASSIGNED'
                  )
            ),
            cpc_totals as (
                select
                    count(*) as citation_event_count_in_cpc_asof
                from cpc_citation_events
            ),
            owner_rollup as (
                select
                    as_of_year,
                    wipo_field,
                    citing_assignee_name,
                    max(citation_year) as latest_citation_year,
                    count(*) as citation_event_count,
                    cast(coalesce(sum(clean_edge_weight), 0.0) as double) as clean_citation_count,
                    cast(coalesce(sum(citation_lethality_score), 0.0) as double) as citation_lethality_sum,
                    count(
                        distinct case
                            when citing_jurisdiction_code not in ('', '_', 'UNKNOWN', 'UNKNOWN_OWNER', 'UNASSIGNED')
                            then citing_jurisdiction_code
                        end
                    ) as distinct_citing_jurisdiction_count,
                    count(distinct cited_docdb_family_id) as cited_family_count
                from cpc_citation_events
                group by as_of_year, wipo_field, citing_assignee_name
            ),
            ranked as (
                select
                    owner_rollup.*,
                    row_number() over (
                        order by citation_lethality_sum desc,
                                 citation_event_count desc,
                                 clean_citation_count desc,
                                 citing_assignee_name asc
                    ) as leaderboard_rank
                from owner_rollup
            )
            select
                ranked.as_of_year,
                ranked.wipo_field,
                ? as cpc_main_group,
                ranked.leaderboard_rank,
                ranked.citing_assignee_name,
                ranked.latest_citation_year,
                ranked.citation_event_count,
                ranked.clean_citation_count,
                ranked.citation_lethality_sum,
                ranked.distinct_citing_jurisdiction_count,
                ranked.cited_family_count,
                case
                    when coalesce(cpc_totals.citation_event_count_in_cpc_asof, 0) = 0 then 0.0
                    else ranked.citation_event_count / cpc_totals.citation_event_count_in_cpc_asof
                end as citation_event_share_within_cpc_asof,
                count(*) over () as total_count
            from ranked
            cross join cpc_totals
            order by ranked.leaderboard_rank asc, ranked.citing_assignee_name asc
            limit ?
            offset ?
            """
            return self._query_rows(con, query, parameters)

    def get_citation_trends(
        self,
        segment_id: str | None = None,
        as_of_year: int | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict[str, object]]:
        if not self._source_available(self.citation_trend_path):
            return []
        with DuckDbProvider().connect() as con:
            citation_trend_ref = self._relation_for_path(con, self.citation_trend_path)
            parameters: list[object] = []
            filters = f" and cast(as_of_year as integer) <= {self.SUPPORTED_YEAR_CAP}"
            if segment_id:
                filters += " and wipo_industry_code = ?"
                parameters.append(segment_id)
            if as_of_year is not None:
                filters += " and as_of_year = ?"
                parameters.append(min(int(as_of_year), self.SUPPORTED_YEAR_CAP))
            query = f"""
            select
                *,
                count(*) over () as total_count
            from {citation_trend_ref}
            where true
            {filters}
            order by as_of_year desc, citation_lethality_sum_raw desc, wipo_industry_code asc
            limit ?
            offset ?
            """
            parameters.extend([int(limit), int(offset)])
            return self._query_rows(con, query, parameters)

    def get_citation_jurisdictions(
        self,
        segment_id: str | None = None,
        as_of_year: int | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict[str, object]]:
        if not self._source_available(self.citation_jurisdiction_path):
            return []
        effective_year = self._supported_year(self.citation_jurisdiction_path, requested_year=as_of_year)
        if effective_year is None:
            return []
        with DuckDbProvider().connect() as con:
            citation_jurisdiction_ref = self._relation_for_path(con, self.citation_jurisdiction_path)
            parameters: list[object] = [int(effective_year)]
            filters = " and as_of_year = ?"
            if segment_id:
                filters += " and wipo_industry_code = ?"
                parameters.append(segment_id)
            query = f"""
            select
                *,
                count(*) over () as total_count
            from {citation_jurisdiction_ref}
            where true
            {filters}
            order by as_of_year desc, citation_lethality_sum_raw desc, jurisdiction_code asc
            limit ?
            offset ?
            """
            parameters.extend([int(limit), int(offset)])
            return self._query_rows(con, query, parameters)

    def get_citation_attackers(
        self,
        segment_id: str | None = None,
        as_of_year: int | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict[str, object]]:
        if not self._source_available(self.citation_attacker_path):
            return []
        effective_year = self._supported_year(self.citation_attacker_path, requested_year=as_of_year)
        if effective_year is None:
            return []
        with DuckDbProvider().connect() as con:
            citation_attacker_ref = self._relation_for_path(con, self.citation_attacker_path)
            parameters: list[object] = [int(effective_year)]
            filters = " and as_of_year = ?"
            if segment_id:
                filters += " and wipo_industry_code = ?"
                parameters.append(segment_id)
            query = f"""
            select
                *,
                count(*) over () as total_count
            from {citation_attacker_ref}
            where trim(coalesce(citing_assignee_name, '')) not in ('', '_', 'UNKNOWN', 'UNKNOWN_OWNER', 'UNASSIGNED')
            {filters}
            order by as_of_year desc, citation_lethality_sum_raw desc, citing_assignee_name asc
            limit ?
            offset ?
            """
            parameters.extend([int(limit), int(offset)])
            return self._query_rows(con, query, parameters)
