# Kind Code Normalization And Tiered Market Weighting Build Guide

## Source

User-provided implementation guidance captured on March 8, 2026.

## Purpose

Provide a concrete MVP blueprint for generating the two supporting tables required by:

1. `global-legal-status-normalization-and-influence-evaluation-requirements.md`
2. market-weighted family blocking and value analytics
3. jurisdiction-aware kind-code normalization across global families

## Scope

This guide covers:

1. how to build `tiered_market_weighting`
2. how to build `kind_code_normalization`
3. how to combine both tables in family-level scoring

It is intentionally implementation-oriented and suitable for a 5-week MVP using DuckDB.

## Part 1: Tiered Market Weighting Table

## Goal

Estimate the commercial significance of each jurisdiction by combining:

1. market size
2. legal/IP enforceability quality

The result is a reusable multiplier for market-weighted family breadth and blocking-value calculations.

## Data Inputs

### KMW-01: World Bank GDP PPP

Source:
World Bank Open Data

Indicator:
`NY.GDP.MKTP.PP.CD`

Meaning:
GDP, PPP in current international dollars

Expected file:
World Bank CSV extracted from the downloaded ZIP, for example:
`API_NY.GDP.MKTP.PP.CD_DS2_en_csv_v2.csv`

### KMW-02: U.S. Chamber International IP Index

Source:
Latest U.S. Chamber International IP Index report and data annex

Required field:
`Overall Score`

Meaning:
Proxy for legal enforceability quality on a `0-100` scale.

### KMW-03: ISO Mapping Table

Source:
Any reliable ISO mapping CSV with at least:

1. `iso2`
2. `iso3`

Why:
The World Bank uses ISO-3 while most patent data uses ISO-2.

## Metric Definition

## KMW-04: Final Market Multiplier

Recommended formula:

`Final Market Multiplier = GDP Tier Base Weight * (IP Index Score / 100)`

### GDP tier base weights

Recommended buckets:

1. `>= 5 trillion`: `5.0`
2. `>= 1 trillion`: `3.0`
3. `>= 100 billion`: `1.0`
4. `< 100 billion`: `0.2`

### IP index modifier

Recommended handling:

1. use the reported `Overall Score / 100`
2. if a jurisdiction is missing from the IP index coverage set, assign a default penalty score of `25.0`, which becomes modifier `0.25`

## DuckDB Build Sequence

## KMW-05: Load ISO Mapping

```sql
CREATE TABLE iso_map AS
SELECT *
FROM read_csv_auto('iso_mapping.csv');
```

## KMW-06: Load GDP Data

Assuming latest year column is `2023`:

```sql
CREATE TEMP TABLE wb_gdp AS
SELECT
    "Country Code" AS iso3,
    "2023" AS gdp_value
FROM read_csv_auto(
    'API_NY.GDP.MKTP.PP.CD_DS2_en_csv_v2.csv',
    skip=4
);
```

## KMW-07: Load IP Index Data

```sql
CREATE TEMP TABLE ip_index AS
SELECT
    "Country Code" AS iso2,
    "Overall Score" AS ip_score
FROM read_csv_auto('us_chamber_ip_index.csv');
```

## KMW-08: Generate Tiered Market Weighting Table

```sql
CREATE TABLE tiered_market_weighting AS
SELECT
    m.iso2 AS jurisdiction_code,
    g.gdp_value,
    COALESCE(i.ip_score, 25.0) AS ip_score,
    CASE
        WHEN g.gdp_value >= 5000000000000 THEN 5.0
        WHEN g.gdp_value >= 1000000000000 THEN 3.0
        WHEN g.gdp_value >= 100000000000  THEN 1.0
        ELSE 0.2
    END AS gdp_tier_weight,
    ROUND(
        (
            CASE
                WHEN g.gdp_value >= 5000000000000 THEN 5.0
                WHEN g.gdp_value >= 1000000000000 THEN 3.0
                WHEN g.gdp_value >= 100000000000  THEN 1.0
                ELSE 0.2
            END
        ) * (COALESCE(i.ip_score, 25.0) / 100.0),
        2
    ) AS final_market_multiplier
FROM wb_gdp g
JOIN iso_map m
    ON g.iso3 = m.iso3
LEFT JOIN ip_index i
    ON m.iso2 = i.iso2;
```

## Expected Columns

Recommended schema:

1. `jurisdiction_code`
2. `gdp_value`
3. `ip_score`
4. `gdp_tier_weight`
5. `final_market_multiplier`

## Part 2: Kind Code Normalization Table

## Goal

Standardize raw office-specific kind codes into a small set of universal legal stages that downstream analytics can use consistently.

## Data Inputs

### KCN-01: EPO DOCDB User Manual

Source:
EPO DOCDB user manual or equivalent official kind-code references.

Purpose:
Authoritative mapping of office-specific kind codes.

### KCN-02: LLM-Assisted Extraction For MVP

Recommendation:
For the MVP, do not manually encode thousands of kind-code combinations.

Suggested workflow:
1. extract the top target jurisdictions from the DOCDB manual,
2. use an LLM agent to draft a CSV mapping of `jurisdiction_code + kind_code`,
3. manually review the resulting CSV before loading it into DuckDB.

## Universal Stage Design

## KCN-03: Required Universal Stages

Minimum recommended stages:

1. `PENDING_APPLICATION`
2. `STANDARD_GRANT`
3. `OPPOSITION_SURVIVOR`
4. `UNITARY_GRANT`

Optional future extensions:

1. `CORRECTED_GRANT`
2. `REEXAMINED_GRANT`
3. `POST_GRANT_MODIFIER`

## KCN-04: Stage Multipliers

Recommended MVP multipliers:

1. `PENDING_APPLICATION`: `0.2`
2. `STANDARD_GRANT`: `1.0`
3. `OPPOSITION_SURVIVOR`: `3.0`
4. `UNITARY_GRANT`: `1.0`

These are not market weights. They are legal-stage weights.

## KCN-05: Enforceability Flag

Requirement:
The normalization table should include an explicit `is_enforceable` boolean so downstream queries do not need to infer enforceability from stage names repeatedly.

## Static CSV Shape

Recommended file:
`kind_code_normalization.csv`

Recommended columns:

1. `jurisdiction_code`
2. `kind_code`
3. `universal_stage`
4. `stage_multiplier`
5. `is_enforceable`

Illustrative rows:

```csv
jurisdiction_code,kind_code,universal_stage,stage_multiplier,is_enforceable
US,A1,PENDING_APPLICATION,0.2,FALSE
US,B1,STANDARD_GRANT,1.0,TRUE
US,B2,STANDARD_GRANT,1.0,TRUE
EP,A1,PENDING_APPLICATION,0.2,FALSE
EP,B1,STANDARD_GRANT,1.0,TRUE
EP,B2,OPPOSITION_SURVIVOR,3.0,TRUE
EP,C0,UNITARY_GRANT,1.0,TRUE
CN,A,PENDING_APPLICATION,0.2,FALSE
CN,C,STANDARD_GRANT,1.0,TRUE
```

## DuckDB Load Step

## KCN-06: Load Kind Code Normalization CSV

```sql
CREATE TABLE kind_code_normalization AS
SELECT *
FROM read_csv_auto('kind_code_normalization.csv');
```

## Part 3: Final Family-Level Scoring

## Goal

Combine:

1. the jurisdiction market multiplier
2. the normalized legal-stage multiplier

to produce a family-level geographic blocking or market-value score.

## Scoring Formula

## KFS-01: Family Geographic Value Score

Recommended formula:

`Family Score = SUM(Final Market Multiplier_jurisdiction * Stage Multiplier_document)`

Interpretation:

1. market weight captures jurisdiction importance
2. stage multiplier captures legal maturity or legal resilience
3. current-state filters ensure dead rights do not inflate present blocking power

## DuckDB Example

## KFS-02: Family Blocking Power Query

```sql
SELECT
    f.docdb_family_id,
    SUM(m.final_market_multiplier * n.stage_multiplier) AS family_blocking_power_score
FROM family_documents f
JOIN kind_code_normalization n
    ON f.jurisdiction_code = n.jurisdiction_code
   AND f.kind_code = n.kind_code
JOIN tiered_market_weighting m
    ON f.jurisdiction_code = m.jurisdiction_code
WHERE f.is_currently_active = TRUE
GROUP BY f.docdb_family_id;
```

## Important Semantics

### KFS-03: This Score Is Not Raw Family Breadth

Requirement:
The resulting score is a weighted blocking or geographic-value score, not a replacement for raw jurisdiction breadth.

The product should keep both:

1. raw breadth,
2. weighted market reach / blocking score.

### KFS-04: `B2` And Similar Stages Must Increase Defensive Weight

Requirement:
If a family contains an EP `B2`, the stage multiplier should materially increase the family’s weighted legal strength in that jurisdiction.

### KFS-05: Pending Applications Should Contribute Less

Requirement:
Pending application-stage rights may contribute to pipeline visibility but should carry much less blocking weight than granted rights.

## Validation Rules

## KVG-01: Validate ISO Mapping Coverage

Requirement:
Check that all jurisdictions used in patent-family data resolve through the ISO map and market-weight table.

## KVG-02: Validate Kind Code Coverage

Requirement:
Check that all relevant `jurisdiction_code + kind_code` pairs seen in the family data resolve through the normalization table.

## KVG-03: Flag Unmapped Jurisdiction Or Kind Codes

Requirement:
Any unmapped code pair must be surfaced in QA output rather than silently dropped.

## KVG-04: Keep Methodology Versioned

Requirement:
Version:

1. market weighting methodology,
2. GDP snapshot year,
3. IP index edition,
4. kind-code normalization mapping version,
5. stage multipliers.

## MVP Recommendations

## KMR-01: Start Narrow

For the 5-week MVP, start with the highest-value jurisdictions and offices first, such as:

1. `US`
2. `EP`
3. `CN`
4. `JP`
5. `KR`
6. `CA`
7. `AU`
8. `IN`

Then expand coverage later.

## KMR-02: Keep Tables Static But Versioned

For MVP speed, both tables can be static reference tables in DuckDB, as long as they are:

1. reviewable,
2. versioned,
3. easy to regenerate.

## KMR-03: Use The Tables As Inputs, Not Final Truth

Requirement:
These tables support downstream family scoring. They do not replace:

1. point-in-time legal filtering,
2. family collapse logic,
3. UP unrolling,
4. office-aware legal-event logic.

## Relationship To Other Notes

This guide supports:

1. `global-legal-status-normalization-and-influence-evaluation-requirements.md`
2. `patent-kind-codes-and-document-lifecycle-representation-requirements.md`
3. `unitary-patent-and-upc-representation-requirements.md`
4. `legal-status-lifecycle-and-point-in-time-analytics-requirements.md`
5. `family-level-collapse-and-metric-calculation-requirements.md`
