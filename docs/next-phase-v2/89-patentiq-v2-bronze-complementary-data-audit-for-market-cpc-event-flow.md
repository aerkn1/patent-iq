# PatentIQ v2 Bronze Complementary Data Audit For Market CPC Event Flow

## Scope

Follow-up audit to answer:

1. whether the Bronze layer contains missing raw signals that can complement the constraints found in the CPC event-flow audit,
2. which constraints are upstream source gaps versus downstream mart gaps,
3. what complementary analytics can be added cheaply without overstating the data contract.

This note complements:

- [88-patentiq-v2-market-technology-tab-cpc-event-flow-audit.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/88-patentiq-v2-market-technology-tab-cpc-event-flow-audit.md)
- [57-patentiq-v2-classification-first-seen-visibility-audit-and-upgrade-plan.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/57-patentiq-v2-classification-first-seen-visibility-audit-and-upgrade-plan.md)

## Short Conclusion

Yes, partly.

Bronze does contain useful complementary raw data for:

1. stronger chronology
2. first-seen classification visibility
3. field and IPC coverage on families that have no CPC rows
4. richer publication and legal-event overlays

Bronze does **not** contain the missing pieces needed to:

1. fill the CPC coverage gap for families that truly have no source CPC rows
2. support true dated CPC mutation history
3. remove CPC overlap and non-additivity

So the correct interpretation is:

1. some constraints can be complemented,
2. some constraints are fundamental source limitations,
3. the next upgrade should add complementary analytics rather than pretending the CPC layer is complete.

## Bronze Sources Audited

### Classification and field anchors

- [bronze_patstat_appln.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_appln.parquet)
- [bronze_patstat_appln_cpc.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_appln_cpc.parquet)
- [bronze_patstat_appln_ipc.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_appln_ipc.parquet)
- [bronze_patstat_appln_techn_field.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_appln_techn_field.parquet)

Observed schemas:

1. `bronze_patstat_appln_cpc`: `appln_id`, `cpc_class_symbol`
2. `bronze_patstat_appln_ipc`: `appln_id`, `ipc_class_symbol`, `ipc_version`, plus IPC support columns
3. `bronze_patstat_appln_techn_field`: `appln_id`, `techn_field_nr`, `weight`
4. `bronze_patstat_appln`: includes `appln_id`, `docdb_family_id`, filing/publication anchors, and family ids

### Publication and legal chronology

- [bronze_patstat_pat_publn.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_pat_publn.parquet)
- [bronze_patstat_inpadoc_legal_event.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_inpadoc_legal_event.parquet)

Observed schemas:

1. `bronze_patstat_pat_publn`: `appln_id`, `publn_auth`, `publn_kind`, `publn_date`, `publn_first_grant`
2. `bronze_patstat_inpadoc_legal_event`: rich legal-event columns including `event_code`, `event_effective_date`, `lapse_*`, `reinstate_*`, plus sparse classification-related fields `class_scheme`, `class_symbol`

## Findings By Constraint

## 1. Missing CPC coverage

### Can Bronze fill it?

No.

This is the most important result.

For `Computer technology` in `2023`, the current gold PIT shows `715,395` families with `0` CPC main groups.

I checked those same families against Bronze:

1. families with Bronze CPC rows: `0`
2. families with Bronze techn-field rows: `715,395`
3. families with Bronze IPC rows: `715,395`

Interpretation:

1. these families are not missing from the bounded source universe,
2. they are still in-field and still classification-bearing at the IPC/field level,
3. but they genuinely do not have source CPC rows in the bounded Bronze slice.

So the CPC coverage gap is a source-level limitation, not a Gold-only derivation loss.

### What Bronze can still do here

Bronze gives enough evidence to build complementary coverage analytics such as:

1. `share of field families with CPC`
2. `share of field events on CPC-coded families`
3. `IPC-only residual families`
4. `field families with no CPC main-group assignment`

Those additions would make the CPC technology surfaces more honest without pretending the missing CPC rows exist.

## 2. Historical classification timing

### Can Bronze improve it?

Yes.

Bronze contains enough raw ingredients to support stronger classification visibility chronology.

Evidence already documented in:

- [57-patentiq-v2-classification-first-seen-visibility-audit-and-upgrade-plan.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/57-patentiq-v2-classification-first-seen-visibility-audit-and-upgrade-plan.md)

Key numbers from that audit:

1. distinct CPC applications: `24,535,049`
2. CPC applications joined to member-publication chronology: `21,889,868`
3. approximate CPC appln chronology join coverage: about `89.2%`

Local Bronze checks also show:

1. all `24,535,049` distinct CPC applications join to Bronze publication rows
2. Bronze publication rows therefore preserve full raw publication backbone for the CPC-bearing application set

Interpretation:

1. Bronze is sufficient for `first_seen_classification_visibility`
2. Bronze is not sufficient for exact code mutation history

This means Bronze can improve:

1. when a CPC first becomes visible on a family,
2. when a CPC begins contributing to field-level chronology,
3. the realism of historical CPC trend surfaces

But Bronze still does not let us claim:

1. exact CPC reassignment date,
2. exact code removal date,
3. fully dated mutation truth after first visibility

## 3. Publication and grant chronology richness

### Can Bronze complement the current event flow?

Yes.

`bronze_patstat_pat_publn` carries direct publication-level fields:

1. `publn_date`
2. `publn_auth`
3. `publn_kind`
4. `publn_first_grant`

Observed `publn_first_grant` values:

1. `N`: `27,958,065`
2. `Y`: `19,840,778`

This means Bronze can support a more explicit first-grant-publication treatment than a generic application/grant stage flag alone.

That does not replace the current Silver event-flow layer, but it can complement it with:

1. first-grant publication chronology
2. first-grant share inside a CPC slice
3. grant timing overlays by office

## 4. Legal-event chronology

### Can Bronze add useful complementary signals?

Yes, but selectively.

For the CPC-bearing application universe:

1. distinct CPC applications: `24,535,049`
2. distinct CPC applications with Bronze legal events: `18,210,349`

So Bronze legal events can support complementary lifecycle analytics for a large subset of the CPC-bearing universe.

Potentially useful additions:

1. lapse / reinstatement overlays
2. renewal pressure indicators
3. opposition / appeal presence where event-code mapping is mature
4. post-grant lifecycle views for CPC slices

### Can legal events solve CPC history?

No.

The raw legal-event table does not provide a strong generic CPC mutation feed.

Observed profile:

1. `class_scheme` is overwhelmingly blank
2. the non-blank audited scheme is mostly `IPC`
3. `event_type` is also mostly blank

So legal events are useful for legal lifecycle overlays, but not for reconstructing dated CPC classification changes.

## 5. Overlap and non-additivity

### Can Bronze solve it?

No.

This is intrinsic to CPC multi-membership.

Even with raw Bronze CPC:

1. one application can contribute to multiple CPC symbols,
2. one family can appear in multiple CPC slices,
3. summed totals across CPC groups remain unsafe.

So Bronze does not change the settlement rule:

- CPC rows must remain non-additive across groups

## 6. Row volume and endpoint settlement

### Can Bronze make the UI settlement cheaper?

No, not directly.

If anything, raw Bronze joins are heavier than using a dedicated aggregated mart.

So Bronze confirms the feature is possible, but it does not change the architectural recommendation:

1. require `cpc_main_group`
2. lazy-load the panel
3. prefer a dedicated market aggregation over repeated raw Bronze joins in the UI path

## What Complementary Analytics Are Cheaply Obtainable

These are the strongest low-to-medium-cost complements now that Bronze has been checked.

## 1. CPC coverage strip for the technology tab

For the selected field and year, show:

1. families with CPC main-group assignment
2. families without CPC main-group assignment
3. application events on CPC-coded families
4. grant events on CPC-coded families

This directly addresses the current completeness caveat.

## 2. IPC-backed residual slice

For the field/year families with no CPC rows, show:

1. top IPC subclasses
2. application/grant flow for the IPC residual

This is the cleanest complementary analytic for the CPC-missing population because those families do have Bronze IPC coverage.

## 3. First-seen CPC visibility chronology

Use the first-seen classification visibility lane to show:

1. first visible year of a CPC within a field
2. visible-family accumulation over time

This complements the existing selected-year CPC tables by making historical emergence more believable.

## 4. First-grant publication overlay for selected CPC

Inside the future CPC event-flow panel, add an optional overlay for:

1. first-grant publication rows only

This is a stronger grant milestone view than generic application/grant counts alone.

## 5. Legal lifecycle overlay for selected CPC

For a selected CPC slice, add a later-phase drilldown based on legal events:

1. lapse presence
2. reinstatement presence
3. renewal-related signals

This is not a cheap default panel, but it is a valid extension path.

## Recommended Upgrade Path

## Phase 1

Keep the planned CPC applications/grants panel narrow:

1. selected field
2. selected CPC main group
3. yearly total event flow
4. optional jurisdiction drilldown

## Phase 2

Add a small complementary coverage surface above it:

1. `CPC-coded coverage`
2. `Residual without CPC`

This is the highest-signal Bronze-driven complement.

## Phase 3

Add an IPC residual analytic for the non-CPC families:

1. top IPC subclasses
2. event flow on the IPC residual

## Phase 4

If needed, enrich the selected-CPC flow with:

1. first-grant publication overlay
2. legal lifecycle overlay

## Final Verdict

The Bronze layer does contain meaningful complementary data.

But it complements the CPC event-flow gaps asymmetrically:

1. `Yes` for stronger chronology and visibility
2. `Yes` for IPC-backed residual analytics
3. `Yes` for publication and legal-event enrichment
4. `No` for filling true missing CPC source coverage
5. `No` for true dated CPC mutation history
6. `No` for removing CPC overlap or the need for a filtered settlement

So the right next move is not to force CPC into acting complete.

It is to pair the future CPC event-flow panel with:

1. coverage disclosure,
2. IPC residual analytics,
3. stronger first-seen chronology,
4. optional legal/publication milestone overlays.
