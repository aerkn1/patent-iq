# PatentIQ V2 Derived Metric Formula Alignment Audit

## Purpose

This note classifies the major derived metric families currently used across PatentIQ V2 as one of:

1. `aligned`
2. `acceptable proxy`
3. `needs rebuild`
4. `labeling-only issue`

The goal is to separate the metrics that are fundamentally mis-specified from the metrics that are mostly sound but need clearer naming, caveats, or future refinement.

This note builds on:

1. [63-patentiq-v2-ui-serving-silver-gold-boundary-audit.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/63-patentiq-v2-ui-serving-silver-gold-boundary-audit.md)
2. [65-patentiq-v2-blocking-power-rebuild-impact-matrix.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/65-patentiq-v2-blocking-power-rebuild-impact-matrix.md)
3. [66-patentiq-v2-blocking-power-current-state-audit.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/66-patentiq-v2-blocking-power-current-state-audit.md)

Audit date: `2026-04-10`

Important status note:

1. this audit describes the active on-disk marts and the formula family they currently expose in built artifacts,
2. on `2026-04-10`, the Gold builder code was patched to damp the citation pillar, gate pending families, and normalize current/historical blocking within primary-field cohorts,
3. the real Gold marts have not yet been fully rebuilt after that code change, so the artifact-level conclusions in this note still remain operationally relevant until the rebuild is executed.

---

## Executive Conclusion

The current formula landscape is mixed rather than uniformly wrong.

1. `blocking power` is the main metric family that is materially misaligned with the intended requirements.
2. `enforceability` is directionally correct but currently simplified and underpowered in the fallback branch path.
3. `citation lethality` is largely aligned with the intended design.
4. `OECD family metrics` are mostly aligned in the current build because the richer family-first longform artifact exists and is used.
5. many `portfolio` and `market` rollups are structurally acceptable but inherit the family blocking-power problem.
6. several executive-card metrics are not mathematically wrong, but they are mislabeled if presented as normalized scores instead of aggregates or indices.

---

## Rating Criteria

### `aligned`

The current code path matches the intended notes closely enough to be trusted as the active contract.

### `acceptable proxy`

The current implementation is semantically reasonable for MVP serving, but it is simplified, incomplete, or explicitly proxy-based relative to the intended note set.

### `needs rebuild`

The implementation is materially inconsistent with the intended semantics or is already proven to distort downstream product behavior.

### `labeling-only issue`

The underlying math is acceptable, but the metric is likely to mislead users if presented as a bounded or normalized score rather than as an aggregate or evidence-oriented measure.

---

## Family-Level Metric Audit

### 1. `family_adjusted_citation_score_raw`

Rating: `needs rebuild`

Current implementation:

1. `family_forward_citations_weighted / cohort_avg_forward_citations_weighted`
2. cohort anchor: `family_priority_year x primary_wipo_field`
3. fallback: if cohort average is zero, use weighted forward citations directly

Current code:

1. [build_enrichment.py:455](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/src/patentiq_etl/silver/build_enrichment.py#L455)

Why:

1. the formula is unstable for sparse recent cohorts,
2. it can explode when the denominator is tiny,
3. it currently feeds directly into blocking-power serving,
4. the pending-family audit already proves that this distortion is material at scale.

### 2. `family_market_threat_score_raw`

Rating: `acceptable proxy`

Current implementation:

1. simple family-level sum of `branch_enforceability_contribution_raw`

Current code:

1. [build_gold.py:856](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/src/patentiq_etl/gold/build_gold.py#L856)

Why:

1. the intended direction is correct: family-level aggregation of jurisdiction-aware branch contributions,
2. but the current branch path is a fallback simplification,
3. localized legal nuance, opposition-survival resilience, and richer branch-event semantics are still incomplete.

### 3. `family_overall_legal_enforceability_score`

Rating: `acceptable proxy`

Current implementation:

1. alias of the same summed branch contribution used for `family_market_threat_score_raw`

Current code:

1. [build_gold.py:856](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/src/patentiq_etl/gold/build_gold.py#L856)

Why:

1. this is acceptable as a current product-facing rollup,
2. but it is not yet a richer legal-state engine,
3. pending-phase behavior is weaker than intended in the notes.

### 4. `family_raw_absolute_blocking_power`

Rating: `needs rebuild`

Current implementation:

1. `(0.65 * family_market_threat_score_raw) + (0.35 * family_adjusted_citation_score_raw)`

Current code:

1. [build_gold.py:1049](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/src/patentiq_etl/gold/build_gold.py#L1049)

Why:

1. the fusion idea itself is valid,
2. but the citation component is unstable,
3. the intended breadth pillar is not explicitly included,
4. pending-stage gating is not enforced,
5. the weighting is explicit but not calibrated or metadata-exposed as intended by the notes.

### 5. `family_ui_blocking_power_score`

Rating: `needs rebuild`

Current implementation:

1. `percent_rank(raw_blocking_power) * 100`
2. applied across all main families in the current snapshot

Current code:

1. [build_gold.py:1056](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/src/patentiq_etl/gold/build_gold.py#L1056)

Why:

1. the notes call for peer-relative normalization after fusion,
2. but the current normalization is not constrained to a field/time cohort,
3. the current input distortion makes the final percentile misleading,
4. pending families can still surface as top blockers.

### 6. `family_blocking_power_score_asof`

Rating: `needs rebuild`

Current implementation:

1. the PIT layer looks up the latest blocking-timeseries snapshot at or before `as_of_year`

Current code:

1. [build_pit.py:196](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/src/patentiq_etl/silver/build_pit.py#L196)

Why:

1. this is only partially historical,
2. it depends on the already-problematic blocking-timeseries logic,
3. it does not fully satisfy the note’s stricter event-reconstruction ideal.

### 7. `family_enforceability_score_asof`

Rating: `acceptable proxy`

Current implementation:

1. the PIT layer looks up `overall_legal_enforceability_score` from the latest blocking-timeseries row at or before `as_of_year`

Current code:

1. [build_pit.py:196](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/src/patentiq_etl/silver/build_pit.py#L196)

Why:

1. the historical direction is reasonable,
2. but it still inherits the simplified family blocking-timeseries construction rather than a full event-native legal engine.

### 8. `citation_lethality_score`

Rating: `aligned`

Current implementation:

1. `clean_edge_weight * citing_stage_multiplier * citing_market_multiplier * clipped_trend_coefficient`

Current code:

1. [build_enrichment.py:273](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/src/patentiq_etl/silver/build_enrichment.py#L273)

Why:

1. self and intra-family edges are zeroed,
2. localized trend is preferred over global fallback,
3. the trend coefficient is clipped for stability,
4. the formula matches the intended lineage note well.

### 9. OECD family metrics

Metrics:

1. `family_generality_percentile`
2. `family_originality_percentile`
3. `family_radicalness_percentile`
4. `quality_index_4`
5. `quality_index_6`

Rating: `aligned` for the family-first normalized path, with an explicit proxy caveat on the composite variants

Current implementation:

1. Silver prefers the richer `oecd_indicator_longform.parquet` family-first longform artifact
2. cohort normalization is by `family_priority_year x primary_wipo_field`
3. `quality_index_4` and `quality_index_6` are explicit family-first composite variants with claims omitted and labeled in-schema

Current code:

1. [build_enrichment.py:34](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/src/patentiq_etl/silver/build_enrichment.py#L34)
2. [oecd_seed.py:80](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/src/patentiq_etl/prebronze/oecd_seed.py#L80)
3. [oecd_seed.py:488](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/src/patentiq_etl/prebronze/oecd_seed.py#L488)
4. [oecd_seed.py:609](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/src/patentiq_etl/prebronze/oecd_seed.py#L609)

Why:

1. the current build is family-first and collapse-first rather than patent-average-first,
2. the cohort normalization is explicit and note-consistent,
3. the composite variants are proxy composites, but they are explicitly labeled that way rather than silently pretending to be canonical OECD claims-inclusive metrics.

---

## Portfolio-Level Metric Audit

### 1. `portfolio_avg_blocking_power_within_mega_cluster`

Rating: `needs rebuild`

Current implementation:

1. average of `family_ui_blocking_power_score`

Current code:

1. [build_gold.py:1977](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/src/patentiq_etl/gold/build_gold.py#L1977)

Why:

1. it directly inherits the family blocking problem,
2. it also reflects the distortion of mean-based rollups for small portfolios.

### 2. `portfolio_hit_rate_top_decile`

Rating: `needs rebuild`

Current implementation:

1. average of `family_ui_blocking_power_score >= 90.0`

Current code:

1. [build_gold.py:1982](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/src/patentiq_etl/gold/build_gold.py#L1982)

Why:

1. the product intent is a cohort top-decile density view,
2. the current implementation is a simple threshold-on-current-score proxy,
3. because the underlying blocking score is misaligned, the hit-rate is also distorted.

### 3. `portfolio_crown_jewel_index`

Rating: `needs rebuild`

Current implementation:

1. sum of top-`N` family raw blocking scores

Current code:

1. [build_gold.py:1983](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/src/patentiq_etl/gold/build_gold.py#L1983)

Why:

1. the crown-jewel idea is aligned with the notes,
2. but its current input family scores are not yet trustworthy.

### 4. `portfolio_total_mass_score`

Rating: `acceptable proxy`

Current implementation:

1. sum of active families’ `family_raw_absolute_blocking_power`

Current code:

1. [build_gold.py:1981](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/src/patentiq_etl/gold/build_gold.py#L1981)

Why:

1. this is conceptually the intended total-mass axis,
2. but it still inherits the family blocking rebuild requirement,
3. it should not be presented as a normalized score.

### 5. `portfolio_current_threat_score`

Rating: `labeling-only issue`

Current implementation:

1. sum of active families’ `family_market_threat_score_raw`

Current code:

1. [build_gold.py:1991](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/src/patentiq_etl/gold/build_gold.py#L1991)

Why:

1. the metric is a valid aggregate mass/index,
2. it is not bounded,
3. it becomes misleading only when surfaced as if it were a 0-100 score.

### 6. `portfolio_heritage_score`

Rating: `labeling-only issue`

Current implementation:

1. sum of `family_adjusted_citation_score_raw`

Current code:

1. [build_gold.py:1992](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/src/patentiq_etl/gold/build_gold.py#L1992)

Why:

1. it is an aggregate mass measure rather than a normalized score,
2. it should be framed as citation heritage mass or similar,
3. its main issue in product is naming, not the fact that sums are inherently invalid.

### 7. `portfolio_opposition_rate`

Rating: `acceptable proxy`

Current implementation:

1. share of granted families with any opposed branch

Current code:

1. [build_gold.py:1984](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/src/patentiq_etl/gold/build_gold.py#L1984)

Why:

1. this is a simple and reasonable MVP proxy,
2. it is not the same as a richer jurisdiction-weighted opposition-friction model.

### 8. Portfolio OECD-style rollups

Rating: `needs rebuild or redesign when exposed as default summary`

Why:

1. the notes prefer density or hit-rate framing over mean OECD score,
2. portfolio OECD views should emphasize top-decile family shares rather than plain averages,
3. if average OECD composites are surfaced as default portfolio truth, that would be misaligned with the notes.

---

## Market-Level Metric Audit

### 1. `segment_blocking_density_asof`

Rating: `acceptable proxy`

Why:

1. the aggregation idea is fine,
2. but it depends on family blocking logic that still needs rebuild,
3. so it is directionally useful but not yet a fully validated end-state metric.

### 2. `segment_enforceability_density_asof`

Rating: `acceptable proxy`

Why:

1. it is a reasonable density rollup of current enforceability,
2. but it still inherits the simplified family legal foundation.

### 3. `cpc_blocking_density_asof`

Rating: `needs rebuild`

Why:

1. it directly inherits the family blocking foundation,
2. it is already marked in the rebuild matrix and should stay there.

### 4. `cpc_enforceability_density_asof`

Rating: `acceptable proxy`

Why:

1. it is a semantically sensible rollup,
2. but it still belongs in the dependent rebuild chain because the upstream family legal logic is being corrected.

### 5. Market citation heat, pressure, and attacker marts

Rating: `aligned`

Why:

1. these marts are evidence-first or aggregate `citation_lethality_score`,
2. they do not depend on the blocking-power formula,
3. the structural audit already confirmed they are not contaminated by blocking/enforceability/heritage-serving fields.

---

## Filing And Publication Metrics

### Publication/Filing evidence metrics

Examples:

1. citation ledgers
2. assignee/jurisdiction evidence tables
3. raw publication-stage legal or kind-code evidence

Rating: `aligned`

Why:

1. these are mostly evidence-first surfaces,
2. they are not trying to masquerade as strategic fused scores,
3. their main responsibility is transparency rather than normalized ranking.

### Publication/Filing strategic score layers

Rating: `not yet in scope as a sealed serving contract`

Why:

1. the current platform does not yet define a mature publication-level blocking or quality score family that should be trusted as a primary strategic score,
2. publication-serving should remain evidence-first unless a dedicated serving contract is introduced.

---

## Consolidated Status Table

| Metric family | Status | Main issue |
|---|---|---|
| Family blocking power | `needs rebuild` | fusion input distortion, weak pending gating, incomplete cohort normalization |
| Family enforceability | `acceptable proxy` | simplified fallback branch logic |
| Citation lethality | `aligned` | no major semantic issue found |
| OECD family metrics | `aligned` | composite variants are explicit proxies, but correctly labeled |
| Portfolio blocking rollups | `needs rebuild` | inherit family blocking distortion |
| Portfolio threat / heritage aggregates | `labeling-only issue` | valid aggregates, misleading if shown as normalized scores |
| Portfolio opposition rate | `acceptable proxy` | simple MVP rate, not full friction model |
| Market blocking densities | `acceptable proxy` or `needs rebuild` depending on field | inherit family blocking/enforceability foundation |
| Market citation marts | `aligned` | evidence-first and structurally clean |
| Filing/publication evidence views | `aligned` | evidence-first by design |

---

## Practical Implications

### Safe To Keep Serving

1. citation lethality and attacker views,
2. family-first OECD metrics,
3. filing/publication evidence-first views,
4. citation evidence and chronology marts,
5. market citation pressure and attacker marts.

### Keep But Relabel

1. `portfolio_current_threat_score`
2. `portfolio_heritage_score`
3. other unbounded mass/index cards that are valid aggregates but not normalized score surfaces

### Rebuild Before Trusting As Strategic Score

1. `family_ui_blocking_power_score`
2. `family_blocking_power_score_asof`
3. `portfolio_avg_blocking_power_within_mega_cluster`
4. `portfolio_hit_rate_top_decile`
5. `portfolio_crown_jewel_index`
6. blocking-density-based market ranking marts

---

## Recommended Next Action

The next implementation step should still be:

1. fix the family blocking-power contract,
2. rebuild the dependent family, portfolio, market, and ranking marts from [65-patentiq-v2-blocking-power-rebuild-impact-matrix.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/65-patentiq-v2-blocking-power-rebuild-impact-matrix.md),
3. keep the aligned citation and OECD surfaces in service,
4. keep labeling caveats in backend/UI for aggregate mass metrics until the rebuild is complete.
