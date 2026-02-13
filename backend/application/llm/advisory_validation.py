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
        if dumped.get("executive_summary"):
            require_and_validate_tokens(texts=[dumped["executive_summary"].get("one_sentence_takeaway", "")], input_obj=input_obj)

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
        if dumped.get("licensing_readiness"):
            require_and_validate_tokens(texts=[dumped["licensing_readiness"].get("justification", "")], input_obj=input_obj)
            dumped["licensing_readiness"]["justification"] = strip_trace_tokens(
                dumped["licensing_readiness"].get("justification", "")
            )

        if dumped.get("competitive_positioning"):
            require_and_validate_tokens(texts=[dumped["competitive_positioning"].get("explanation", "")], input_obj=input_obj)
            dumped["competitive_positioning"]["explanation"] = strip_trace_tokens(
                dumped["competitive_positioning"].get("explanation", "")
            )

        for field in ("blocking_analysis", "innovation_assessment", "legal_health_interpretation", "citation_dynamics_note"):
            val = dumped.get(field, "")
            if val:
                require_and_validate_tokens(texts=[val], input_obj=input_obj)

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
        if dumped.get("confidence"):
            require_and_validate_tokens(texts=[dumped["confidence"].get("limitations", "")], input_obj=input_obj)
            dumped["confidence"]["limitations"] = strip_trace_tokens(dumped["confidence"].get("limitations", ""))

    except TraceTokenError as e:
        raise AdvisoryValidationError(f"Portfolio trace token validation failed: {e}") from e

    if dumped.get("executive_summary"):
        dumped["executive_summary"]["one_sentence_takeaway"] = strip_trace_tokens(
            dumped["executive_summary"].get("one_sentence_takeaway", "")
        )

    for field in ("blocking_analysis", "innovation_assessment", "legal_health_interpretation", "citation_dynamics_note"):
        if dumped.get(field):
            dumped[field] = strip_trace_tokens(dumped.get(field, ""))

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
        if dumped.get("strategic_value"):
            require_and_validate_tokens(texts=[dumped.get("strategic_value", "")], input_obj=input_obj)

        if dumped.get("risk_assessment"):
            require_and_validate_tokens(texts=[dumped["risk_assessment"].get("explanation", "")], input_obj=input_obj)

        if dumped.get("confidence"):
            require_and_validate_tokens(texts=[dumped["confidence"].get("limitations", "")], input_obj=input_obj)

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

        for field in ("technology_insight", "market_insight", "legal_health_note", "innovation_insight", "blocking_insight"):
            val = dumped.get(field)
            if val:
                require_and_validate_tokens(texts=[val], input_obj=input_obj)

        for rec in dumped.get("actionable_recommendations", []):
            if rec:
                require_and_validate_tokens(texts=[rec], input_obj=input_obj)

    except TraceTokenError as e:
        raise AdvisoryValidationError(f"Patent trace token validation failed: {e}") from e

    if dumped.get("strategic_value"):
        dumped["strategic_value"] = strip_trace_tokens(dumped.get("strategic_value", ""))

    if dumped.get("risk_assessment"):
        dumped["risk_assessment"]["explanation"] = strip_trace_tokens(dumped["risk_assessment"].get("explanation", ""))

    if dumped.get("confidence"):
        dumped["confidence"]["limitations"] = strip_trace_tokens(dumped["confidence"].get("limitations", ""))

    for field in ("technology_insight", "market_insight", "legal_health_note", "innovation_insight", "blocking_insight"):
        if dumped.get(field):
            dumped[field] = strip_trace_tokens(dumped.get(field, ""))

    dumped["actionable_recommendations"] = [
        strip_trace_tokens(r) for r in dumped.get("actionable_recommendations", [])
    ]

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
