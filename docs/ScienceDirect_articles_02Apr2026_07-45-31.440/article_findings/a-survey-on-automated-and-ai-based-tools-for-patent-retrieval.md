# A Survey on Automated and AI-based Tools for Patent Retrieval

## Why It Matters For PatentIQ
- Confirms that patent retrieval should be treated as a high-recall, multi-stage workflow rather than a single-model search problem.
- Repeats a core PatentIQ concern: false negatives are more dangerous than false positives in patent search.
- Supports the current PatentIQ direction of combining semantic, bibliographic, citation, classification, and image or multimodal signals instead of relying on one retrieval mode.

## Key Findings Relevant To PatentIQ
- Patent retrieval remains hard because of legal drafting style, synonym drift, abstract language, translation effects, and fragmented data sources.
- Transformer and semantic retrieval methods materially improve over keyword-only search, but the survey still presents retrieval as hybrid and workflow-driven.
- Hybrid retrieval repeatedly appears as the practical direction:
  - semantic retrieval
  - citation and bibliographic filters
  - classification-aware narrowing
  - multimodal/image support where relevant
- Cross-lingual quality matters. Translation quality directly affects recall.
- Domain-specific models outperform generic search setups, especially in technically dense areas.

## PatentIQ Implications
- PatentIQ semantic search should stay hybrid:
  - vector shortlist first
  - deterministic legal, field, jurisdiction, chronology, and citation overlays after retrieval
- High-recall workflows should be optimized differently from analyst-facing precision workflows.
- Translation and multilingual handling should be treated as an explicit quality dimension, not a hidden preprocessing detail.
- The survey strengthens the case for keeping abstract and claims spaces separate.

## Good Ideas To Reuse
- Retrieval ensembles rather than one canonical search score.
- Recall-sensitive evaluation by workflow, not only overall ranking metrics.
- Query-type-specific retrieval policies:
  - prior-art style search
  - landscape discovery
  - invalidity-style search
  - semantic comparison

## Cautions
- The paper is broad and survey-oriented. It gives strong design direction but not one directly portable PatentIQ model recipe.
- Multimodal and image-based ideas are real but should stay secondary until text-first semantics are fully operational.
