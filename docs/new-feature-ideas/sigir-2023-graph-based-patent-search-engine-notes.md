# Notes: Building a Graph-Based Patent Search Engine (SIGIR 2023)

## Source
- Local PDF reviewed: `docs/3539618.3591842.pdf`
- DOI: [10.1145/3539618.3591842](https://doi.org/10.1145/3539618.3591842)
- Venue: SIGIR 2023 (short paper), pages 3300-3304
- Accessed/revised: March 6, 2026

## Core Idea
The paper proposes a prior-art search engine that mimics patent examiner behavior by:
1. Parsing patent text into a technical **graph** (parts + relations).
2. Embedding graphs with a **graph neural network**.
3. Training with **examiner citation signals** from patent office search reports.

## System Design
### End-to-end flow
1. Patent corpus is parsed to graphs, then embedded to vectors.
2. User query goes through the same parser + embedding pipeline.
3. Retrieval is nearest-neighbor search in embedding space.
4. Post-filters can apply metadata constraints (date, country, applicant).
5. Non-English queries are machine-translated to English before parsing.

### Parser details
Three-stage parser:
1. Linguistic analysis (SpaCy noun-chunk based feature detection).
2. Relation extraction (meronym, hyponym, and functional relation terms).
3. Graph creation with pruning of contradictory/redundant relations.

Graph semantics:
1. Parent-child edges represent part-of/example-of structure.
2. Additional relation nodes/edges store functional links.
3. Output graph is a directed acyclic graph for model compatibility.

Per-document graph variants:
1. First independent claim only.
2. All claims.
3. Claims + description.

### Model and training
1. Model: modified Tree-LSTM that supports directed acyclic graphs.
2. Node initialization:
   - short feature nodes: weighted average of word embeddings,
   - longer relation snippets: GRU encoder.
3. Word vectors trained with GloVe on patent text.
4. Supervision from examiner citations:
   - X (novelty-destroying),
   - A (state-of-the-art),
   - Y (obviousness-related).
5. Loss: triplet loss.
6. Training triplet:
   - anchor = first independent claim graph of application,
   - positive = cited document description graph,
   - negative = online hard negative (close vector in batch).

## Evaluation
Test setup:
1. In-house holdout due lack of large public prior-art gold set.
2. About 44k X-citations in test data.
3. About 27k unique cited documents as retrieval space.
4. Metric: top-n recall with:
   - top 0.01% (n=3),
   - top 0.1% (n=27).

Results (Table 1):
1. Tree-LSTM: recall@0.01% = **0.543**, recall@0.1% = **0.827**
2. Baseline (GloVe-average, ignores graph structure): **0.333**, **0.639**

Interpretation:
1. Graph structure materially improves retrieval over text-only averaging.
2. Authors note recall values are conservative due to incomplete citation graph (false negatives).

## Paper-Reported Limitations
1. Citation graph incompleteness makes strict recall interpretation difficult.
2. Tree-LSTM DAG constraint forces one-direction edge handling; richer message-passing GNNs could capture more structure.
3. No large human-curated gold benchmark exists for prior-art search.

## Practical Implications for PatentIQ
1. Use structured claim/description graphing for retrieval, not only text embeddings.
2. Train with examiner citation supervision where possible (high-signal labels).
3. Keep separate graph views (claim-only vs full text) for short vs long query behavior.
4. Expose metadata filters post-retrieval (jurisdiction, date, assignee).
5. Evaluate with recall-at-tight-cutoffs and track likely false-negative effects from incomplete citation labels.

