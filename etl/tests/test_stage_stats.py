from __future__ import annotations

import json

from patentiq_etl.common.stats import write_stage_stats
from patentiq_etl.common.types import StageResult


def test_write_stage_stats_persists_metrics_snapshot(tmp_path) -> None:
    stats_path = tmp_path / "stats.json"
    result = StageResult(
        stage="scope",
        status="success",
        summary="snapshot",
        metrics={"scope_family_count": 10, "scope_publn_count": 25},
        outputs=[],
    ).finish()

    write_stage_stats(stats_path, result)

    payload = json.loads(stats_path.read_text(encoding="utf-8"))
    assert payload["stage"] == "scope"
    assert payload["metrics"]["scope_family_count"] == 10
    assert payload["output_profiles"] == []
