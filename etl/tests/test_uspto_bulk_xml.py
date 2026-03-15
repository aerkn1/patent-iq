from __future__ import annotations

import textwrap

from patentiq_etl.bronze.ingest_uspto_fulltext import extract_publication_numbers, iter_publication_payloads


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
