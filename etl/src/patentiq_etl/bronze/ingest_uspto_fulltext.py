from __future__ import annotations

import copy
from datetime import date
from pathlib import Path
import xml.etree.ElementTree as ET

from patentiq_etl.common.io import ensure_dir, normalize_ws, write_pylist_parquet
from patentiq_etl.common.types import BuildSettings, StageResult


USPTO_BRONZE_OUTPUT_COLUMNS = {
    "bronze_uspto_ft_document": [
        "publication_number_full",
        "publication_country",
        "publication_number",
        "publication_kind",
        "publication_date",
        "application_number_full",
        "application_date",
        "application_type",
        "us_application_series_code",
        "source_file_name",
    ],
    "bronze_uspto_ft_biblio_application": [
        "publication_number_full",
        "application_number_full",
        "application_type",
        "us_application_series_code",
        "filing_date",
        "source_file_name",
    ],
    "bronze_uspto_ft_abstract": ["publication_number_full", "abstract_text", "source_file_name"],
    "bronze_uspto_ft_claims": ["publication_number_full", "claim_id", "claim_num", "claim_text_plain", "source_file_name"],
    "bronze_uspto_ft_related_documents": [
        "publication_number_full",
        "related_document_type",
        "related_country",
        "related_doc_number",
        "related_date",
        "source_file_name",
    ],
    "bronze_uspto_ft_applicants": [
        "publication_number_full",
        "sequence_no",
        "party_role",
        "designation",
        "first_name",
        "last_name",
        "city",
        "state",
        "country",
        "source_file_name",
    ],
    "bronze_uspto_ft_inventors": [
        "publication_number_full",
        "sequence_no",
        "designation",
        "first_name",
        "last_name",
        "city",
        "state",
        "country",
        "source_file_name",
    ],
}


def _text(elem: ET.Element | None) -> str | None:
    """Return normalized inner text for an XML element."""
    if elem is None:
        return None
    return normalize_ws("".join(elem.itertext()))


def _date(text: str | None) -> date | None:
    """Parse USPTO compact `YYYYMMDD` strings into Python dates."""
    if not text or len(text) != 8 or not text.isdigit():
        return None
    return date(int(text[0:4]), int(text[4:6]), int(text[6:8]))


def _local_name(elem: ET.Element) -> str:
    """Return the namespace-stripped local tag name for an XML element."""
    return elem.tag.rsplit("}", 1)[-1] if "}" in elem.tag else elem.tag


def _iter_document_roots(root: ET.Element) -> list[ET.Element]:
    """Return publication-level document roots from a USPTO bulk XML tree."""
    direct_document_tags = {"patent-application-publication", "us-patent-application", "us-patent-grant"}
    if _local_name(root) in direct_document_tags:
        return [root]
    document_roots = [elem for elem in root.iter() if _local_name(elem) in direct_document_tags]
    return document_roots or [root]


def _parse_document_root(document_root: ET.Element, source_file_name: str) -> tuple[dict, dict | None, list[dict], list[dict], list[dict], list[dict]]:
    """Parse one publication-level USPTO XML element into Bronze rows."""
    root = document_root

    pub_doc = root.find(".//publication-reference/document-id")
    app_doc = root.find(".//application-reference/document-id")
    application_reference = root.find(".//application-reference")
    series_code = _text(root.find(".//us-application-series-code"))
    publication_number_full = None
    if pub_doc is not None:
        publication_number_full = "".join(
            filter(
                None,
                [
                    _text(pub_doc.find("country")),
                    _text(pub_doc.find("doc-number")),
                    _text(pub_doc.find("kind")),
                ],
            )
        )

    doc_row = {
        "publication_number_full": publication_number_full,
        "publication_country": _text(pub_doc.find("country")) if pub_doc is not None else None,
        "publication_number": _text(pub_doc.find("doc-number")) if pub_doc is not None else None,
        "publication_kind": _text(pub_doc.find("kind")) if pub_doc is not None else None,
        "publication_date": _date(_text(pub_doc.find("date")) if pub_doc is not None else None),
        "application_number_full": _text(app_doc.find("doc-number")) if app_doc is not None else None,
        "application_date": _date(_text(app_doc.find("date")) if app_doc is not None else None),
        "application_type": application_reference.attrib.get("appl-type") if application_reference is not None else None,
        "us_application_series_code": series_code,
        "source_file_name": source_file_name,
    }

    abstract_elem = root.find(".//abstract")
    abstract_row = None
    if publication_number_full and abstract_elem is not None:
        abstract_row = {
            "publication_number_full": publication_number_full,
            "abstract_text": _text(abstract_elem),
            "source_file_name": source_file_name,
        }

    claim_rows: list[dict] = []
    related_rows: list[dict] = []
    applicant_rows: list[dict] = []
    inventor_rows: list[dict] = []
    for claim in root.findall(".//claims/claim"):
        claim_text = _text(claim)
        if not publication_number_full or not claim_text:
            continue
        claim_rows.append(
            {
                "publication_number_full": publication_number_full,
                "claim_id": claim.attrib.get("id"),
                "claim_num": int(claim.attrib["num"]) if claim.attrib.get("num", "").isdigit() else None,
                "claim_text_plain": claim_text,
                "source_file_name": source_file_name,
            }
        )
    for provisional in root.findall(".//us-related-documents/us-provisional-application"):
        document_id = provisional.find("document-id")
        related_rows.append(
            {
                "publication_number_full": publication_number_full,
                "related_document_type": "us_provisional_application",
                "related_country": _text(document_id.find("country")) if document_id is not None else None,
                "related_doc_number": _text(document_id.find("doc-number")) if document_id is not None else None,
                "related_date": _date(_text(document_id.find("date")) if document_id is not None else None),
                "source_file_name": source_file_name,
            }
        )

    for applicant in root.findall(".//us-parties/us-applicants/us-applicant"):
        addressbook = applicant.find("addressbook")
        address = addressbook.find("address") if addressbook is not None else None
        applicant_rows.append(
            {
                "publication_number_full": publication_number_full,
                "sequence_no": applicant.attrib.get("sequence"),
                "party_role": applicant.attrib.get("app-type"),
                "designation": applicant.attrib.get("designation"),
                "first_name": _text(addressbook.find("first-name")) if addressbook is not None else None,
                "last_name": _text(addressbook.find("last-name")) if addressbook is not None else None,
                "city": _text(address.find("city")) if address is not None else None,
                "state": _text(address.find("state")) if address is not None else None,
                "country": _text(address.find("country")) if address is not None else None,
                "source_file_name": source_file_name,
            }
        )

    for inventor in root.findall(".//us-parties/inventors/inventor"):
        addressbook = inventor.find("addressbook")
        address = addressbook.find("address") if addressbook is not None else None
        inventor_rows.append(
            {
                "publication_number_full": publication_number_full,
                "sequence_no": inventor.attrib.get("sequence"),
                "designation": inventor.attrib.get("designation"),
                "first_name": _text(addressbook.find("first-name")) if addressbook is not None else None,
                "last_name": _text(addressbook.find("last-name")) if addressbook is not None else None,
                "city": _text(address.find("city")) if address is not None else None,
                "state": _text(address.find("state")) if address is not None else None,
                "country": _text(address.find("country")) if address is not None else None,
                "source_file_name": source_file_name,
            }
        )

    return doc_row, abstract_row, claim_rows, related_rows, applicant_rows, inventor_rows


def iter_publication_payloads(xml_path: Path) -> list[tuple[dict, dict | None, list[dict], list[dict], list[dict], list[dict]]]:
    """Parse a USPTO bulk XML file into one payload tuple per publication contained in the file."""
    tree = ET.parse(xml_path)
    root = tree.getroot()
    return [_parse_document_root(document_root, xml_path.name) for document_root in _iter_document_roots(root)]


def extract_publication_numbers(xml_path: Path) -> set[str]:
    """Return all publication_number_full values found in a USPTO bulk XML file."""
    publication_numbers: set[str] = set()
    for doc_row, _, _, _, _, _ in iter_publication_payloads(xml_path):
        if doc_row.get("publication_number_full"):
            publication_numbers.add(doc_row["publication_number_full"])
    return publication_numbers


def filter_bulk_xml_to_publications(xml_path: Path, publication_numbers: set[str], out_path: Path) -> int:
    """Write a filtered USPTO bulk XML file containing only the requested publication documents."""
    if not publication_numbers:
        return 0

    tree = ET.parse(xml_path)
    root = tree.getroot()
    matched_roots: list[ET.Element] = []
    for document_root in _iter_document_roots(root):
        doc_row, _, _, _, _, _ = _parse_document_root(document_root, xml_path.name)
        publication_number_full = doc_row.get("publication_number_full")
        if publication_number_full and publication_number_full in publication_numbers:
            matched_roots.append(copy.deepcopy(document_root))

    if not matched_roots:
        return 0

    direct_document_tags = {"patent-application-publication", "us-patent-application", "us-patent-grant"}
    if _local_name(root) in direct_document_tags and len(matched_roots) == 1:
        filtered_root = matched_roots[0]
    else:
        filtered_root = ET.Element(root.tag, root.attrib)
        filtered_root.text = root.text
        filtered_root.tail = root.tail
        for document_root in matched_roots:
            filtered_root.append(document_root)

    ensure_dir(out_path.parent)
    ET.ElementTree(filtered_root).write(out_path, encoding="utf-8", xml_declaration=True)
    return len(matched_roots)


def build_biblio_rows(documents: list[dict]) -> list[dict]:
    """Build USPTO biblio rows from parsed document rows."""
    return [
        {
            "publication_number_full": row["publication_number_full"],
            "application_number_full": row["application_number_full"],
            "application_type": row["application_type"],
            "us_application_series_code": row["us_application_series_code"],
            "filing_date": row["application_date"],
            "source_file_name": row["source_file_name"],
        }
        for row in documents
    ]


def write_uspto_bronze_outputs(
    bronze_dir: Path,
    documents: list[dict],
    abstracts: list[dict],
    claims: list[dict],
    related_documents: list[dict],
    applicants: list[dict],
    inventors: list[dict],
) -> dict[str, int]:
    """Write the canonical USPTO Bronze parquet outputs and return row counts by table stem."""
    outputs = {
        "bronze_uspto_ft_document": documents,
        "bronze_uspto_ft_biblio_application": build_biblio_rows(documents),
        "bronze_uspto_ft_abstract": abstracts,
        "bronze_uspto_ft_claims": claims,
        "bronze_uspto_ft_related_documents": related_documents,
        "bronze_uspto_ft_applicants": applicants,
        "bronze_uspto_ft_inventors": inventors,
    }
    row_counts: dict[str, int] = {}
    for table_name, rows in outputs.items():
        row_counts[table_name] = write_pylist_parquet(
            rows,
            bronze_dir / f"{table_name}.parquet",
            columns=USPTO_BRONZE_OUTPUT_COLUMNS[table_name],
        )
    return row_counts


def ingest_uspto_fulltext(settings: BuildSettings) -> StageResult:
    """Parse raw USPTO XML payloads into schema-aligned Bronze parquet text-provider tables."""
    result = StageResult(
        stage="bronze-uspto-fulltext",
        status="success",
        summary="Parsed USPTO XML into Bronze text-provider tables for semantic workflows.",
        methods=[
            "Parsed USPTO XML application/publication identifiers, abstracts, and claims.",
            "Preserved publication kind and claim ordering fields required for semantic hierarchy selection.",
        ],
        calculations=[
            "No family collapse or semantic prioritization occurs in Bronze. This stage only lands text-provider tables.",
        ],
        downstream_impacts=[
            "These tables feed representative claim and abstract selection in the semantic Silver stage only.",
            "They must not be used to override PATSTAT or Register harmonized metadata layers downstream.",
        ],
        doc_refs=[
            "docs/data/uspto-full-text-schema.md",
            "docs/new-feature-ideas/semantic-similarity-and-vector-layer-requirements.md",
            "docs/next-phase-v2/24-patentiq-v2-local-etl-and-artifact-build-runbook.md",
        ],
    )

    if settings.uspto_source_mode == "odp_api":
        existing_outputs = [settings.bronze_dir / f"{table_name}.parquet" for table_name in USPTO_BRONZE_OUTPUT_COLUMNS]
        if all(path.exists() for path in existing_outputs):
            result.inputs.extend(str(path) for path in existing_outputs)
            result.outputs.extend(str(path) for path in existing_outputs)
            result.summary = "USPTO Bronze parquet was already materialized during the ODP stream extraction path."
            result.methods.append("Skipped redundant bounded-XML parsing because direct USPTO Bronze parquet outputs already exist.")
            return result
        result.summary = "USPTO Bronze parsing was deferred because USPTO is configured for the external ODP stream path and no direct Bronze outputs are present in this runtime."
        result.methods.append("Skipped bounded-XML parsing because USPTO is handled by the separate `prebronze-uspto-odp` stage when that external path is executed.")
        result.metrics["uspto_odp_outputs_present"] = 0
        return result

    documents: list[dict] = []
    abstracts: list[dict] = []
    claims: list[dict] = []
    related_documents: list[dict] = []
    applicants: list[dict] = []
    inventors: list[dict] = []
    for xml_path in list(settings.bounded_uspto_dir.glob("*.XML")) + list(settings.bounded_uspto_dir.glob("*.xml")):
        result.inputs.append(str(xml_path))
        for doc_row, abstract_row, claim_rows, related_rows, applicant_rows, inventor_rows in iter_publication_payloads(xml_path):
            if not doc_row.get("publication_number_full"):
                continue
            documents.append(doc_row)
            if abstract_row:
                abstracts.append(abstract_row)
            claims.extend(claim_rows)
            related_documents.extend(related_rows)
            applicants.extend(applicant_rows)
            inventors.extend(inventor_rows)

    if not documents:
        result.status = "degraded"
        result.warnings.append("No USPTO XML source files were found for Bronze parsing.")
        return result
    row_counts = write_uspto_bronze_outputs(
        settings.bronze_dir,
        documents,
        abstracts,
        claims,
        related_documents,
        applicants,
        inventors,
    )
    for table_name, row_count in row_counts.items():
        out_path = settings.bronze_dir / f"{table_name}.parquet"
        result.outputs.append(str(out_path))
        result.metrics[f"{table_name}_rows"] = row_count
    result.metrics["uspto_total_parsed_rows"] = sum(
        value for key, value in result.metrics.items() if key.startswith("bronze_uspto_ft_") and key.endswith("_rows")
    )
    return result
