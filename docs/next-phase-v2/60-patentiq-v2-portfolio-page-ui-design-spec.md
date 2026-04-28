# PatentIQ V2 Portfolio Page UI Design Specification

## Purpose

Define the concrete Portfolio V2 page implementation before backend endpoint binding, with explicit component hierarchy, library stack, animation behavior, and shape system. This is the visual and interaction contract that frontend implementation and backend V2 section responses will target.

## Scope

- Owner-scoped portfolio page as the first visible V2 product slice.
- Must use canonical portfolio prediction artifacts and expose coverage/probability caveats prominently.
- Aligns with:
  - [33-patentiq-v2-portfolio-and-forecast-page-contract.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/ui-contracts/33-patentiq-v2-portfolio-and-forecast-page-contract.md)
  - [53-patentiq-v2-portfolio-derived-prediction-layer-implementation-and-serving-contract.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/53-patentiq-v2-portfolio-derived-prediction-layer-implementation-and-serving-contract.md)
  - [61-patentiq-v2-portfolio-current-state-audit-and-remediation-plan.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/61-patentiq-v2-portfolio-current-state-audit-and-remediation-plan.md)

## Visual language and theme

- Keep the V2 glass/surface layout approach, but inherit the core token and typography direction from `frontend_v1`.
- Theme inheritance:
  - `Geist` for UI sans
  - `Geist Mono` for ids / numeric technical labels
  - `Lora` for serif headline / metric emphasis
  - V1 red / white / gray palette as the base token system
- Add a controlled premium feel without replacing the base theme:
  - soft glass cards
  - restrained depth via shadows and borders
  - editorial spacing and strong section separations
- Layout language:
  - bento grid for cards on desktop
  - list-first progressive layout on mobile

## Page-level shape system

Desktop layout (12-column rhythm):

1. `PortfolioHeroBand` (full-width)
2. `PortfolioPrimaryTabs`
3. active tab canvas only
4. within `Citations`, render chronology and attacker sub-views
5. within `Field Clusters`, render a secondary dynamic chip rail for top WIPO fields
6. within `Forecast`, render horizon switchers and risk sub-views
7. within `Compare`, render compare-specific normalized components only

Mobile shape order:

1. Hero band
2. Executive cards
3. Mini reliability rail
4. Primary tabs: Executive / Families / Citations / Field Clusters / Threats / Forecast / Classification / Compare
5. Secondary cluster chips under `Field Clusters`
6. Expandable drawers only for dense sub-panels inside a tab

## Audit correction for current state

The current portfolio product must reflect the actual state of the marts:

1. `Field Clusters` is a current exposure and current overlay tab,
2. `Classification` is the historical WIPO/CPC chronology tab,
3. `Compare` is the normalized historical portfolio-shape tab,
4. `market context` should be labeled as `Current Market Overlay`,
5. `field-timeseries` should not be styled or described as a true multi-snapshot chronology source until the mart is rebuilt as such.

## Component map

### Page shell

- `PortfolioPageShell`
  - title
  - owner name input
  - scope chips
  - year selector
  - data freshness chips
  - export action

### 1) Header strip

- `PortfolioHeader`
  - ownership identity
  - scope badge
  - family count
  - active grant family count
  - semantic candidate count

### 2) Executive summary cards

- `PortfolioSummaryCards`
  - cards:
    - `portfolio_family_count_within_mega_cluster`
    - `portfolio_avg_blocking_power_within_mega_cluster`
    - `portfolio_total_mass_score`
    - `portfolio_hit_rate_top_decile`
    - `portfolio_crown_jewel_index`
    - `portfolio_current_threat_score`
    - `portfolio_heritage_score`
  - each card with trend direction, confidence color, and caveat icon slot

### 3) Coverage and reliability

- `CoverageReliabilityPanel`
  - `portfolio_prediction_coverage_status`
  - `phase03_family_coverage_pct`
  - `phase04_family_coverage_pct`
  - `coverage_caveat_text`
  - `portfolio_prediction_contribution_method`

### 4) Top families

- `TopFamiliesPanel`
  - table view with pinned top rows
  - supports sort/filter/search
  - columns:
    - family id
    - owner weight
    - blocking score
    - legal status
    - heritage
    - primary field
    - forecast contributor value when available

### 4A) Filing strength over time

- `PortfolioFilingStrengthPanel`
  - historical family filing counts by `family_priority_year`
  - cumulative portfolio build curve
  - rolling `3y` filing mass
  - `accelerating / stable / cooling` momentum label
  - current-owner replay caveat

### 5) Concentration and fragility

- `ConcentrationPanel`
  - concentration curve or Pareto bar for top contributors
  - `portfolio_top_contributor_dependence_pct_{3y,5y}`

- `FragilityPanel`
  - unsupported share
  - effective family counts
  - support-level badges

### 6) Field and momentum

- `FieldExposurePanel`
  - ranked current exposure bars for top fields
  - current field concentration only unless a true chronology mart is rebuilt

- `FieldClusterChipRail`
  - `All`
  - top WIPO field chips from live owner exposure
  - selected chip stored in URL state

- `FieldTimeseriesPanel`
  - selected field chronology only when the backing mart is truly multi-snapshot
  - otherwise show a current-state evidence panel or an explicitly caveated fallback

- `ClassificationExposurePanel`
  - stacked WIPO/CPC mix
  - top gaining / declining CPC groups
  - links to portfolio-level classification drill-down

### 6A) Citations

- `PortfolioCitationSummaryPanel`
  - forward / backward / NPL summary
  - self / intra-family scrub indicators

- `PortfolioCitationChronologyPanel`
  - forward citation chronology
  - cumulative and per-effective-family variants

- `PortfolioAttackerMomentumPanel`
  - citing-assignee momentum over time
  - field and jurisdiction filters

- `PortfolioCitationDiversityPanel`
  - citing family diversity
  - citing assignee diversity
  - attacker concentration

- `PortfolioMostCitedFamiliesPanel`
  - ranked cited-family table
  - default sort by forward citations
  - alternate sort options for early citations and blocking context
  - exact WIPO field dropdown filter
  - lifecycle status filter
  - family links into the family workspace

### 7) Threat and exposure

- `ThreatPanel`
  - threat matrix list grouped by assignee
  - top external pressure rows
  - warning chips for high pressure clusters

### 8) Forecast section

- `ForecastHorizonTabs` (`3y`, `5y`)
- `ForecastHeadlinePanel`
  - expected future citations (interval)
  - per-effective-family projection
  - coverage status for forecast scope
- `CurrentMarketOverlayPanel`
  - current heating / cooling field overlay
  - current support level only
- `CoverageAttritionRiskPanel`
  - `12m` / `24m`
  - high-risk branch count/share
  - top risky jurisdictions
  - top risky families
- `PendingGrantPanel` (feature-gated)
  - rank, percentile, priority tier

### 9) Drilldowns

- `PortfolioPrimaryTabs`
  - `Executive`
  - `Families`
  - `Citations`
  - `Field Clusters`
  - `Threats`
  - `Forecast`
  - `Classification`
  - `Compare`

The old drilldown block should be replaced by page-level tabs. Dense sub-content may still use secondary tabs inside a top-level tab, but not as the main portfolio IA.

## Library stack (explicit)

Implementation-first stack:

- `recharts` for charts: line/area/stacked bars/treemap/radar fallback alternatives
- `@tanstack/react-table` for data tables (sorting, filtering, pagination)
- `framer-motion` for page and section motion, not for every interaction
- `lucide-react` for iconography
- `clsx` for class/state composition
- `react-use` for small utility hooks
- optional: `d3-hierarchy` only if treemap customization is needed beyond Recharts

No first-slice 3D requirement for production stability.

## Animation and motion contract

### Global

- honor `prefers-reduced-motion: reduce` by disabling entrance animations

### Enter/reveal pattern

1. Hero shell enters with staggered fade-up.
2. Summary cards enter with progressive stagger.
3. Forecast cards animate after endpoint data is available.
4. Drill-down tables use a short row fade on first load only.

### Micro interactions

- sort/filter updates use short cross-fade
- section switching uses horizontal slide + fade
- no autoplay motion that competes with analysis scan speed

## Interaction and state behavior

- Primary actions:
  - owner search + deep link support (`/portfolio/[owner_id]`)
  - top-level tab deep link support (`?tab=forecast`)
  - field cluster deep link support (`?tab=fields&field=computer-technology`)
  - horizon toggle
  - compare mode (current vs selected year / year A vs year B)
  - sort/filter toggles
  - reliability view vs impact view
- Hard stop behavior:
  - when support is limited, suppress hard forecast numbers and show caveat card
  - do not render probability-heavy headlines in candidate-only zones

## Error and fallback behavior

- `loading`: shimmer per card, section skeletons by component.
- `partial`: banner for missing endpoints.
- `empty`: zero-coverage card with recovery action.
- `error`: partial rendering keeps other sections interactive.

## Data wiring to sections

### Overview payload

- portfolio identity summary
- coverage metadata
- coverage status + caveats
- forecast KPI and top-family preview
- filing-strength preview

### Section payload map

- `/overview`: header, summary, reliability, top families
- `/families`: full family table
- `/citation-summary`: citation summary cards
- `/citation-timeseries`: citation chronology
- `/citation-families`: most cited family ranking
- `/citation-attackers`: attacker momentum and top citers
- `/fields`: current field concentration and top field chips
- `/field-timeseries`: current field overlay only until a true chronology mart exists
- `/filing-timeseries`: historical portfolio filing strength by family priority year
- `/threats`: external pressure matrix and table
- `/forecast`: forecast KPI + risk band + contributor summary
- `/forecast-contributors`: contributor drill-down table
- `/classification`: WIPO/CPC mix and exposure trend
- `/compare-timeslice`: compare-only normalized shape delta

## Implementation skeleton

- `frontend_v2/app/portfolio/[ownerId]/page.tsx`
- `frontend_v2/components/portfolio/portfolio-page-shell.tsx`
- `frontend_v2/components/portfolio/portfolio-header.tsx`
- `frontend_v2/components/portfolio/portfolio-primary-tabs.tsx`
- `frontend_v2/components/portfolio/portfolio-cluster-chip-rail.tsx`
- `frontend_v2/components/portfolio/portfolio-summary-cards.tsx`
- `frontend_v2/components/portfolio/portfolio-coverage-reliability.tsx`
- `frontend_v2/components/portfolio/top-families-table.tsx`
- `frontend_v2/components/portfolio/field-exposure-panel.tsx`
- `frontend_v2/components/portfolio/field-timeseries-panel.tsx`
- `frontend_v2/components/portfolio/threat-panel.tsx`
- `frontend_v2/components/portfolio/forecast-horizon-panel.tsx`
- `frontend_v2/components/portfolio/forecast-risk-panel.tsx`
- `frontend_v2/components/portfolio/portfolio-drilldown-tabs.tsx`

## Frontend action checklist before backend binding

1. Confirm this file is the portfolio UI contract reference.
2. Define DTOs for portfolio overview and section payloads.
3. Create API adapters in `frontend_v2/lib/api/portfolio-v2.ts` from planned endpoints.
4. Add static mocked payload + story-style render checks for all key sections.
5. Replace section-level placeholders during backend integration.
