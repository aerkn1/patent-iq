from __future__ import annotations

from patentiq_etl.common.types import StageResult


def test_stage_result_carries_downstream_impacts_in_dict() -> None:
    result = StageResult(
        stage="unit-test",
        status="success",
        summary="contract",
        downstream_impacts=["gold_family_summary", "semantic payload generation"],
    ).finish()

    payload = result.to_dict()

    assert payload["downstream_impacts"] == ["gold_family_summary", "semantic payload generation"]
    assert payload["finished_at"] is not None
