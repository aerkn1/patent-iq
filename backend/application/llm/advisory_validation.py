from __future__ import annotations

from typing import Any

from domain.schemas.advisory_outputs import (
    PortfolioAdvisoryOutput,
    PatentAdvisoryOutput,
    PortfolioEvolutionAdvisoryOutput,
)

from application.llm.trace_tokens import (
    TraceTokenError,
    evidence_tokens_to_string,
    parse_llm_json_object,
    require_and_validate_tokens,
    strip_trace_tokens,
    extract_trace_tokens,
)


class AdvisoryValidationError(ValueError):
    pass


def validate_and_sanitize_portfolio_advisory(
    *,
    llm_content: str,
    input_obj: dict[str, Any],
) -> dict[str, Any]:
    raw = parse_llm_json_object(llm_content)
    try:
        model = PortfolioAdvisoryOutput.model_validate(raw)
    except Exception as e:
        raise AdvisoryValidationError(f"Portfolio output schema validation failed: {e}") from e

    dumped = model.model_dump()

    try:
        # Executive summary takeaway
        require_and_validate_tokens(texts=[dumped["executive_summary"]["one_sentence_takeaway"]], input_obj=input_obj)

        # Strengths/weaknesses
        for item in dumped.get("strengths", []):
            ev_toks = extract_trace_tokens(item.get("evidence", ""))
            require_and_validate_tokens(texts=[item.get("evidence", "")], input_obj=input_obj)
            require_and_validate_tokens(texts=[item.get("interpretation", "")], input_obj=input_obj)
            item["evidence"] = evidence_tokens_to_string(ev_toks)
            item["interpretation"] = strip_trace_tokens(item["interpretation"])

        for item in dumped.get("weaknesses", []):
            ev_toks = extract_trace_tokens(item.get("evidence", ""))
            require_and_validate_tokens(texts=[item.get("evidence", "")], input_obj=input_obj)
            require_and_validate_tokens(texts=[item.get("interpretation", "")], input_obj=input_obj)
            item["evidence"] = evidence_tokens_to_string(ev_toks)
            item["interpretation"] = strip_trace_tokens(item["interpretation"])

        # Licensing / competitive
        require_and_validate_tokens(texts=[dumped["licensing_readiness"]["justification"]], input_obj=input_obj)
        require_and_validate_tokens(texts=[dumped["competitive_positioning"]["explanation"]], input_obj=input_obj)

        dumped["licensing_readiness"]["justification"] = strip_trace_tokens(
            dumped["licensing_readiness"]["justification"]
        )
        dumped["competitive_positioning"]["explanation"] = strip_trace_tokens(
            dumped["competitive_positioning"]["explanation"]
        )

        # Recommendations
        for rec in dumped.get("strategic_recommendations", []):
            require_and_validate_tokens(texts=[rec.get("rationale", "")], input_obj=input_obj)
            rec["action"] = strip_trace_tokens(rec.get("action", ""))
            rec["rationale"] = strip_trace_tokens(rec.get("rationale", ""))

        # Risks
        for rf in dumped.get("risk_flags", []):
            require_and_validate_tokens(texts=[rf.get("reason", "")], input_obj=input_obj)
            rf["reason"] = strip_trace_tokens(rf.get("reason", ""))

        # Confidence
        require_and_validate_tokens(texts=[dumped["confidence"]["limitations"]], input_obj=input_obj)
        dumped["confidence"]["limitations"] = strip_trace_tokens(dumped["confidence"]["limitations"])

    except TraceTokenError as e:
        raise AdvisoryValidationError(f"Portfolio trace token validation failed: {e}") from e

    dumped["executive_summary"]["one_sentence_takeaway"] = strip_trace_tokens(
        dumped["executive_summary"]["one_sentence_takeaway"]
    )

    return dumped


def validate_and_sanitize_patent_advisory(
    *,
    llm_content: str,
    input_obj: dict[str, Any],
) -> dict[str, Any]:
    raw = parse_llm_json_object(llm_content)
    try:
        model = PatentAdvisoryOutput.model_validate(raw)
    except Exception as e:
        raise AdvisoryValidationError(f"Patent output schema validation failed: {e}") from e

    dumped = model.model_dump()

    try:
        require_and_validate_tokens(texts=[dumped.get("strategic_value", "")], input_obj=input_obj)
        require_and_validate_tokens(texts=[dumped["risk_assessment"]["explanation"]], input_obj=input_obj)
        require_and_validate_tokens(texts=[dumped["confidence"]["limitations"]], input_obj=input_obj)

        # Each strength/weakness item must contain at least one token
        require_and_validate_tokens(texts=dumped.get("strengths", []), input_obj=input_obj)
        require_and_validate_tokens(texts=dumped.get("weaknesses", []), input_obj=input_obj)

    except TraceTokenError as e:
        raise AdvisoryValidationError(f"Patent trace token validation failed: {e}") from e

    dumped["strengths"] = [strip_trace_tokens(s) for s in dumped.get("strengths", [])]
    dumped["weaknesses"] = [strip_trace_tokens(s) for s in dumped.get("weaknesses", [])]
    dumped["strategic_value"] = strip_trace_tokens(dumped.get("strategic_value", ""))
    dumped["risk_assessment"]["explanation"] = strip_trace_tokens(dumped["risk_assessment"]["explanation"])
    dumped["confidence"]["limitations"] = strip_trace_tokens(dumped["confidence"]["limitations"])

    return dumped


def validate_and_sanitize_portfolio_evolution_advisory(
    *,
    llm_content: str,
    input_obj: dict[str, Any],
) -> dict[str, Any]:
    raw = parse_llm_json_object(llm_content)
    try:
        model = PortfolioEvolutionAdvisoryOutput.model_validate(raw)
    except Exception as e:
        raise AdvisoryValidationError(f"Portfolio evolution schema validation failed: {e}") from e

    dumped = model.model_dump()

    # Build a quick lookup for YoY % by year from the input.
    series = (
        input_obj.get("ui_payload", {})
        .get("portfolio_citation_timeseries", {})
        .get("series", [])
    )
    yoy_by_year: dict[int, float] = {}
    for row in series:
        try:
            year = int(row.get("year"))
            yoy = float(row.get("citations_yoy_pct") or 0.0)
            yoy_by_year[year] = yoy
        except Exception:
            continue

    try:
        require_and_validate_tokens(
            texts=[dumped["executive_summary"]["one_sentence_takeaway"]], input_obj=input_obj
        )
        require_and_validate_tokens(
            texts=[dumped["confidence"]["limitations"]], input_obj=input_obj
        )

        for y in dumped.get("yearly", []):
            # Enforce yoy_growth_pct is copied from provided data (no computation).
            yy = int(y.get("year"))
            expected = yoy_by_year.get(yy)
            if expected is not None:
                actual = float(y.get("yoy_growth_pct") or 0.0)
                if abs(actual - float(expected)) > 1e-6:
                    raise AdvisoryValidationError(
                        f"yoy_growth_pct mismatch for year={yy}: output={actual} expected={expected}"
                    )

            ev_toks = extract_trace_tokens(y.get("evidence", ""))
            require_and_validate_tokens(texts=[y.get("evidence", "")], input_obj=input_obj)
            require_and_validate_tokens(texts=[y.get("interpretation", "")], input_obj=input_obj)
            y["evidence"] = evidence_tokens_to_string(ev_toks)
            y["interpretation"] = strip_trace_tokens(y.get("interpretation", ""))

        for rf in dumped.get("risk_flags", []):
            require_and_validate_tokens(texts=[rf.get("reason", "")], input_obj=input_obj)
            rf["reason"] = strip_trace_tokens(rf.get("reason", ""))

    except TraceTokenError as e:
        raise AdvisoryValidationError(
            f"Portfolio evolution trace token validation failed: {e}"
        ) from e

    dumped["executive_summary"]["one_sentence_takeaway"] = strip_trace_tokens(
        dumped["executive_summary"]["one_sentence_takeaway"]
    )
    dumped["confidence"]["limitations"] = strip_trace_tokens(dumped["confidence"]["limitations"])

    return dumped
