from __future__ import annotations

from pathlib import Path

from patentiq_etl.common.types import StageResult


def _section(title: str, items: list[str]) -> str:
    """Render one markdown section for the ETL implementation journal."""
    if not items:
        return ""
    lines = [f"### {title}", ""]
    lines.extend([f"1. {items[0]}"] + [f"{idx}. {item}" for idx, item in enumerate(items[1:], start=2)])
    lines.append("")
    return "\n".join(lines)


def append_stage_entry(journal_path: Path, result: StageResult) -> None:
    """Append a human-readable stage record to the persistent ETL markdown journal."""
    journal_path.parent.mkdir(parents=True, exist_ok=True)
    if not journal_path.exists():
        journal_path.write_text("# PatentIQ ETL Implementation Log\n\n", encoding="utf-8")

    lines: list[str] = []
    lines.append(f"## {result.stage} | {result.status}")
    lines.append("")
    lines.append(f"- Summary: {result.summary}")
    lines.append(f"- Started: {result.started_at}")
    lines.append(f"- Finished: {result.finished_at or 'pending'}")
    lines.append("")
    lines.append(_section("Inputs", result.inputs))
    lines.append(_section("Outputs", result.outputs))
    if result.artifacts:
        lines.append("### Artifacts")
        lines.append("")
        for key, value in result.artifacts.items():
            lines.append(f"- `{key}`: `{value}`")
        lines.append("")
    lines.append(_section("Methods", result.methods))
    lines.append(_section("Calculations", result.calculations))
    lines.append(_section("Downstream Impacts", result.downstream_impacts))
    lines.append(_section("Governing Docs", result.doc_refs))
    lines.append(_section("Warnings", result.warnings))
    if result.metrics:
        lines.append("### Metrics")
        lines.append("")
        for key, value in result.metrics.items():
            lines.append(f"- `{key}`: `{value}`")
        lines.append("")
    journal_path.write_text(
        journal_path.read_text(encoding="utf-8") + "\n".join([line for line in lines if line is not None]) + "\n",
        encoding="utf-8",
    )
