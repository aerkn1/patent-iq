# Quality Gates And Demo Readiness

## Quality Standard

For the contest, reliability matters more than breadth. A smaller feature set with strong caveats and reproducible outputs is better than a wider but fragile release.

## Required Test Layers

### Layer 1: Metric unit tests

1. Family aggregation,
2. citation adjustment,
3. grant-rate denominator logic,
4. cohort normalization,
5. score component assembly.

### Layer 2: Repository and service integration tests

1. Family drill-down,
2. assignee harmonization joins,
3. OECD family mapping,
4. trend matrix generation,
5. compare-workspace payloads.

### Layer 3: Critical API smoke tests

1. Single patent overview,
2. patent analysis,
3. portfolio overview,
4. portfolio analytics,
5. comparison endpoints,
6. export/report flow.

### Layer 4: Frontend smoke coverage

1. Patent page renders caveats correctly,
2. portfolio page renders family-first metrics,
3. comparison workspace handles missing data,
4. export/report path is reachable.

### Layer 5: ML validation coverage

1. Training split integrity and leakage checks,
2. feature completeness and drift checks,
3. ranking and error metrics by horizon,
4. calibration coverage overall and by subgroup,
5. explainability payload sanity checks.

## Mandatory Release Gates

### Gate A: Metric integrity

Pass conditions:
1. No known counting-unit ambiguity in contest-visible screens.
2. Raw and adjusted citation logic validated on fixtures.
3. OECD normalization validated on sample cohorts.

### Gate B: Product integrity

Pass conditions:
1. Critical workflows render successfully.
2. No major broken navigation or dead-end flows.
3. Fallback copy appears for partial-data scenarios.

### Gate C: Performance

Pass conditions:
1. Seeded demo paths are warmed and benchmarked.
2. Cold-cache performance is acceptable for rehearsal.
3. No request path uses avoidable full scans in hot flows.

### Gate D: Demo readiness

Pass conditions:
1. Primary demo script is rehearsed.
2. Backup screenshots and exports are available.
3. One degraded-mode fallback demo exists.

### Gate E: ML release readiness

Pass conditions:
1. Retrained 3-year and 5-year models beat or justify replacing the current baseline.
2. Calibration reaches target coverage overall and within defined subgroup tolerances.
3. Serving artifacts, metadata, and feature contracts are versioned and reproducible.
4. Rollback path to previous model version is documented.

## Demo Workflow Set

### Workflow 1: Single patent

Show:
1. Family summary,
2. adjusted citation impact,
3. quality context,
4. explainable forecast or trend signal.

### Workflow 2: Portfolio

Show:
1. Top families,
2. filing momentum,
3. grant mix,
4. concentration and technology spread.

### Workflow 3: Competitive intelligence

Show:
1. Company comparison,
2. assignee-to-family comparison,
3. cluster view by CPC/market,
4. exportable summary.

## Demo Failure Fallbacks

1. If live query is slow, switch to seeded saved state.
2. If one analytic layer fails, use exported backup artifact.
3. If clustering is unstable, demo comparison and trend workflows instead.
4. If the V2 model is not gate-ready, ship the stronger feature-table scaffolding but keep the previous forecast model behind a clearly labeled fallback.

## Final Release Checklist

1. Feature flags reviewed.
2. Smoke tests passed.
3. Benchmarks recorded.
4. Seed data loaded.
5. Exports generated.
6. Deck screenshots captured.
7. Final ML validation report approved.
8. Known issues documented with demo-safe mitigations.
