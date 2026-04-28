# Semantic Similarity And Vector Layer Requirements

## Source

User-provided implementation guidance captured on March 9, 2026.

## Purpose

Define how PatentIQ should add a semantic-similarity and vector-retrieval layer without breaking the deterministic family-first, legal-status, chronology, and blocking-power architecture already established.

## Core Principle

Semantic similarity should act as a matching and discovery engine that feeds the deterministic patent-intelligence stack.

It must not:
1. replace family-first legal analytics,
2. replace chronology-aware prior-art and threat logic,
3. replace blocking-power or enforceability scoring,
4. return document-cluttered duplicate family results.

## Current MVP Operating Policy

The current semantic MVP should assume:
1. USPTO full text is not available as a usable semantic text provider,
2. EPAB remains the only claim-grade text provider in the semantic layer,
3. PATSTAT English abstract fallback remains the broad coverage floor,
4. semantic retrieval must therefore be positioned as discovery and comparison first, not full legal-risk search.

## Premium Use Cases

## SVR-01: Semantic FTO Radar

Requirement:
PatentIQ may support text-to-threat workflows only after a stronger claim-text corpus exists.

Expected output:
Current MVP interpretation:
1. this use case is deferred without USPTO full text,
2. the semantic MVP should not present itself as a broad FTO or infringement engine,
3. exploratory text-to-family discovery remains allowed under separate rules below.

## SVR-02: Semantic Portfolio Collision And Whitespace Mapping

Requirement:
PatentIQ should support portfolio-to-portfolio semantic comparison, while whitespace mapping remains a later or caveated workflow when claim-grade coverage is incomplete.

Expected output:
Safe MVP output:
1. semantic cluster overlap,
2. semantically adjacent family groups,
3. comparison-level overlap and gap indicators,
4. opportunity zones only when clearly labeled as abstract-first or EP-claim-enriched rather than legal whitespace proof.

## Vector-Space Separation Rules

## SVR-03: Abstract And Claims Must Use Separate Vector Spaces

Requirement:
PatentIQ should maintain at least two distinct vector spaces:
1. `vector_abstract` as the primary global MVP space for landscaping, discovery, and technology exploration,
2. `vector_claims` as a narrower EPAB-backed space rather than a full cross-jurisdiction claim layer.

Rationale:
1. abstracts describe the invention broadly,
2. claims define the legally enforceable scope,
3. FTO-style workflows using abstract-only embeddings will create false positives,
4. without USPTO full text, claim-space must not be marketed as universally representative.

## SVR-04: Workflow-Type Must Control Which Vector Space Is Queried

Requirement:
The product should choose the vector space based on the workflow being executed.

Examples:
1. landscape discovery should query abstract-oriented vectors first,
2. family and portfolio comparison should prefer abstract vectors by default,
3. EP claim-enriched workflows may query claim-oriented vectors where coverage exists,
4. mixed workflows may show both spaces, but results must remain labeled.

## Family Collapse Rules

## SVR-05: Semantic Embeddings Must Follow Family Collapse

Requirement:
PatentIQ should embed representative family members rather than every raw publication in the family.

Rationale:
1. embedding all `A`, `B`, and `C` publications clutters retrieval with near-duplicates,
2. semantic hits should map directly to `docdb_family_id`,
3. family-level retrieval keeps semantic search aligned with the rest of the analytics platform.

## SVR-06: Representative Family Member Selection Must Use A Text Hierarchy

Requirement:
Representative text selection should follow a deterministic hierarchy.

Current MVP order:
1. English EP granted `B` claims from EPAB, using Claim 1 only,
2. if no usable EP grant claim exists, English abstract fallback from PATSTAT `tls203_appln_abstr`,
3. never default to `A`-document claims for claim-oriented workflows,
4. never default to `C0` as the technical text source unless it is the only usable text artifact.

### SVR-06A: Global Full-Text Source Hierarchy Must Be Deterministic

Requirement:
PatentIQ should use the currently available text sources in this strict order when building the representative family text payload:
1. `EPAB` for English EP grant claims,
2. `PATSTAT tls203_appln_abstr` for English abstract fallback across the remaining in-scope families.

Rationale:
1. EPAB provides the strongest currently available claim text,
2. PATSTAT provides the broadest fallback coverage,
3. this keeps vector generation global while preserving family-first collapse,
4. the resulting semantic layer is mixed-provenance and must be labeled as such.

## Model And Text Rules

## SVR-07: Patent-Specialized Embedding Models Are Required

Requirement:
Semantic retrieval should prefer patent-specialized or legal-technical embedding models rather than generic consumer-text embeddings.

Rationale:
1. patent drafting language is intentionally broad and indirect,
2. generic models often miss the real engineering equivalence hidden in patentese,
3. domain-trained models reduce false semantic distance for technical synonyms and claim language.

## SVR-08: Semantic Search Must Preserve The Underlying Text Provenance

Requirement:
Each semantic result should preserve:
1. representative document id,
2. family id,
3. vector space used,
4. model version,
5. text section used,
6. language and translation status where applicable.

Mandatory provenance flags for the representative payload:
1. `text_provenance`, such as `EPAB_EP1234567B1` or `PATSTAT_ABSTRACT`,
2. `is_abstract_fallback`,
3. `earliest_priority_timestamp` or equivalent chronology anchor,
4. `text_source_type` or equivalent corpus-strength flag.

## Chronology And Legal Guardrails

## SVR-09: Semantic Similarity Must Be Intersected With Time

Requirement:
Semantic matches must always be joinable to the family-time mart so the platform can separate:
1. prior art,
2. peers,
3. followers,
4. potential infringers or later collisions.

Rationale:
Semantic distance is timeless, but patent strategy is not.

## SVR-10: Semantic Results Must Never Be Shown Without Legal And Temporal Context

Requirement:
Semantic search outputs should be joined to current legal status, family chronology, and family-first score layers before they are presented as strategic insights.

Examples:
1. an older dead family may be highly relevant as prior art but not as current threat,
2. a newer active `B` family may be a true current blocking risk,
3. a semantically similar pending family may be a shadow-portfolio watch item rather than immediate litigation risk.

## Architecture Rules

## SVR-11: Vector Search Runs Server-Side Or In A Dedicated Vector Store

Requirement:
The heavy embedding and nearest-neighbor search should run on the backend or a dedicated vector database rather than being pushed wholesale to client-side DuckDB/WASM.

Recommended implementations:
1. a dedicated vector store such as Qdrant, Milvus, or pgvector,
2. or server-side similarity functions where appropriate.

## SVR-12: The Backend Should Return Lightweight Family-Match Payloads

Requirement:
The semantic API layer should return lightweight result payloads such as:
1. `docdb_family_id`,
2. semantic similarity score,
3. representative document metadata,
4. vector space used,
5. model version.

These payloads should then be joined to deterministic Gold-layer analytics.

## SVR-13: Semantic Retrieval Must Feed Deterministic Analytics Rather Than Bypass Them

Requirement:
Semantic retrieval should be treated as an upstream matcher that feeds:
1. enforceability scoring,
2. legal-event interpretation,
3. blocking-power analytics,
4. chronology classification,
5. client-enriched overlays where enabled.

## Guardrails

## SVR-14: Semantic Similarity Must Not Be Treated As Legal Infringement Proof

Requirement:
Semantic closeness is a discovery aid only and must not be labeled as infringement, invalidity, or legal opinion by itself.

## SVR-14A: A-Document Claims Must Be Rejected For FTO Workflows

Requirement:
For claim-oriented workflows, the parser must not use claims from `A1`, `A2`, or other application-stage publications.

Rule:
1. if the only available EP document is an `A`-document, skip claim extraction,
2. fall back to abstract-based embedding with `is_abstract_fallback = TRUE`,
3. keep that fallback visibly labeled in the vector payload and UI.

## SVR-14B: Claim Extraction Must Be Surgical

Requirement:
Claim-oriented embedding generation should extract only the first independent claim for MVP.

Rules:
1. in EPAB, extract only the first usable English claim for MVP,
2. dependent claims should not be embedded by default in MVP because they dilute the core semantic representation and increase compute cost,
3. a future USPTO-enabled build may restore a broader claim hierarchy, but that is not part of the current semantic MVP.

## SVR-14C: Text Sanitization Is Mandatory

Requirement:
The semantic ETL must sanitize raw full-text content before embedding.

Minimum sanitization rules:
1. strip XML and HTML tags,
2. remove layout line breaks and formatting noise,
3. remove inline reference numerals where safe,
4. preserve meaningful claim language rather than flattening it into unreadable fragments.

## SVR-14D: Full-Text Metadata Duplication Must Be Banned

Requirement:
When USPTO full text or EPAB are used in the semantic layer, they must be treated strictly as text providers.

Do not ingest from those sources into the semantic pipeline:
1. classifications,
2. citation metadata,
3. party metadata,
4. duplicated legal-status metadata

because PatentIQ already has globally harmonized versions in PATSTAT and Register.

## SVR-14E: Semantic Compute Must Respect The MVP Sampling Cap

Requirement:
The semantic layer must honor the mega-cluster semantic sampling guardrail for MVP.

Recommended MVP rule:
1. filter to in-scope families with active grants,
2. take a reproducible random `5%` to `10%` sample,
3. embed only that sample for the MVP semantic collections unless a wider corpus is explicitly approved.

## SVR-15: Semantic Whitespace Must Be Filtered By Enforceability Reality

Requirement:
Whitespace views should not rely on vector sparsity alone. They should also intersect with:
1. active family density,
2. blocking power,
3. legal status,
4. trend context,
5. chronology.

## SVR-16: Result Deduplication Must Occur At Family Level

Requirement:
The semantic layer should deduplicate results at `docdb_family_id` before ranking, display, or downstream scoring.

## Recommended Data Contracts

## SVR-17: Family Embedding Registry

Recommended table or registry:
`family_embedding_registry`

Suggested fields:
1. `docdb_family_id`,
2. `representative_doc_id`,
3. `vector_space`,
4. `embedding_model_version`,
5. `text_source_type`,
6. `language_code`,
7. `is_machine_translated`,
8. `text_provenance`,
9. `is_abstract_fallback`,
10. `earliest_priority_timestamp`.

### SVR-17A: Separate Scalar Payload Contracts Are Mandatory

Requirement:
The vector backend should preserve scalar payloads needed for chronology and deterministic joins.

For `vector_claims`:
1. `docdb_family_id`
2. `earliest_priority_timestamp`
3. `text_provenance`
4. `is_abstract_fallback`

For `vector_abstract`:
1. `docdb_family_id`
2. `wipo_field`
3. `overall_bp_percentile` or equivalent current enforceability summary field where the backend needs a fast whitespace overlay

## SVR-18: Semantic Match Result Contract

Recommended API contract:
1. `query_id`,
2. `docdb_family_id`,
3. `semantic_similarity_score`,
4. `vector_space`,
5. `representative_doc_id`,
6. `priority_date_relation`,
7. `current_legal_status`,
8. `blocking_power_score`,
9. `match_explanation`.

## Relationship To Existing Notes

This note extends the family-first analytics stack with a semantic retrieval layer.

### Overlaps With Existing Docs

1. `citation-semantics-and-tech-field-mapping-requirements.md`
2. `patent-kind-codes-and-document-lifecycle-representation-requirements.md`
3. `family-level-collapse-and-metric-calculation-requirements.md`
4. `predictive-signals-and-interpretable-forecasting-requirements.md`

### Net-New Additions

1. semantic discovery and comparison workflows,
2. claim-versus-abstract vector-space separation,
3. representative-family embedding hierarchy,
4. chronology-safe semantic retrieval,
5. backend vector-search to deterministic DuckDB join pattern.

## Delivery Priority

### P0

1. family-level embedding collapse,
2. representative text hierarchy,
3. vector-space separation,
4. chronological and legal filtering.

### P1

1. portfolio semantic collision maps,
2. abstract-first overlap maps with blocking-power context,
3. EP-claim-enriched semantic slices where coverage is strong enough.

### P2

1. richer semantic cluster labeling,
2. multilingual retrieval refinement,
3. deeper portfolio-to-portfolio semantic benchmarking.
