from __future__ import annotations

import argparse
import html
import json
import re
import urllib.request
from dataclasses import asdict, dataclass
from io import BytesIO
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree as ET
from zipfile import ZipFile

import pandas as pd


WIPO_IPC_CONCORDANCE_URL = "https://www.wipo.int/documents/2948119/3215563/ipc_technology.xlsx"
WIPO_IPC_METHODOLOGY_URL = "https://www.wipo.int/documents/2948119/3215563/wipo_ipc_technology.pdf"
WORLD_BANK_COUNTRIES_URL = "https://api.worldbank.org/v2/country?format=json&per_page=400"
WORLD_BANK_GDP_PPP_URL = "https://api.worldbank.org/v2/country/all/indicator/NY.GDP.MKTP.PP.CD?format=json&per_page=20000"
US_CHAMBER_IP_INDEX_URL = "https://www.uschamber.com/intellectual-property/2025-ip-index"
EPO_UP_MEMBER_STATES_URL = "https://www.epo.org/en/legal/guidelines-up/2025/section_1_5_1.html"


@dataclass
class RefBuildRecord:
    filename: str
    source_url: str
    row_count: int
    note: str


def _fetch_bytes(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "PatentIQ-ETL/1.0"})
    with urllib.request.urlopen(request, timeout=120) as response:
        return response.read()


def _xlsx_shared_strings(zf: ZipFile) -> list[str]:
    ns = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    shared_strings_xml = ET.fromstring(zf.read("xl/sharedStrings.xml"))
    shared_strings: list[str] = []
    for item in shared_strings_xml.findall("a:si", ns):
        text_parts = [node.text or "" for node in item.findall(".//a:t", ns)]
        shared_strings.append("".join(text_parts))
    return shared_strings


def _xlsx_sheet_rows(workbook_bytes: bytes) -> list[dict[str, str]]:
    ns = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    with ZipFile(BytesIO(workbook_bytes)) as zf:
        shared_strings = _xlsx_shared_strings(zf)
        sheet_xml = ET.fromstring(zf.read("xl/worksheets/sheet1.xml"))
    rows: list[dict[str, str]] = []
    headers: list[str] | None = None
    for row in sheet_xml.findall(".//a:sheetData/a:row", ns):
        row_num = int(row.attrib["r"])
        values: dict[str, str] = {}
        for cell in row.findall("a:c", ns):
            cell_ref = cell.attrib.get("r", "")
            column_letters = re.sub(r"\d", "", cell_ref)
            cell_type = cell.attrib.get("t")
            value_node = cell.find("a:v", ns)
            value = value_node.text if value_node is not None else ""
            if cell_type == "s" and value:
                value = shared_strings[int(value)]
            values[column_letters] = value
        if row_num == 7:
            ordered_columns = [column for column in sorted(values.keys())]
            headers = [values[column].strip() for column in ordered_columns]
            continue
        if headers is None or row_num < 8:
            continue
        ordered_columns = [column for column in sorted(values.keys())]
        ordered_values = [values.get(column, "").strip() for column in ordered_columns]
        if not any(ordered_values):
            continue
        padded = ordered_values + [""] * max(0, len(headers) - len(ordered_values))
        rows.append(dict(zip(headers, padded[: len(headers)])))
    return rows


def build_wipo_techn_field_ipc(output_dir: Path) -> RefBuildRecord:
    rows = _xlsx_sheet_rows(_fetch_bytes(WIPO_IPC_CONCORDANCE_URL))
    normalized_rows: list[dict[str, object]] = []
    for row in rows:
        ipc_code = (row.get("IPC_code") or "").strip().replace("%", "")
        normalized_ipc = re.sub(r"[^A-Za-z0-9/]", "", ipc_code).upper()
        ipc_subclass = re.sub(r"[^A-Za-z0-9]", "", normalized_ipc)[:4]
        if not ipc_subclass:
            continue
        normalized_rows.append(
            {
                "ipc_subclass": ipc_subclass,
                "ipc_maingroup_symbol": normalized_ipc,
                "techn_field_nr": int(row["Field_number"]),
                "techn_sector": row["Sector_en"].strip(),
                "techn_field": row["Field_en"].strip(),
                "wipo_industry_code": row["Field_en"].strip(),
            }
        )
    frame = pd.DataFrame(normalized_rows).drop_duplicates()
    output_path = output_dir / "wipo_techn_field_ipc.parquet"
    frame.to_parquet(output_path, index=False)
    return RefBuildRecord(
        filename=output_path.name,
        source_url=WIPO_IPC_CONCORDANCE_URL,
        row_count=len(frame),
        note=f"Built from the official WIPO IPC concordance workbook; methodology: {WIPO_IPC_METHODOLOGY_URL}",
    )


def build_iso_country_map(output_dir: Path) -> tuple[pd.DataFrame, RefBuildRecord]:
    payload = json.loads(_fetch_bytes(WORLD_BANK_COUNTRIES_URL).decode("utf-8"))
    normalized_rows: list[dict[str, str]] = []
    for row in payload[1]:
        iso2 = (row.get("iso2Code") or "").strip().upper()
        iso3 = (row.get("id") or "").strip().upper()
        if len(iso2) != 2 or iso2 == "NA" or len(iso3) != 3:
            continue
        normalized_rows.append(
            {
                "iso2": iso2,
                "iso3": iso3,
                "country_name": (row.get("name") or "").strip(),
            }
        )
    # World Bank omits Taiwan from the public country endpoint, but it is needed by the
    # patent/IP-index corpus and appears explicitly in the 2025 Chamber ranking set.
    normalized_rows.append({"iso2": "TW", "iso3": "TWN", "country_name": "Taiwan"})
    frame = pd.DataFrame(normalized_rows).drop_duplicates().sort_values(["iso2", "iso3"]).reset_index(drop=True)
    output_path = output_dir / "iso_country_map.parquet"
    frame.to_parquet(output_path, index=False)
    return frame, RefBuildRecord(
        filename=output_path.name,
        source_url=WORLD_BANK_COUNTRIES_URL,
        row_count=len(frame),
        note="Built from the official World Bank country API plus an explicit Taiwan supplement for patent-office coverage.",
    )


def build_world_bank_gdp_ppp(output_dir: Path, iso_map: pd.DataFrame) -> RefBuildRecord:
    payload = json.loads(_fetch_bytes(WORLD_BANK_GDP_PPP_URL).decode("utf-8"))
    valid_iso3 = set(iso_map["iso3"].tolist())
    normalized_rows: list[dict[str, object]] = []
    for row in payload[1]:
        iso3 = (row.get("countryiso3code") or "").strip().upper()
        year = row.get("date")
        value = row.get("value")
        if iso3 not in valid_iso3 or value is None:
            continue
        normalized_rows.append(
            {
                "iso3": iso3,
                "snapshot_year": int(year),
                "gdp_value": float(value),
            }
        )
    frame = pd.DataFrame(normalized_rows).drop_duplicates().sort_values(["iso3", "snapshot_year"]).reset_index(drop=True)
    output_path = output_dir / "world_bank_gdp_ppp.parquet"
    frame.to_parquet(output_path, index=False)
    return RefBuildRecord(
        filename=output_path.name,
        source_url=WORLD_BANK_GDP_PPP_URL,
        row_count=len(frame),
        note="Built from the official World Bank GDP PPP indicator API (NY.GDP.MKTP.PP.CD).",
    )


def build_us_chamber_ip_index(output_dir: Path, iso_map: pd.DataFrame) -> RefBuildRecord:
    page_text = _fetch_bytes(US_CHAMBER_IP_INDEX_URL).decode("utf-8", errors="replace")
    table_match = re.search(r'<table id="[^"]+" class="display w-full"><thead><tr><th>.*?</thead><tbody>(.*?)</tbody>', page_text)
    if table_match is None:
        raise RuntimeError("Could not locate the 2025 IP Index score table on the official U.S. Chamber page.")
    row_matches = re.findall(r"<tr><td[^>]*>(.*?)</td><td[^>]*>(.*?)</td><td[^>]*>(.*?)</td></tr>", table_match.group(1))
    option_matches = re.findall(r'<option value="([A-Z]{2})">([^<]+)</option>', page_text)

    option_map = {html.unescape(name).strip(): code.strip().upper() for code, name in option_matches}
    alias_map = {
        "United States": "US",
        "United States of America": "US",
        "UK": "GB",
        "UAE": "AE",
        "South Korea": "KR",
        "Brunei": "BN",
        "Russia": "RU",
        "T¸rkiye": "TR",
        "Türkiye": "TR",
    }
    valid_iso2 = set(iso_map["iso2"].tolist())
    normalized_rows: list[dict[str, object]] = []
    for _, economy_name, score_text in row_matches:
        economy = html.unescape(economy_name).strip()
        iso2 = option_map.get(economy) or alias_map.get(economy)
        if iso2 is None:
            raise RuntimeError(f"Could not map U.S. Chamber economy `{economy}` to ISO-2.")
        if iso2 not in valid_iso2:
            raise RuntimeError(f"Mapped ISO-2 code `{iso2}` for `{economy}` is missing from iso_country_map.")
        normalized_rows.append(
            {
                "iso2": iso2,
                "snapshot_year": 2025,
                "ip_score": float(score_text.strip().replace("%", "")),
            }
        )
    frame = pd.DataFrame(normalized_rows).drop_duplicates().sort_values(["iso2"]).reset_index(drop=True)
    output_path = output_dir / "us_chamber_ip_index.parquet"
    frame.to_parquet(output_path, index=False)
    return RefBuildRecord(
        filename=output_path.name,
        source_url=US_CHAMBER_IP_INDEX_URL,
        row_count=len(frame),
        note="Built from the official 2025 U.S. Chamber IP Index page score table.",
    )


def build_up_member_states(output_dir: Path) -> RefBuildRecord:
    member_states = [
        "AT",
        "BE",
        "BG",
        "DK",
        "EE",
        "FI",
        "FR",
        "DE",
        "IT",
        "LV",
        "LT",
        "LU",
        "MT",
        "NL",
        "PT",
        "RO",
        "SI",
        "SE",
    ]
    frame = pd.DataFrame(
        {
            "jurisdiction_code": member_states,
            "effective_from": ["2024-09-01"] * len(member_states),
            "source_generation": ["UP_SECOND_GENERATION"] * len(member_states),
        }
    )
    output_path = output_dir / "up_member_states.parquet"
    frame.to_parquet(output_path, index=False)
    return RefBuildRecord(
        filename=output_path.name,
        source_url=EPO_UP_MEMBER_STATES_URL,
        row_count=len(frame),
        note="Built from the official EPO 2025 Unitary Patent guidance page covering the 18-state post-Romania scope.",
    )


def _kind_rows_for_jurisdiction(jurisdiction_code: str) -> Iterable[dict[str, object]]:
    pending_codes = ["A"] + [f"A{i}" for i in range(10)]
    grant_codes = ["B"] + [f"B{i}" for i in range(10)]
    modifier_codes = ["C"] + [f"C{i}" for i in range(10)]

    for code in pending_codes:
        yield {
            "jurisdiction_code": jurisdiction_code,
            "kind_code": code,
            "universal_stage": "PENDING_APPLICATION",
            "stage_multiplier": 0.2,
            "is_enforceable": False,
            "legal_status_proxy": "pending_application",
        }
    for code in grant_codes:
        stage = "STANDARD_GRANT"
        multiplier = 1.0
        if jurisdiction_code == "EP" and code == "B2":
            stage = "OPPOSITION_SURVIVOR"
            multiplier = 3.0
        yield {
            "jurisdiction_code": jurisdiction_code,
            "kind_code": code,
            "universal_stage": stage,
            "stage_multiplier": multiplier,
            "is_enforceable": True,
            "legal_status_proxy": "active_grant",
        }
    for code in modifier_codes:
        stage = "POST_GRANT_MODIFIER"
        multiplier = 0.8
        enforceable = False
        legal_status_proxy = "post_grant_modifier"
        if jurisdiction_code == "EP" and code == "C0":
            stage = "UNITARY_GRANT"
            multiplier = 1.0
            enforceable = True
            legal_status_proxy = "active_grant"
        yield {
            "jurisdiction_code": jurisdiction_code,
            "kind_code": code,
            "universal_stage": stage,
            "stage_multiplier": multiplier,
            "is_enforceable": enforceable,
            "legal_status_proxy": legal_status_proxy,
        }


def build_kind_code_normalization(output_dir: Path, iso_map: pd.DataFrame) -> RefBuildRecord:
    jurisdictions = sorted(set(iso_map["iso2"].tolist()) | {"EP", "WO", "TW"})
    rows = [row for jurisdiction_code in jurisdictions for row in _kind_rows_for_jurisdiction(jurisdiction_code)]
    frame = pd.DataFrame(rows).drop_duplicates().sort_values(["jurisdiction_code", "kind_code"]).reset_index(drop=True)
    output_path = output_dir / "kind_code_normalization.parquet"
    frame.to_parquet(output_path, index=False)
    return RefBuildRecord(
        filename=output_path.name,
        source_url="docs/new-feature-ideas/kind-code-normalization-and-tiered-market-weighting-build-guide.md",
        row_count=len(frame),
        note="Bootstrap office-tagged kind-code seed built from the local methodology guide plus explicit EP-specific rules (B2 opposition survivor, C0 unitary grant).",
    )


def write_manifest(output_dir: Path, records: list[RefBuildRecord]) -> None:
    manifest_path = output_dir / "_critical_refs_manifest.json"
    manifest = {
        "built_at_utc": pd.Timestamp.utcnow().isoformat(),
        "records": [asdict(record) for record in records],
    }
    manifest_path.write_text(json.dumps(manifest, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the critical raw reference parquet files for the PatentIQ ETL pipeline.")
    parser.add_argument("--output-dir", type=Path, default=Path("etl/data/raw/refs"))
    args = parser.parse_args()

    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    records: list[RefBuildRecord] = []
    records.append(build_wipo_techn_field_ipc(output_dir))
    iso_map, iso_record = build_iso_country_map(output_dir)
    records.append(iso_record)
    records.append(build_world_bank_gdp_ppp(output_dir, iso_map))
    records.append(build_us_chamber_ip_index(output_dir, iso_map))
    records.append(build_up_member_states(output_dir))
    records.append(build_kind_code_normalization(output_dir, iso_map))
    write_manifest(output_dir, records)

    for record in records:
        print(f"{record.filename}: {record.row_count} rows")


if __name__ == "__main__":
    main()
