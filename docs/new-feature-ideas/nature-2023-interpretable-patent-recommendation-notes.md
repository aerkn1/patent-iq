# Notes: Interpretable Patent Recommendation with Knowledge Graph and Deep Learning

## Source
- Article: [Interpretable patent recommendation with knowledge graph and deep learning](https://www.nature.com/articles/s41598-023-28766-y)
- Journal: *Scientific Reports* (2023), 13:2586
- DOI: `10.1038/s41598-023-28766-y`
- Open full text mirror used for tables/details: [PMC9929065](https://pmc.ncbi.nlm.nih.gov/articles/PMC9929065/)
- Accessed: March 6, 2026

## What the Paper Tries to Solve
Patent transfer recommendation systems often optimize relevance only, but ignore:
1. Patent quality signals.
2. Explainability of why a patent is recommended to a company.

The paper proposes an interpretable hybrid recommender that combines:
1. A patent knowledge graph.
2. Deep neural network scoring.
3. Layer-wise relevance propagation (LRP) for feature-level explanations.

## Method Summary
### 1) Knowledge graph construction
Entity types: companies, patents, countries, inventors, claims, categories, terms.  
Relations include transfer, citation, protected country, inventor, category, claim, and term links.

### 2) Feature extraction
Two feature families are used:
1. **Connectivity features** (meta-path based relevance between company and patent).
2. **Quality features** (8 indicators): forward citations (recency-adjusted), backward citations, claims count, patent scope, previous transfers, family size, generality, originality.

### 3) Recommendation + explanation
1. DNN predicts company-patent match probability.
2. LRP back-propagates relevance to input features to explain each recommendation.

## Experimental Setup
1. Data from USPTO assignment + PatentsView.
2. 500 companies sampled (each with >=50 assignment records).
3. For each company: first 50% purchased patents treated as known history; remainder used as future targets.
4. Train/test split by company: 70% / 30%.
5. Baselines: `DNN+C`, `DNN+Q`, `CF`, `CB`, `SVM`, `RF`, `HIN`, `RippleNet`.

Knowledge graph scale (reported):
1. ~907k patents, ~227k companies, ~816k inventors, ~14.5M claims, ~1.42M terms.
2. ~14.47M citation edges, ~1.82M transfer edges, ~1.12M protection-country edges.

## Key Results
Average over top-k lists (`k=10..50`):
1. Precision: `0.596`
2. Recall: `0.636`
3. MAP: `0.584`

Improvement vs best baseline:
1. Precision: `+7.28%`
2. Recall: `+18.35%`
3. MAP: `+8.60%`

Notable findings:
1. `DNN+Q` (quality-only) performs near zero in this transfer context.
2. Connectivity features are essential for relevance; quality features help ranking when combined.
3. In qualitative explanations, family size + inventor/citation connectivity were often dominant signals.

## Practical Implications for PatentIQ
1. Keep **dual objective**: relevance-to-buyer + asset quality.
2. Build explainability into recommendations (feature attribution per recommendation, not only global model metrics).
3. Use **family-level features** (family size/geographic spread) as core transfer signals.
4. Maintain separate feature blocks for:
   - relevance (connectivity/meta-path),
   - quality (citations/legal/family breadth/maintenance).
5. Test recommendation behavior with ablation to verify that “important” features are causally meaningful.

## Caveats / Implementation Nuances
1. The paper uses US-centric transfer data (USPTO + PatentsView); portability to multi-jurisdiction transfer markets needs validation.
2. The quality-only failure indicates a context risk: “valuable” is not equal to “relevant for this buyer.”
3. Reported connectivity table text appears to have a labeling inconsistency (mentions six features while listing P1..P7); treat as editorial inconsistency and verify during reimplementation.

