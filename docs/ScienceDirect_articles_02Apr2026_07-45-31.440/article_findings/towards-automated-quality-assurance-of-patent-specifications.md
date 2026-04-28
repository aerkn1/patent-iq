# Towards Automated Quality Assurance of Patent Specifications

## Why It Matters For PatentIQ
- This is highly relevant if PatentIQ wants to grow from analytics into drafting intelligence, filing support, or document QA.
- It is less central to current blocking and semantic search, but strong for future product scope.

## Key Findings Relevant To PatentIQ
- Proposes a multi-dimensional LLM QA framework covering:
  - regulatory compliance
  - technical coherence
  - figure-reference consistency
- Uses module-level defect detection plus integrated revision recommendations.
- Evaluates using balanced accuracy, precision, recall, and F1 because the defect classes are imbalanced.
- Treats citation or legal status indicators as too coarse for document-quality assurance by themselves.

## PatentIQ Implications
- PatentIQ can expand into pre-filing or portfolio hygiene workflows with a modular QA architecture.
- The paper supports a design where document quality is not one opaque score but a set of interpretable defect modules.
- A future PatentIQ drafting assistant should likely separate:
  - legal-form defects
  - technical-consistency defects
  - figure-reference defects

## Good Ideas To Reuse
- Multi-module QA rather than one broad LLM evaluator.
- Structured defect inventory with severity and evidence references.
- Balanced metrics and abstention policies for sparse-risk classes.

## Cautions
- This scope is adjacent to, not identical with, PatentIQ's current analytics core.
- It should be treated as a future expansion area after semantic search and forecast models are operational and stable.
