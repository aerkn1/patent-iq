# Section 05. Semantic Search, Vector Assets, And Compare Intelligence

## Table Of Contents

1. [Purpose Of This Section](#purpose-of-this-section)
2. [What Counts As Semantic Search And Compare Intelligence In PatentIQ](#what-counts-as-semantic-search-and-compare-intelligence-in-patentiq)
3. [Primary Data Inputs, Artifacts, And Why They Exist](#primary-data-inputs-artifacts-and-why-they-exist)
4. [Semantic Corpus Policy And Boundary Conditions](#semantic-corpus-policy-and-boundary-conditions)
   - [1. Representative text hierarchy](#1-representative-text-hierarchy)
   - [2. Why the corpus is split into abstract and claim spaces](#2-why-the-corpus-is-split-into-abstract-and-claim-spaces)
   - [3. Current corpus scale and coverage truth](#3-current-corpus-scale-and-coverage-truth)
5. [How The ETL Builds Semantic Vector Assets](#how-the-etl-builds-semantic-vector-assets)
   - [1. Semantic base materialization](#1-semantic-base-materialization)
   - [2. Actual fields embedded and carried forward](#2-actual-fields-embedded-and-carried-forward)
   - [3. Encoder runtime selection](#3-encoder-runtime-selection)
   - [4. Query registry and evaluation fixtures](#4-query-registry-and-evaluation-fixtures)
   - [5. Merge, manifests, and promoted payload packaging](#5-merge-manifests-and-promoted-payload-packaging)
   - [6. ANN snapshots and exact-vs-ANN audit logic](#6-ann-snapshots-and-exact-vs-ann-audit-logic)
   - [7. Aimed quality gates versus obtained values](#7-aimed-quality-gates-versus-obtained-values)
6. [How Semantic Assets Are Wired Into The Backend](#how-semantic-assets-are-wired-into-the-backend)
   - [1. Artifact resolution and serving-snapshot boundary](#1-artifact-resolution-and-serving-snapshot-boundary)
   - [2. Semantic repository behavior](#2-semantic-repository-behavior)
   - [3. Live semantic service contracts](#3-live-semantic-service-contracts)
   - [4. Current runtime truth](#4-current-runtime-truth)
7. [How The Semantic Workspace Is Wired In Frontend V2](#how-the-semantic-workspace-is-wired-in-frontend-v2)
   - [1. Route and page shape](#1-route-and-page-shape)
   - [2. User controls and search flow](#2-user-controls-and-search-flow)
   - [3. What the current page actually renders](#3-what-the-current-page-actually-renders)
   - [4. Important current gap: compare payload exists, active semantic page is still search-first](#4-important-current-gap-compare-payload-exists-active-semantic-page-is-still-search-first)
8. [Compare Intelligence: The Logic Behind Family And Portfolio Compare](#compare-intelligence-the-logic-behind-family-and-portfolio-compare)
   - [1. Why PatentIQ does not use one blended compare score](#1-why-patentiq-does-not-use-one-blended-compare-score)
   - [2. Family compare logic](#2-family-compare-logic)
   - [3. Portfolio compare logic](#3-portfolio-compare-logic)
   - [4. Time-slice compare logic](#4-time-slice-compare-logic)
9. [Metric, API, And UI Traceability](#metric-api-and-ui-traceability)
10. [Current Claim Boundary](#current-claim-boundary)
11. [Key Takeaways](#key-takeaways)

## Purpose Of This Section

Sections 01 through 04 explained the layered data foundation, backend and frontend architecture, and the predictive model layer. This section covers the other intelligence-heavy part of PatentIQ:

1. semantic search and semantic comparison,
2. vector asset generation and auditability,
3. family and portfolio compare logic,
4. the rules that prevent the UI from overstating fuzzy similarity as legal truth.

Primary implementation references:

1. `docs/next-phase-v2/16-patentiq-v2-semantic-search-and-comparison-flow-and-guardrails.md:1-259`
2. `docs/next-phase-v2/71-patentiq-v2-peer-banding-and-compare-ranking-policy.md:1-255`
3. `docs/next-phase-v2/ui-contracts/34-patentiq-v2-compare-and-semantic-workspace-contract.md:1-260`
4. `etl/src/patentiq_etl/semantic/run.py:111-1585`
5. `etl/src/patentiq_etl/serving/run.py:829-930`
6. `backend_v2/application/services/semantic.py:10-329`
7. `backend_v2/application/services/compare.py:526-1520`
8. `frontend_v2/components/semantic/semantic-workspace.tsx:155-638`
9. `frontend_v2/components/compare/family-compare-workspace.tsx:29-420`
10. `frontend_v2/components/compare/portfolio-compare-workspace.tsx:30-420`

## What Counts As Semantic Search And Compare Intelligence In PatentIQ

This section treats the following as one connected intelligence stack:

1. the ETL logic that derives one-row-per-family semantic context and vector payloads,
2. the manifest and ANN audit artifacts under `etl/data/vectors/`,
3. the serving snapshot packaging that exposes `semantic_serving.duckdb`,
4. the backend semantic endpoints under `/api/v1/semantic/*`,
5. the family and portfolio compare services under `/api/v1/compare/*`,
6. the frontend compare workspaces that present those results to users.

This grouping is deliberate. In PatentIQ, "compare intelligence" is not a separate disconnected feature. It is where:

1. semantic similarity,
2. blocking metrics,
3. legal durability,
4. citation heritage,
5. peer-relative bands,
6. time-slice deltas

meet in analyst-facing workflows.

Implementation references:

1. `frontend_v2/app/(workspace)/compare/page.tsx:6-27`
2. `backend_v2/api/v1/semantic.py:6-46`
3. `backend_v2/api/v1/compare.py:11-84`

## Primary Data Inputs, Artifacts, And Why They Exist

The semantic and compare layers do not read directly from raw PATSTAT, DOCDB, or EPAB tables at request time. They consume curated Silver, Gold, and serving artifacts because these workflows need family-first collapse rules, legal overlays, provenance, and comparison-safe semantics already attached.

The most important inputs are:

| Artifact or mart | Why it exists in this stack | Main consumers |
| --- | --- | --- |
| `silver_family_text_representative.parquet` | one deterministic representative text per family, with claim and abstract fallback columns | semantic ETL |
| `silver_semantic_sampling_eligibility.parquet` | marks semantic candidates and vector-sample eligibility | semantic ETL |
| `gold_semantic_match_context.parquet` | one-row-per-family semantic context for owner, field, blocking, and OECD overlay | semantic ETL, semantic serving |
| `silver_family_status_pt.parquet` | current family legal status for semantic result enrichment | semantic ETL, backend semantic |
| `gold_family_summary.parquet` | family-level current metrics and chronology anchors | semantic ETL, compare service, family compare |
| `gold_family_blocking_power.parquet` | rebuilt family blocking score | semantic ETL, semantic result enrichment, compare |
| `gold_portfolio_summary.parquet` | owner-level peer-compare metrics | portfolio compare |
| `gold_portfolio_forecast_summary.parquet` | future-citation rollups that feed compare outlook panels | portfolio compare |
| `gold_family_compare_pit.parquet` | point-in-time compare-safe family history | family time-slice compare, serving packaging |
| `core_serving.duckdb` and `semantic_serving.duckdb` | backend-ready snapshots that make runtime access stable across local and Azure-style deployments | backend_v2 |

Implementation references:

1. `etl/src/patentiq_etl/gold/build_gold.py:2594-2617`
2. `etl/src/patentiq_etl/semantic/run.py:880-885`
3. `etl/src/patentiq_etl/serving/run.py:834-899`
4. `docs/new-feature-ideas/semantic-and-model-development/phases/phase-01-semantic-runtime-foundation.md:7-32`
5. `docs/next-phase-v2/ui-contracts/34-patentiq-v2-compare-and-semantic-workspace-contract.md:26-43`

## Semantic Corpus Policy And Boundary Conditions

### 1. Representative text hierarchy

The semantic corpus is intentionally deterministic. PatentIQ does not embed every publication in a family and does not mix multiple unclear text variants at request time.

The hierarchy is:

1. English EP granted `B` Claim 1 from EPAB,
2. otherwise English PATSTAT abstract fallback.

This rule exists because the semantic MVP is intentionally bounded to deterministic representative text with explicit provenance and fallback behavior. The project therefore narrows its product claim from "global claim-faithful semantic truth" to "family discovery and comparison with provenance and caveats."

Implementation references:

1. `docs/next-phase-v2/16-patentiq-v2-semantic-search-and-comparison-flow-and-guardrails.md:23-30`
2. `docs/next-phase-v2/16-patentiq-v2-semantic-search-and-comparison-flow-and-guardrails.md:236-250`

### 2. Why the corpus is split into abstract and claim spaces

PatentIQ keeps `vector_abstract` and `vector_claims` physically separate. That is not a UI preference; it is a safety rule.

The reasoning is:

1. abstract-backed discovery has much broader coverage,
2. claim-backed similarity is narrower but more precise,
3. blending both into one unlabeled score would hide provenance and coverage limits,
4. downstream legal or strategic interpretation changes depending on which space produced the hit.

The chosen model policy follows the same split:

1. `vector_abstract` uses a strong general retrieval encoder,
2. `vector_claims` uses a patent-specialized retrieval encoder,
3. lexical fallback remains the deterministic local baseline.

Implementation references:

1. `docs/new-feature-ideas/semantic-and-model-development/semantic-embedding-model-selection-decision.md:58-70`
2. `docs/new-feature-ideas/semantic-and-model-development/semantic-embedding-model-selection-decision.md:77-143`
3. `etl/src/patentiq_etl/semantic/run.py:133-150`
4. `etl/src/patentiq_etl/semantic/run.py:1305-1319`

### 3. Current corpus scale and coverage truth

The current semantic stack has to be read with two separate scale numbers in mind:

1. the full semantic context universe,
2. the currently promoted searchable vector payload.

Documented corpus-shape numbers in the semantic model-selection note are:

1. semantic candidate families: `20,295,898`,
2. vector-sample families: `2,135,310`,
3. claim-backed representative rows: `406,639`,
4. abstract-backed representative rows: `19,889,259`.

The Gold build manifest also records `gold_semantic_match_context_rows = 20,295,898`, which confirms the one-row-per-family semantic context mart exists at that wider denominator scale.

Current searchable payload truth is narrower:

1. claims payload: `406,639`,
2. abstract payload: `168,924`.

That abstract payload count is intentionally caveated in the repository as an MVP partial-corpus salvage artifact rather than a final full abstract release.

Implementation references:

1. `docs/new-feature-ideas/semantic-and-model-development/semantic-embedding-model-selection-decision.md:30-44`
2. `etl/manifests/stats/gold.json:7-24`
3. `etl/manifests/stats/semantic-ann.json:4-14`
4. `docs/new-feature-ideas/semantic-and-model-development/phase-01-mvp-partial-corpus-operating-note-2026-04-06.md:13-20`
5. `docs/new-feature-ideas/semantic-and-model-development/phase-01-mvp-partial-corpus-operating-note-2026-04-06.md:48-109`

## How The ETL Builds Semantic Vector Assets

### 1. Semantic base materialization

The semantic ETL first materializes a reusable `_tmp_semantic_base.parquet`. This is the crucial join stage that converts multiple marts into one encoding-ready base table.

The base build joins:

1. representative text,
2. semantic eligibility flags,
3. Gold semantic match context,
4. family status,
5. family summary,
6. family blocking power.

It only keeps rows where:

1. `is_semantic_candidate = true`,
2. `is_in_vector_sample = true`.

This is why the vector payload is smaller than the broader semantic context universe. The searchable corpus is an explicitly governed subset, not an accidental omission.

Implementation references:

1. `etl/src/patentiq_etl/semantic/run.py:1090-1142`

### 2. Actual fields embedded and carried forward

The semantic ETL does not write naked embeddings. Each vector row carries business and audit context alongside the embedding:

1. `docdb_family_id`,
2. representative application and publication ids,
3. representative stage,
4. `vector_space`,
5. `queryable_text`,
6. token count,
7. `text_provenance`,
8. `text_source_type`,
9. `is_abstract_fallback`,
10. earliest priority date,
11. primary WIPO field,
12. harmonized owner name,
13. family UI blocking power,
14. OECD quality percentile,
15. family composite status,
16. embedding model id and version,
17. embedding runtime,
18. language and machine-translation flags,
19. corpus snapshot,
20. the embedding vector itself.

This is why semantic hits can immediately be enriched in the UI without re-running raw-source joins.

Implementation references:

1. `etl/src/patentiq_etl/semantic/run.py:218-243`
2. `etl/src/patentiq_etl/semantic/run.py:1145-1219`

### 3. Encoder runtime selection

The ETL chooses between two runtime modes:

1. promoted dual runtime:
   - abstract encoder: `BAAI/bge-m3`
   - claim encoder: `AI-Growth-Lab/PatentSBERTa`
   - runtime label: `promoted_dual_runtime_dense_only_v1`
2. fallback runtime:
   - lexical hashed embedding for both spaces
   - runtime label: `lexical_hash_exact_scan_v1`

The fallback path is not marketing. It exists for deterministic local regression and for environments where the promoted dense models are not enabled.

The lexical fallback itself is implemented as a normalized hashed token-and-trigram vector, while dense mode uses `SentenceTransformer` encoders with normalized embeddings.

Implementation references:

1. `etl/src/patentiq_etl/semantic/run.py:111-130`
2. `etl/src/patentiq_etl/semantic/run.py:133-196`
3. `docs/new-feature-ideas/semantic-and-model-development/semantic-embedding-candidate-shortlist-and-benchmark-plan.md:51-147`

### 4. Query registry and evaluation fixtures

PatentIQ does not leave semantic evaluation informal. Phase 0 writes two evaluation registries:

1. `semantic_eval_fixture_registry.parquet`
2. `semantic_eval_pair_registry.parquet`

The build manifest records:

1. `600` fixture rows,
2. `144` pair rows,
3. one frozen `ml_split_registry` with `17,633,618` rows.

Semantic ETL then encodes the fixture texts into `vec_query_registry.parquet`, preserving:

1. fixture group,
2. workflow type,
3. anchor family,
4. vector space,
5. expected behavior,
6. whether current-threat display is allowed,
7. the model/runtime metadata used to encode the query.

This matters because ANN audit and later candidate benchmarking are anchored to a stored query registry rather than ad hoc manual probing.

Implementation references:

1. `etl/manifests/stats/ml-phase0-foundation.json:4-9`
2. `etl/src/patentiq_etl/semantic/run.py:1222-1302`
3. `docs/new-feature-ideas/semantic-and-model-development/semantic-embedding-candidate-shortlist-and-benchmark-plan.md:30-50`
4. `docs/new-feature-ideas/semantic-and-model-development/semantic-embedding-candidate-shortlist-and-benchmark-plan.md:183-252`

### 5. Merge, manifests, and promoted payload packaging

The semantic build does not jump directly from one encode loop to a single opaque file. It has three layers of packaging:

1. phase or bucket chunk files,
2. merged final vector payloads,
3. manifest and query metadata files.

`run_semantic_merge()` and `run_semantic()` both refresh:

1. `vec_family_embeddings_claims.parquet`,
2. `vec_family_embeddings_abstracts.parquet`,
3. `vec_embedding_manifest.json`,
4. `vec_ann_index_manifest.json`,
5. `vec_query_registry.parquet`,
6. `vec_query_registry.json`.

The embedding manifest records:

1. release id,
2. runtime label,
3. embedding device,
4. model ids and versions,
5. corpus snapshot,
6. vector sample percent,
7. payload paths,
8. payload counts,
9. query registry count.

Implementation references:

1. `etl/src/patentiq_etl/semantic/run.py:990-1087`
2. `etl/src/patentiq_etl/semantic/run.py:1305-1585`

### 6. ANN snapshots and exact-vs-ANN audit logic

ANN is built after the dense payloads exist. PatentIQ creates separate HNSW indexes for claims and abstracts, with distinct configuration defaults for each space.

The ANN audit logic is explicit:

1. exact top-k neighbors are computed from matrix similarity,
2. ANN top-k neighbors are computed from HNSW,
3. recall is measured as overlap between exact and ANN top-k sets,
4. top-1 agreement is also recorded,
5. query-anchor coverage is tracked separately for each vector space,
6. corpus-sample audits are also run, not only registry-anchor audits.

The exact cosine similarity logic used in backend comparison is also explicit. In the repository path it is:

1. DuckDB `list_cosine_similarity(embedding, anchor_embedding)` for live search ranking,
2. manual cosine similarity `dot(left, right) / (||left|| * ||right||)` for pair compare.

Implementation references:

1. `etl/src/patentiq_etl/semantic/run.py:451-486`
2. `etl/src/patentiq_etl/semantic/run.py:489-621`
3. `etl/src/patentiq_etl/semantic/run.py:624-843`
4. `backend_v2/infrastructure/repositories/semantic_repository.py:208-234`
5. `backend_v2/infrastructure/repositories/semantic_repository.py:261-278`

### 7. Aimed quality gates versus obtained values

The documented promotion thresholds for semantic runtime are:

1. vector-space labeling completeness `= 100%`,
2. legal-status join completeness `>= 99.0%`,
3. chronology join completeness `>= 99.0%`,
4. blocking-context completeness `>= 95.0%`,
5. exact-vs-ANN recall agreement at top-20 `>= 0.95`,
6. duplicate family rate `<= 1.0%`.

The strongest repository-backed obtained values currently visible are:

1. claim payload count: `406,639`,
2. abstract payload count: `168,924`,
3. claim embedding dimension: `768`,
4. abstract embedding dimension: `1024`,
5. claim exact-vs-ANN recall@10: `0.989062`,
6. abstract exact-vs-ANN recall@10: `1.0`,
7. claim corpus-sample exact-vs-ANN recall@10: `0.992188`,
8. abstract corpus-sample exact-vs-ANN recall@10: `0.994531`,
9. query-anchor claim coverage: `1.0`,
10. query-anchor abstract coverage: `0.008`.

The correct interpretation is nuanced:

1. the claim payload is strong enough to support claim-space neighbor search within its narrower EPAB-backed scope,
2. the abstract ANN quality looks strong on the partial corpus that was actually promoted,
3. abstract coverage remains intentionally caveated because the searchable abstract payload is still only a bounded MVP subset of the larger semantic universe.

Implementation references:

1. `docs/new-feature-ideas/semantic-and-model-development/phases/phase-01-semantic-runtime-foundation.md:71-84`
2. `docs/new-feature-ideas/semantic-and-model-development/semantic-embedding-candidate-shortlist-and-benchmark-plan.md:253-302`
3. `etl/manifests/stats/semantic-ann.json:4-14`
4. `docs/new-feature-ideas/semantic-and-model-development/phase-01-mvp-partial-corpus-operating-note-2026-04-06.md:70-109`

## How Semantic Assets Are Wired Into The Backend

### 1. Artifact resolution and serving-snapshot boundary

Backend V2 uses an `ArtifactLocator` to resolve serving snapshots from either:

1. local filesystem manifests,
2. cached remote artifacts in Azure-compatible mode.

For semantic serving, the canonical serving snapshot name is `semantic_serving.duckdb`. The serving build packages `gold_semantic_match_context.parquet` into that semantic snapshot, and the artifact locator can resolve it from `serving_snapshot_manifest.json` without route code needing to know raw parquet paths.

Implementation references:

1. `etl/src/patentiq_etl/serving/run.py:829-899`
2. `backend_v2/infrastructure/artifacts/locator.py:29-55`
3. `backend_v2/infrastructure/artifacts/locator.py:129-174`
4. `backend_v2/tests/test_artifact_locator.py:81-109`

### 2. Semantic repository behavior

The backend semantic repository reads from two kinds of assets:

1. vector payload Parquet files for actual semantic ranking,
2. semantic serving DuckDB for semantic-context denominator counts.

This distinction is important. The live repository does not yet read ANN indexes for request-time search. Instead it:

1. resolves the active vector payload path by space,
2. checks whether a family exists in claims or abstract payloads,
3. pulls the anchor row and its embedding,
4. ranks candidate rows with `list_cosine_similarity`,
5. optionally filters by same field or different owner,
6. reads `semantic_match_context` from `semantic_serving.duckdb` only to compute coverage totals.

Implementation references:

1. `backend_v2/infrastructure/repositories/semantic_repository.py:14-29`
2. `backend_v2/infrastructure/repositories/semantic_repository.py:30-68`
3. `backend_v2/infrastructure/repositories/semantic_repository.py:70-117`
4. `backend_v2/infrastructure/repositories/semantic_repository.py:170-234`

### 3. Live semantic service contracts

The semantic service exposes three live contract families:

1. family-anchor search,
2. family-anchor suggestions,
3. family-to-family semantic compare.

For search it returns:

1. vector space,
2. anchor identity,
3. summary cards,
4. query context,
5. result rows,
6. pagination,
7. artifact sources,
8. coverage metadata,
9. caveats.

For compare it returns:

1. left and right families,
2. abstract similarity and claim similarity as separate cards,
3. compare rows that never blend the spaces,
4. detail panels per family,
5. candidate-only support level and semantic caveats.

The most important safety rules in the live service are:

1. exact ranking is explicitly labeled as the active runtime,
2. free-text semantic query encoding is explicitly marked as not yet exposed,
3. abstract-space discovery is caveated as fallback-heavy,
4. semantic compare is explicitly "discovery signal, not legal proof."

Implementation references:

1. `backend_v2/application/services/semantic.py:14-197`
2. `backend_v2/application/services/semantic.py:225-329`
3. `backend_v2/api/v1/semantic.py:10-46`
4. `backend_v2/tests/test_semantic_service.py:153-209`
5. `backend_v2/tests/test_semantic_endpoints.py:11-146`

### 4. Current runtime truth

The live semantic runtime should be read as follows:

1. semantic ETL has already built dense payloads, manifests, query registries, and ANN snapshots,
2. backend V2 currently serves exact cosine ranking rather than ANN-backed request-time search,
3. family-anchor search is live,
4. family-to-family semantic compare exists in backend contract form,
5. free-text query encoding is planned but not yet active in the live workspace.

This is why the correct claim is "artifact-complete and partially productized" rather than "all originally planned semantic modes are already fully exposed."

Implementation references:

1. `backend_v2/application/services/semantic.py:96-145`
2. `docs/next-phase-v2/75-patentiq-v2-compare-ui-and-semantic-runtime-plan.md:43-76`
3. `docs/next-phase-v2/75-patentiq-v2-compare-ui-and-semantic-runtime-plan.md:150-182`

## How The Semantic Workspace Is Wired In Frontend V2

### 1. Route and page shape

Frontend V2 exposes semantic work through the compare workspace group:

1. `/compare`
2. `/compare/semantic`

The compare landing page explicitly presents semantic as its own lane alongside family compare and portfolio compare, with the current message that the workspace is:

1. family-anchor,
2. abstract-vs-claim explicit,
3. exact-vector-runtime,
4. caveat-heavy by design.

Implementation references:

1. `frontend_v2/app/(workspace)/compare/page.tsx:6-27`
2. `frontend_v2/app/(workspace)/compare/semantic/page.tsx:1-14`

### 2. User controls and search flow

The live semantic workspace is URL-driven. It reads:

1. `familyId`,
2. `space`,
3. `sameFieldOnly`,
4. `excludeSameOwner`

from query parameters, fetches suggestions as the user types, and then calls the semantic family-anchor search API when a family is selected.

The UI controls make the scope boundary visible:

1. `Abstract scope` is presented as broader discovery,
2. `Claim scope` is presented as narrower similarity,
3. same-field filtering is optional,
4. same-owner exclusion is optional.

Implementation references:

1. `frontend_v2/components/semantic/semantic-workspace.tsx:155-250`
2. `frontend_v2/components/semantic/semantic-workspace.tsx:304-405`
3. `frontend_v2/lib/api/semantic-v2.ts:253-316`

### 3. What the current page actually renders

The current semantic page renders four main evidence blocks:

1. search controls,
2. anchor-and-scope context,
3. ranked semantic neighbor cards,
4. methodology and caveat disclosure.

The result cards expose exactly the kind of context the semantic governance notes require:

1. family id,
2. owner,
3. primary field,
4. semantic similarity score,
5. status,
6. abstract-fallback badge when applicable,
7. blocking score,
8. OECD percentile,
9. representative text excerpt,
10. a deep link to the family page.

The page also computes result-composition summaries such as field mix and top-owner concentration for the currently ranked set.

Implementation references:

1. `frontend_v2/components/semantic/semantic-workspace.tsx:415-633`

### 4. Important current gap: compare payload exists, active semantic page is still search-first

The repository already contains a typed frontend client for `GET /api/v1/semantic/families/compare`, and backend tests confirm that contract. However, by inspection the active semantic workspace imports only:

1. `fetchFamilyAnchorSemanticSearch`,
2. `fetchSemanticFamilySuggestions`

and does not yet render the typed family semantic compare payload.

This means the current frontend truth is:

1. semantic search is live,
2. semantic compare exists in backend and typed-client form,
3. the active UI is still search-first rather than full compare-rollup-first.

That separates implemented contracts from the currently rendered product surface.

Implementation references:

1. `frontend_v2/components/semantic/semantic-workspace.tsx:11-18`
2. `frontend_v2/lib/api/semantic-v2.ts:318-337`
3. `backend_v2/tests/test_semantic_endpoints.py:106-146`

Inference note:
The statement that the active page is still search-first is based on code inspection of the live page and import graph, not on a separate design note.

## Compare Intelligence: The Logic Behind Family And Portfolio Compare

### 1. Why PatentIQ does not use one blended compare score

PatentIQ compare intentionally refuses a single blended "winner score" because different comparison questions require different denominators and peer logic.

The compare policy explicitly separates:

1. entity peer ranking,
2. market-slice ranking,
3. mass metrics,
4. density metrics,
5. crown-jewel metrics,
6. family cohort logic,
7. portfolio peer-bucket logic.

This is the reason the compare UI can stay honest when comparing:

1. two families from different cohorts,
2. a small focused portfolio against a giant incumbent,
3. one entity across two historical years.

Implementation references:

1. `docs/next-phase-v2/71-patentiq-v2-peer-banding-and-compare-ranking-policy.md:26-99`
2. `docs/next-phase-v2/71-patentiq-v2-peer-banding-and-compare-ranking-policy.md:102-206`

### 2. Family compare logic

Family compare uses three explicit lenses:

1. blocking posture,
2. legal durability,
3. citation heritage.

Each lens has its own cohort logic:

1. blocking posture compares within primary WIPO field,
2. legal durability compares within field plus lifecycle/status cohort,
3. citation heritage compares within priority-year plus field.

The winner logic is also conditional:

1. if both families are in the same cohort, PatentIQ compares peer percentiles directly,
2. if they are in different cohorts, PatentIQ falls back to band-first logic rather than pretending the percentiles are directly comparable.

Citation heritage also has a repository-backed fallback rule:

1. use weighted forward-citation history when available,
2. otherwise fall back to the OECD quality proxy,
3. add a caveat to the response.

Implementation references:

1. `backend_v2/application/services/compare.py:526-779`
2. `backend_v2/application/services/compare.py:811-959`
3. `backend_v2/tests/test_compare_service.py:553-599`

### 3. Portfolio compare logic

Portfolio compare uses three different lenses:

1. mass,
2. density,
3. crown-jewel strength.

The peer denominator is `portfolio_family_count_within_mega_cluster`, which is mapped into canonical peer buckets:

1. `1`,
2. `2_5`,
3. `6_20`,
4. `21_100`,
5. `101_500`,
6. `501_plus`.

Band thresholds are percentile-based:

1. `0-25` = `low`,
2. `25-50` = `medium`,
3. `50-75` = `high`,
4. `75-100` = `very_high`.

The service then maps those percentile bands into client-facing labels such as:

1. `Outsize Footprint`,
2. `Dense`,
3. `Dominant Arsenal`.

There is also a critical suppression rule:

1. density compare is suppressed if either portfolio has fewer than `5` in-scope families.

This is exactly the sort of safety logic the system needs. It is designed to avoid visually confident but statistically weak comparisons.

Implementation references:

1. `docs/next-phase-v2/71-patentiq-v2-peer-banding-and-compare-ranking-policy.md:54-204`
2. `backend_v2/application/services/compare.py:57-120`
3. `backend_v2/application/services/compare.py:961-1211`
4. `backend_v2/tests/test_compare_service.py:498-551`

### 4. Time-slice compare logic

PatentIQ compare is not limited to entity A vs entity B. The compare service also supports time-slice comparison for:

1. one family across two years,
2. one portfolio across two years.

This matters because many patent-intelligence questions are trajectory questions:

1. is blocking strength rising or falling,
2. is legal durability improving,
3. is field breadth expanding,
4. is concentration increasing.

The family and portfolio compare workspaces both expose dedicated tabs and query-state logic for this historical compare mode, and the backend emits separate `compare_mode="timeslice"` responses rather than overloading entity compare payloads.

Implementation references:

1. `backend_v2/application/services/compare.py:1435-1520`
2. `backend_v2/tests/test_compare_service.py:601-711`
3. `frontend_v2/components/compare/family-compare-workspace.tsx:29-41`
4. `frontend_v2/components/compare/family-compare-workspace.tsx:346-420`
5. `frontend_v2/components/compare/portfolio-compare-workspace.tsx:30-42`
6. `frontend_v2/components/compare/portfolio-compare-workspace.tsx:205-264`

## Metric, API, And UI Traceability

The main traceability chain for this section is:

| Business concept | Upstream source | Backend contract | Frontend surface |
| --- | --- | --- | --- |
| semantic searchable text | `silver_family_text_representative` -> vector payloads | `/api/v1/semantic/families/search` | `/compare/semantic` |
| semantic coverage denominator | `gold_semantic_match_context` -> `semantic_serving.duckdb` | semantic search `coverage` metadata | scope card and methodology notes |
| abstract vs claim support | vector payload existence by family | semantic repository support check | scope switch and unsupported-space errors |
| semantic similarity | exact cosine over embeddings | semantic result rows and compare rows | ranked semantic neighbors, future compare rollup path |
| family blocking compare | `gold_family_blocking_power` + compare serving | `/api/v1/compare/families` | family compare overview |
| family legal durability compare | compare serving percentile cohorts | `/api/v1/compare/families` | family compare overview and outlook tabs |
| family citation heritage compare | compare mart weighted citations or OECD proxy | `/api/v1/compare/families` | family compare overview |
| portfolio peer bands | `gold_portfolio_summary` + peer context | `/api/v1/compare/portfolios` | portfolio compare summary cards |
| density suppression | portfolio family-count rule in service | `/api/v1/compare/portfolios` caveats and row flags | portfolio compare lens rendering |
| top-family support previews | portfolio family bridge and forecast contributors | `/api/v1/compare/portfolios` support rows | portfolio compare evidence tab |

Implementation references:

1. `backend_v2/api/v1/semantic.py:10-46`
2. `backend_v2/api/v1/compare.py:15-84`
3. `frontend_v2/lib/api/semantic-v2.ts:253-337`
4. `frontend_v2/lib/api/compare-v2.ts:132-318`

## Current Claim Boundary

The technically correct statement is:

1. PatentIQ already contains a serious semantic ETL and audit stack, not a mock placeholder,
2. the semantic runtime is family-first, provenance-aware, and explicitly split into abstract and claim spaces,
3. the live backend currently serves exact cosine ranking, even though ANN assets and audits already exist,
4. semantic search is live in the current frontend workspace,
5. semantic compare exists as backend and typed-client contract but is not yet fully rendered as the dominant active semantic UI experience,
6. compare intelligence for families and portfolios is already live and intentionally guarded by cohort logic, peer buckets, suppression rules, and evidence rows.

What this section does not claim:

1. that PatentIQ currently offers universal claim-faithful cross-jurisdiction semantic search,
2. that the current searchable abstract payload equals the full semantic-context universe,
3. that family and portfolio compare use one universal global score,
4. that semantic similarity alone is treated as legal proof.

## Key Takeaways

1. PatentIQ's semantic layer is not just embeddings. It is a governed pipeline with representative-text selection, candidate scoping, manifests, query registries, ANN audits, provenance fields, and serving packaging.
2. The project explicitly separates broad abstract discovery from narrower claim-backed similarity, and that split is visible in ETL, backend contracts, and frontend controls.
3. The compare layer is analytically stronger than a generic dashboard compare because it uses cohort-aware family logic, peer-bucketed portfolio logic, suppression rules, and evidence rows instead of fake cross-scale precision.
4. The current implementation is honest about its boundary: semantic search is operational, semantic compare contracts exist, ANN assets are audited, and some originally planned semantic surfaces remain intentionally caveated or still search-first in the UI.
