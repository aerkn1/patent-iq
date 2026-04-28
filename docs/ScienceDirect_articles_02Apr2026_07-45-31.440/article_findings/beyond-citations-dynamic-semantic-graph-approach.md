# Beyond Citations: A Dynamic Semantic Graph Approach for Early-stage Patent Valuation

## Why It Matters For PatentIQ
- This is one of the most directly relevant articles in the set for PatentIQ forecasting and early-value analytics.
- It attacks the exact problem PatentIQ cares about: how to estimate importance before forward citations mature.

## Key Findings Relevant To PatentIQ
- The paper proposes a zero-lag valuation idea by combining:
  - SBERT semantic embeddings
  - dynamic graph construction
  - graph neural modeling
  - structural importance rather than waiting for mature citation counts
- It explicitly argues that document-only NLP is topology-blind.
- It uses semantic graph structure to recover latent technological relationships when citation data is sparse or delayed.
- It also states that abstracts are a pragmatic high-SNR input, even though claims would better capture legal scope.

## PatentIQ Implications
- PatentIQ should not rely only on citation-based future influence for early-stage asset assessment.
- A semantic-topology feature family is justified for:
  - family future citation forecast
  - hidden-gem discovery
  - early-stage asset ranking
  - portfolio contributor detection
- The article supports a future PatentIQ model layer like:
  - semantic centrality
  - local novelty versus neighborhood density
  - bridge or betweenness features in a family semantic graph

## Good Ideas To Reuse
- Add graph-derived features to forecast models:
  - semantic degree
  - local clustering coefficient
  - bridge score
  - community centrality
- Use semantic topology as an early proxy before citations accumulate.
- Compare performance against pure citation, pure semantic, and fused models.

## Cautions
- The article uses abstract-first semantics. That aligns with PatentIQ's current data reality, but it also limits legal-scope fidelity.
- This should enrich early-value modeling, not replace legal and citation evidence.
