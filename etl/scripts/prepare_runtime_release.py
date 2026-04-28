#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    etl_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(etl_root / "src"))

    from patentiq_etl.publish.runtime_release import main as runtime_release_main

    return runtime_release_main()


if __name__ == "__main__":
    raise SystemExit(main())
