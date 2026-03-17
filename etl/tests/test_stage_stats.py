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


def test_write_stage_stats_profiles_directory_outputs(tmp_path) -> None:
    stats_path = tmp_path / "stats.json"
    output_dir = tmp_path / "chunks"
    output_dir.mkdir()
    (output_dir / "tip_chunk_plan.json").write_text("{}", encoding="utf-8")
    result = StageResult(
        stage="tip-chunk-plan",
        status="success",
        summary="planned",
        outputs=[str(output_dir)],
    ).finish()

    write_stage_stats(stats_path, result)

    payload = json.loads(stats_path.read_text(encoding="utf-8"))
    assert payload["output_profiles"][0]["path"] == str(output_dir)
    assert payload["output_profiles"][0]["type"] == "directory"
    assert payload["output_profiles"][0]["entry_count"] == 1
    assert "sha256" not in payload["output_profiles"][0]
