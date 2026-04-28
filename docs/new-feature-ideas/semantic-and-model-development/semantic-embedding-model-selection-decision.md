# Semantic Embedding Model Selection Decision

## Purpose

Document the recommended embedding-model policy for PatentIQ semantic runtime promotion.

This note turns the article findings, current corpus reality, and current roadmap constraints into an explicit model-selection decision for:

1. `vector_abstract`
2. `vector_claims`
3. later prior-art specific retrieval lanes

It is intended to guide:

1. Phase 01 semantic runtime promotion
2. Phase 02 semantic reranking and structured summaries
3. later semantic graph and portfolio-semantic intelligence work

## Inputs Considered

### Local PatentIQ state

1. [enriched-semantic-and-model-roadmap-from-2026-sciencedirect-findings.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/new-feature-ideas/semantic-and-model-development/enriched-semantic-and-model-roadmap-from-2026-sciencedirect-findings.md)
2. [enriched-semantic-and-model-implementation-runbook-backlog.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/new-feature-ideas/semantic-and-model-development/enriched-semantic-and-model-implementation-runbook-backlog.md)
3. [phases/phase-01-semantic-runtime-foundation.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/new-feature-ideas/semantic-and-model-development/phases/phase-01-semantic-runtime-foundation.md)
4. [a-survey-on-automated-and-ai-based-tools-for-patent-retrieval.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/ScienceDirect_articles_02Apr2026_07-45-31.440/article_findings/a-survey-on-automated-and-ai-based-tools-for-patent-retrieval.md)
5. [beyond-citations-dynamic-semantic-graph-approach.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/ScienceDirect_articles_02Apr2026_07-45-31.440/article_findings/beyond-citations-dynamic-semantic-graph-approach.md)
6. [patent-intelligence-in-the-age-of-ai.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/ScienceDirect_articles_02Apr2026_07-45-31.440/article_findings/patent-intelligence-in-the-age-of-ai.md)

### Current corpus shape

From [enriched-semantic-and-model-roadmap-from-2026-sciencedirect-findings.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/new-feature-ideas/semantic-and-model-development/enriched-semantic-and-model-roadmap-from-2026-sciencedirect-findings.md):

1. semantic candidate families: `20,295,898`
2. vector sample families: `2,135,310`
3. claim-backed representative rows: `406,639`
4. abstract-backed representative rows: `19,889,259`

Interpretation:

1. PatentIQ is currently an `abstract-dominant` semantic corpus.
2. Claim-space is real and valuable, but still narrow and EP-heavy.
3. One single embedding model for both spaces would be a bad fit.

### External references used

1. Patent retrieval survey / 2026 review:
   - https://www.sciencedirect.com/science/article/pii/S0172219026000086
2. PatentSBERTa article:
   - https://www.sciencedirect.com/science/article/pii/S0040162524003329
3. PatentSBERTa model card:
   - https://huggingface.co/AI-Growth-Lab/PatentSBERTa
4. PatentBERT paper entry:
   - https://huggingface.co/papers/1906.02124
5. SEARCHFORMER article:
   - https://www.sciencedirect.com/science/article/pii/S0172219023000224

## Decision Summary

PatentIQ should use a `dual-model semantic policy`, not one universal embedding model.

### Chosen policy

1. `vector_abstract`
   - use a `strong general retrieval embedding model`
2. `vector_claims`
   - use a `patent-specialized retrieval embedding model`, with `PatentSBERTa-family` as the default starting choice
3. prior-art specific lane
   - reserve `SEARCHFORMER`-style retrieval for a later examiner-style or invalidity-style search track

### Explicit non-decision

PatentIQ should `not` make `PatentBERT` the default runtime embedding model for current semantic search.

## Reasons

## 1. Why `vector_abstract` should use a strong general retrieval model

### Corpus fit

PatentIQ semantic coverage is overwhelmingly abstract-backed.

That means the first production semantic runtime has to optimize for:

1. broad abstract-space discovery
2. family-to-family similarity
3. portfolio-to-portfolio semantic comparison
4. segment exploration and collision discovery

Those are natural-language retrieval problems more than claim-exact legal matching problems.

### Evidence from literature

The 2026 patent retrieval review reports that:

1. transformer retrieval is materially better than keyword-only retrieval
2. retrieval should stay hybrid rather than embedding-only
3. domain-specific models can help
4. but modern general retrieval models can outperform older patent-specific embeddings
5. abstracts are often preferable to claims for general patent search workflows

This lines up with PatentIQ's current data shape and product direction.

### Practical implication

For abstract-space, the best first promoted runtime is:

1. a strong retrieval-focused general embedding model
2. benchmarked directly on PatentIQ Phase 00 fixtures
3. always reranked with legal and chronology overlays

This gives the best fit to the actual corpus PatentIQ has today.

## 2. Why `vector_claims` should use PatentSBERTa-family

### Retrieval shape

Claim-space is not the large-volume default corpus, but it is the highest-value precision lane.

That means the claim model should optimize for:

1. claim-style technical similarity
2. denser semantic comparison
3. better domain sensitivity than generic semantic text encoders

### Evidence from literature

PatentSBERTa is the most natural current fit because:

1. it is sentence-transformer style, which maps directly to ANN-style retrieval workflows
2. it is built specifically for patent similarity and patent semantic search use cases
3. it fits the separate-claims-space architecture already defined in PatentIQ notes

This is also more aligned with the ScienceDirect semantic-graph paper, which explicitly worked with SBERT-style semantic embeddings.

### Practical implication

For `vector_claims`, PatentIQ should:

1. start with a PatentSBERTa-family encoder
2. keep coverage labeling explicit
3. avoid overstating claim-space coverage in the UI and product messaging

## 3. Why `PatentBERT` is not the best runtime default

PatentBERT matters as a domain foundation model, but it is the wrong first production default for PatentIQ semantic runtime.

### Reasons

1. PatentBERT is best known for classification-oriented use, not sentence-level retrieval runtime.
2. It does not naturally fit the `embedding + ANN shortlist + reranking` design as well as a sentence-transformer retrieval model.
3. PatentIQ needs retrieval-first runtime behavior now, not a classification-first encoder baseline.

### Correct place for PatentBERT

PatentBERT remains useful as:

1. a research baseline
2. a possible encoder source for later fine-tuning
3. a comparison point in offline experiments

But it should not be the default production semantic runtime choice.

## 4. Why `SEARCHFORMER` should be a later lane, not the default now

SEARCHFORMER is strong, but it is best suited to a narrower workflow.

### Reasons

1. it is closer to examiner-style prior-art retrieval than to PatentIQ's current broad semantic product scope
2. it is better matched to claim-to-passage or high-recall prior-art search
3. PatentIQ's current semantic product is broader:
   - discovery
   - comparison
   - portfolio intelligence
   - semantic overlays

### Correct place for SEARCHFORMER

Use it later for:

1. prior-art search
2. invalidity-oriented retrieval
3. claim-heavy examiner workflow tooling

It should not be the first general semantic runtime for PatentIQ.

## Final Recommendation

## Production semantic policy

### `vector_abstract`

Use:

1. a strong general retrieval embedding model

Why:

1. the corpus is abstract-dominant
2. general retrieval encoders fit discovery and comparison better here
3. literature does not support forcing a patent-specific encoder everywhere by default

### `vector_claims`

Use:

1. PatentSBERTa-family

Why:

1. retrieval-native design
2. patent-domain fit
3. better match for the current `vector_claims` lane than PatentBERT

### `prior-art / invalidity lane`

Use later:

1. SEARCHFORMER-style retrieval

Why:

1. narrower high-recall examiner workflow
2. not the same objective as PatentIQ's initial product semantic runtime

## Evaluation policy

PatentIQ should not adopt any model only because it is patent-specific.

The actual winner should be chosen by offline evaluation on:

1. [semantic_eval_fixture_registry.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/semantic_eval_fixture_registry.parquet)
2. [semantic_eval_pair_registry.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/semantic_eval_pair_registry.parquet)

The evaluation should compare at minimum:

1. chosen general abstract model
2. PatentSBERTa-family for claims
3. lexical fallback baseline
4. optional PatentBERT baseline

## What to test

For `vector_abstract`:

1. top-k retrieval usefulness on abstract-backed fixtures
2. family-to-family comparison usefulness
3. legal-overlay completeness after retrieval

For `vector_claims`:

1. claim-backed fixture quality
2. same-field semantic compare coherence
3. abstention behavior when claim coverage is unavailable

## Promotion rule

Promote the specialized runtime only when it beats the lexical baseline and respects the documented guardrails:

1. exact-vs-ANN recall agreement at top-20 `>= 0.95`
2. legal-status join completeness `>= 99.0%`
3. chronology join completeness `>= 99.0%`
4. blocking-context completeness `>= 95.0%`
5. vector-space labeling completeness `= 100%`

## What this means for current Phase 01 implementation

Current local Phase 01 should be treated as:

1. runtime contract foundation
2. exact-scan baseline
3. provenance and evaluation scaffolding

It should not be treated as the final promoted semantic model.

The next true semantic promotion step should be:

1. add a real general retrieval encoder for abstracts
2. add PatentSBERTa-family for claims
3. run side-by-side evaluation on Phase 00 fixtures
4. then promote ANN and backend retrieval

## Recommended Next Step

Document the concrete candidate shortlist and benchmark plan:

1. `vector_abstract` candidate shortlist
2. `vector_claims` candidate shortlist
3. offline evaluation procedure
4. promotion thresholds and rollback rules

That should become the next execution note before wiring the promoted runtime into backend serving.
