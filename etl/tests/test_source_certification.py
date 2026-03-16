from __future__ import annotations

from pathlib import Path

from patentiq_etl.common.config import load_settings


def test_settings_load_selected_scope() -> None:
    etl_root = Path(__file__).resolve().parents[1]
    settings = load_settings(etl_root)
    assert settings.scope_type == "mega_cluster_bounded"
    assert len(settings.selected_wipo_fields) == 10
    assert settings.year_window_start == 2007
    assert settings.year_window_end == 2026
    assert settings.heritage_backfill_start == 1996
    assert settings.heritage_backfill_end == 2006
    assert settings.patstat_source_mode == "tip"
    assert settings.register_source_mode == "tip"
    assert settings.epab_source_mode == "tip"
    assert settings.uspto_source_mode == "odp_api"
    assert settings.bounded_patstat_dir.name == "patstat"
    assert settings.bounded_seed_dir.name == "_seeds"
    assert settings.execution["tip_chunked_export_enabled"] is True
    assert settings.execution["chunk_year_span"] == 3
