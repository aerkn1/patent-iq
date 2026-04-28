from __future__ import annotations

from _bootstrap import bootstrap

etl_root = bootstrap()

from patentiq_etl.common.config import load_settings
from patentiq_etl.common.journal import append_stage_entry
from patentiq_etl.common.logging_utils import configure_logger
from patentiq_etl.common.manifest import write_stage_manifest
from patentiq_etl.publish.run import publish_release


def main() -> None:
    """Run release publication as a standalone command-line entrypoint."""
    settings = load_settings(etl_root)
    logger = configure_logger("publish", settings.manifests_dir / "stages" / "publish.log")
    results = publish_release(settings)
    for result in results:
        result = result.finish()
        logger.info("Publish stage completed with status=%s", result.status)
        write_stage_manifest(settings.manifests_dir / "stages" / "publish.json", result)
        append_stage_entry(settings.journal_path, result)


if __name__ == "__main__":
    main()
