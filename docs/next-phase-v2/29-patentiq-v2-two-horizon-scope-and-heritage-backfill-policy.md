# PatentIQ V2 Two-Horizon Scope And Heritage Backfill Policy

## Purpose

Define a clean scope policy so PatentIQ can keep the main MVP warehouse operationally bounded while still supporting historically meaningful heritage and citation-influence analytics.

## Core Decision

PatentIQ should use two separate analytical horizons:

1. `primary operating window`
2. `heritage backfill window`

These horizons share the same mega-cluster field boundary, but they do not serve the same analytical purpose.

## Horizon 1: Primary Operating Window

The primary operating window should be:

1. `2007-2026`
2. inclusive
3. bounded to the selected 10 mega-cluster fields

Why:

1. this is a true 20-year window as of 2026,
2. it is operationally feasible for TIP chunked extraction,
3. it is sufficient for the main MVP current-state product surfaces,
4. it preserves enough cohort depth for trends, OECD normalization, forecasting, and current portfolio analysis.

This horizon should drive the main warehouse outputs:

1. current portfolio views,
2. blocking power,
3. market intelligence,
4. current trend and forecast features,
5. semantic representative-text workflows,
6. most Bronze, Silver, and Gold marts.

## Horizon 2: Heritage Backfill Window

The heritage backfill window should be:

1. older than the main operating window,
2. bounded to the same mega-cluster field universe,
3. focused on historical influence support rather than full heavy warehouse treatment.

Recommended starting policy:

1. `1996-2006` as the first backfill layer,
2. extend earlier only if the heritage use cases prove it is necessary.

Why:

1. foundational pre-2007 families can materially affect heritage and pioneer rankings,
2. older citation context improves RCF-style and historical influence interpretation,
3. many heritage use cases do not require the full enrichment depth of the main operating window.

## What Belongs In The Heritage Backfill

The heritage backfill should include only families that remain relevant to the mega-cluster.

Include:

1. older families that map into the selected mega-cluster fields,
2. publication anchors needed to preserve citation relationships,
3. citation and ghost-node support needed for heritage and OECD-style historical influence,
4. enough owner linkage to support portfolio heritage where needed.

Do not treat the backfill as:

1. a full universal patent estate,
2. a full heavy-enrichment layer for every old family,
3. a reason to widen current-state operational analytics to all history.

## Clean Data-Model Separation

The canonical family entity should remain shared, but scope flags must make the horizon explicit.

Recommended family-level scope flags:

1. `is_main_window_family`
2. `is_heritage_backfill_family`
3. `is_out_of_bounds_ghost`
4. `family_priority_year`

Interpretation:

1. `is_main_window_family = true` means the family belongs to the main `2007-2026` warehouse horizon,
2. `is_heritage_backfill_family = true` means the family is primarily retained for historical analytics support,
3. `is_out_of_bounds_ghost = true` means the family is not a first-class in-scope family object and exists only to preserve graph integrity.

## Metric Separation

Current-state and historical metrics must stay logically separate.

### Current / operational metrics

Use only the primary operating window plus point-in-time legal truth.

Examples:

1. current blocking power,
2. current active portfolio size,
3. current attacker and enforceability views,
4. current market positioning.

### Historical / heritage metrics

Use the primary window plus the heritage backfill where needed.

Examples:

1. pioneer rankings,
2. heritage contribution,
3. long-run field influence,
4. historical citation leadership,
5. OECD-style historical interpretation support.

## ETL Management Model

### Pre-Bronze

Extract two bounded raw horizons:

1. main `2007-2026` mega-cluster horizon
2. lighter heritage backfill horizon for older mega-cluster families

### Bronze

Keep both horizons source-faithful, but do not force them into one undifferentiated scope.

### Silver

Use explicit scope flags and separate support tables where needed, especially for:

1. point-in-time legal state,
2. citation influence,
3. OECD cohort logic,
4. field contribution and heritage outputs.

### Gold

Expose current and historical outputs separately rather than blending them into one ambiguous score.

## Product Rule

The user experience should answer two different questions clearly:

1. `What is strategically active or threatening now?`
2. `What historically shaped this field?`

PatentIQ should not answer both with the same inclusion rules.

## Operational Recommendation

For MVP:

1. make `2007-2026` the main ETL window,
2. define `1996-2006` as the first heritage backfill target,
3. treat any expansion earlier than 1996 as a later evidence-based decision,
4. label heritage outputs explicitly when they use the backfill horizon.
