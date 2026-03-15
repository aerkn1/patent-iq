from __future__ import annotations

import sys
from pathlib import Path


def bootstrap() -> Path:
    """Add the ETL source directory to `sys.path` and return the ETL root."""
    script_path = Path(__file__).resolve()
    etl_root = script_path.parent.parent
    src_path = etl_root / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    return etl_root
