from __future__ import annotations

from patentiq_etl.common.types import StageResult


def test_stage_result_finish_sets_timestamp() -> None:
    result = StageResult(stage="test", status="success", summary="ok")
    assert result.finished_at is None
    result.finish()
    assert result.finished_at is not None
