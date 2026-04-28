from __future__ import annotations

from patentiq_etl.common.types import BuildSettings, StageResult
from patentiq_etl.silver.build_core import build_core_silver, build_history_refresh, build_owner_refresh, build_scope_seed
from patentiq_etl.silver.build_enrichment import (
    build_enrichment_silver,
    build_kindcode_legal_refresh_layers,
    build_kindcode_refresh_layers,
    build_legal_status_refresh_layers,
    build_oecd_quality_refresh,
)
from patentiq_etl.silver.build_pit import (
    build_silver_family_classification_visibility_timeline,
    build_silver_family_classification_pit_dense,
    build_silver_family_pit,
    build_silver_family_pit_dense,
)


def run_scope(settings: BuildSettings) -> list[StageResult]:
    """Run the scope-seeding Silver substage."""
    return [build_scope_seed(settings)]


def run_silver(settings: BuildSettings) -> list[StageResult]:
    """Run the full Silver stage group after bounded scope seeds exist."""
    return [build_core_silver(settings), *build_enrichment_silver(settings)]


def run_silver_kind_refresh(settings: BuildSettings) -> list[StageResult]:
    """Refresh Silver outputs impacted by kind-code curation without rerunning semantic."""
    return [build_core_silver(settings), build_kindcode_refresh_layers(settings)]


def run_silver_kind_legal_refresh(settings: BuildSettings) -> list[StageResult]:
    """Refresh only legal-weighted Silver marts after kind-code-dependent citation outputs already exist."""
    return [build_kindcode_legal_refresh_layers(settings)]


def run_silver_legal_status_refresh(settings: BuildSettings) -> list[StageResult]:
    """Refresh coverage and legal-weighted Silver marts after legal-ledger date corrections."""
    return [build_legal_status_refresh_layers(settings)]


def run_silver_oecd_refresh(settings: BuildSettings) -> list[StageResult]:
    """Refresh only the Silver OECD mart from the richer raw OECD artifacts."""
    return [build_oecd_quality_refresh(settings)]


def run_silver_history_refresh(settings: BuildSettings) -> list[StageResult]:
    """Refresh only the Silver legal-history sidecars in batches."""
    return [build_history_refresh(settings)]


def run_silver_owner_refresh(settings: BuildSettings) -> list[StageResult]:
    """Refresh only the Silver owner bridge and primary-owner outputs."""
    return [build_owner_refresh(settings)]


def run_silver_pit(settings: BuildSettings) -> list[StageResult]:
    """Build the point-in-time family feature snapshot for Phase 03 ML and historical product views."""
    return [build_silver_family_pit(settings)]


def run_silver_pit_dense(settings: BuildSettings) -> list[StageResult]:
    """Build the dense family-year PIT snapshot for historical compare and portfolio product views."""
    return [build_silver_family_pit_dense(settings)]


def run_silver_pit_classification_dense(settings: BuildSettings) -> list[StageResult]:
    """Build the dense family-year classification PIT snapshot for CPC/WIPO chronology surfaces."""
    return [build_silver_family_classification_pit_dense(settings)]


def run_silver_pit_classification_visibility(settings: BuildSettings) -> list[StageResult]:
    """Build the first-seen classification visibility timeline used by dense classification PIT."""
    return [build_silver_family_classification_visibility_timeline(settings)]
