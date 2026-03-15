# Patent Kind Codes And Document Lifecycle Representation Requirements

## Source

User-provided implementation guidance captured on March 8, 2026.

## Purpose

Define how PatentIQ must parse and use patent kind codes (`A`, `B`, `C`) so the platform does not:

1. double-count inventions,
2. confuse pending applications with enforceable rights,
3. embed duplicate or legally stale text,
4. fragment citations across lifecycle documents,
5. overstate or understate value and legal strength.

## Why This Matters

Kind codes are not cosmetic suffixes. They indicate the legal and documentary stage of the same invention across its lifecycle.

If kind codes are ignored or flattened incorrectly:

1. a family can appear as multiple inventions,
2. semantic search can index duplicate text,
3. blocking-risk analysis can rely on unenforceable claims,
4. filing trends can be inflated by lifecycle documents,
5. opposition-survived assets can be undervalued.

## Fundamental Kind-Code Semantics

## PKR-01: A-Level Documents = Published Applications

Requirement:
`A`-level documents must be treated as publication-stage application records, not enforceable rights.

Common meanings:
1. `A1`: published application,
2. `A2`: published application without search report,
3. `A3`: later-published search report.

Analytics meaning:
1. high signal for R&D intent,
2. low legal certainty,
3. claims may be much broader than eventual granted scope.

## PKR-02: B-Level Documents = Granted Rights

Requirement:
`B`-level documents must be treated as granted, legally enforceable patent rights, subject to office-specific nuances.

Common meanings:
1. `B1` in EP: first grant,
2. `B2` in EP: maintained in amended form after opposition,
3. `B1`/`B2` in US: grant-stage distinctions that do not mean exactly the same thing as EP.

Analytics meaning:
1. enforceable rights,
2. higher legal certainty than `A` documents,
3. correct primary source for blocking and enforceability analysis.

## PKR-03: C-Level Documents = Post-Grant Modifiers Or Special Legal Status

Requirement:
`C`-level documents must be treated as legal modifiers attached to a granted right, not as new technical inventions.

Examples:
1. `C0` in EP: Unitary Patent registration,
2. `C1`, `C2`, etc. in some systems: re-examination or corrected post-grant certificates.

Analytics meaning:
1. modify scope, jurisdictional effect, or legal validity,
2. critical for legal-status and territorial analysis,
3. must remain connected to the parent grant and family.

## Lifecycle And Family Rules

## PKR-04: Collapse Lifecycle Documents Into One Invention Family

Requirement:
`A`, `B`, and `C` lifecycle documents for the same invention must roll up to the same canonical family-level entity for core analytics.

Implication:
The platform must not count the lifecycle documents as separate inventions.

## PKR-05: Preserve Document-Level Detail For Drill-Down

Requirement:
Even though family-first rollup is the default, document-level lifecycle detail must remain available for:
1. prosecution history,
2. text-source selection,
3. legal-status inspection,
4. citation audit.

## Text And Search Best Practices

## PKR-06: Enforce Text Hierarchy For Embedding And Semantic Search

Requirement:
When building vector-search or semantic-search corpora, PatentIQ must not embed both `A` and `B` versions of the same patent by default.

Preferred hierarchy:
1. if a family has a relevant `B` document, embed the `B` text,
2. otherwise, if only `A` text exists, embed the `A` text,
3. treat `C` records as legal modifiers, not primary technical text sources.

Why:
1. avoids duplicate semantic hits,
2. prefers legally accurate granted claims when available,
3. reduces confusion in AI-assisted search results.

## PKR-07: Separate Search-Intent Modes

Requirement:
Search workflows should distinguish:
1. `research intent` mode, where `A` documents may be useful,
2. `enforceable rights` mode, where `B` and relevant `C`-linked rights are primary.

## Citation And Counting Rules

## PKR-08: Group Citations Across Kind Codes To The Canonical Family

Requirement:
All citations to `A`, `B`, and `C` lifecycle documents must aggregate to the parent family for impact metrics.

Why:
Different actors cite different lifecycle documents of the same invention. Document-level counting alone fractures influence.

## PKR-09: Do Not Expect Citation Volume On Legal Modifier Records

Requirement:
`C`-level records such as `C0` should not be expected to behave like technical citation targets.

Implication:
The family must absorb the impact, while `C` contributes legal-status meaning, not technical novelty meaning.

## PKR-10: Filing Trends Must Count Families, Not Lifecycle Documents

Requirement:
R&D momentum and filing-trend analytics must count the invention once by family and anchor it on earliest priority date.

Implication:
`A`, `B`, and `C` records must not create multiple filing events.

## Enforceability And Risk Rules

## PKR-11: Blocking And Freedom-To-Operate Logic Must Prefer Granted Claims

Requirement:
Any blocking-power, FTO, or enforceability-oriented workflow must use `B`-level claims by default, not `A`-level claims.

Why:
Application claims are often intentionally broad and may materially shrink before grant.

## PKR-12: AI Copilot Must Be Kind-Code-Aware

Requirement:
When summarizing claim scope, blocking power, or legal strength, AI features must be instructed to:
1. prefer `B`-level text where available,
2. avoid presenting `A`-level claim breadth as enforceable reality,
3. label any fallback to application-stage text clearly.

## PKR-13: “Show Enforceable Patents” Filter Must Be Explicit

Requirement:
UI and backend filtering for enforceable patent views must be kind-code aware.

Suggested logic:
Include records where granted-right semantics apply, typically:
1. `kind_code LIKE 'B%'`,
2. relevant legal-modifier rights such as `C0` where they extend or modify a granted right.

## European EP-Specific Valuation Rules

## PKR-14: EP B2 Must Receive Special Legal-Strength Treatment

Requirement:
For EP data, `B2` documents must receive a significant legal-strength and defensive-value uplift because they reflect survival through EPO opposition in amended form.

Why:
An EP `B2` is a strong real-world validation signal:
1. competitor challenge occurred,
2. the patent survived,
3. legal resilience is therefore demonstrated.

## PKR-15: Office-Specific Semantics Must Not Be Mixed Naively

Requirement:
The platform must not assume that `B1`, `B2`, or `C*` codes mean the same thing across all offices.

Implication:
Any cross-office logic must use office-aware interpretation tables rather than raw code-pattern assumptions.

## Data Engineering Requirements

## PKR-16: Kind Code Must Be Present In Core ETL Outputs

Requirement:
When extracting or materializing global family members, the ETL pipeline must explicitly preserve `kind_code` as a first-class field.

## PKR-17: Add Kind-Code Classification Layer

Requirement:
The ETL should derive normalized lifecycle categories such as:
1. `application_publication`,
2. `grant`,
3. `post_grant_modifier`,
4. `unitary_registration`,
5. `corrected_or_reexamined`.

Why:
Product logic should not depend only on raw office-specific strings.

## PKR-18: Add Preferred Text Source Flag

Requirement:
For semantic retrieval and AI summarization, ETL should precompute a preferred text-source flag per family using the document hierarchy rules.

## PKR-19: Add Enforceability Flag

Requirement:
ETL should precompute an `is_enforceable_document` or equivalent lifecycle-aware flag for fast UI and analytics filtering.

## Product And UI Expectations

## PKR-20: Distinguish “Research Pipeline” From “Enforceable Portfolio”

Requirement:
UI should make it obvious when a user is looking at:
1. published applications,
2. granted rights,
3. post-grant modifiers.

## PKR-21: Show Lifecycle Context On Patent Detail Pages

Requirement:
Patent detail or family views should expose lifecycle context such as:
1. application publication,
2. grant status,
3. opposition-amended grant,
4. UP or other post-grant modifier.

## PKR-22: Semantic Search Results Must Avoid Same-Invention Duplication

Requirement:
Semantic and vector-search results should avoid returning both `A` and `B` versions of the same invention as separate primary hits unless the user explicitly requests document-level mode.

## Mapping To Existing Requirements

This note sharpens several already-existing ideas.

### Overlaps With Existing Docs

1. `MKT-01`: semantic retrieval,
2. `R-02`, `R-14`, `R-22`: family-first analytics and citation rollups,
3. `R-04`: blocking-power logic,
4. `R-16`: opposition resilience,
5. `UPR-01` to `UPR-17`: `C0` and UP-specific treatment,
6. `PMC-01`: family as default counting unit.

### Net-New Additions

1. explicit `A/B/C` lifecycle semantics,
2. text hierarchy for vector search,
3. enforceability filter logic by kind code,
4. AI-copilot rules for granted-claims preference,
5. EP `B2` valuation multiplier requirement.

## Delivery Priority

### P0

1. preserve and normalize `kind_code` in ETL,
2. family-first citation grouping across lifecycle docs,
3. enforceable-right filtering,
4. text hierarchy for semantic retrieval,
5. `B`-level preference for blocking/FTO logic.

### P1

1. EP `B2` valuation uplift,
2. UI lifecycle labeling,
3. preferred text-source flags,
4. office-aware lifecycle interpretation layer.

### P2

1. advanced lifecycle timeline visualization,
2. deeper document-mode exploration features.
