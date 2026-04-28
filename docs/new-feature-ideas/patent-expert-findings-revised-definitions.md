# Patent Expert Findings: Revised Product Definitions (Current PatentIQ Baseline)

## Scope
This document refines your findings into implementation-ready definitions based on the current PatentIQ codebase (portfolio tabs, analytics, citations, family metrics, discovery, and forecast modules).

## Current Baseline (Observed)
1. Portfolio page currently has `Overview`, `Patents`, `Licensing`, `Analysis`, `Forecast`.
2. Citation totals/distributions are mostly application-level aggregates.
3. Family metrics exist (size, jurisdiction reach, grant coverage), but family-level citation ranking is not exposed.
4. Blocking power already includes multiple drivers (`forward_impact`, `family_breadth`, `tech_penalty`, `self_blocking`), but weighting is not citation-first by definition.
5. Peer positioning exists; side-by-side company/patent comparison does not.

## Mandatory Analytics Principles (Apply Across All New Features)
1. **Family-first aggregation**: portfolio analytics must provide family-level metrics as default view; publication-level remains drill-down.
2. **Family size as value proxy**: larger family size (jurisdiction spread) is a positive commercial-intent signal and must be explicitly represented in valuation context.
3. **Priority date for trend analysis**: any filing/trend chart must use family priority date (`earliest_priority_date`) as canonical event date, not publication date.
4. **Intra-family self-citation exclusion**: citations between members of the same family must be excluded from innovation-impact hit counts.
5. **Self-citation transparency**: expose both raw citations and adjusted citations (after self/intra-family exclusion).

## Revised Definitions

### R-01 (Refine Existing): Remove Licensing Tab from Product Navigation
Definition: Deprecate the `Licensing` tab in portfolio UI. Keep backend endpoint temporarily for compatibility, but remove user-facing entry point and card copy referencing licensing workflows.

### R-02 (Refine Existing): Family-Aware Citation Distribution
Definition: Forward/backward citation distributions must be computed at patent family level (DocDB family aggregation) in addition to raw application level, with family view as default.

### R-03 (Refine Existing): Family-Aware Early Citation Signals
Definition: Early/mid/late and early-signal indicators must include citations received by any member of the same family, not only the selected EP/application record.

### R-04 (Refine Existing): Blocking Power Definition Update
Definition: Blocking power should be citation-led: family-normalized forward impact is the primary driver; legal/family breadth remain supporting drivers.

### R-05 (New Feature): Most-Cited Families Ranking
Definition: Add portfolio view showing top cited patent families (not single publications), with links to all family members and owners.

### R-06 (Refine Existing): Pending/Application Indicators
Definition: For companies, use count/share of `PENDING` applications as a momentum indicator, not direct value score.

### R-07 (New Feature): Pending-but-Cited Signal
Definition: Flag pending applications whose family already receives meaningful citations as high-potential emerging assets.

### R-08 (New Feature): Company Comparison Workspace
Definition: Add side-by-side portfolio comparison (at least 2 companies) across patent count, family citations, innovation/novelty proxy, legal strength, and filing momentum.

### R-09 (Refine Existing): CPC Peer Exploration
Definition: Extend current CPC discovery into “peer actions by CPC” view showing top competing assignees and their trend direction in selected CPC domains.

### R-10 (New Feature): Patent-vs-Patent Compare
Definition: Add direct comparison for two patents/families across citation trajectory, family breadth, legal events, and CPC overlap.

### R-11 (New Feature): CPC Trend Analytics
Definition: Add time-series for CPC share evolution, including “share of granted patents by CPC over time.”

### R-12 (Refine Existing): Forward/Backward Citation Terminology
Definition: Distinguish clearly:
1. `Unique citing records` (lower valuation weight).
2. `Total citation events to family members` (higher valuation weight; primary impact metric).

### R-13 (New Feature): Ranked Citing Applicants
Definition: Provide ranked list of applicants citing a patent family, and portfolio-level rollup of top external citing applicants.

### R-14 (Refine Existing): Family Citation Evolution
Definition: Portfolio citation evolution should include cumulative citations to portfolio family members (not only per-application aggregation).

### R-15 (New Feature): Large Family Strength Indicator
Definition: Add metric: proportion of portfolio families with `>10` members.

### R-16 (New Feature): Opposition Resilience Indicator
Definition: Add metric: proportion of granted patents that faced opposition and remained active/granted (resilience signal).

### R-17 (New Feature): Application vs Granted Mix
Definition: Add portfolio stage mix: counts and trend of `PENDING` applications vs `GRANTED` patents.

### R-18 (New Feature): Filing Momentum Trend
Definition: Add yearly filing count trend as a core strategic-strength indicator.

### R-19 (Refine Existing): Family Size Value Signal
Definition: Add explicit value-context metric for family size and jurisdictional spread, with interpretation bands (`narrow`, `moderate`, `broad`) to support valuation narratives.

### R-20 (Refine Existing): Priority-Date Trend Backbone
Definition: Rebuild all trend analytics (filings, CPC trend, citation cohort baselines) on family earliest priority date.

### R-21 (Refine Existing): Intra-Family Citation De-duplication
Definition: Exclude citations where citing and cited applications resolve to the same family from innovation impact, influence rank, and blocking-impact hit counters.

### R-22 (New Feature): Family-Level Analytics Mode
Definition: Add global analytics mode switch (`family default` / `publication detail`) so investigation and ranking workflows start at family level.

### R-23 (New Feature): Tech-Level Patent Family Ranking
Definition: Rank patent families within each technology cluster/CPC domain using a composite score from adjusted forward impact, family breadth/jurisdiction strength, legal durability, and recency/trajectory.

## Priority Proposal
1. **P0**: R-01, R-02, R-03, R-04, R-12, R-14, R-20, R-21
2. **P1**: R-05, R-06, R-07, R-11, R-17, R-18, R-19, R-22, R-23
3. **P2**: R-08, R-09, R-10, R-13, R-15, R-16

## Linked Specs
- data-analytics-powerups-and-nuances-requirements.md

## Additional Ideas Mapping (March 6, 2026)

### A-01: Market Trends
Status: **Partially covered** (`R-11`, `R-18`, `R-20`).

Refined definition: Add macro-level market trend dashboard combining:
1. Family-priority-based filing momentum,
2. Family-level citation momentum,
3. CPC/industry share shifts over time.

### A-02: Tech-Level Based Patent Family Ranking
Status: **Covered by `R-23`**.

Refined definition: Rank patent families within each technology cluster/CPC domain using a composite score:
1. Adjusted forward impact (self/intra-family scrubbed),
2. Family breadth/jurisdiction strength,
3. Legal durability (status + renewals),
4. Recency/trajectory signal.

### A-03: Patent Filing Trends by Year (Family-Based Timeline)
Status: **Already covered** (`R-18`, `R-20`).

Clarification: Timeline must be computed by **earliest family priority year**; publication-year charts are secondary diagnostic views only.

### A-04: Tech + Market Trend Analytics (Filing/Granting Rates)
Status: **Partially covered** (`R-11`, `R-17`, `R-18`, `R-20`).

Refined definition: Add a dedicated trend layer by technology (CPC/tech field) and market (jurisdiction/region) showing:
1. Total filings over time (family-priority-year based),
2. Total grants over time,
3. Granting rate (`granted_families / filed_families`) with pendency-adjusted cutoff policy.

Implementation caution:
1. Use family-level counting by default (`docdb_family_id`).
2. Apply 18-month publication-lag disclaimers for recent filing cohorts.
3. Apply exam-pendency caveats for recent grant-rate cohorts.

## OECD Quality Mapping Addendum (March 6, 2026)

### OMAP-01: Citation-Led Features
Map `R-02`, `R-03`, `R-04`, `R-05`, `R-13`, `R-14` to OECD forward-citation indicators:
1. `fwd_cits5`, `fwd_cits7` as baseline impact windows,
2. `breakthrough` as top-impact family/patent signal,
3. EPO-specific `fwd_cits*_xy` as optional stricter relevance mode.

### OMAP-02: Strength and Value Context Features
Map `R-15`, `R-19`, `R-23` to:
1. `family_size` (breadth/value-intent proxy),
2. `patent_scope`, `claims`, `generality`, `originality`, `radicalness`,
3. `quality_index_4`/`quality_index_6` as composite rank features (explainable only).

### OMAP-03: Timeline and Maturity Features
Map `R-17`, `R-18`, `R-20` to:
1. `filing` (cohort year, not publication trend substitute),
2. `grant_lag` (speed/maturity context),
3. `renewal` (granted-life persistence; combine with legal status events).

### OMAP-04: Mandatory Cautions for Product Use
1. OECD metrics are published at application level; convert to family-level aggregates before default portfolio analytics.
2. Do not compare raw values across different `(filing year, tech_field)` cohorts.
3. Recent years are incomplete for forward-citation and grant-lag dependent metrics.
4. `many_field=1` implies category overlap; chart totals can exceed unique patent totals.
