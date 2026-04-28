from __future__ import annotations

import textwrap

from patentiq_etl.bronze.ingest_uspto_fulltext import (
    extract_publication_numbers,
    filter_bulk_xml_to_publications,
    iter_publication_payloads,
)
from patentiq_etl.prebronze.uspto_odp import detect_schema_version, iter_concatenated_xml_documents


def test_uspto_bulk_xml_parses_multiple_publications(tmp_path) -> None:
    xml_path = tmp_path / "bulk.xml"
    xml_path.write_text(
        textwrap.dedent(
            """\
            <bulk-data>
              <patent-application-publication>
                <publication-reference><document-id><country>US</country><doc-number>111</doc-number><kind>A1</kind><date>20240101</date></document-id></publication-reference>
                <application-reference appl-type="utility"><document-id><doc-number>111</doc-number><date>20230101</date></document-id></application-reference>
                <abstract><p>First abstract.</p></abstract>
              </patent-application-publication>
              <patent-application-publication>
                <publication-reference><document-id><country>US</country><doc-number>222</doc-number><kind>B1</kind><date>20240202</date></document-id></publication-reference>
                <application-reference appl-type="utility"><document-id><doc-number>222</doc-number><date>20230202</date></document-id></application-reference>
                <claims><claim id="CLM-1" num="1"><claim-text>Second claim.</claim-text></claim></claims>
              </patent-application-publication>
            </bulk-data>
            """
        ),
        encoding="utf-8",
    )

    payloads = iter_publication_payloads(xml_path)
    publication_numbers = extract_publication_numbers(xml_path)

    assert len(payloads) == 2
    assert publication_numbers == {"US111A1", "US222B1"}


def test_uspto_bulk_xml_can_be_filtered_to_chunk_publications(tmp_path) -> None:
    xml_path = tmp_path / "bulk.xml"
    xml_path.write_text(
        textwrap.dedent(
            """\
            <bulk-data>
              <patent-application-publication>
                <publication-reference><document-id><country>US</country><doc-number>111</doc-number><kind>A1</kind><date>20240101</date></document-id></publication-reference>
                <application-reference appl-type="utility"><document-id><doc-number>111</doc-number><date>20230101</date></document-id></application-reference>
                <abstract><p>First abstract.</p></abstract>
              </patent-application-publication>
              <patent-application-publication>
                <publication-reference><document-id><country>US</country><doc-number>222</doc-number><kind>B1</kind><date>20240202</date></document-id></publication-reference>
                <application-reference appl-type="utility"><document-id><doc-number>222</doc-number><date>20230202</date></document-id></application-reference>
                <claims><claim id="CLM-1" num="1"><claim-text>Second claim.</claim-text></claim></claims>
              </patent-application-publication>
            </bulk-data>
            """
        ),
        encoding="utf-8",
    )

    filtered_path = tmp_path / "filtered.xml"
    matched_count = filter_bulk_xml_to_publications(xml_path, {"US222B1"}, filtered_path)

    payloads = iter_publication_payloads(filtered_path)
    publication_numbers = extract_publication_numbers(filtered_path)

    assert matched_count == 1
    assert len(payloads) == 1
    assert publication_numbers == {"US222B1"}


def test_uspto_odp_concatenated_documents_are_split_and_versioned(tmp_path) -> None:
    xml_path = tmp_path / "bulk.xml"
    xml_path.write_text(
        textwrap.dedent(
            """\
            <?xml version="1.0" encoding="UTF-8"?>
            <!DOCTYPE us-patent-application SYSTEM "us-patent-application-v42-2006-08-23.dtd">
            <us-patent-application dtd-version="v4.2 2006-08-23">
              <publication-reference><document-id><country>US</country><doc-number>111</doc-number><kind>A1</kind><date>20240101</date></document-id></publication-reference>
            </us-patent-application>
            <?xml version="1.0" encoding="UTF-8"?>
            <!DOCTYPE us-patent-application SYSTEM "us-patent-application-v44-2014-04-03.dtd">
            <us-patent-application dtd-version="v4.4 2014-04-03">
              <publication-reference><document-id><country>US</country><doc-number>222</doc-number><kind>B1</kind><date>20240202</date></document-id></publication-reference>
            </us-patent-application>
            """
        ),
        encoding="utf-8",
    )

    documents = list(iter_concatenated_xml_documents(xml_path))

    assert len(documents) == 2
    assert detect_schema_version(documents[0]) == "v42"
    assert detect_schema_version(documents[1]) == "v44"
