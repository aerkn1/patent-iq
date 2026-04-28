# PatentIQ V2 Azure OpenAI GPT-4o-mini LLM Augmentation Contract

## Purpose

Define how PatentIQ V2 should use `Azure OpenAI gpt-4o-mini` as a disciplined LLM augmentation layer, based on the already documented PatentIQ use cases for:

1. report narration,
2. compare summaries,
3. forecast explanation,
4. semantic explanation,
5. methodology and data-room assistance.

This note assumes:

1. Azure is the chosen deployment platform,
2. heavy PatentIQ truth generation remains deterministic,
3. the LLM is a bounded explanation and summarization layer,
4. `gpt-4o-mini` is the first preferred deployed model for demo and early V2 use.

---

## 1. Decision

PatentIQ V2 should use:

1. `Azure OpenAI gpt-4o-mini`

as the `default first LLM augmentation model`.

Why:

1. it is cheap enough for demo and early product use,
2. it has high Azure quota ceilings,
3. it is fast enough for interactive explanation and report sections,
4. it fits the Azure-first hosting and student-credit setup,
5. it is strong enough for grounded narrative tasks without introducing unnecessary provider sprawl.

This note does not claim that `gpt-4o-mini` is the best model for every future PatentIQ workload.

It is the best `first practical deployed model` for the currently defined LLM augmentation layer.

---

## 2. What The LLM Is Allowed To Do

The LLM layer is allowed to:

1. narrate already computed insights,
2. summarize structured compare outputs,
3. explain forecast outputs in plain language,
4. explain semantic retrieval results in grounded language,
5. summarize methodology and caveats from structured inputs,
6. help users phrase report or comparison requests.

The LLM layer is not allowed to:

1. compute blocking power,
2. determine legal status,
3. generate portfolio scores,
4. generate forecast scores,
5. produce monetary valuation figures from public patent data,
6. replace deterministic semantic retrieval or ranking.

The platform rule is:

1. deterministic engine first,
2. LLM narration second.

---

## 3. Supported PatentIQ Use Cases

## 3.1 Report Narration

Applicable to:

1. family intelligence report
2. portfolio intelligence report
3. compare report
4. market intelligence report
5. client-enriched executive report

LLM role:

1. write executive summary paragraphs,
2. produce short section introductions,
3. summarize the strongest evidence-backed conclusions,
4. restate caveats in human-readable form.

## 3.2 Compare Summary

Applicable to:

1. family vs family
2. portfolio vs portfolio
3. same entity across time
4. current vs projected compare

LLM role:

1. explain the highest-signal differences,
2. identify which dimensions widened or narrowed,
3. summarize the change without inventing unsupported reasons.

## 3.3 Forecast Explanation

Applicable to:

1. family future influence
2. portfolio bottom-up forecast summary

LLM role:

1. explain what the `3y` and `5y` forecasts mean,
2. summarize drivers and interval interpretation,
3. restate model caveats and feature completeness.

## 3.4 Semantic Explanation

Applicable to:

1. semantic search results
2. family-to-family semantic compare
3. semantic report generation

LLM role:

1. explain why a result appears relevant,
2. summarize representative text overlap,
3. restate legal/status and provenance caveats.

## 3.5 Data Room / Methodology Assistant

Applicable to:

1. metric explanations
2. model cards
3. methodology summaries
4. release manifest summaries

LLM role:

1. turn structured methodology into readable explanation,
2. answer metric-definition questions from approved sources only.

---

## 4. Why GPT-4o-mini Is A Good Fit

## 4.1 Cost

The verified Azure retail rates for `gpt-4o-mini` are approximately:

1. input: `$0.00015 / 1K tokens`
2. output: `$0.0006 / 1K tokens`
3. batch input: `$0.000075 / 1K tokens`
4. batch output: `$0.0003 / 1K tokens`

These are low enough that report narration and explanation use cases are inexpensive even under repeated demo use.

## 4.2 Quotas

Azure’s current default quotas are high enough for PatentIQ demo workloads.

Current Microsoft Learn quotas list:

1. `gpt-4o-mini` Global Standard:
   - `2M TPM`
   - `12K RPM`

That is far beyond the expected demo traffic for PatentIQ.

## 4.3 Speed

PatentIQ’s first LLM use cases are:

1. bounded summaries,
2. report section generation,
3. explanation blocks,
4. compare narration.

These do not require frontier-model deep reasoning loops.

So `gpt-4o-mini` is fast enough in practice if prompts are kept compact and grounded.

## 4.4 Context

PatentIQ does need moderately large context windows, but not because it should dump raw tables into the model.

The correct pattern is:

1. backend compacts structured inputs,
2. LLM receives a concise grounded payload,
3. LLM generates one section / one explanation at a time.

Under that pattern, `gpt-4o-mini` has enough context for PatentIQ’s current use cases.

---

## 5. Cost Model For PatentIQ Use Cases

These are practical estimates, not billing guarantees.

## 5.1 Small Explanation Request

Example:

1. `3K` input tokens
2. `600` output tokens

Approximate cost:

1. input: `3 x 0.00015 = $0.00045`
2. output: `0.6 x 0.0006 = $0.00036`
3. total: `~$0.00081`

## 5.2 Medium Report Section

Example:

1. `6K` input tokens
2. `1.2K` output tokens

Approximate cost:

1. input: `6 x 0.00015 = $0.0009`
2. output: `1.2 x 0.0006 = $0.00072`
3. total: `~$0.00162`

## 5.3 Large Compare Narrative

Example:

1. `10K` input tokens
2. `2K` output tokens

Approximate cost:

1. input: `10 x 0.00015 = $0.0015`
2. output: `2 x 0.0006 = $0.0012`
3. total: `~$0.0027`

Implication:

1. hundreds of explanation requests remain inexpensive,
2. jury/demo-level usage is easily supportable,
3. Azure student credit should comfortably cover meaningful experimentation.

---

## 6. Prompt Budget Policy

PatentIQ should define explicit token budgets per feature.

## 6.1 Family Report Executive Summary

Recommended max:

1. input: `<= 6K`
2. output: `<= 800`

## 6.2 Portfolio Report Executive Summary

Recommended max:

1. input: `<= 8K`
2. output: `<= 1K`

## 6.3 Compare Summary

Recommended max:

1. input: `<= 8K`
2. output: `<= 900`

## 6.4 Forecast Explanation

Recommended max:

1. input: `<= 4K`
2. output: `<= 600`

## 6.5 Semantic Result Explanation

Recommended max:

1. input: `<= 4K`
2. output: `<= 500`

## 6.6 Data Room Methodology Summary

Recommended max:

1. input: `<= 6K`
2. output: `<= 700`

## Rule

Do not pass:

1. giant raw tables,
2. full report payloads,
3. entire semantic result sets,
4. giant historical ledgers,

directly into the model.

Always pre-compact and structure the payload first.

---

## 7. Input Construction Pattern

Every LLM call should receive:

1. a small system instruction,
2. a structured JSON-like payload,
3. explicit caveats,
4. explicit allowed claims,
5. explicit forbidden claims.

Recommended structure:

```json
{
  "task": "family_report_summary",
  "entity": {
    "docdb_family_id": 12345678,
    "title": "..."
  },
  "metrics": {
    "blocking_power_percentile": 91,
    "coverage_breadth_percentile": 74,
    "current_status": "ACTIVE"
  },
  "history": {
    "blocking_change": "increasing",
    "field_shift": "stable"
  },
  "caveats": [
    "semantic evidence is abstract-backed",
    "oecd metric is current-only"
  ],
  "instructions": {
    "max_bullets": 4,
    "tone": "analytical",
    "forbidden_claims": [
      "do not assign monetary value",
      "do not infer legal infringement"
    ]
  }
}
```

---

## 8. Output Contract

PatentIQ should prefer structured outputs from the LLM layer when backend code consumes the result.

Recommended response shape:

```json
{
  "headline": "...",
  "summary_paragraph": "...",
  "key_points": [
    "...",
    "...",
    "..."
  ],
  "caveat_summary": "...",
  "confidence": "bounded-grounded"
}
```

For UI-only text, plain text can be acceptable, but structured output is still better for:

1. consistency,
2. logging,
3. traceability,
4. export generation.

---

## 9. Grounding Rules

The LLM must always be grounded in supplied structured data.

Mandatory grounding rules:

1. no external knowledge needed for the answer,
2. no independent factual invention,
3. no unsupported causal claims,
4. no numeric invention,
5. no legal conclusions,
6. no monetary valuation claims.

The LLM may:

1. restate,
2. rank emphasis,
3. compress,
4. explain terminology,
5. summarize deltas.

The LLM may not:

1. replace missing data with plausible prose,
2. infer private business facts,
3. turn proxy metrics into real-world cash values.

---

## 10. Feature-Level Design

## 10.1 Family Report Summary

Input sources:

1. family summary
2. blocking power
3. history slices
4. caveats

Output:

1. executive summary paragraph
2. 3-4 key takeaways
3. concise caveat paragraph

## 10.2 Portfolio Summary Narrative

Input sources:

1. portfolio summary
2. top families
3. concentration metrics
4. forecast rollup
5. threat matrix summary

Output:

1. portfolio headline narrative
2. strengths
3. vulnerabilities
4. concentration comment

## 10.3 Compare Narrative

Input sources:

1. compare metrics
2. delta tables
3. historical compare data

Output:

1. “what differs most”
2. “what changed over time”
3. “what remains uncertain”

## 10.4 Semantic Explanation

Input sources:

1. query summary
2. representative text snippets
3. semantic scores
4. legal/status context

Output:

1. short relevance explanation
2. provenance note
3. caveat note if abstract-backed

## 10.5 Forecast Explanation

Input sources:

1. point forecast
2. interval
3. top drivers
4. feature completeness

Output:

1. short explanation of expected trajectory
2. interval interpretation
3. caveat note about uncertainty and horizon

---

## 11. UI Contract Implications

## 11.1 Report Composer

The report composer should include:

1. `Include AI Summary` toggle
2. model provenance badge
3. note that summary is grounded on current report data

## 11.2 Family / Portfolio Pages

LLM usage should appear as:

1. `AI Summary` card
2. `Key Takeaways` list
3. `Caveat Summary` card

It should not replace:

1. KPI cards
2. tables
3. evidence panels

## 11.3 Compare Workspace

Best use:

1. `AI Compare Summary`
2. `What Changed Most`
3. `Main Caveats`

## 11.4 Data Room

Must expose:

1. model used
2. prompt template version
3. grounding fields included
4. generation timestamp

---

## 12. Backend Contract

Recommended location:

1. `backend/v2/application/services/llm/`
2. `backend/v2/domain/schemas/llm/`
3. `backend/v2/infrastructure/llm/`

Suggested service families:

1. `report_llm_service`
2. `compare_llm_service`
3. `forecast_llm_service`
4. `semantic_llm_service`
5. `methodology_llm_service`

Suggested endpoint families:

1. `/api/v2/reports/.../summary`
2. `/api/v2/compare/.../summary`
3. `/api/v2/forecast/.../explanation`
4. `/api/v2/semantic/.../explanation`
5. `/api/v2/data-room/.../explanation`

All endpoints should return:

1. generated text,
2. model name,
3. generation timestamp,
4. release version,
5. caveat and grounding metadata.

---

## 13. Reliability And Fallback Policy

If the LLM request fails or is throttled:

1. the page/report must still work,
2. deterministic metrics remain primary,
3. UI should fall back to:
   - no AI summary,
   - or a rule-based short summary.

Fallback hierarchy:

1. use cached LLM output if available,
2. use deterministic fallback summary,
3. omit summary block entirely.

Never block core product use on LLM success.

---

## 14. Caching Policy

Cache should be keyed by:

1. entity id / scope,
2. report type,
3. compare mode,
4. release version,
5. prompt template version,
6. model version.

Good cache candidates:

1. family report summaries
2. portfolio summaries
3. compare summaries
4. stable methodology explanations

This reduces:

1. latency,
2. token cost,
3. repeated generation during demos.

---

## 15. Security And Data Rules

For public-data-native use:

1. normal backend-to-Azure-OpenAI flow is acceptable.

For client-enriched use:

1. do not send raw sensitive client financial rows unless explicitly allowed,
2. prefer sending only compact derived scenario payloads,
3. never log raw client financial payloads in plain text,
4. preserve provenance that a summary is client-enriched.

---

## 16. Why GPT-4o-mini Instead Of A Larger Model First

Because PatentIQ’s first LLM tasks are:

1. grounded,
2. bounded,
3. structurally simple,
4. explanation-heavy rather than frontier-reasoning-heavy.

So the product gains more from:

1. low cost,
2. high quota,
3. easy deployment,
4. acceptable speed,

than from paying for a larger premium model immediately.

If a later use case requires stronger reasoning or higher narrative quality, a larger model can be added selectively.

---

## 17. Current Recommendation

Use `Azure OpenAI gpt-4o-mini` for:

1. report summaries,
2. compare summaries,
3. forecast explanations,
4. semantic explanations,
5. methodology summaries.

Keep it:

1. grounded,
2. compact,
3. structured,
4. cached,
5. optional.

Do not use it for:

1. core analytics generation,
2. legal truth,
3. forecast scoring,
4. monetary valuation.

This gives PatentIQ a meaningful LLM layer without overengineering or undermining the deterministic analytics foundation.
