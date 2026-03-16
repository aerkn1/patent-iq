from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from patentiq_etl.common.types import BuildSettings


def _load_yaml(path: Path) -> dict[str, Any]:
    """Load a YAML file into a dictionary, defaulting to an empty mapping."""
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def load_settings(etl_root: Path) -> BuildSettings:
    """Resolve ETL configuration files into one typed build-settings object."""
    build_cfg = _load_yaml(etl_root / "conf" / "build.yaml")
    scope_cfg = _load_yaml(etl_root / "conf" / "scope.yaml")
    azure_cfg = _load_yaml(etl_root / "conf" / "azure.yaml")
    threshold_cfg = _load_yaml(etl_root / "conf" / "thresholds.yaml")

    build = build_cfg["build"]
    paths = build_cfg["paths"]
    methods = build_cfg["methods"]
    sources = build_cfg.get("sources", {})
    execution = build_cfg.get("execution", {})
    scope = scope_cfg["scope"]

    repo_root = (etl_root / paths["repo_root"]).resolve()

    def resolve(value: str) -> Path:
        return (repo_root / value).resolve()

    return BuildSettings(
        repo_root=repo_root,
        release_id=build["release_id"],
        snapshot_date=build["snapshot_date"],
        year_window_start=build["year_window_start"],
        year_window_end=build["year_window_end"],
        heritage_backfill_start=int(build.get("heritage_backfill_start", 1996)),
        heritage_backfill_end=int(build.get("heritage_backfill_end", build["year_window_start"] - 1)),
        azure_publish_enabled=bool(build["azure_publish_enabled"]),
        vector_sample_pct=float(build["vector_sample_pct"]),
        active_grant_only_for_semantic=bool(build["active_grant_only_for_semantic"]),
        method_version=methods["method_version"],
        semantic_embedding_method=methods["semantic_embedding_method"],
        semantic_ann_method=methods["semantic_ann_method"],
        patstat_source_mode=sources.get("patstat_source_mode", "local_files"),
        register_source_mode=sources.get("register_source_mode", "local_files"),
        epab_source_mode=sources.get("epab_source_mode", "local_files"),
        uspto_source_mode=sources.get("uspto_source_mode", "local_files"),
        refs_source_mode=sources.get("refs_source_mode", "local_files"),
        tip_env=sources.get("tip_env", "PROD"),
        raw_patstat_dir=resolve(paths["raw_patstat_dir"]),
        raw_register_dir=resolve(paths["raw_register_dir"]),
        raw_uspto_dir=resolve(paths["raw_uspto_dir"]),
        raw_epab_dir=resolve(paths["raw_epab_dir"]),
        raw_refs_dir=resolve(paths["raw_refs_dir"]),
        bounded_patstat_dir=resolve(paths["bounded_patstat_dir"]),
        bounded_register_dir=resolve(paths["bounded_register_dir"]),
        bounded_uspto_dir=resolve(paths["bounded_uspto_dir"]),
        bounded_epab_dir=resolve(paths["bounded_epab_dir"]),
        bounded_refs_dir=resolve(paths["bounded_refs_dir"]),
        bounded_seed_dir=resolve(paths["bounded_seed_dir"]),
        bronze_dir=resolve(paths["bronze_dir"]),
        silver_dir=resolve(paths["silver_dir"]),
        gold_dir=resolve(paths["gold_dir"]),
        ml_dir=resolve(paths["ml_dir"]),
        vectors_dir=resolve(paths["vectors_dir"]),
        releases_dir=resolve(paths["releases_dir"]),
        manifests_dir=resolve(paths["manifests_dir"]),
        journal_path=resolve(paths["journal_path"]),
        ref_techn_field_ipc=resolve(paths["ref_techn_field_ipc"]),
        scope_type=scope["type"],
        field_source=scope["field_source"],
        selected_wipo_fields=list(scope["selected_wipo_fields"]),
        thresholds=threshold_cfg["thresholds"],
        azure=azure_cfg["azure"],
        execution=execution,
    )
