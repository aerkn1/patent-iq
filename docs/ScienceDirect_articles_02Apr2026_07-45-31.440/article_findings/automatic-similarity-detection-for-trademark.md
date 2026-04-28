# Automatic Similarity Detection for Trademark

## Why It Matters For PatentIQ
- The domain is trademark, not patent, but the methodological pattern is highly relevant:
  - embedding-based similarity
  - context-aware hybrid classifier
  - threshold tuning by workflow
  - escalation of uncertain cases

## Key Findings Relevant To PatentIQ
- Hybrid models that combine embeddings with structured context outperform embedding-only approaches.
- Thresholds should be workflow-specific because precision and recall trade off differently depending on user intent.
- Lightweight, more explainable models may still be preferable in some operational settings.
- Retrieval can reduce analyst workload by shortlisting likely conflicts before manual review.

## PatentIQ Implications
- PatentIQ semantic workflows should combine semantic similarity with structured context instead of relying on embedding distance alone.
- Different PatentIQ workflows should have different thresholds:
  - broad discovery
  - family comparison
  - potential threat review
  - whitespace exploration
- A human-escalation lane for uncertain cases is a sound design pattern for PatentIQ semantic and forecast workflows.

## Good Ideas To Reuse
- Confidence-banded routing:
  - high-confidence automated ranking
  - medium-confidence analyst review
  - low-confidence abstention or broader evidence request
- Context-augmented semantic scoring rather than pure cosine similarity.

## Cautions
- Trademark legal similarity is not patent legal similarity.
- The useful transfer here is workflow and model design, not legal semantics.
