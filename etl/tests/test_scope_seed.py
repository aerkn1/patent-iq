from __future__ import annotations

from pathlib import Path

from patentiq_etl.common.config import load_settings


def test_scope_fields_are_unique() -> None:
    etl_root = Path(__file__).resolve().parents[1]
    settings = load_settings(etl_root)
    assert len(settings.selected_wipo_fields) == len(set(settings.selected_wipo_fields))
