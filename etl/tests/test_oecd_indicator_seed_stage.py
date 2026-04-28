from __future__ import annotations

from patentiq_etl.prebronze.oecd_seed import (
    build_oecd_indicator_bronze_projection,
    build_oecd_indicator_cohort_stats,
    build_oecd_indicator_longform,
    build_oecd_indicator_seed,
)
from patentiq_etl.prebronze.run import (
    run_build_oecd_indicator_bronze_projection,
    run_build_oecd_indicator_cohort_stats,
    run_build_oecd_indicator_longform,
    run_build_oecd_indicator_seed,
)


def test_oecd_indicator_seed_stage_is_exposed() -> None:
    assert callable(build_oecd_indicator_seed)
    assert callable(run_build_oecd_indicator_seed)
    assert callable(build_oecd_indicator_cohort_stats)
    assert callable(run_build_oecd_indicator_cohort_stats)
    assert callable(build_oecd_indicator_longform)
    assert callable(run_build_oecd_indicator_longform)
    assert callable(build_oecd_indicator_bronze_projection)
    assert callable(run_build_oecd_indicator_bronze_projection)
