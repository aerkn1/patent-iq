from __future__ import annotations

import argparse
import json
from pathlib import Path

from _bootstrap import bootstrap


ETL_ROOT = bootstrap()
REPO_ROOT = ETL_ROOT.parent

from patentiq_etl.ml.phase_grant import build_pending_grant_prediction_parquet  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build the global current-pending pending-grant prediction parquet from existing model artifacts."
    )
    parser.add_argument(
        "--output-path",
        default=str(REPO_ROOT / "etl" / "data" / "ml" / "ml_prediction_pending_grant_pipeline.parquet"),
        help="Output parquet path.",
    )
    parser.add_argument(
        "--chunk-row-limit",
        type=int,
        default=250_000,
        help="Maximum rows to score per in-memory chunk.",
    )
    parser.add_argument(
        "--temp-dir",
        default=str(REPO_ROOT / "etl" / "data" / "ml" / "_tmp_pending_grant_prediction_chunks"),
        help="Temporary parquet chunk directory.",
    )
    args = parser.parse_args()

    ml_dir = REPO_ROOT / "etl" / "data" / "ml"
    silver_dir = REPO_ROOT / "etl" / "data" / "silver"
    metrics = build_pending_grant_prediction_parquet(
        feature_path=ml_dir / "ml_feature_pending_grant_pipeline.parquet",
        branch_history_path=silver_dir / "silver_branch_status_history_dense.parquet",
        model_card_path=ml_dir / "model_card_pending_grant_pipeline.json",
        calibration_path=ml_dir / "pending_grant_pipeline_calibration.json",
        model_12m_path=ml_dir / "pending_grant_pipeline_12m_model.txt",
        model_24m_path=ml_dir / "pending_grant_pipeline_24m_model.txt",
        output_path=Path(args.output_path),
        chunk_row_limit=int(args.chunk_row_limit),
        temp_dir=Path(args.temp_dir),
    )
    print(json.dumps(metrics, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
