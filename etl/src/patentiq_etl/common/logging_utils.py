from __future__ import annotations

import logging
from pathlib import Path


def configure_logger(stage: str, log_path: Path) -> logging.Logger:
    """Create a stage-scoped logger that writes to both stdout and a file."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logger_name = f"patentiq_etl.{stage}"
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    logger.propagate = False

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        "%Y-%m-%d %H:%M:%S",
    )

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
