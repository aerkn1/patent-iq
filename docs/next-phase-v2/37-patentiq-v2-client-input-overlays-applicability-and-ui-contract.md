# PatentIQ V2 Client Input Overlays Applicability And UI Contract

## Purpose

Define which user-provided or client-provided inputs are actually applicable with the current PatentIQ V2 data platform, how those inputs should flow through the product, what outputs they can legitimately produce, and how the UI contracts should represent them.

This note is a `current-state applicability guide`, not a speculative finance roadmap.

It reconciles:

1. the current Silver/Gold data actually available,
2. the optional overlay logic described in [client-provided-data-financial-intelligence-requirements.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/new-feature-ideas/client-provided-data-financial-intelligence-requirements.md),
3. the current UI contract pack under [ui-contracts](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/ui-contracts),
4. the shift away from presenting unsupported hard financial valuation as if it were already natively available.

---

## 1. Core Position

PatentIQ V2 should treat client/user inputs as:

1. optional overlays,
2. family-first joins,
3. aggregation-first,
4. scenario-aware,
5. clearly labeled as client-enriched.

PatentIQ should `not` currently present:

1. direct monetary patent valuation,
2. damages estimates,
3. licensing deal value estimates,
4. hard finance-grade asset prices,

as core outputs derived from public patent data alone.

What is supportable now:

1. `value context`,
2. `revenue exposure overlays`,
3. `maintenance / pruning scenarios`,
4. `R&D efficiency overlays`,
5. `product-family business mapping`,
6. scenario-driven strategic dashboards.

---

## 2. Data Foundation That Already Exists

These current marts make client-input overlays possible.

### Family And Legal Core

1. [gold_family_summary.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_summary.parquet)
2. [silver_family_status_pt.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_status_pt.parquet)
3. [silver_family_status_history.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_status_history.parquet)
4. [silver_branch_status_history_dense.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_branch_status_history_dense.parquet)

### Blocking / Strategic Strength

1. [gold_family_blocking_power.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_blocking_power.parquet)
2. [gold_family_blocking_power_timeseries.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_blocking_power_timeseries.parquet)
3. [gold_family_heritage_summary.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_heritage_summary.parquet)
4. [gold_family_attacker_summary.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_attacker_summary.parquet)

### Coverage / Field / Market

1. [silver_family_coverage_metrics.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_coverage_metrics.parquet)
2. [silver_family_wipo_fields.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_wipo_fields.parquet)
3. [gold_family_field_contributions_timeseries.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_field_contributions_timeseries.parquet)
4. [gold_market_intelligence_overview.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_market_intelligence_overview.parquet)
5. [gold_market_intelligence_segments.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_market_intelligence_segments.parquet)
6. [gold_market_intelligence_timeseries.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_market_intelligence_timeseries.parquet)

### Portfolio / Owner

1. [silver_family_owner_bridge.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_owner_bridge.parquet)
2. [silver_assignee_harmonized.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_assignee_harmonized.parquet)
3. [gold_portfolio_summary.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_summary.parquet)
4. [gold_portfolio_threat_matrix.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_threat_matrix.parquet)
5. [gold_portfolio_forecast_summary.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_forecast_summary.parquet)

### Forecast And Quality

1. [silver_family_oecd_quality.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_oecd_quality.parquet)
2. [silver_family_citation_metrics.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_citation_metrics.parquet)
3. [silver_enriched_citation_network.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_enriched_citation_network.parquet)
4. future Phase 03/04/05 model outputs once promoted

These are enough to support `client-enriched business overlays`, but not enough to claim standalone hard financial valuation.

---

## 3. Applicability Matrix

## 3.1 Fully Applicable Now

These options are well supported by the current data platform.

1. `Product-to-family mapping`
2. `Revenue-at-risk overlay`
3. `Portfolio pruning ROI scenario`
4. `R&D spend efficiency overlay`
5. `Manual strategic threshold controls`

## 3.2 Partially Applicable

These are usable only with explicit caveats.

1. peer benchmark assumptions,
2. licensing / monetization proxy overlays,
3. commercial value proxy cards.

## 3.3 Not Ready As Core Outputs

These should not be treated as current-native product features.

1. direct monetary patent valuation,
2. deal-value estimation,
3. damages modeling,
4. DCF/NPV-style outputs,
5. broad licensing-value ranges from public data alone.

---

## 4. Supported Overlay Option 1: Product-To-Family Mapping

## Purpose

Map business products or product lines to the patent families that protect them.

This is the anchor overlay that makes the other business-facing workflows useful.

## Required Inputs

Recommended minimum schema:

1. `product_sku`
2. `product_name`
3. `linked_docdb_family_ids`

Optional but strongly useful:

1. `product_line`
2. `region`
3. `annual_revenue_usd`
4. `business_unit`
5. `product_status`

Recommended CSV example:

```csv
product_sku,product_name,product_line,annual_revenue_usd,linked_docdb_family_ids
SKU-101,Advanced Sensor Module,Sensors,2400000,"12345678|23456789|34567890"
SKU-201,Autonomous Vision Stack,Vision,7800000,"45678901|56789012"
```

## Validation Rules

1. `linked_docdb_family_ids` must resolve to valid families in current PatentIQ scope,
2. revenue fields must be numeric if provided,
3. orphan family ids must be flagged,
4. duplicates in `(product_sku, family_id)` should be deduped before downstream use,
5. products with no resolved family links must appear in an exceptions table.

## Processing Flow

1. user uploads CSV,
2. ingestion layer expands the family-id list,
3. each family is joined to:
   - `gold_family_summary`,
   - `gold_family_blocking_power`,
   - `silver_family_status_pt`,
   - `silver_family_status_history` when timeline views are needed,
4. overlay outputs are materialized in a client-enriched layer or kept client-local,
5. product-level rollups are generated from family-level signals.

## Outputs

1. product -> protected family table,
2. product protection summary,
3. count of linked active families,
4. count of weak / expired / uncovered linked families,
5. product-level evidence cards,
6. optional product risk score.

## UI Contract

Best UI surfaces:

1. executive/product dashboard,
2. family detail side panel as “linked products”,
3. portfolio page business overlay mode,
4. data room dataset card.

Best components:

1. `ProductProtectionTable`
2. `LinkedFamiliesHealthBar`
3. `ProductRiskChipSet`
4. `ClientDataProvenanceBadge`

Rules:

1. all product-linked outputs must be visibly labeled `Client-Enriched`,
2. products with unresolved family links must show warning badges,
3. no business overlay should appear in base patent views unless the client enrichment is active.

---

## 5. Supported Overlay Option 2: Revenue At Risk

## Purpose

Estimate how much client-provided product revenue is exposed when linked families weaken, lapse, narrow in coverage, or approach expiration.

This is a `scenario overlay`, not a fact table of real financial loss.

## Required Inputs

Required:

1. `product_sku`
2. `product_name`
3. `annual_revenue_usd`
4. `linked_docdb_family_ids`

Optional:

1. `revenue_region`
2. `product_line`
3. `revenue_year`
4. `importance_weight`

## Public Inputs Used

1. [gold_family_blocking_power.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_blocking_power.parquet)
2. [gold_family_blocking_power_timeseries.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_blocking_power_timeseries.parquet)
3. [silver_family_status_pt.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_status_pt.parquet)
4. [silver_family_status_history.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_status_history.parquet)
5. [silver_family_coverage_metrics.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_coverage_metrics.parquet)
6. [gold_family_summary.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_summary.parquet)

## Flow

1. resolve linked families,
2. compute family legal durability / current protection state,
3. combine:
   - current legal state,
   - blocking power,
   - coverage breadth,
   - time-to-expiry or weakening signal,
4. generate product-level revenue exposure bands,
5. aggregate to portfolio / business unit if needed.

## Output Types

1. `current revenue protected`
2. `revenue in weakly defended zone`
3. `revenue at upcoming risk`
4. `family cliffs affecting revenue`
5. `product-level exposure timeline`

## Output Caveats

1. this is not an accounting metric,
2. this is not legal advice,
3. it depends on client linkage quality,
4. it must be explicitly labeled as a scenario/proxy result.

## UI Contract

Best surfaces:

1. product dashboard,
2. executive dashboard,
3. portfolio page in client-enriched mode,
4. compare workspace for `current vs future exposure`.

Best components:

1. `RevenueCliffTimeline`
2. `RevenueExposureHeatTable`
3. `ProductExposureList`
4. `AtRiskLinkedFamiliesDrawer`
5. `ScenarioAssumptionPanel`

Rules:

1. the chart title must include `Client-Enriched` or `Scenario`,
2. protected vs exposed revenue must be paired with linked family counts,
3. every revenue chart must show the assumptions used,
4. time-based views may compare `current vs selected future year`.

---

## 6. Supported Overlay Option 3: Portfolio Pruning ROI Scenario

## Purpose

Help the client estimate savings if strategically weak families were pruned under explicit scenario thresholds.

This is a scenario-planning tool, not a recommendation engine pretending to know actual maintenance invoices.

## Required Inputs

Minimum:

1. `estimated_annual_maintenance_cost_per_active_family`

Optional:

1. `country_specific_cost_table`
2. `pruning_percentile_threshold`
3. `minimum_blocking_power`
4. `require_zero_citation_flag`
5. `exclude_crown_jewels_flag`

## Public Inputs Used

1. [gold_family_blocking_power.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_blocking_power.parquet)
2. [gold_family_heritage_summary.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_heritage_summary.parquet)
3. [silver_family_status_pt.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_status_pt.parquet)
4. [silver_family_citation_metrics.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_citation_metrics.parquet)
5. [silver_family_coverage_metrics.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_coverage_metrics.parquet)
6. [gold_portfolio_summary.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_summary.parquet)

## Flow

1. identify active families,
2. compute candidate set using selected thresholds,
3. estimate annual savings from the client assumption,
4. present prune candidates with evidence, not just one score,
5. allow export of affected families.

## Outputs

1. prune-zone family list,
2. estimated annual savings,
3. savings by field / owner / status group,
4. strategic-risk warnings where pruning would hit strong families,
5. exportable action list.

## UI Contract

Best surfaces:

1. portfolio page,
2. dedicated portfolio action planner,
3. executive scenario dashboard.

Best components:

1. `PruneZoneTable`
2. `SavingsScenarioCard`
3. `ThresholdControlPanel`
4. `WhyInPruneZonePopover`
5. `ExportActionListButton`

Rules:

1. savings must be labeled as estimated scenario savings,
2. each candidate family must expose the factors that put it into the prune zone,
3. crown-jewel or high-blocking families must produce warning banners if selected for pruning.

---

## 7. Supported Overlay Option 4: R&D Spend Efficiency

## Purpose

Compare client-provided R&D spend against family-first strategic outputs by field and year.

## Required Inputs

Minimum schema:

1. `year`
2. `wipo_field`
3. `spend_amount`

Optional:

1. `business_unit`
2. `region`
3. `currency`
4. `benchmark_group`

## Public Inputs Used

1. [silver_family_wipo_fields.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_wipo_fields.parquet)
2. [gold_family_field_contributions_timeseries.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_field_contributions_timeseries.parquet)
3. [gold_market_intelligence_timeseries.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_market_intelligence_timeseries.parquet)
4. [gold_family_summary.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_summary.parquet)
5. [silver_family_oecd_quality.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_oecd_quality.parquet)

## Flow

1. validate WIPO field labels,
2. join field/year spend to family and market outputs,
3. compute efficiency indicators such as:
   - spend per elite family,
   - spend per high-quality family,
   - spend per active strategic family,
4. compare current year against historical years and optional benchmark inputs,
5. surface conversion efficiency rather than a fake ROI number.

## Outputs

1. `cost per crown-jewel family`
2. `cost per top-decile quality family`
3. `field-year efficiency grid`
4. `efficiency trend over time`
5. benchmark-relative view if benchmark input exists

## UI Contract

Best surfaces:

1. strategy dashboard,
2. market intelligence page in client-enriched mode,
3. compare workspace for `field-year vs field-year`,
4. data room model/methodology card.

Best components:

1. `FieldEfficiencyMatrix`
2. `SpendVsEliteOutputChart`
3. `EfficiencyTrendLines`
4. `BenchmarkDeltaCards`
5. `AssumptionAndCoverageBanner`

Rules:

1. field labels must map to PatentIQ taxonomy,
2. all spend-derived metrics must be labeled as client-enriched,
3. values should be comparable across years only when taxonomy alignment is complete.

---

## 8. Supported Overlay Option 5: Manual Threshold And Scenario Controls

## Purpose

Allow the user to tune overlays without requiring additional dataset uploads.

## Inputs

Examples:

1. blocking-power cutoff
2. forecast percentile cutoff
3. prune threshold
4. risk horizon
5. concentration tolerance
6. year selector for compare mode

## Public Inputs Used

These operate on top of existing Gold/Silver outputs and current model outputs.

## Outputs

1. filtered entity lists,
2. scenario cards,
3. “if threshold changed” deltas,
4. compare overlays.

## UI Contract

Best surfaces:

1. compare workspace,
2. portfolio and forecast pages,
3. market intelligence filters,
4. semantic workspace weighting controls later.

Best components:

1. `ScenarioControlsDrawer`
2. `ThresholdChipGroup`
3. `DeltaFromBaselineCard`
4. `SavedScenarioPresetSelector`

---

## 9. Partially Applicable Options

## 9.1 Peer Benchmark Assumptions

Possible input:

1. benchmark spend values,
2. anonymized peer group assumptions,
3. peer segment labels.

Status:

1. partially applicable,
2. must be clearly labeled as client-supplied or heuristic,
3. should not be treated as a public-data-native benchmark.

## 9.2 Licensing / Monetization Proxy Overlays

What exists now:

1. EP registered license flags,
2. legal/register overlays,
3. blocking power,
4. strategic strength and citation context.

What does not exist as a strong engine:

1. reliable licensee-matching runtime,
2. observed deal value data,
3. robust licensing-value estimation.

So the allowed output is:

1. `licensing relevance proxy`,
2. `commercial readiness proxy`,
3. `registered-license evidence badge`,

but not:

1. hard licensing value range.

---

## 10. Unsupported As Current Core Outputs

These should not be represented as current-native product capabilities.

1. direct patent monetary valuation,
2. DCF or NPV-style asset outputs,
3. damages estimation,
4. royalty forecast,
5. broad deal-value estimation.

If these appear in legacy notes or diagrams, they should be interpreted as:

1. historical product ambition,
2. optional future client-enriched module,
3. not current-core V2 functionality.

---

## 11. Recommended Processing Architecture

## 11.1 Preferred Security Pattern

The safest pattern remains:

1. backend computes public patent metrics,
2. client uploads optional business CSVs,
3. join happens locally when feasible,
4. results are shown as client-enriched overlays.

This aligns with the earlier requirement note recommending browser-local or client-local joining for sensitive inputs.

## 11.2 Practical V2 Deployment Pattern

For the first remote V2 deployment:

1. public patent metrics remain server-hosted,
2. optional client inputs may be:
   - browser-local,
   - or uploaded to a client-specific workspace if needed later,
3. overlay outputs should preserve provenance:
   - input file name,
   - upload date,
   - assumptions used,
   - active Gold/model release.

---

## 12. UI Contract Rules Across The Product

These rules apply to every client-enriched workflow.

## 12.1 Labeling Rules

Every enriched component must show:

1. `Client-Enriched`
2. `Scenario`
3. or equivalent overlay badge

Never let a client-enriched chart look identical to a public-data-native chart.

## 12.2 Provenance Rules

Each overlay view should expose:

1. which public metrics were used,
2. which client inputs were used,
3. date of computation,
4. active assumptions,
5. coverage or missing-link caveats.

## 12.3 Caveat Rules

Must disclose:

1. unresolved family mappings,
2. missing revenue rows,
3. unsupported years or fields,
4. client-side assumption sensitivity,
5. sampled semantic coverage if semantic overlays later participate.

## 12.4 Compare Rules

For compare or time-slice UI:

1. client-enriched compare can use the same time-slice compare pattern defined in the V2 UI contracts,
2. compare radar is allowed only for normalized compare metrics,
3. exact values and deltas must appear next to the radar,
4. current-only public metrics must not be back-projected into history.

---

## 13. Page-Level UI Contract Implications

## 13.1 Family Page

Allowed client-enriched additions:

1. linked products panel,
2. business exposure badge,
3. client-linked risk notes,
4. optional “protected revenue context” card.

Should not appear as core family summary fields by default.

## 13.2 Publication Page

Use sparingly.

Allowed:

1. “linked business context” side note if the publication belongs to a client-linked family.

Not recommended:

1. publication-level revenue or ROI components.

## 13.3 Portfolio Page

This is the strongest client-enriched surface.

Addable modules:

1. `RevenueAtRiskPanel`
2. `PruningScenarioPanel`
3. `TopExposedProductsTable`
4. `ClientEnrichedForecastOverlay`

## 13.4 Market Intelligence Page

Allowed:

1. R&D efficiency overlays by field and year,
2. benchmark overlays,
3. field-spend vs output conversion panels.

Not allowed:

1. unsupported hard value claims for segments.

## 13.5 Compare Workspace

Best place for:

1. `portfolio current vs projected`
2. `portfolio year A vs year B`
3. `product exposure before vs after scenario threshold`
4. `field efficiency across years`

This workspace should carry most of the radar-based client-enriched comparison logic.

## 13.6 Data Room

Must include:

1. dataset cards for uploaded client files,
2. schema preview,
3. validation results,
4. provenance cards,
5. scenario-method explanation blocks,
6. export lineage.

---

## 14. Backend Contract Implications

Client-enriched overlays should not be bolted into legacy endpoints silently.

Recommended V2 backend behavior:

1. public endpoint returns public metrics only,
2. client-enriched endpoint returns:
   - public metrics,
   - overlay outputs,
   - provenance block,
   - caveats block,
3. data-room endpoints expose uploaded/validated client datasets separately.

Recommended V2 endpoint families:

1. `/api/v2/client-overlays/products`
2. `/api/v2/client-overlays/revenue-risk`
3. `/api/v2/client-overlays/pruning`
4. `/api/v2/client-overlays/rd-efficiency`
5. `/api/v2/data-room/client-datasets`

---

## 15. Recommended V2 Priority

Implement in this order:

1. `Product-to-family mapping`
2. `Revenue-at-risk`
3. `Pruning ROI`
4. `R&D efficiency`
5. optional benchmark overlays

Why:

1. product mapping is the anchor join,
2. revenue-at-risk is the most intuitive business story,
3. pruning ROI uses already strong strategic signals,
4. R&D efficiency becomes stronger once field and forecast work continue maturing.

---

## 16. Final Recommendation

The current PatentIQ V2 platform can already support a strong `client-enriched business overlay layer`, but only if the product is disciplined about what is:

1. public-data-native,
2. client-enriched,
3. proxy-only,
4. not yet supported.

The best current overlays are:

1. product-to-family mapping,
2. revenue-at-risk,
3. pruning ROI,
4. R&D efficiency,
5. scenario controls.

These should be implemented as:

1. optional,
2. family-first,
3. caveated,
4. provenance-rich,
5. clearly separated from the base patent-intelligence engine.

That preserves analytical honesty while still making the platform much more valuable for real client workflows.
