from __future__ import annotations

import argparse
import json
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import duckdb


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(frozen=True)
class Paths:
    repo_root: Path
    serving_dir: Path
    core_path: Path
    semantic_path: Path
    market_path: Path
    manifest_path: Path
    audit_path: Path
    temp_dir: Path
    title_path: Path
    abstract_path: Path
    epab_publication_path: Path
    epab_claims_path: Path
    register_core_path: Path
    register_display_path: Path
    register_proc_path: Path
    register_up_path: Path
    register_opposition_path: Path
    register_agent_path: Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Materialize publication_evidence_serving into the live core_serving.duckdb snapshot."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Repository root. Defaults to the patent-iq repo root.",
    )
    parser.add_argument(
        "--abstract-buckets",
        type=int,
        default=8,
        help="Number of buckets used for abstract aggregation. Higher values reduce peak memory at the cost of more scans.",
    )
    parser.add_argument(
        "--memory-limit",
        default="14GiB",
        help="DuckDB memory limit for the rebuild connection.",
    )
    parser.add_argument(
        "--temp-limit",
        default="37GiB",
        help="DuckDB max temp directory size for the rebuild connection.",
    )
    parser.add_argument(
        "--threads",
        type=int,
        default=1,
        help="DuckDB worker threads for the rebuild connection.",
    )
    return parser.parse_args()


def build_paths(repo_root: Path) -> Paths:
    bronze_dir = repo_root / "etl" / "data" / "bronze"
    silver_dir = repo_root / "etl" / "data" / "silver"
    serving_dir = repo_root / "etl" / "data" / "serving"
    return Paths(
        repo_root=repo_root,
        serving_dir=serving_dir,
        core_path=serving_dir / "core_serving.duckdb",
        semantic_path=serving_dir / "semantic_serving.duckdb",
        market_path=serving_dir / "market_serving.duckdb",
        manifest_path=serving_dir / "serving_snapshot_manifest.json",
        audit_path=serving_dir / "serving_snapshot_audit.json",
        temp_dir=repo_root / "tmp" / "duckdb_pub_serving",
        title_path=bronze_dir / "bronze_patstat_appln_title.parquet",
        abstract_path=bronze_dir / "bronze_patstat_appln_abstr.parquet",
        epab_publication_path=bronze_dir / "bronze_epab_publication.parquet",
        epab_claims_path=bronze_dir / "bronze_epab_claims.parquet",
        register_core_path=silver_dir / "silver_ep_register_core.parquet",
        register_display_path=silver_dir / "silver_ep_register_display_ledger.parquet",
        register_proc_path=silver_dir / "silver_ep_register_proc_step_features.parquet",
        register_up_path=silver_dir / "silver_ep_register_up_status.parquet",
        register_opposition_path=silver_dir / "silver_ep_register_current_opposition.parquet",
        register_agent_path=silver_dir / "silver_ep_register_agent_summary.parquet",
    )


def log(message: str) -> None:
    print(message, flush=True)


def snapshot_tables(db_path: Path) -> tuple[list[str], dict[str, dict[str, int]]]:
    con = duckdb.connect(str(db_path), read_only=True)
    try:
        tables = [
            str(row[0])
            for row in con.execute(
                """
                select table_name
                from information_schema.tables
                where table_schema = 'main'
                order by table_name
                """
            ).fetchall()
        ]
        stats: dict[str, dict[str, int]] = {}
        for table in tables:
            rows = int(con.execute(f"select count(*) from {table}").fetchone()[0])
            cols = int(
                con.execute(
                    """
                    select count(*)
                    from information_schema.columns
                    where table_schema = 'main' and table_name = ?
                    """,
                    [table],
                ).fetchone()[0]
            )
            stats[table] = {"rows": rows, "columns": cols}
        return tables, stats
    finally:
        con.close()


def materialize_title_best(con: duckdb.DuckDBPyConnection, title_path: Path, warnings: list[str]) -> None:
    if not title_path.exists():
        warnings.append(f"Missing optional title source for publication_evidence_serving: {title_path}")
        con.execute(
            """
            create or replace temp table publication_title_best as
            select
                null::bigint as appln_id,
                null::varchar as title_text,
                null::varchar as title_language_code
            where false
            """
        )
        return

    log("building english title selection")
    con.execute(
        f"""
        create or replace temp table publication_title_en as
        select
            cast(appln_id as bigint) as appln_id,
            first(nullif(trim(cast(appln_title as varchar)), '') order by length(cast(appln_title as varchar)) desc) as title_text,
            'en'::varchar as title_language_code
        from read_parquet('{title_path.as_posix()}')
        join publication_member_appln_ids using (appln_id)
        where lower(coalesce(cast(appln_title_lg as varchar), 'en')) = 'en'
          and nullif(trim(cast(appln_title as varchar)), '') is not null
        group by cast(appln_id as bigint)
        """
    )
    log("building fallback title selection")
    con.execute(
        f"""
        create or replace temp table publication_title_non_en as
        select
            cast(src.appln_id as bigint) as appln_id,
            first(nullif(trim(cast(src.appln_title as varchar)), '') order by
                lower(coalesce(cast(src.appln_title_lg as varchar), 'en')) asc,
                length(cast(src.appln_title as varchar)) desc
            ) as title_text,
            first(lower(coalesce(cast(src.appln_title_lg as varchar), 'en')) order by
                lower(coalesce(cast(src.appln_title_lg as varchar), 'en')) asc,
                length(cast(src.appln_title as varchar)) desc
            ) as title_language_code
        from read_parquet('{title_path.as_posix()}') src
        join publication_member_appln_ids ids using (appln_id)
        anti join publication_title_en en using (appln_id)
        where nullif(trim(cast(src.appln_title as varchar)), '') is not null
        group by cast(src.appln_id as bigint)
        """
    )
    con.execute(
        """
        create or replace temp table publication_title_best as
        select * from publication_title_en
        union all
        select * from publication_title_non_en
        """
    )
    con.execute("create index if not exists idx_publication_title_best_appln on publication_title_best(appln_id)")


def materialize_abstract_best(
    con: duckdb.DuckDBPyConnection,
    abstract_path: Path,
    temp_dir: Path,
    bucket_count: int,
    warnings: list[str],
) -> None:
    if not abstract_path.exists():
        warnings.append(f"Missing optional abstract source for publication_evidence_serving: {abstract_path}")
        con.execute(
            """
            create or replace temp table publication_abstract_best as
            select
                null::bigint as appln_id,
                null::varchar as abstract_text,
                null::varchar as abstract_language_code
            where false
            """
        )
        return

    candidate_dir = temp_dir / "abstract_candidates"
    if candidate_dir.exists():
        shutil.rmtree(candidate_dir)
    candidate_dir.mkdir(parents=True, exist_ok=True)

    log("materializing abstract candidates")
    con.execute(
        f"""
        copy (
            select
                cast(appln_id as bigint) as appln_id,
                nullif(trim(cast(appln_abstract as varchar)), '') as abstract_text,
                lower(coalesce(cast(appln_abstract_lg as varchar), 'en')) as abstract_language_code,
                abs(hash(cast(appln_id as bigint))) % {bucket_count} as bucket_id,
                length(cast(appln_abstract as varchar)) as abstract_length
            from read_parquet('{abstract_path.as_posix()}')
            join publication_member_appln_ids using (appln_id)
            where nullif(trim(cast(appln_abstract as varchar)), '') is not null
        ) to '{candidate_dir.as_posix()}'
        (format parquet, compression zstd, partition_by (bucket_id))
        """
    )

    con.execute(
        """
        create or replace temp table publication_abstract_en (
            appln_id bigint,
            abstract_text varchar,
            abstract_language_code varchar
        )
        """
    )
    for bucket in range(bucket_count):
        bucket_path = candidate_dir / f"bucket_id={bucket}" / "*.parquet"
        if not bucket_path.parent.exists():
            continue
        log(f"building english abstract selection bucket {bucket + 1}/{bucket_count}")
        con.execute(
            f"""
            insert into publication_abstract_en
            select
                appln_id,
                first(abstract_text order by abstract_length desc) as abstract_text,
                'en'::varchar as abstract_language_code
            from read_parquet('{bucket_path.as_posix()}')
            where abstract_language_code = 'en'
            group by appln_id
            """
        )

    con.execute("create index if not exists idx_publication_abstract_en_appln on publication_abstract_en(appln_id)")
    con.execute(
        """
        create or replace temp table publication_abstract_best as
        select * from publication_abstract_en
        """
    )

    for bucket in range(bucket_count):
        bucket_path = candidate_dir / f"bucket_id={bucket}" / "*.parquet"
        if not bucket_path.parent.exists():
            continue
        log(f"building fallback abstract selection bucket {bucket + 1}/{bucket_count}")
        con.execute(
            f"""
            insert into publication_abstract_best
            select
                src.appln_id,
                first(src.abstract_text order by
                    src.abstract_language_code asc,
                    src.abstract_length desc
                ) as abstract_text,
                first(src.abstract_language_code order by
                    src.abstract_language_code asc,
                    src.abstract_length desc
                ) as abstract_language_code
            from read_parquet('{bucket_path.as_posix()}') src
            anti join publication_abstract_en en using (appln_id)
            group by src.appln_id
            """
        )

    con.execute("create index if not exists idx_publication_abstract_best_appln on publication_abstract_best(appln_id)")


def materialize_claim_best(
    con: duckdb.DuckDBPyConnection,
    epab_publication_path: Path,
    epab_claims_path: Path,
    warnings: list[str],
) -> None:
    if not epab_publication_path.exists() or not epab_claims_path.exists():
        warnings.append("Missing optional EPAB claim sources for publication_evidence_serving")
        con.execute(
            """
            create or replace temp table publication_claim_best as
            select
                null::varchar as publication_number_full,
                null::varchar as claim_1_text,
                null::varchar as claim_1_language_code
            where false
            """
        )
        return

    log("building claim selection")
    con.execute(
        f"""
        create or replace temp table publication_claim_best as
        select
            upper(cast(p.publication_number_full as varchar)) as publication_number_full,
            first(nullif(trim(cast(c.claim_text_plain as varchar)), '')) as claim_1_text,
            'en'::varchar as claim_1_language_code
        from read_parquet('{epab_publication_path.as_posix()}') p
        join publication_member_numbers pm
          on upper(cast(p.publication_number_full as varchar)) = pm.publication_number_full
        join read_parquet('{epab_claims_path.as_posix()}') c using (epab_doc_id)
        where try_cast(c.claim_sequence_no as bigint) = 1
          and lower(coalesce(cast(c.language_code as varchar), 'en')) = 'en'
          and nullif(trim(cast(c.claim_text_plain as varchar)), '') is not null
        group by upper(cast(p.publication_number_full as varchar))
        """
    )
    con.execute("create index if not exists idx_publication_claim_best_pub on publication_claim_best(publication_number_full)")


def empty_table(con: duckdb.DuckDBPyConnection, name: str, cols: str) -> None:
    con.execute(f"create or replace temp table {name} as select {cols} where false")


def materialize_register_tables(con: duckdb.DuckDBPyConnection, paths: Paths, warnings: list[str]) -> None:
    if paths.register_core_path.exists():
        log("building register core selection")
        con.execute(
            f"""
            create or replace temp table publication_register_core_best as
            select
                cast(appln_id as bigint) as appln_id,
                cast(reg101_id as bigint) as reg101_id,
                cast(register_record_present as boolean) as register_record_present,
                cast(ep_registered_license_flag as boolean) as ep_registered_license_flag,
                cast(ep_licensee_names as varchar) as ep_licensee_names,
                cast(register_snapshot_date as date) as register_snapshot_date
            from read_parquet('{paths.register_core_path.as_posix()}')
            join publication_member_appln_ids using (appln_id)
            """
        )
        con.execute(
            "create index if not exists idx_publication_register_core_best_appln on publication_register_core_best(appln_id)"
        )
    else:
        warnings.append(f"Missing optional register core source for publication_evidence_serving: {paths.register_core_path}")
        empty_table(
            con,
            "publication_register_core_best",
            "null::bigint as appln_id, null::bigint as reg101_id, null::boolean as register_record_present, "
            "null::boolean as ep_registered_license_flag, null::varchar as ep_licensee_names, null::date as register_snapshot_date",
        )

    if paths.register_display_path.exists():
        log("building register display selection")
        con.execute(
            f"""
            create or replace temp table publication_register_display_best as
            select
                cast(appln_id as bigint) as appln_id,
                first(cast(snapshot_date as date) order by cast(snapshot_date as date) desc nulls last) as display_snapshot_date,
                first(cast(ep_display_status_text as varchar) order by cast(snapshot_date as date) desc nulls last) as ep_display_status_text,
                first(cast(status_source as varchar) order by cast(snapshot_date as date) desc nulls last) as status_source
            from read_parquet('{paths.register_display_path.as_posix()}')
            join publication_member_appln_ids using (appln_id)
            group by cast(appln_id as bigint)
            """
        )
        con.execute(
            "create index if not exists idx_publication_register_display_best_appln on publication_register_display_best(appln_id)"
        )
    else:
        warnings.append(
            f"Missing optional register display source for publication_evidence_serving: {paths.register_display_path}"
        )
        empty_table(
            con,
            "publication_register_display_best",
            "null::bigint as appln_id, null::date as display_snapshot_date, null::varchar as ep_display_status_text, null::varchar as status_source",
        )

    if paths.register_proc_path.exists():
        log("building register procedure selection")
        con.execute(
            f"""
            create or replace temp table publication_register_proc_best as
            select
                cast(appln_id as bigint) as appln_id,
                cast(ep_proc_step_maturity_score as double) as ep_proc_step_maturity_score,
                cast(ep_search_report_mailed_date as date) as ep_search_report_mailed_date,
                cast(ep_latest_proc_phase_code as varchar) as ep_latest_proc_phase_code,
                cast(ep_latest_proc_result_code as varchar) as ep_latest_proc_result_code,
                cast(ep_proc_time_limit_days as bigint) as ep_proc_time_limit_days
            from read_parquet('{paths.register_proc_path.as_posix()}')
            join publication_member_appln_ids using (appln_id)
            """
        )
        con.execute(
            "create index if not exists idx_publication_register_proc_best_appln on publication_register_proc_best(appln_id)"
        )
    else:
        warnings.append(
            f"Missing optional register procedure source for publication_evidence_serving: {paths.register_proc_path}"
        )
        empty_table(
            con,
            "publication_register_proc_best",
            "null::bigint as appln_id, null::double as ep_proc_step_maturity_score, null::date as ep_search_report_mailed_date, "
            "null::varchar as ep_latest_proc_phase_code, null::varchar as ep_latest_proc_result_code, null::bigint as ep_proc_time_limit_days",
        )

    if paths.register_up_path.exists():
        log("building register up selection")
        con.execute(
            f"""
            create or replace temp table publication_register_up_best as
            select
                cast(appln_id as bigint) as appln_id,
                cast(ep_register_is_unitary_patent as boolean) as ep_register_is_unitary_patent,
                cast(ep_register_up_status_code as varchar) as ep_register_up_status_code,
                cast(ep_register_up_status_text as varchar) as ep_register_up_status_text,
                cast(ep_register_up_event_latest_date as date) as ep_register_up_event_latest_date
            from read_parquet('{paths.register_up_path.as_posix()}')
            join publication_member_appln_ids using (appln_id)
            """
        )
        con.execute(
            "create index if not exists idx_publication_register_up_best_appln on publication_register_up_best(appln_id)"
        )
    else:
        warnings.append(f"Missing optional register UP source for publication_evidence_serving: {paths.register_up_path}")
        empty_table(
            con,
            "publication_register_up_best",
            "null::bigint as appln_id, null::boolean as ep_register_is_unitary_patent, null::varchar as ep_register_up_status_code, "
            "null::varchar as ep_register_up_status_text, null::date as ep_register_up_event_latest_date",
        )

    if paths.register_opposition_path.exists():
        log("building register opposition selection")
        con.execute(
            f"""
            create or replace temp table publication_register_opposition_best as
            select
                cast(appln_id as bigint) as appln_id,
                cast(ep_opposition_active as boolean) as ep_opposition_active,
                cast(ep_opposition_status_text as varchar) as ep_opposition_status_text,
                cast(ep_opponent_names as varchar) as ep_opponent_names,
                cast(ep_opponent_agent_names as varchar) as ep_opponent_agent_names,
                cast(ep_appeal_active as boolean) as ep_appeal_active,
                cast(ep_appeal_result_text as varchar) as ep_appeal_result_text
            from read_parquet('{paths.register_opposition_path.as_posix()}')
            join publication_member_appln_ids using (appln_id)
            """
        )
        con.execute(
            "create index if not exists idx_publication_register_opp_best_appln on publication_register_opposition_best(appln_id)"
        )
    else:
        warnings.append(
            f"Missing optional register opposition source for publication_evidence_serving: {paths.register_opposition_path}"
        )
        empty_table(
            con,
            "publication_register_opposition_best",
            "null::bigint as appln_id, null::boolean as ep_opposition_active, null::varchar as ep_opposition_status_text, "
            "null::varchar as ep_opponent_names, null::varchar as ep_opponent_agent_names, null::boolean as ep_appeal_active, null::varchar as ep_appeal_result_text",
        )

    if paths.register_agent_path.exists():
        log("building register agent selection")
        con.execute(
            f"""
            create or replace temp table publication_register_agent_best as
            select
                cast(appln_id as bigint) as appln_id,
                cast(ep_register_lead_agent_name as varchar) as ep_register_lead_agent_name,
                cast(ep_register_lead_agent_country as varchar) as ep_register_lead_agent_country
            from read_parquet('{paths.register_agent_path.as_posix()}')
            join publication_member_appln_ids using (appln_id)
            """
        )
        con.execute(
            "create index if not exists idx_publication_register_agent_best_appln on publication_register_agent_best(appln_id)"
        )
    else:
        warnings.append(
            f"Missing optional register agent source for publication_evidence_serving: {paths.register_agent_path}"
        )
        empty_table(
            con,
            "publication_register_agent_best",
            "null::bigint as appln_id, null::varchar as ep_register_lead_agent_name, null::varchar as ep_register_lead_agent_country",
        )


def update_manifest_and_audit(paths: Paths, warnings: list[str]) -> None:
    core_tables, core_stats = snapshot_tables(paths.core_path)
    semantic_tables, semantic_stats = snapshot_tables(paths.semantic_path)
    market_tables, market_stats = snapshot_tables(paths.market_path)

    source_gold_release = "mvp-local-build"
    serving_release = "2026-03-15-serving"
    if paths.manifest_path.exists():
        try:
            existing_manifest = json.loads(paths.manifest_path.read_text())
            source_gold_release = existing_manifest.get("source_gold_release", source_gold_release)
            serving_release = existing_manifest.get("serving_release", serving_release)
        except Exception:
            pass

    built_at = utc_now_iso()
    manifest_payload = {
        "serving_release": serving_release,
        "contract_version": "1",
        "built_at": built_at,
        "source_gold_release": source_gold_release,
        "snapshots": {
            "core": {
                "filename": paths.core_path.name,
                "tables": core_tables,
                "bytes": paths.core_path.stat().st_size,
            },
            "semantic": {
                "filename": paths.semantic_path.name,
                "tables": semantic_tables,
                "bytes": paths.semantic_path.stat().st_size,
            },
            "market": {
                "filename": paths.market_path.name,
                "tables": market_tables,
                "bytes": paths.market_path.stat().st_size,
            },
        },
    }
    audit_payload = {
        "serving_release": serving_release,
        "source_gold_release": source_gold_release,
        "built_at": built_at,
        "snapshots": {
            "core": {
                "path": str(paths.core_path),
                "bytes": paths.core_path.stat().st_size,
                "table_stats": core_stats,
            },
            "semantic": {
                "path": str(paths.semantic_path),
                "bytes": paths.semantic_path.stat().st_size,
                "table_stats": semantic_stats,
            },
            "market": {
                "path": str(paths.market_path),
                "bytes": paths.market_path.stat().st_size,
                "table_stats": market_stats,
            },
        },
        "warnings": warnings,
    }
    paths.manifest_path.write_text(json.dumps(manifest_payload, indent=2, sort_keys=True) + "\n")
    paths.audit_path.write_text(json.dumps(audit_payload, indent=2, sort_keys=True) + "\n")
    log(
        json.dumps(
            {
                "publication_rows": core_stats.get("publication_evidence_serving", {}).get("rows", 0),
                "core_bytes": paths.core_path.stat().st_size,
                "warnings": warnings,
            },
            indent=2,
        )
    )


def main() -> int:
    args = parse_args()
    paths = build_paths(args.repo_root.resolve())
    warnings: list[str] = []

    if paths.temp_dir.exists():
        shutil.rmtree(paths.temp_dir)
    paths.temp_dir.mkdir(parents=True, exist_ok=True)
    (paths.core_path.parent / f"{paths.core_path.name}.wal").unlink(missing_ok=True)

    con = duckdb.connect(str(paths.core_path))
    con.execute("set preserve_insertion_order=false")
    con.execute(f"set temp_directory='{paths.temp_dir.as_posix()}'")
    con.execute(f"set max_temp_directory_size='{args.temp_limit}'")
    con.execute(f"set memory_limit='{args.memory_limit}'")
    con.execute(f"set threads={args.threads}")

    try:
        log("building publication member staging")
        con.execute(
            """
            create or replace temp table publication_member_base as
            select
                cast(pat_publn_id as bigint) as pat_publn_id,
                cast(appln_id as bigint) as appln_id,
                cast(docdb_family_id as bigint) as docdb_family_id,
                upper(cast(publication_number_full as varchar)) as publication_number_full,
                cast(publn_auth as varchar) as publn_auth,
                cast(publn_nr as varchar) as publn_nr,
                cast(publn_kind as varchar) as publn_kind,
                cast(publn_date as date) as publn_date,
                cast(is_application_stage as boolean) as is_application_stage,
                cast(is_grant_stage as boolean) as is_grant_stage,
                cast(is_modifier_stage as boolean) as is_modifier_stage,
                cast(scope_type as varchar) as scope_type,
                cast(snapshot_date as varchar) as snapshot_date
            from family_member_publications
            """
        )
        con.execute(
            """
            create or replace temp table publication_member_appln_ids as
            select distinct appln_id
            from publication_member_base
            where appln_id is not null
            """
        )
        con.execute("create index if not exists idx_pub_member_appln_ids on publication_member_appln_ids(appln_id)")
        con.execute(
            """
            create or replace temp table publication_member_numbers as
            select distinct publication_number_full
            from publication_member_base
            where publication_number_full is not null
            """
        )
        con.execute(
            "create index if not exists idx_pub_member_numbers on publication_member_numbers(publication_number_full)"
        )

        materialize_title_best(con, paths.title_path, warnings)
        materialize_abstract_best(con, paths.abstract_path, paths.temp_dir, args.abstract_buckets, warnings)
        materialize_claim_best(con, paths.epab_publication_path, paths.epab_claims_path, warnings)
        materialize_register_tables(con, paths, warnings)

        log("materializing publication_evidence_serving")
        con.execute(
            """
            create or replace table publication_evidence_serving as
            select
                m.*,
                t.title_text,
                t.title_language_code,
                a.abstract_text,
                a.abstract_language_code,
                c.claim_1_text,
                c.claim_1_language_code,
                rc.reg101_id,
                rc.register_record_present,
                rc.ep_registered_license_flag,
                rc.ep_licensee_names,
                rc.register_snapshot_date,
                rd.ep_display_status_text,
                rd.status_source,
                rd.display_snapshot_date,
                rp.ep_proc_step_maturity_score,
                rp.ep_search_report_mailed_date,
                rp.ep_latest_proc_phase_code,
                rp.ep_latest_proc_result_code,
                rp.ep_proc_time_limit_days,
                ru.ep_register_is_unitary_patent,
                ru.ep_register_up_status_code,
                ru.ep_register_up_status_text,
                ru.ep_register_up_event_latest_date,
                ro.ep_opposition_active,
                ro.ep_opposition_status_text,
                ro.ep_opponent_names,
                ro.ep_opponent_agent_names,
                ro.ep_appeal_active,
                ro.ep_appeal_result_text,
                ra.ep_register_lead_agent_name,
                ra.ep_register_lead_agent_country
            from publication_member_base m
            left join publication_title_best t using (appln_id)
            left join publication_abstract_best a using (appln_id)
            left join publication_claim_best c using (publication_number_full)
            left join publication_register_core_best rc using (appln_id)
            left join publication_register_display_best rd using (appln_id)
            left join publication_register_proc_best rp using (appln_id)
            left join publication_register_up_best ru using (appln_id)
            left join publication_register_opposition_best ro using (appln_id)
            left join publication_register_agent_best ra using (appln_id)
            """
        )
        con.execute(
            "create index if not exists idx_publication_evidence_serving_publication on publication_evidence_serving(publication_number_full)"
        )
        con.execute(
            "create index if not exists idx_publication_evidence_serving_appln on publication_evidence_serving(appln_id)"
        )
        con.execute(
            "create index if not exists idx_publication_evidence_serving_family on publication_evidence_serving(docdb_family_id)"
        )
        con.execute("analyze publication_evidence_serving")
        con.execute("checkpoint")
    finally:
        con.close()

    log("recomputing snapshot metadata")
    update_manifest_and_audit(paths, warnings)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
