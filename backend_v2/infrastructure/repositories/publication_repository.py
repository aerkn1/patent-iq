from __future__ import annotations

import hashlib
from functools import lru_cache
from pathlib import Path
from typing import Any

import duckdb

from config.settings import get_settings
from infrastructure.artifacts import ArtifactLocator
from infrastructure.duckdb import DuckDbProvider


_PUBLICATION_MEMBER_DATASET = "publication_member_by_number"
_APPLICATION_EVIDENCE_DATASET = "application_evidence_by_appln"
_PUBLICATION_CLAIM_DATASET = "publication_claim_by_number"
_FAMILY_PUBLICATIONS_DATASET = "family_publications_by_family"
_PUBLICATION_SHARD_COUNT = 256


class PublicationRepository:
    def __init__(self) -> None:
        settings = get_settings()
        self.settings = settings
        self.member_publications_path = settings.etl_data_root / "silver" / "silver_family_member_publications.parquet"
        self.application_path = settings.etl_data_root / "bronze" / "bronze_patstat_appln.parquet"
        self.title_path = settings.etl_data_root / "bronze" / "bronze_patstat_appln_title.parquet"
        self.abstract_path = settings.etl_data_root / "bronze" / "bronze_patstat_appln_abstr.parquet"
        self.epab_publication_path = settings.etl_data_root / "bronze" / "bronze_epab_publication.parquet"
        self.epab_claims_path = settings.etl_data_root / "bronze" / "bronze_epab_claims.parquet"
        self.register_core_path = settings.etl_data_root / "silver" / "silver_ep_register_core.parquet"
        self.register_display_path = settings.etl_data_root / "silver" / "silver_ep_register_display_ledger.parquet"
        self.register_proc_path = settings.etl_data_root / "silver" / "silver_ep_register_proc_step_features.parquet"
        self.register_up_path = settings.etl_data_root / "silver" / "silver_ep_register_up_status.parquet"
        self.register_opposition_path = settings.etl_data_root / "silver" / "silver_ep_register_current_opposition.parquet"
        self.register_agent_path = settings.etl_data_root / "silver" / "silver_ep_register_agent_summary.parquet"
        self.artifact_locator = ArtifactLocator(settings=settings)
        self.duckdb_provider = DuckDbProvider()
        self._column_cache: dict[Path, list[str]] = {}
        self._publication_serving_checked = False
        self._publication_serving_path: Path | None = None

    def artifacts(self) -> list[Path]:
        publication_serving_path = self._resolve_publication_serving_path()
        if publication_serving_path is not None:
            return [publication_serving_path]
        return [
            self.member_publications_path,
            self.application_path,
            self.title_path,
            self.abstract_path,
            self.epab_publication_path,
            self.epab_claims_path,
            self.register_core_path,
            self.register_display_path,
            self.register_proc_path,
            self.register_up_path,
            self.register_opposition_path,
            self.register_agent_path,
        ]

    def _to_dict(self, columns: list[str], row: Any) -> dict[str, object]:
        if row is None:
            return {}
        return dict(zip(columns, row, strict=False))

    def _query_rows(
        self,
        query: str,
        parameters: list[object] | tuple[object, ...] = (),
    ) -> list[dict[str, object]]:
        with self.duckdb_provider.connect() as con:
            cursor = con.execute(query, parameters)
            rows = cursor.fetchall()
            if not rows:
                return []
            columns = [name for name, *_ in cursor.description]
        return [self._to_dict(columns, row) for row in rows]

    def _query_one(
        self,
        query: str,
        parameters: list[object] | tuple[object, ...] = (),
    ) -> dict[str, object] | None:
        rows = self._query_rows(query, parameters)
        return rows[0] if rows else None

    def _columns(self, path: Path) -> list[str]:
        if not path.exists():
            return []
        cached = self._column_cache.get(path)
        if cached is not None:
            return cached
        with self.duckdb_provider.connect() as con:
            rows = con.execute("describe select * from read_parquet(?)", [str(path)]).fetchall()
        columns = [row[0] for row in rows]
        self._column_cache[path] = columns
        return columns

    def _pick(self, columns: list[str], candidates: list[str], required: bool = False) -> str | None:
        lowered = {column.lower(): column for column in columns}
        for candidate in candidates:
            match = lowered.get(candidate.lower())
            if match is not None:
                return match
        if required:
            joined = ", ".join(candidates)
            raise ValueError(f"Could not resolve one of [{joined}] from parquet columns: {columns}")
        return None

    def _has_text(self, value: object) -> bool:
        return value is not None and str(value).strip() != ""

    def _is_publication_serving_dir(self, path: Path) -> bool:
        return path.is_dir() and (path / _PUBLICATION_MEMBER_DATASET).exists()

    def _serving_dataset_ready(self, publication_serving_path: Path | None, dataset_name: str) -> bool:
        if publication_serving_path is None:
            return False
        if not self._is_publication_serving_dir(publication_serving_path):
            return True
        return (publication_serving_path / dataset_name).exists()

    def _publication_bucket(self, normalized_publication_id: str) -> str:
        return hashlib.sha256(normalized_publication_id.encode("utf-8")).hexdigest()[:2]

    def _numeric_bucket(self, value: int) -> str:
        return str(abs(int(value)) % _PUBLICATION_SHARD_COUNT)

    def _bucket_glob(
        self,
        root: Path,
        dataset_name: str,
        partition_key: str,
        partition_value: str,
    ) -> str | None:
        bucket_dir = root / dataset_name / f"{partition_key}={partition_value}"
        if not bucket_dir.exists():
            return None
        return str(bucket_dir / "*.parquet")

    def _attach_publication_serving(self, con: duckdb.DuckDBPyConnection, publication_serving_path: Path) -> None:
        attached = con.execute("pragma database_list").fetchall()
        if any(str(row[1]) == "publication_db" for row in attached):
            return
        con.execute(f"ATTACH '{publication_serving_path}' AS publication_db (READ_ONLY)")

    def _publication_table_exists(self, con: duckdb.DuckDBPyConnection, table_name: str) -> bool:
        row = con.execute(
            """
            select 1
            from information_schema.tables
            where table_catalog = 'publication_db'
              and table_schema = 'main'
              and table_name = ?
            limit 1
            """,
            [table_name],
        ).fetchone()
        return row is not None

    def _resolve_publication_serving_path(self) -> Path | None:
        if self._publication_serving_checked:
            return self._publication_serving_path
        self._publication_serving_checked = True

        for candidate in [
            self.artifact_locator.resolve_publication_serving_duckdb(),
            self.artifact_locator.resolve_core_serving_duckdb(),
        ]:
            if candidate is None:
                continue
            if self._is_publication_serving_dir(candidate):
                self._publication_serving_path = candidate
                break
            with self.duckdb_provider.connect() as con:
                self._attach_publication_serving(con, candidate)
                if self._publication_table_exists(con, "publication_evidence_serving"):
                    self._publication_serving_path = candidate
                    break
        return self._publication_serving_path

    def _query_serving_one(
        self,
        publication_serving_path: Path,
        query: str,
        parameters: list[object] | tuple[object, ...],
    ) -> dict[str, object] | None:
        with self.duckdb_provider.connect() as con:
            self._attach_publication_serving(con, publication_serving_path)
            cursor = con.execute(query, parameters)
            row = cursor.fetchone()
            if row is None:
                return None
            columns = [name for name, *_ in cursor.description]
        return self._to_dict(columns, row)

    def _query_serving_rows(
        self,
        publication_serving_path: Path,
        query: str,
        parameters: list[object] | tuple[object, ...],
    ) -> list[dict[str, object]]:
        with self.duckdb_provider.connect() as con:
            self._attach_publication_serving(con, publication_serving_path)
            cursor = con.execute(query, parameters)
            rows = cursor.fetchall()
            if not rows:
                return []
            columns = [name for name, *_ in cursor.description]
        return [self._to_dict(columns, row) for row in rows]

    def get_publication_member(self, publication_id: str) -> dict[str, object] | None:
        normalized_publication_id = publication_id.strip().upper()
        publication_serving_path = self._resolve_publication_serving_path()
        if publication_serving_path is not None:
            row = self._get_publication_member_from_serving_cached(publication_serving_path, normalized_publication_id)
            if row is None and self._is_publication_serving_dir(publication_serving_path):
                row = self._get_publication_member_from_serving_scan_cached(
                    publication_serving_path,
                    normalized_publication_id,
                )
            if row is not None:
                return dict(row)
            if not self.settings.raw_parquet_fallback_enabled:
                return None
        row = self._get_publication_member_cached(normalized_publication_id)
        return dict(row) if row is not None else None

    def get_publication_suggestions(self, query: str, limit: int = 8) -> list[dict[str, object]]:
        normalized_query = "".join(char for char in str(query).strip().upper() if char.isalnum())
        if len(normalized_query) < 2:
            return []

        safe_limit = max(1, min(int(limit), 20))
        id_prefix = f"{normalized_query}%"
        id_contains = f"%{normalized_query}%"
        publication_serving_path = self._resolve_publication_serving_path()
        if publication_serving_path is None:
            return []

        if self._is_publication_serving_dir(publication_serving_path):
            glob = str(publication_serving_path / _PUBLICATION_MEMBER_DATASET / "*" / "*.parquet")
            return self._query_rows(
                """
                with scoped as (
                    select
                        cast(publication_number_full as varchar) as publication_id,
                        regexp_replace(upper(cast(publication_number_full as varchar)), '[^A-Z0-9]+', '', 'g') as normalized_publication_id,
                        cast(publn_auth as varchar) as authority,
                        cast(publn_kind as varchar) as kind_code,
                        cast(publn_date as varchar) as publication_date,
                        cast(docdb_family_id as varchar) as family_id
                    from read_parquet(?, hive_partitioning=true)
                    where regexp_replace(upper(cast(publication_number_full as varchar)), '[^A-Z0-9]+', '', 'g') like ?
                       or regexp_replace(upper(cast(publication_number_full as varchar)), '[^A-Z0-9]+', '', 'g') like ?
                )
                select
                    publication_id,
                    publication_id as label,
                    authority,
                    kind_code,
                    publication_date,
                    family_id
                from scoped
                order by
                    case
                        when normalized_publication_id = ? then 0
                        when normalized_publication_id like ? then 1
                        else 2
                    end,
                    publication_id asc
                limit ?
                """,
                [glob, id_prefix, id_contains, normalized_query, id_prefix, safe_limit],
            )

        return self._query_serving_rows(
            publication_serving_path,
            """
            with scoped as (
                select
                    cast(publication_number_full as varchar) as publication_id,
                    regexp_replace(upper(cast(publication_number_full as varchar)), '[^A-Z0-9]+', '', 'g') as normalized_publication_id,
                    cast(publn_auth as varchar) as authority,
                    cast(publn_kind as varchar) as kind_code,
                    cast(publn_date as varchar) as publication_date,
                    cast(docdb_family_id as varchar) as family_id
                from publication_db.publication_evidence_serving
                where regexp_replace(upper(cast(publication_number_full as varchar)), '[^A-Z0-9]+', '', 'g') like ?
                   or regexp_replace(upper(cast(publication_number_full as varchar)), '[^A-Z0-9]+', '', 'g') like ?
            )
            select
                publication_id,
                publication_id as label,
                authority,
                kind_code,
                publication_date,
                family_id
            from scoped
            order by
                case
                    when normalized_publication_id = ? then 0
                    when normalized_publication_id like ? then 1
                    else 2
                end,
                publication_id asc
            limit ?
            """,
            [id_prefix, id_contains, normalized_query, id_prefix, safe_limit],
        )

    @lru_cache(maxsize=8192)
    def _get_publication_member_from_serving_cached(
        self,
        publication_serving_path: Path,
        normalized_publication_id: str,
    ) -> dict[str, object] | None:
        if self._is_publication_serving_dir(publication_serving_path):
            glob = self._bucket_glob(
                publication_serving_path,
                _PUBLICATION_MEMBER_DATASET,
                "publication_bucket",
                self._publication_bucket(normalized_publication_id),
            )
            if glob is None:
                return None
            return self._query_one(
                """
                select
                    pat_publn_id,
                    appln_id,
                    docdb_family_id,
                    publn_auth,
                    publn_nr,
                    publn_kind,
                    publn_date,
                    publication_number_full,
                    is_application_stage,
                    is_grant_stage,
                    is_modifier_stage,
                    scope_type,
                    snapshot_date
                from read_parquet(?, hive_partitioning=true)
                where publication_number_full = ?
                limit 1
                """,
                [glob, normalized_publication_id],
            )
        return self._query_serving_one(
            publication_serving_path,
            """
            select
                pat_publn_id,
                appln_id,
                docdb_family_id,
                publn_auth,
                publn_nr,
                publn_kind,
                publn_date,
                publication_number_full,
                is_application_stage,
                is_grant_stage,
                is_modifier_stage,
                scope_type,
                snapshot_date
            from publication_db.publication_evidence_serving
            where publication_number_full = ?
            limit 1
            """,
            [normalized_publication_id],
        )

    @lru_cache(maxsize=8192)
    def _get_publication_member_from_serving_scan_cached(
        self,
        publication_serving_path: Path,
        normalized_publication_id: str,
    ) -> dict[str, object] | None:
        glob = str(publication_serving_path / _PUBLICATION_MEMBER_DATASET / "*" / "*.parquet")
        return self._query_one(
            """
            select
                pat_publn_id,
                appln_id,
                docdb_family_id,
                publication_number_full,
                publn_auth,
                publn_nr,
                publn_kind,
                publn_date,
                is_application_stage,
                is_grant_stage,
                is_modifier_stage,
                scope_type,
                snapshot_date,
                family_composite_status,
                mart_family_composite_status,
                effective_family_composite_status,
                active_opposition_application_count,
                opposition_overlay_active
            from read_parquet(?, hive_partitioning=true)
            where upper(publication_number_full) = ?
            limit 1
            """,
            [glob, normalized_publication_id],
        )

    @lru_cache(maxsize=8192)
    def _get_publication_member_cached(self, normalized_publication_id: str) -> dict[str, object] | None:
        if not self.member_publications_path.exists():
            return None
        query = f"""
        select
            cast(pat_publn_id as bigint) as pat_publn_id,
            cast(appln_id as bigint) as appln_id,
            cast(docdb_family_id as bigint) as docdb_family_id,
            cast(publn_auth as varchar) as publn_auth,
            cast(publn_nr as varchar) as publn_nr,
            cast(publn_kind as varchar) as publn_kind,
            cast(publn_date as varchar) as publn_date,
            cast(publication_number_full as varchar) as publication_number_full,
            cast(is_application_stage as boolean) as is_application_stage,
            cast(is_grant_stage as boolean) as is_grant_stage,
            cast(is_modifier_stage as boolean) as is_modifier_stage,
            cast(scope_type as varchar) as scope_type,
            cast(snapshot_date as varchar) as snapshot_date
        from read_parquet('{self.member_publications_path}')
        where upper(cast(publication_number_full as varchar)) = ?
        limit 1
        """
        return self._query_one(query, [normalized_publication_id])

    def get_title_for_application(self, appln_id: int) -> dict[str, object] | None:
        publication_serving_path = self._resolve_publication_serving_path()
        if self._serving_dataset_ready(publication_serving_path, _APPLICATION_EVIDENCE_DATASET):
            row = self._get_application_evidence_from_serving_cached(publication_serving_path, int(appln_id))
            if row is not None and self._has_text(row.get("title_text")):
                return {
                    "title_text": row.get("title_text"),
                    "language_code": row.get("title_language_code"),
                }
            return None
        if not self.settings.raw_parquet_fallback_enabled:
            return None
        row = self._get_title_for_application_cached(int(appln_id))
        return dict(row) if row is not None else None

    def get_filing_date_for_application(self, appln_id: int) -> str | None:
        publication_serving_path = self._resolve_publication_serving_path()
        if self._serving_dataset_ready(publication_serving_path, _APPLICATION_EVIDENCE_DATASET):
            row = self._get_application_evidence_from_serving_cached(publication_serving_path, int(appln_id))
            if row is not None:
                filing_date = row.get("appln_filing_date")
                if self._has_text(filing_date):
                    return str(filing_date).strip()
            return None
        if not self.settings.raw_parquet_fallback_enabled:
            return None
        return self._get_filing_date_for_application_cached(int(appln_id))

    @lru_cache(maxsize=8192)
    def _get_filing_date_for_application_cached(self, appln_id: int) -> str | None:
        if not self.application_path.exists():
            return None
        columns = self._columns(self.application_path)
        filing_date_column = self._pick(columns, ["appln_filing_date", "earliest_filing_date"], required=False)
        if filing_date_column is None:
            return None
        query = f"""
        select cast({filing_date_column} as varchar) as filing_date
        from read_parquet('{self.application_path}')
        where cast(appln_id as bigint) = ?
          and {filing_date_column} is not null
        limit 1
        """
        row = self._query_one(query, [appln_id])
        if row is None:
            return None
        filing_date = row.get("filing_date")
        return str(filing_date).strip() if self._has_text(filing_date) else None

    @lru_cache(maxsize=8192)
    def _get_application_evidence_from_serving_cached(
        self,
        publication_serving_path: Path,
        appln_id: int,
    ) -> dict[str, object] | None:
        if self._is_publication_serving_dir(publication_serving_path):
            glob = self._bucket_glob(
                publication_serving_path,
                _APPLICATION_EVIDENCE_DATASET,
                "appln_bucket",
                self._numeric_bucket(appln_id),
            )
            if glob is None:
                return None
            return self._query_one(
                """
                select *
                from read_parquet(?, hive_partitioning=true)
                where appln_id = ?
                limit 1
                """,
                [glob, appln_id],
            )
        return self._query_serving_one(
            publication_serving_path,
            """
            select *
            from publication_db.publication_evidence_serving
            where appln_id = ?
            order by
                coalesce(is_grant_stage, false) desc,
                publn_date desc nulls last,
                publication_number_full asc
            limit 1
            """,
            [appln_id],
        )

    @lru_cache(maxsize=8192)
    def _get_title_for_application_cached(self, appln_id: int) -> dict[str, object] | None:
        if not self.title_path.exists():
            return None
        columns = self._columns(self.title_path)
        title_column = self._pick(columns, ["appln_title", "title_text", "title"], required=False)
        language_column = self._pick(columns, ["appln_title_lg", "language_code", "title_lang"], required=False)
        if title_column is None:
            return None
        language_expr = (
            f"lower(coalesce(cast({language_column} as varchar), 'en'))"
            if language_column is not None
            else "'en'"
        )
        query = f"""
        select
            nullif(trim(cast({title_column} as varchar)), '') as title_text,
            {language_expr} as language_code
        from read_parquet('{self.title_path}')
        where cast(appln_id as bigint) = ?
          and nullif(trim(cast({title_column} as varchar)), '') is not null
        order by
            case when {language_expr} = 'en' then 0 else 1 end,
            {language_expr} asc,
            length(cast({title_column} as varchar)) desc
        limit 1
        """
        return self._query_one(query, [appln_id])

    def get_abstract_for_application(self, appln_id: int) -> dict[str, object] | None:
        publication_serving_path = self._resolve_publication_serving_path()
        if self._serving_dataset_ready(publication_serving_path, _APPLICATION_EVIDENCE_DATASET):
            row = self._get_application_evidence_from_serving_cached(publication_serving_path, int(appln_id))
            if row is not None and self._has_text(row.get("abstract_text")):
                return {
                    "abstract_text": row.get("abstract_text"),
                    "language_code": row.get("abstract_language_code"),
                }
            return None
        if not self.settings.raw_parquet_fallback_enabled:
            return None
        row = self._get_abstract_for_application_cached(int(appln_id))
        return dict(row) if row is not None else None

    @lru_cache(maxsize=8192)
    def _get_abstract_for_application_cached(self, appln_id: int) -> dict[str, object] | None:
        if not self.abstract_path.exists():
            return None
        columns = self._columns(self.abstract_path)
        abstract_column = self._pick(columns, ["appln_abstract", "abstract_text", "abstract"], required=False)
        language_column = self._pick(columns, ["appln_abstract_lg", "language_code", "abstract_lang"], required=False)
        if abstract_column is None:
            return None
        language_expr = (
            f"lower(coalesce(cast({language_column} as varchar), 'en'))"
            if language_column is not None
            else "'en'"
        )
        query = f"""
        select
            nullif(trim(cast({abstract_column} as varchar)), '') as abstract_text,
            {language_expr} as language_code
        from read_parquet('{self.abstract_path}')
        where cast(appln_id as bigint) = ?
          and nullif(trim(cast({abstract_column} as varchar)), '') is not null
        order by
            case when {language_expr} = 'en' then 0 else 1 end,
            {language_expr} asc,
            length(cast({abstract_column} as varchar)) desc
        limit 1
        """
        return self._query_one(query, [appln_id])

    def get_claim_for_publication(self, publication_id: str) -> dict[str, object] | None:
        normalized_publication_id = publication_id.strip().upper()
        publication_serving_path = self._resolve_publication_serving_path()
        if self._serving_dataset_ready(publication_serving_path, _PUBLICATION_CLAIM_DATASET):
            row = self._get_publication_claim_from_serving_cached(publication_serving_path, normalized_publication_id)
            if row is not None and self._has_text(row.get("claim_text")):
                return dict(row)
            return None
        if not self.settings.raw_parquet_fallback_enabled:
            return None
        row = self._get_claim_for_publication_cached(normalized_publication_id)
        return dict(row) if row is not None else None

    @lru_cache(maxsize=8192)
    def _get_publication_claim_from_serving_cached(
        self,
        publication_serving_path: Path,
        normalized_publication_id: str,
    ) -> dict[str, object] | None:
        if self._is_publication_serving_dir(publication_serving_path):
            glob = self._bucket_glob(
                publication_serving_path,
                _PUBLICATION_CLAIM_DATASET,
                "publication_bucket",
                self._publication_bucket(normalized_publication_id),
            )
            if glob is None:
                return None
            return self._query_one(
                """
                select
                    claim_1_text as claim_text,
                    claim_1_language_code as language_code,
                    1::bigint as claim_sequence_no
                from read_parquet(?, hive_partitioning=true)
                where publication_number_full = ?
                  and nullif(trim(cast(claim_1_text as varchar)), '') is not null
                limit 1
                """,
                [glob, normalized_publication_id],
            )
        return self._query_serving_one(
            publication_serving_path,
            """
            select
                claim_1_text as claim_text,
                claim_1_language_code as language_code,
                1::bigint as claim_sequence_no
            from publication_db.publication_evidence_serving
            where publication_number_full = ?
              and nullif(trim(cast(claim_1_text as varchar)), '') is not null
            limit 1
            """,
            [normalized_publication_id],
        )

    @lru_cache(maxsize=8192)
    def _get_claim_for_publication_cached(self, normalized_publication_id: str) -> dict[str, object] | None:
        if not self.epab_publication_path.exists() or not self.epab_claims_path.exists():
            return None
        query = f"""
        with matched_publication as (
            select cast(epab_doc_id as varchar) as epab_doc_id
            from read_parquet('{self.epab_publication_path}')
            where upper(cast(publication_number_full as varchar)) = ?
            limit 1
        )
        select
            nullif(trim(cast(claim_text_plain as varchar)), '') as claim_text,
            lower(coalesce(cast(language_code as varchar), 'en')) as language_code,
            try_cast(claim_sequence_no as bigint) as claim_sequence_no
        from read_parquet('{self.epab_claims_path}')
        where cast(epab_doc_id as varchar) = (select epab_doc_id from matched_publication)
          and try_cast(claim_sequence_no as bigint) = 1
          and lower(coalesce(cast(language_code as varchar), 'en')) = 'en'
          and nullif(trim(cast(claim_text_plain as varchar)), '') is not null
        order by lower(coalesce(cast(language_code as varchar), 'en')) asc
        limit 1
        """
        return self._query_one(query, [normalized_publication_id])

    def get_register_evidence(self, appln_id: int) -> dict[str, object]:
        publication_serving_path = self._resolve_publication_serving_path()
        if self._serving_dataset_ready(publication_serving_path, _APPLICATION_EVIDENCE_DATASET):
            row = self._get_application_evidence_from_serving_cached(publication_serving_path, int(appln_id))
            if row is not None:
                payload = {
                    "reg101_id": row.get("reg101_id"),
                    "register_record_present": row.get("register_record_present"),
                    "ep_registered_license_flag": row.get("ep_registered_license_flag"),
                    "ep_licensee_names": row.get("ep_licensee_names"),
                    "register_snapshot_date": row.get("register_snapshot_date"),
                    "ep_display_status_text": row.get("ep_display_status_text"),
                    "status_source": row.get("status_source"),
                    "display_snapshot_date": row.get("display_snapshot_date"),
                    "ep_proc_step_maturity_score": row.get("ep_proc_step_maturity_score"),
                    "ep_search_report_mailed_date": row.get("ep_search_report_mailed_date"),
                    "ep_latest_proc_phase_code": row.get("ep_latest_proc_phase_code"),
                    "ep_latest_proc_result_code": row.get("ep_latest_proc_result_code"),
                    "ep_proc_time_limit_days": row.get("ep_proc_time_limit_days"),
                    "ep_register_is_unitary_patent": row.get("ep_register_is_unitary_patent"),
                    "ep_register_up_status_code": row.get("ep_register_up_status_code"),
                    "ep_register_up_status_text": row.get("ep_register_up_status_text"),
                    "ep_register_up_event_latest_date": row.get("ep_register_up_event_latest_date"),
                    "ep_opposition_active": row.get("ep_opposition_active"),
                    "ep_opposition_status_text": row.get("ep_opposition_status_text"),
                    "ep_opponent_names": row.get("ep_opponent_names"),
                    "ep_opponent_agent_names": row.get("ep_opponent_agent_names"),
                    "ep_appeal_active": row.get("ep_appeal_active"),
                    "ep_appeal_result_text": row.get("ep_appeal_result_text"),
                    "ep_register_lead_agent_name": row.get("ep_register_lead_agent_name"),
                    "ep_register_lead_agent_country": row.get("ep_register_lead_agent_country"),
                }
                return payload
            return {}
        if not self.settings.raw_parquet_fallback_enabled:
            return {}
        return dict(self._get_register_evidence_cached(int(appln_id)))

    @lru_cache(maxsize=8192)
    def _get_register_evidence_cached(self, appln_id: int) -> dict[str, object]:
        payload: dict[str, object] = {}

        if self.register_core_path.exists():
            core = self._query_one(
                f"""
                select
                    cast(reg101_id as bigint) as reg101_id,
                    cast(register_record_present as boolean) as register_record_present,
                    cast(ep_registered_license_flag as boolean) as ep_registered_license_flag,
                    cast(ep_licensee_names as varchar) as ep_licensee_names,
                    cast(register_snapshot_date as varchar) as register_snapshot_date
                from read_parquet('{self.register_core_path}')
                where cast(appln_id as bigint) = ?
                limit 1
                """,
                [appln_id],
            )
            if core:
                payload.update(core)

        if self.register_display_path.exists():
            display = self._query_one(
                f"""
                select
                    cast(ep_display_status_text as varchar) as ep_display_status_text,
                    cast(status_source as varchar) as status_source,
                    cast(snapshot_date as varchar) as display_snapshot_date
                from read_parquet('{self.register_display_path}')
                where cast(appln_id as bigint) = ?
                limit 1
                """,
                [appln_id],
            )
            if display:
                payload.update(display)

        if self.register_proc_path.exists():
            proc = self._query_one(
                f"""
                select
                    cast(ep_proc_step_maturity_score as double) as ep_proc_step_maturity_score,
                    cast(ep_search_report_mailed_date as varchar) as ep_search_report_mailed_date,
                    cast(ep_latest_proc_phase_code as varchar) as ep_latest_proc_phase_code,
                    cast(ep_latest_proc_result_code as varchar) as ep_latest_proc_result_code,
                    cast(ep_proc_time_limit_days as bigint) as ep_proc_time_limit_days
                from read_parquet('{self.register_proc_path}')
                where cast(appln_id as bigint) = ?
                limit 1
                """,
                [appln_id],
            )
            if proc:
                payload.update(proc)

        if self.register_up_path.exists():
            up = self._query_one(
                f"""
                select
                    cast(ep_register_is_unitary_patent as boolean) as ep_register_is_unitary_patent,
                    cast(ep_register_up_status_code as varchar) as ep_register_up_status_code,
                    cast(ep_register_up_status_text as varchar) as ep_register_up_status_text,
                    cast(ep_register_up_event_latest_date as varchar) as ep_register_up_event_latest_date
                from read_parquet('{self.register_up_path}')
                where cast(appln_id as bigint) = ?
                limit 1
                """,
                [appln_id],
            )
            if up:
                payload.update(up)

        if self.register_opposition_path.exists():
            opposition = self._query_one(
                f"""
                select
                    cast(ep_opposition_active as boolean) as ep_opposition_active,
                    cast(ep_opposition_status_text as varchar) as ep_opposition_status_text,
                    cast(ep_opponent_names as varchar) as ep_opponent_names,
                    cast(ep_opponent_agent_names as varchar) as ep_opponent_agent_names,
                    cast(ep_appeal_active as boolean) as ep_appeal_active,
                    cast(ep_appeal_result_text as varchar) as ep_appeal_result_text
                from read_parquet('{self.register_opposition_path}')
                where cast(appln_id as bigint) = ?
                limit 1
                """,
                [appln_id],
            )
            if opposition:
                payload.update(opposition)

        if self.register_agent_path.exists():
            agent = self._query_one(
                f"""
                select
                    cast(ep_register_lead_agent_name as varchar) as ep_register_lead_agent_name,
                    cast(ep_register_lead_agent_country as varchar) as ep_register_lead_agent_country
                from read_parquet('{self.register_agent_path}')
                where cast(appln_id as bigint) = ?
                limit 1
                """,
                [appln_id],
            )
            if agent:
                payload.update(agent)

        return payload

    def get_related_family_publications(
        self,
        docdb_family_id: int,
        exclude_publication_id: str,
        limit: int = 6,
    ) -> list[dict[str, object]]:
        normalized_exclude_publication_id = exclude_publication_id.strip().upper()
        publication_serving_path = self._resolve_publication_serving_path()
        if publication_serving_path is not None:
            rows = self._get_related_family_publications_from_serving_cached(
                publication_serving_path,
                int(docdb_family_id),
                normalized_exclude_publication_id,
                int(limit),
            )
            if rows or not self.settings.raw_parquet_fallback_enabled:
                return [dict(row) for row in rows]
        rows = self._get_related_family_publications_cached(
            int(docdb_family_id),
            normalized_exclude_publication_id,
            int(limit),
        )
        return [dict(row) for row in rows]

    def get_family_publications(
        self,
        docdb_family_id: int,
        limit: int = 10,
        offset: int = 0,
    ) -> tuple[list[dict[str, object]], int]:
        normalized_family_id = int(docdb_family_id)
        safe_limit = max(1, min(int(limit), 1000))
        safe_offset = max(0, int(offset))

        publication_serving_path = self._resolve_publication_serving_path()
        if publication_serving_path is not None:
            total_count = self._get_family_publication_count_from_serving_cached(
                publication_serving_path,
                normalized_family_id,
            )
            rows = self._get_family_publications_from_serving_cached(
                publication_serving_path,
                normalized_family_id,
                safe_limit,
                safe_offset,
            )
            if rows or total_count or not self.settings.raw_parquet_fallback_enabled:
                return [self._hydrate_family_publication_row(dict(row)) for row in rows], total_count

        total_count = self._get_family_publication_count_from_raw_cached(normalized_family_id)
        rows = self._get_family_publications_from_raw_cached(
            normalized_family_id,
            safe_limit,
            safe_offset,
        )
        return [dict(row) for row in rows], total_count

    def get_family_publication_summary(self, docdb_family_id: int) -> dict[str, object]:
        normalized_family_id = int(docdb_family_id)
        publication_serving_path = self._resolve_publication_serving_path()
        if publication_serving_path is not None:
            summary = self._get_family_publication_summary_from_serving_cached(
                publication_serving_path,
                normalized_family_id,
            )
            if summary or not self.settings.raw_parquet_fallback_enabled:
                return dict(summary)
        summary = self._get_family_publication_summary_from_raw_cached(normalized_family_id)
        return dict(summary)

    @lru_cache(maxsize=8192)
    def _get_related_family_publications_from_serving_cached(
        self,
        publication_serving_path: Path,
        docdb_family_id: int,
        exclude_publication_id: str,
        limit: int = 6,
    ) -> list[dict[str, object]]:
        if self._is_publication_serving_dir(publication_serving_path):
            glob = self._bucket_glob(
                publication_serving_path,
                _FAMILY_PUBLICATIONS_DATASET,
                "family_bucket",
                self._numeric_bucket(docdb_family_id),
            )
            if glob is None:
                return []
            return self._query_rows(
                """
                select
                    publication_number_full,
                    publn_auth,
                    publn_kind,
                    publn_date,
                    is_application_stage,
                    is_grant_stage,
                    is_modifier_stage
                from read_parquet(?, hive_partitioning=true)
                where docdb_family_id = ?
                  and publication_number_full <> ?
                order by publn_date desc nulls last, publication_number_full asc
                limit ?
                """,
                [glob, docdb_family_id, exclude_publication_id, limit],
            )
        return self._query_serving_rows(
            publication_serving_path,
            """
            select
                publication_number_full,
                publn_auth,
                publn_kind,
                publn_date,
                is_application_stage,
                is_grant_stage,
                is_modifier_stage
            from publication_db.publication_evidence_serving
            where docdb_family_id = ?
              and publication_number_full <> ?
            order by publn_date desc nulls last, publication_number_full asc
            limit ?
            """,
            [docdb_family_id, exclude_publication_id, limit],
        )

    @lru_cache(maxsize=8192)
    def _get_related_family_publications_cached(
        self,
        docdb_family_id: int,
        exclude_publication_id: str,
        limit: int = 6,
    ) -> list[dict[str, object]]:
        if not self.member_publications_path.exists():
            return []
        query = f"""
        select
            cast(publication_number_full as varchar) as publication_number_full,
            cast(publn_auth as varchar) as publn_auth,
            cast(publn_kind as varchar) as publn_kind,
            cast(publn_date as varchar) as publn_date,
            cast(is_application_stage as boolean) as is_application_stage,
            cast(is_grant_stage as boolean) as is_grant_stage,
            cast(is_modifier_stage as boolean) as is_modifier_stage
        from read_parquet('{self.member_publications_path}')
        where cast(docdb_family_id as bigint) = ?
          and upper(cast(publication_number_full as varchar)) <> ?
        order by try_cast(publn_date as date) desc nulls last, publication_number_full asc
        limit ?
        """
        return self._query_rows(query, [docdb_family_id, exclude_publication_id, limit])

    def _hydrate_family_publication_row(self, row: dict[str, object]) -> dict[str, object]:
        publication_number = str(row.get("publication_number_full") or "").strip().upper()
        if not publication_number:
            return row
        member = self.get_publication_member(publication_number)
        if member is None:
            return row
        hydrated = dict(member)
        hydrated.update(row)
        return hydrated

    @lru_cache(maxsize=8192)
    def _get_family_publication_count_from_serving_cached(
        self,
        publication_serving_path: Path,
        docdb_family_id: int,
    ) -> int:
        if self._is_publication_serving_dir(publication_serving_path):
            glob = self._bucket_glob(
                publication_serving_path,
                _FAMILY_PUBLICATIONS_DATASET,
                "family_bucket",
                self._numeric_bucket(docdb_family_id),
            )
            if glob is None:
                return 0
            row = self._query_one(
                """
                select count(*) as publication_count
                from read_parquet(?, hive_partitioning=true)
                where docdb_family_id = ?
                """,
                [glob, docdb_family_id],
            )
            return int((row or {}).get("publication_count") or 0)
        row = self._query_serving_one(
            publication_serving_path,
            """
            select count(*) as publication_count
            from publication_db.publication_evidence_serving
            where docdb_family_id = ?
            """,
            [docdb_family_id],
        )
        return int((row or {}).get("publication_count") or 0)

    @lru_cache(maxsize=8192)
    def _get_family_publications_from_serving_cached(
        self,
        publication_serving_path: Path,
        docdb_family_id: int,
        limit: int,
        offset: int,
    ) -> list[dict[str, object]]:
        if self._is_publication_serving_dir(publication_serving_path):
            glob = self._bucket_glob(
                publication_serving_path,
                _FAMILY_PUBLICATIONS_DATASET,
                "family_bucket",
                self._numeric_bucket(docdb_family_id),
            )
            if glob is None:
                return []
            return self._query_rows(
                """
                select
                    docdb_family_id,
                    publication_number_full,
                    publn_auth,
                    publn_kind,
                    publn_date,
                    is_application_stage,
                    is_grant_stage,
                    is_modifier_stage
                from read_parquet(?, hive_partitioning=true)
                where docdb_family_id = ?
                order by publn_date desc nulls last, publication_number_full asc
                limit ?
                offset ?
                """,
                [glob, docdb_family_id, limit, offset],
            )
        return self._query_serving_rows(
            publication_serving_path,
            """
            select
                pat_publn_id,
                appln_id,
                docdb_family_id,
                publication_number_full,
                publn_auth,
                publn_nr,
                publn_kind,
                publn_date,
                is_application_stage,
                is_grant_stage,
                is_modifier_stage,
                scope_type,
                snapshot_date
            from publication_db.publication_evidence_serving
            where docdb_family_id = ?
            order by publn_date desc nulls last, publication_number_full asc
            limit ?
            offset ?
            """,
            [docdb_family_id, limit, offset],
        )

    @lru_cache(maxsize=8192)
    def _get_family_publication_summary_from_serving_cached(
        self,
        publication_serving_path: Path,
        docdb_family_id: int,
    ) -> dict[str, object]:
        if self._is_publication_serving_dir(publication_serving_path):
            glob = self._bucket_glob(
                publication_serving_path,
                _FAMILY_PUBLICATIONS_DATASET,
                "family_bucket",
                self._numeric_bucket(docdb_family_id),
            )
            if glob is None:
                return {}
            row = self._query_one(
                """
                select
                    count(*) as publication_count,
                    sum(case when is_application_stage then 1 else 0 end) as application_stage_count,
                    sum(case when is_grant_stage then 1 else 0 end) as grant_stage_count,
                    sum(case when is_modifier_stage then 1 else 0 end) as modifier_stage_count,
                    count(distinct publn_auth) as office_count
                from read_parquet(?, hive_partitioning=true)
                where docdb_family_id = ?
                """,
                [glob, docdb_family_id],
            )
            return row or {}
        row = self._query_serving_one(
            publication_serving_path,
            """
            select
                count(*) as publication_count,
                sum(case when is_application_stage then 1 else 0 end) as application_stage_count,
                sum(case when is_grant_stage then 1 else 0 end) as grant_stage_count,
                sum(case when is_modifier_stage then 1 else 0 end) as modifier_stage_count,
                count(distinct publn_auth) as office_count
            from publication_db.publication_evidence_serving
            where docdb_family_id = ?
            """,
            [docdb_family_id],
        )
        return row or {}

    @lru_cache(maxsize=8192)
    def _get_family_publication_count_from_raw_cached(self, docdb_family_id: int) -> int:
        if not self.member_publications_path.exists():
            return 0
        row = self._query_one(
            f"""
            select count(*) as publication_count
            from read_parquet('{self.member_publications_path}')
            where cast(docdb_family_id as bigint) = ?
            """,
            [docdb_family_id],
        )
        return int((row or {}).get("publication_count") or 0)

    @lru_cache(maxsize=8192)
    def _get_family_publications_from_raw_cached(
        self,
        docdb_family_id: int,
        limit: int,
        offset: int,
    ) -> list[dict[str, object]]:
        if not self.member_publications_path.exists():
            return []
        query = f"""
        select
            pat_publn_id,
            appln_id,
            docdb_family_id,
            publn_auth,
            publn_nr,
            publn_kind,
            publn_date,
            publication_number_full,
            is_application_stage,
            is_grant_stage,
            is_modifier_stage,
            scope_type,
            snapshot_date
        from read_parquet('{self.member_publications_path}')
        where cast(docdb_family_id as bigint) = ?
        order by try_cast(publn_date as date) desc nulls last, publication_number_full asc
        limit ?
        offset ?
        """
        return self._query_rows(query, [docdb_family_id, limit, offset])

    @lru_cache(maxsize=8192)
    def _get_family_publication_summary_from_raw_cached(self, docdb_family_id: int) -> dict[str, object]:
        if not self.member_publications_path.exists():
            return {}
        row = self._query_one(
            f"""
            select
                count(*) as publication_count,
                sum(case when is_application_stage then 1 else 0 end) as application_stage_count,
                sum(case when is_grant_stage then 1 else 0 end) as grant_stage_count,
                sum(case when is_modifier_stage then 1 else 0 end) as modifier_stage_count,
                count(distinct publn_auth) as office_count
            from read_parquet('{self.member_publications_path}')
            where cast(docdb_family_id as bigint) = ?
            """,
            [docdb_family_id],
        )
        return row or {}
