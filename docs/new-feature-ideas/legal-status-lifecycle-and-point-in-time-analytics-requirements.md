# Legal Status Lifecycle And Point-In-Time Analytics Requirements

## Source

User-provided implementation guidance captured on March 8, 2026.

## Purpose

Define how PatentIQ must represent legal status over time so patents and families can be evaluated correctly for:

1. current blocking power,
2. current market coverage,
3. historical R&D activity,
4. prior-art credibility,
5. opposition resilience,
6. cohort and predictive decay analysis.

## Core Principle

### LSR-01: Legal Power Can Die While Analytical Value Survives

Requirement:
A lapsed, abandoned, or expired patent may lose current legal enforceability, but it must remain analytically available for historical innovation, prior-art, and citation-impact use cases.

Implication:
PatentIQ must never equate `not enforceable today` with `irrelevant historically`.

## Family-Level Status Logic

### LSR-02: Family Status Is Composite, Not Singular

Requirement:
A patent family must not be represented by a naive single document-level status. Family status must be derived as a composite state from all family members and jurisdictions.

### LSR-03: Fully Active Family

Requirement:
Mark a family as `fully_active` or equivalent when at least one granted (`B`-level or equivalent) right is currently alive in a major jurisdiction and the family has active enforceable coverage.

### LSR-04: Pending / Emerging Family

Requirement:
Mark a family as `pending_emerging` when it contains only application-stage rights and none have yet been explicitly abandoned, rejected, or converted into granted status.

### LSR-05: Under Fire / Opposed Family

Requirement:
Mark a family as `under_fire` or `opposed` when at least one granted family member is currently in a post-grant challenge state such as EPO opposition or UPC attack.

Why:
This is a critical legal-risk state even if the family still has active enforceable rights.

### LSR-06: Partially Lapsed Family

Requirement:
Mark a family as `partially_lapsed` when enforceable rights remain active in some jurisdictions while other family members have lapsed, expired early, or been abandoned.

### LSR-07: Dead Family

Requirement:
Mark a family as `dead` only when every member of the family has either:
1. reached full term expiry,
2. been abandoned,
3. lapsed irreversibly,
4. been revoked or otherwise lost in all relevant jurisdictions.

## Inclusion / Exclusion Rules By Metric Type

## Current Legal And Market Metrics

### LSR-08: Exclude Dead Rights From Current Blocking Power

Requirement:
Current blocking-power or current monopoly metrics must exclude lapsed, abandoned, expired, and revoked rights.

Why:
A dead patent cannot currently block a competitor.

### LSR-09: Current Family Breadth Must Use Current Active Coverage

Requirement:
Current family breadth must reflect only the jurisdictions where the family still has live enforceable coverage at the requested point in time.

Implication:
If a family originally covered 10 countries but only 2 remain active, current breadth is `2`, not `10`.

### LSR-10: Current Litigation And Legal-Risk Metrics Must Use Live Rights

Requirement:
Risk surfaces such as litigation exposure, enforceability risk, and current defensive score must be computed using currently active or currently contested rights only.

## Historical Innovation And Prior-Art Metrics

### LSR-11: Historical Filing Trends Must Include Dead Families

Requirement:
Historical R&D and filing-momentum analytics must include families that were later abandoned or expired.

Why:
They still prove historical innovation effort at the time of filing.

### LSR-12: Citation Impact Must Retain Dead Families

Requirement:
Foundational or highly cited patents must retain their historical citation importance even after expiry or abandonment.

Why:
Expiry does not erase technological influence.

### LSR-13: Prior-Art And Novelty Workflows Must Include Abandoned Applications

Requirement:
Abandoned or non-granted application publications must remain available to prior-art, novelty, and defensive-publication analysis.

Why:
Even abandoned applications can still destroy novelty for later competing filings.

## Point-In-Time Architecture

### LSR-14: Single Status Column Is Insufficient

Requirement:
PatentIQ must not rely on one static `status` field for family analytics. The platform needs a time-series legal-status event architecture.

### LSR-15: Legal Status Event Mart Is Mandatory

Requirement:
PatentIQ must implement a legal-status event mart or equivalent slowly changing dimension ledger containing:
1. event date,
2. jurisdiction,
3. prior state,
4. new state,
5. event type,
6. family identifier,
7. affected document/member identifier,
8. effective active coverage after the event where derivable.

### LSR-16: Coverage Metrics Must Be Reconstructable By Date

Requirement:
For any `point_in_time` query, the platform must be able to reconstruct:
1. active family breadth,
2. pending breadth,
3. active jurisdiction list,
4. challenged/opposed status,
5. current blocking-power footprint.

## Time-Series Examples And Intended Behavior

### LSR-17: Blocking Power Must Rise And Fall With Events

Requirement:
Blocking-power and enforceability metrics must change over time as grant, lapse, opposition, renewal, and revocation events occur.

### LSR-18: Family Breadth Must Decay Through Events, Not Be Static

Requirement:
Family breadth over time must be modeled as a time series rather than a single lifetime maximum.

Why:
Coverage often decays from strategic abandonment or missed renewals.

## Query Semantics

### LSR-19: Every Legal/Market Metric Query Needs A `point_in_time` Parameter

Requirement:
Queries for current landscape, legal strength, current breadth, or blocking power must support an explicit `point_in_time` input, defaulting to “now” only where appropriate.

### LSR-20: Current Landscape Filters Must Use Current Activity

Requirement:
If a user runs a current-state analysis, SQL or API filters must effectively evaluate `is_currently_active = TRUE` at the requested time.

### LSR-21: Historical Innovation Queries Must Drop Current-Activity Filters

Requirement:
If a user runs historical innovation, pioneer, or R&D-momentum analysis, the system must include historical families regardless of whether they remain active today.

## Opposition And Resilience Logic

### LSR-22: Opposition Resilience Must Be Event-Based

Requirement:
To compute opposition resilience, the platform must detect families that:
1. entered an opposed or challenged state,
2. later returned to an active granted state or remained active after amendment.

### LSR-23: Survived-Challenge Assets Are Crown-Jewel Signals

Requirement:
Families that survive post-grant challenge and remain active should receive a strong resilience and strategic-value uplift.

## Predictive Cohort Analytics

### LSR-24: Status Timelines Enable Decay Forecasting

Requirement:
The legal-status event mart must support cohort analysis of how families decay over time by:
1. jurisdiction,
2. owner,
3. tech field,
4. family breadth,
5. grant cohort.

### LSR-25: Strategic-Abandonment Patterns Must Be Queryable

Requirement:
The platform should support analyses such as:
1. percent of EP rights abandoned by year 7,
2. owner-specific lapse behavior,
3. survival curves by technology domain,
4. expected remaining coverage by cohort.

## Implementation Requirements

### LSR-26: Never Delete Dead Records

Requirement:
Lapsed, abandoned, expired, and revoked records must remain in the warehouse and marts.

Why:
Deleting them destroys historical truth and prevents lifecycle analysis.

### LSR-27: Maintain Both Current And Historical Derived Views

Requirement:
Engineering should maintain:
1. current-state convenience views,
2. event-level history marts,
3. point-in-time reconstruction logic.

### LSR-28: Family Status Must Be Derived, Not Manually Stored As Final Truth

Requirement:
Any current family status label should be a derived product of member events and effective dates, not an untraceable flat label.

## Product And UI Expectations

### LSR-29: Distinguish Current Legal Power From Historical Innovation

Requirement:
The UI must clearly distinguish:
1. currently enforceable assets,
2. historically important but no-longer-active assets,
3. pending/emerging families,
4. challenged or under-fire families.

### LSR-30: Current And Historical Metrics Must Not Be Mixed Silently

Requirement:
When displaying a metric, the UI should indicate whether it reflects:
1. current active state,
2. lifetime family footprint,
3. historical innovation activity,
4. historical citation impact.

### LSR-31: EP Detail Views May Use PATSTAT Register As Procedural Override

Requirement:
For EP applications where PATSTAT Register data exists, the publication-detail and EP evidence views may treat Register procedural status as the primary display source when it conflicts with INPADOC.

Constraint:
This override is for EP procedural display and auditability only. It must not silently alter cross-office family-ranking math.

### LSR-32: Dual-Clock Provenance Must Remain Visible

Requirement:
If EP detail views use Register-derived status instead of INPADOC-derived status, the data layer should expose:
1. `status_source`,
2. `status_source_priority`,
3. both underlying event timestamps where feasible.

## Mapping To Existing Requirements

This note sharpens existing legal-status and family-first requirements.

### Overlaps With Existing Docs

1. `DAP-01`: global legal-status layer,
2. `R-16`: opposition resilience,
3. `R-17`, `R-18`, `R-20`: stage mix and trend timing,
4. `UPR-09`, `UPR-10`, `UPR-11`: UP cliff and centralized legal risk,
5. `FCR-08`, `FCR-10`, `FCR-14`, `FCR-15`: family-level legal and time-based logic,
6. `XR-03` in `optimum-product-gap-analysis-architecture-requirements.md`: legal-status event mart.

### Net-New Additions

1. explicit composite family-status taxonomy,
2. strict current-vs-historical inclusion rules,
3. mandatory `point_in_time` query semantics,
4. predictive cohort-decay use cases grounded in event history.

## Delivery Priority

### P0

1. legal-status event mart,
2. point-in-time filters,
3. current-vs-historical metric separation,
4. composite family-status derivation,
5. opposition-resilience event detection.

### P1

1. current vs historical UI labeling,
2. survival/decay cohort views,
3. strategic-abandonment analytics.

### P2

1. deeper predictive lapse forecasting,
2. scenario analysis and wait-to-lapse strategy tooling.
