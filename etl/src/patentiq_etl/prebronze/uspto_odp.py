from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from datetime import date, datetime
import json
import os
from pathlib import Path
import re
import shutil
import time
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET
import zipfile

import duckdb

from patentiq_etl.bronze.ingest_uspto_fulltext import (
    USPTO_BRONZE_OUTPUT_COLUMNS,
    _parse_document_root,
    build_biblio_rows,
)
from patentiq_etl.common.io import append_jsonl, ensure_dir, write_pylist_parquet, write_text_json
from patentiq_etl.common.types import BuildSettings, StageResult, utc_now_iso


LISTING_URL = "https://api.uspto.gov/api/v1/datasets/products/appxml"
DOWNLOAD_URL_TEMPLATE = "https://api.uspto.gov/api/v1/datasets/products/files/APPXML/{file_name}"
ZIP_NAME_RE = re.compile(r"^(?P<base>ipa\d{6})(?:_r(?P<revision>\d+))?\.zip$", re.IGNORECASE)
SCHEMA_RE = re.compile(r"us-patent-application-(v\d+)", re.IGNORECASE)
DTD_VERSION_RE = re.compile(r'dtd-version="v?(\d+\.\d+)', re.IGNORECASE)


def _headers(api_key: str) -> dict[str, str]:
    """Return the ODP HTTP headers for JSON and bulk download requests."""
    return {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "x-api-key": api_key,
    }


def _read_json(url: str, headers: dict[str, str], timeout: int) -> dict[str, Any]:
    """Perform one JSON GET request against the USPTO ODP API."""
    request = Request(url, headers=headers, method="GET")
    with urlopen(request, timeout=timeout) as response:  # noqa: S310 - controlled USPTO endpoint
        return json.loads(response.read().decode("utf-8"))


def _download_to_path(url: str, headers: dict[str, str], out_path: Path, timeout: int) -> int:
    """Download one ODP bulk file to `out_path` and return bytes written."""
    request = Request(url, headers=headers, method="GET")
    ensure_dir(out_path.parent)
    written = 0
    with urlopen(request, timeout=timeout) as response, out_path.open("wb") as handle:  # noqa: S310 - controlled USPTO endpoint
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            handle.write(chunk)
            written += len(chunk)
    return written


def _seed_publication_rows(seed_path: Path) -> list[dict[str, Any]]:
    """Load the bounded U.S. publication seed rows from parquet."""
    if not seed_path.exists():
        return []
    con = duckdb.connect()
    columns = [row[0] for row in con.execute("describe select * from read_parquet(?)", [str(seed_path)]).fetchall()]
    date_column = "publication_date" if "publication_date" in columns else None
    rows = con.execute(
        f"""
        select
            cast(publication_number_full as varchar) as publication_number_full,
            {f"try_cast({date_column} as date)" if date_column else "null::date"} as publication_date
        from read_parquet(?)
        where publication_number_full is not null
        """,
        [str(seed_path)],
    ).fetchall()
    return [{"publication_number_full": row[0], "publication_date": row[1]} for row in rows if row[0]]


def _manifest_rows(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract normalized file-manifest rows from the ODP listing response."""
    bag = data.get("productFileBag", {}).get("fileDataBag", [])
    rows: list[dict[str, Any]] = []
    for entry in bag:
        file_name = entry.get("fileName")
        if not file_name:
            continue
        rows.append(
            {
                "file_name": file_name,
                "file_size": int(entry.get("fileSize") or 0),
                "file_data_from_date": entry.get("fileDataFromDate"),
                "file_data_to_date": entry.get("fileDataToDate"),
                "file_release_date": entry.get("fileReleaseDate"),
                "file_download_uri": entry.get("fileDownloadURI"),
            }
        )
    return rows


def _parse_iso_date(value: str | None) -> date | None:
    """Parse an ISO `YYYY-MM-DD` string to `date`."""
    if not value:
        return None
    try:
        return datetime.strptime(value[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def _revision_rank(file_name: str) -> tuple[str, int]:
    """Return the base weekly id and revision rank for one APPXML file name."""
    match = ZIP_NAME_RE.match(file_name)
    if not match:
        return file_name, 0
    return match.group("base"), int(match.group("revision") or 0)


def _dedupe_latest_revisions(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep only the highest available revision for each weekly APPXML file."""
    best: dict[str, dict[str, Any]] = {}
    for row in rows:
        base, revision = _revision_rank(row["file_name"])
        previous = best.get(base)
        if previous is None or revision >= previous["selected_revision"]:
            item = dict(row)
            item["base_week"] = base
            item["selected_revision"] = revision
            best[base] = item
    return sorted(best.values(), key=lambda row: row["file_name"])


def _filter_manifest_to_seed(rows: Iterable[dict[str, Any]], seed_rows: list[dict[str, Any]], start_year: int, end_year: int) -> list[dict[str, Any]]:
    """Prune weekly files to those overlapping the bounded seed publication dates when available."""
    seed_dates = [row["publication_date"] for row in seed_rows if row.get("publication_date") is not None]
    bounded_seed_dates = [value for value in seed_dates if start_year <= value.year <= end_year]
    if not bounded_seed_dates:
        return [
            row
            for row in rows
            if (
                (_parse_iso_date(row.get("file_data_from_date")) or date(start_year, 1, 1)).year <= end_year
                and (_parse_iso_date(row.get("file_data_to_date")) or date(end_year, 12, 31)).year >= start_year
            )
        ]

    min_seed = min(bounded_seed_dates)
    max_seed = max(bounded_seed_dates)
    filtered: list[dict[str, Any]] = []
    for row in rows:
        from_date = _parse_iso_date(row.get("file_data_from_date")) or min_seed
        to_date = _parse_iso_date(row.get("file_data_to_date")) or max_seed
        if to_date < min_seed or from_date > max_seed:
            continue
        filtered.append(row)
    return filtered


def detect_schema_version(xml_bytes: bytes) -> str:
    """Return a normalized schema version label such as `v42` or `v46`."""
    head = xml_bytes[:500].decode("utf-8", errors="ignore")
    match = SCHEMA_RE.search(head)
    if match:
        return match.group(1).lower()
    fallback = DTD_VERSION_RE.search(head)
    if fallback:
        return "v" + fallback.group(1).replace(".", "")
    return "unknown"


def iter_concatenated_xml_documents(xml_path: Path, chunk_size: int = 1024 * 1024) -> Iterable[bytes]:
    """Yield individual XML documents from one concatenated USPTO APPXML payload."""
    marker = b"<?xml"
    buffer = b""
    seen_start = False
    with xml_path.open("rb") as handle:
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break
            buffer += chunk
            starts: list[int] = []
            search_from = 0
            while True:
                idx = buffer.find(marker, search_from)
                if idx == -1:
                    break
                starts.append(idx)
                search_from = idx + len(marker)
            if not starts:
                continue
            if not seen_start and starts[0] > 0:
                buffer = buffer[starts[0]:]
                starts = [pos - starts[0] for pos in starts]
            seen_start = True
            for index in range(len(starts) - 1):
                payload = buffer[starts[index] : starts[index + 1]].strip()
                if payload:
                    yield payload
            buffer = buffer[starts[-1] :]
    if buffer.strip():
        yield buffer.strip()


def _empty_rows(table_name: str) -> list[dict[str, Any]]:
    """Return an empty row list placeholder for one USPTO Bronze table."""
    return []


def _merge_shards(table_name: str, shard_paths: list[Path], out_path: Path) -> int:
    """Merge parquet shards for one USPTO Bronze table into the final Bronze artifact."""
    ensure_dir(out_path.parent)
    columns = USPTO_BRONZE_OUTPUT_COLUMNS[table_name]
    if not shard_paths:
        return write_pylist_parquet(_empty_rows(table_name), out_path, columns=columns)
    con = duckdb.connect()
    source_glob = str(shard_paths[0].parent / "*.parquet")
    con.execute(f"copy (select * from read_parquet('{source_glob}')) to '{out_path}' (format parquet, compression zstd)")
    return int(con.execute("select count(*) from read_parquet(?)", [str(out_path)]).fetchone()[0])


def _download_retries(settings: BuildSettings) -> int:
    return int(settings.execution.get("uspto_odp_max_retries", 5))


def _download_timeout(settings: BuildSettings) -> int:
    return int(settings.execution.get("uspto_odp_timeout_seconds", 600))


def _download_delay(settings: BuildSettings) -> float:
    return float(settings.execution.get("uspto_odp_delay_seconds", 2.5))


def _api_key_env(settings: BuildSettings) -> str:
    return str(settings.execution.get("uspto_odp_api_key_env", "USPTO_ODP_API_KEY"))


def _temp_root(settings: BuildSettings) -> Path:
    return settings.repo_root / "etl" / "data" / "temp" / "uspto_odp"


def _logs_root(settings: BuildSettings) -> Path:
    return settings.manifests_dir / "stats" / "uspto_odp"


def _download_manifest(settings: BuildSettings, seed_path: Path) -> list[dict[str, Any]]:
    """Build the bounded APPXML manifest from ODP metadata and the U.S. seed."""
    api_key = os.environ.get(_api_key_env(settings))
    if not api_key:
        raise RuntimeError(f"Missing USPTO ODP API key env var `{_api_key_env(settings)}`.")
    params = urlencode(
        {
            "fileDataFromDate": f"{settings.year_window_start}-01-01",
            "fileDataToDate": f"{settings.year_window_end}-12-31",
            "includeFiles": "true",
        }
    )
    payload = _read_json(f"{LISTING_URL}?{params}", _headers(api_key), _download_timeout(settings))
    rows = _dedupe_latest_revisions(_manifest_rows(payload))
    seed_rows = _seed_publication_rows(seed_path)
    return _filter_manifest_to_seed(rows, seed_rows, settings.year_window_start, settings.year_window_end)


def extract_uspto_odp_to_bronze(settings: BuildSettings, publication_seed_path: Path, result: StageResult) -> None:
    """Download bounded USPTO APPXML ZIPs from ODP and write direct Bronze parquet outputs."""
    api_key = os.environ.get(_api_key_env(settings))
    if not api_key:
        result.status = "degraded" if result.status == "success" else result.status
        result.warnings.append(f"USPTO ODP API key env var `{_api_key_env(settings)}` is not set.")
        return
    if not publication_seed_path.exists():
        result.warnings.append("USPTO ODP extraction was skipped because `seed_us_publication_numbers` is unavailable.")
        return

    publication_seed_rows = _seed_publication_rows(publication_seed_path)
    publication_numbers = {
        row["publication_number_full"]
        for row in publication_seed_rows
        if row.get("publication_number_full")
    }
    result.metrics["uspto_odp_publication_seed_count"] = len(publication_numbers)
    if not publication_numbers:
        result.warnings.append("USPTO ODP extraction was skipped because the bounded U.S. publication seed is empty.")
        return

    logs_root = ensure_dir(_logs_root(settings))
    temp_root = ensure_dir(_temp_root(settings))
    shard_root = ensure_dir(temp_root / "shards")
    file_log_path = logs_root / "extraction_files.jsonl"
    summary_path = logs_root / "extraction_summary.json"
    manifest_path = logs_root / "manifest.json"
    file_log_path.unlink(missing_ok=True)
    summary_path.unlink(missing_ok=True)
    manifest_path.unlink(missing_ok=True)

    try:
        manifest_rows = _download_manifest(settings, publication_seed_path)
    except Exception as exc:
        result.status = "failed"
        result.warnings.append(f"USPTO ODP manifest build failed: {exc}")
        return

    result.metrics["uspto_odp_selected_file_count"] = len(manifest_rows)
    write_text_json(
        manifest_path,
        {
            "generated_at": utc_now_iso(),
            "scope_start_year": settings.year_window_start,
            "scope_end_year": settings.year_window_end,
            "selected_file_count": len(manifest_rows),
            "files": manifest_rows,
        },
    )
    result.artifacts["uspto_odp_manifest"] = str(manifest_path)
    result.artifacts["uspto_odp_file_log"] = str(file_log_path)
    result.inputs.append(f"uspto-odp://APPXML/{settings.year_window_start}-{settings.year_window_end}")

    shard_paths: dict[str, list[Path]] = {table: [] for table in USPTO_BRONZE_OUTPUT_COLUMNS}
    schema_counter: Counter[str] = Counter()
    totals = {
        "downloads": 0,
        "skipped": 0,
        "zip_bytes_downloaded": 0,
        "xml_bytes_processed": 0,
        "bytes_deleted_after_cleanup": 0,
        "publication_documents_seen": 0,
        "publication_documents_matched": 0,
    }

    for row in manifest_rows:
        file_name = row["file_name"]
        zip_path = temp_root / file_name
        xml_path = temp_root / f"{Path(file_name).stem}.xml"
        file_record: dict[str, Any] = {
            "file_name": file_name,
            "base_week": row.get("base_week"),
            "selected_revision": row.get("selected_revision", 0),
            "download_started_at": utc_now_iso(),
            "warnings": [],
        }
        documents: list[dict[str, Any]] = []
        abstracts: list[dict[str, Any]] = []
        claims: list[dict[str, Any]] = []
        related_documents: list[dict[str, Any]] = []
        applicants: list[dict[str, Any]] = []
        inventors: list[dict[str, Any]] = []
        retry = 0
        downloaded_bytes = 0
        download_url = row.get("file_download_uri") or DOWNLOAD_URL_TEMPLATE.format(file_name=file_name)
        while retry < _download_retries(settings):
            try:
                downloaded_bytes = _download_to_path(download_url, _headers(api_key), zip_path, _download_timeout(settings))
                break
            except Exception as exc:
                retry += 1
                if retry >= _download_retries(settings):
                    file_record["status"] = "failed"
                    file_record["warnings"].append(f"download failed after {retry} attempts: {exc}")
                    append_jsonl(file_log_path, file_record)
                    result.status = "degraded" if result.status == "success" else result.status
                    result.warnings.append(f"USPTO ODP download failed for `{file_name}`: {exc}")
                    downloaded_bytes = 0
                    break
                time.sleep(_download_delay(settings) * retry)
        if downloaded_bytes == 0 or not zip_path.exists():
            continue

        totals["downloads"] += 1
        totals["zip_bytes_downloaded"] += downloaded_bytes
        file_record["download_finished_at"] = utc_now_iso()
        file_record["zip_size_bytes"] = downloaded_bytes
        file_record["retry_count"] = retry

        with zipfile.ZipFile(zip_path) as archive:
            xml_members = [member for member in archive.namelist() if member.lower().endswith(".xml")]
            if not xml_members:
                file_record["status"] = "failed"
                file_record["warnings"].append("zip contained no XML payload")
                append_jsonl(file_log_path, file_record)
                result.status = "degraded" if result.status == "success" else result.status
                zip_size = zip_path.stat().st_size
                zip_path.unlink(missing_ok=True)
                totals["bytes_deleted_after_cleanup"] += zip_size
                continue
            with archive.open(xml_members[0]) as source, xml_path.open("wb") as target:
                shutil.copyfileobj(source, target)

        xml_size = xml_path.stat().st_size if xml_path.exists() else 0
        totals["xml_bytes_processed"] += xml_size
        file_record["xml_size_bytes"] = xml_size
        file_record["parse_started_at"] = utc_now_iso()
        schema_version = "unknown"
        documents_seen = 0
        matched_documents = 0
        for payload in iter_concatenated_xml_documents(xml_path):
            documents_seen += 1
            if documents_seen == 1:
                schema_version = detect_schema_version(payload)
            try:
                document_root = ET.fromstring(payload)
            except ET.ParseError as exc:
                file_record["warnings"].append(f"xml parse error: {exc}")
                continue
            doc_row, abstract_row, claim_rows, related_rows, applicant_rows, inventor_rows = _parse_document_root(document_root, file_name)
            publication_number_full = doc_row.get("publication_number_full")
            if not publication_number_full or publication_number_full not in publication_numbers:
                continue
            matched_documents += 1
            documents.append(doc_row)
            if abstract_row:
                abstracts.append(abstract_row)
            claims.extend(claim_rows)
            related_documents.extend(related_rows)
            applicants.extend(applicant_rows)
            inventors.extend(inventor_rows)

        schema_counter[schema_version] += 1
        file_record["schema_version"] = schema_version
        file_record["publication_documents_seen"] = documents_seen
        file_record["publication_documents_matched"] = matched_documents
        file_record["publication_documents_discarded"] = max(documents_seen - matched_documents, 0)
        file_record["parse_finished_at"] = utc_now_iso()
        totals["publication_documents_seen"] += documents_seen
        totals["publication_documents_matched"] += matched_documents

        table_rows = {
            "bronze_uspto_ft_document": documents,
            "bronze_uspto_ft_biblio_application": build_biblio_rows(documents),
            "bronze_uspto_ft_abstract": abstracts,
            "bronze_uspto_ft_claims": claims,
            "bronze_uspto_ft_related_documents": related_documents,
            "bronze_uspto_ft_applicants": applicants,
            "bronze_uspto_ft_inventors": inventors,
        }
        for table_name, rows in table_rows.items():
            if not rows:
                file_record[f"row_count_{table_name}"] = 0
                continue
            table_dir = ensure_dir(shard_root / table_name)
            shard_path = table_dir / f"{Path(file_name).stem}.parquet"
            file_record[f"row_count_{table_name}"] = write_pylist_parquet(rows, shard_path, columns=USPTO_BRONZE_OUTPUT_COLUMNS[table_name])
            shard_paths[table_name].append(shard_path)

        deleted_bytes = 0
        if xml_path.exists():
            deleted_bytes += xml_path.stat().st_size
            xml_path.unlink()
        if zip_path.exists():
            deleted_bytes += zip_path.stat().st_size
            zip_path.unlink()
        totals["bytes_deleted_after_cleanup"] += deleted_bytes
        file_record["cleanup_status"] = "deleted"
        file_record["bytes_deleted_after_cleanup"] = deleted_bytes
        file_record["status"] = "success"
        append_jsonl(file_log_path, file_record)
        time.sleep(_download_delay(settings))

    totals["publication_documents_discarded"] = max(
        totals["publication_documents_seen"] - totals["publication_documents_matched"],
        0,
    )

    for table_name, columns in USPTO_BRONZE_OUTPUT_COLUMNS.items():
        out_path = settings.bronze_dir / f"{table_name}.parquet"
        row_count = _merge_shards(table_name, shard_paths[table_name], out_path)
        result.outputs.append(str(out_path))
        result.metrics[f"{table_name}_rows"] = row_count

    result.metrics["uspto_total_parsed_rows"] = sum(
        result.metrics.get(f"{table_name}_rows", 0) for table_name in USPTO_BRONZE_OUTPUT_COLUMNS
    )
    result.metrics["uspto_odp_downloaded_file_count"] = totals["downloads"]
    result.metrics["uspto_odp_skipped_file_count"] = totals["skipped"]
    result.metrics["uspto_odp_zip_bytes_downloaded"] = totals["zip_bytes_downloaded"]
    result.metrics["uspto_odp_xml_bytes_processed"] = totals["xml_bytes_processed"]
    result.metrics["uspto_odp_bytes_deleted_after_cleanup"] = totals["bytes_deleted_after_cleanup"]
    result.metrics["uspto_odp_publication_documents_seen"] = totals["publication_documents_seen"]
    result.metrics["uspto_odp_publication_documents_matched"] = totals["publication_documents_matched"]
    result.metrics["uspto_odp_publication_documents_discarded"] = totals["publication_documents_discarded"]
    for schema_version, count in sorted(schema_counter.items()):
        result.metrics[f"uspto_odp_schema_file_count__{schema_version}"] = count

    write_text_json(
        summary_path,
        {
            "generated_at": utc_now_iso(),
            "metrics": {key: value for key, value in result.metrics.items() if key.startswith("uspto_") or key.startswith("bronze_uspto_")},
            "selected_file_count": len(manifest_rows),
            "schema_distribution": dict(schema_counter),
            "file_log_path": str(file_log_path),
        },
    )
    result.artifacts["uspto_odp_summary"] = str(summary_path)
    shutil.rmtree(shard_root, ignore_errors=True)
