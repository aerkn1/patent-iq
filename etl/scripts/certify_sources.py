from __future__ import annotations

from pathlib import Path

from _bootstrap import bootstrap

etl_root = bootstrap()

from patentiq_etl.bronze.certify import certify_sources
from patentiq_etl.common.config import load_settings
from patentiq_etl.common.journal import append_stage_entry
from patentiq_etl.common.logging_utils import configure_logger
from patentiq_etl.common.manifest import write_stage_manifest


def main() -> None:
    """Run source certification as a standalone command-line entrypoint."""
    settings = load_settings(etl_root)
    log_path = settings.manifests_dir / "stages" / "source-certification.log"
    logger = configure_logger("source-certification", log_path)
    logger.info("Starting source certification for PatentIQ ETL.")
    result = certify_sources(settings).finish()
    logger.info("Source certification completed with status=%s", result.status)
    manifest_path = settings.manifests_dir / "stages" / "source-certification.json"
    write_stage_manifest(manifest_path, result)
    append_stage_entry(settings.journal_path, result)


if __name__ == "__main__":
    main()
