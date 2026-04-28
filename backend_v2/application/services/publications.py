from __future__ import annotations

from datetime import date

from fastapi import HTTPException

from domain.schemas.common import Caveat, PageIdentity, ResponseMeta, SupportLevel
from domain.schemas.publication import (
    PublicationOverviewResponse,
    PublicationSectionResponse,
    PublicationSuggestion,
    PublicationSuggestionResponse,
)
from infrastructure.repositories.publication_repository import PublicationRepository


class PublicationService:
    def __init__(self, repository: PublicationRepository | None = None) -> None:
        self.repository = repository or PublicationRepository()

    def get_publication_suggestions(self, query: str, limit: int = 8) -> PublicationSuggestionResponse:
        rows = self.repository.get_publication_suggestions(query=query, limit=limit)
        return PublicationSuggestionResponse(
            query=self._to_text(query),
            rows=[
                PublicationSuggestion(
                    publication_id=self._to_text(row.get("publication_id")),
                    label=self._to_text(row.get("label") or row.get("publication_id")),
                    authority=self._to_text(row.get("authority")) or None,
                    kind_code=self._to_text(row.get("kind_code")) or None,
                    publication_date=self._to_text(row.get("publication_date")) or None,
                    family_id=self._to_text(row.get("family_id")) or None,
                )
                for row in rows
                if self._to_text(row.get("publication_id"))
            ],
        )

    def get_overview(self, publication_id: str) -> PublicationOverviewResponse:
        member = self.repository.get_publication_member(publication_id=publication_id)
        if member is None:
            raise HTTPException(status_code=404, detail=f"Publication {publication_id} was not found.")

        appln_id = self._to_int(member.get("appln_id"))
        family_id = self._to_int(member.get("docdb_family_id"))
        filing_date = self.repository.get_filing_date_for_application(appln_id) if appln_id is not None else None
        title = self.repository.get_title_for_application(appln_id) if appln_id is not None else None
        abstract = self.repository.get_abstract_for_application(appln_id) if appln_id is not None else None
        register = self.repository.get_register_evidence(appln_id) if appln_id is not None and self._to_text(member.get("publn_auth")) == "EP" else {}
        normalized_publication_id = self._normalize_publication_id(publication_id)
        related = (
            self.repository.get_related_family_publications(
                docdb_family_id=family_id,
                exclude_publication_id=normalized_publication_id,
                limit=6,
            )
            if family_id is not None
            else []
        )
        stage_label = self._stage_label(member)
        has_title = bool(self._to_text(title.get("title_text")) if title else None)
        has_abstract = bool(self._to_text(abstract.get("abstract_text")) if abstract else None)
        register_present = self._to_bool(register.get("register_record_present"))

        return PublicationOverviewResponse(
            identity=PageIdentity(
                id=normalized_publication_id,
                label=normalized_publication_id,
                page_kind="publication",
            ),
            overview={
                "publication_id": normalized_publication_id,
                "authority": self._to_text(member.get("publn_auth")),
                "kind_code": self._to_text(member.get("publn_kind")),
                "stage_label": stage_label,
                "publication_date": self._to_text(member.get("publn_date")),
                "filing_date": filing_date,
                "docdb_family_id": family_id,
                "appln_id": appln_id,
                "pat_publn_id": self._to_int(member.get("pat_publn_id")),
                "scope_type": self._to_text(member.get("scope_type")),
                "snapshot_date": self._to_text(member.get("snapshot_date")),
                "title": self._to_text(title.get("title_text")) if title else None,
            },
            summary_cards=[
                {
                    "key": "office",
                    "label": "Office",
                    "value": self._to_text(member.get("publn_auth")) or "—",
                },
                {
                    "key": "kind_code",
                    "label": "Kind code",
                    "value": self._to_text(member.get("publn_kind")) or "—",
                },
                {
                    "key": "stage",
                    "label": "Stage",
                    "value": stage_label,
                },
                {
                    "key": "publication_date",
                    "label": "Publication date",
                    "value": self._to_text(member.get("publn_date")) or "—",
                },
                {
                    "key": "filing_date",
                    "label": "Filing date",
                    "value": filing_date or "—",
                },
                {
                    "key": "register_evidence",
                    "label": "Register evidence",
                    "value": "Present" if register_present else ("EP only" if self._to_text(member.get("publn_auth")) != "EP" else "Not observed"),
                },
                {
                    "key": "text_coverage",
                    "label": "Text evidence",
                    "value": self._text_coverage_label(has_title=has_title, has_abstract=has_abstract),
                },
            ],
            bibliography=[
                {"label": "Publication number", "value": normalized_publication_id},
                {"label": "Authority", "value": self._to_text(member.get("publn_auth"))},
                {"label": "Publication number body", "value": self._to_text(member.get("publn_nr"))},
                {"label": "Kind code", "value": self._to_text(member.get("publn_kind"))},
                {"label": "Publication date", "value": self._to_text(member.get("publn_date"))},
                {"label": "PATSTAT application id", "value": appln_id},
                {"label": "PATSTAT publication id", "value": self._to_int(member.get("pat_publn_id"))},
            ],
            family_context=[
                {"label": "DOCDB family", "value": family_id},
                {"label": "Document stage", "value": stage_label},
                {"label": "Scope type", "value": self._to_text(member.get("scope_type"))},
                {"label": "Snapshot date", "value": self._to_text(member.get("snapshot_date"))},
            ],
            text_availability=[
                {
                    "key": "title",
                    "label": "Title",
                    "status": "available" if has_title else "missing",
                    "detail": (
                        "Publication serving snapshot, sourced from PATSTAT application title."
                        if has_title
                        else "No usable title row was found in the publication serving snapshot for this application."
                    ),
                },
                {
                    "key": "abstract",
                    "label": "Abstract",
                    "status": "available" if has_abstract else "missing",
                    "detail": (
                        "Publication serving snapshot, sourced from PATSTAT application abstract."
                        if has_abstract
                        else "No usable abstract row was found in the publication serving snapshot for this application."
                    ),
                },
                {
                    "key": "claim_1",
                    "label": "Claim 1",
                    "status": "candidate" if self._to_text(member.get("publn_auth")) == "EP" else "not_supported",
                    "detail": (
                        "EPAB English Claim 1 is checked lazily when the text panel opens."
                        if self._to_text(member.get("publn_auth")) == "EP"
                        else "Claim-backed publication evidence is only wired for EPAB-backed EP publications in the current MVP."
                    ),
                },
            ],
            register_evidence=[
                {
                    "label": "Register record present",
                    "value": "Yes" if register_present else "No",
                    "detail": "EP Register evidence only applies to EP publications with register anchors.",
                },
                {
                    "label": "Display status",
                    "value": self._to_text(register.get("ep_display_status_text")) or "—",
                    "detail": self._to_text(register.get("status_source")) or "No display ledger source recorded.",
                },
                {
                    "label": "Registered license",
                    "value": "Yes" if self._to_bool(register.get("ep_registered_license_flag")) else "No",
                    "detail": self._to_text(register.get("ep_licensee_names")) or "No licensee names observed.",
                },
            ],
            related_publications=[
                {
                    "publication_number_full": self._to_text(row.get("publication_number_full")),
                    "publn_auth": self._to_text(row.get("publn_auth")),
                    "publn_kind": self._to_text(row.get("publn_kind")),
                    "publn_date": self._to_text(row.get("publn_date")),
                    "stage_label": self._stage_label(row),
                }
                for row in related
            ],
            meta=ResponseMeta(
                page="publication.overview",
                artifact_sources=[str(path) for path in self.repository.artifacts()],
                support_level=SupportLevel.moderate,
                caveats=[
                    Caveat(
                        code="publication_evidence_first",
                        title="Publication pages stay evidence-first",
                        detail="This view is intentionally factual and document-level. It does not introduce synthetic publication strength or threat scoring.",
                    ),
                    Caveat(
                        code="claim_text_scope",
                        title="Claim text is EP-only in V2",
                        detail="Claim-backed text is currently served only when publication serving contains an EPAB-backed English Claim 1 for the exact publication.",
                    ),
                    Caveat(
                        code="register_scope",
                        title="Register evidence is EP-scoped",
                        detail="Legal and register evidence is projected from EP Register into publication serving and may be blank for non-EP publications.",
                    ),
                ],
            ),
        )

    def get_section(self, publication_id: str, section: str) -> PublicationSectionResponse:
        member = self.repository.get_publication_member(publication_id=publication_id)
        if member is None:
            raise HTTPException(status_code=404, detail=f"Publication {publication_id} was not found.")

        normalized_publication_id = self._normalize_publication_id(publication_id)
        appln_id = self._to_int(member.get("appln_id"))

        rows: list[dict[str, object]]
        summary: dict[str, object] | None = None
        support_level = SupportLevel.moderate
        caveats: list[Caveat] = []

        if section == "text":
            title = self.repository.get_title_for_application(appln_id) if appln_id is not None else None
            abstract = self.repository.get_abstract_for_application(appln_id) if appln_id is not None else None
            claim = (
                self.repository.get_claim_for_publication(normalized_publication_id)
                if self._to_text(member.get("publn_auth")) == "EP"
                else None
            )
            rows = [
                {
                    "panel_key": "title",
                    "label": "Title",
                    "text": self._to_text(title.get("title_text")) if title else None,
                    "language_code": self._to_text(title.get("language_code")) if title else None,
                    "source": "PATSTAT_TITLE",
                    "available": bool(self._to_text(title.get("title_text")) if title else None),
                },
                {
                    "panel_key": "abstract",
                    "label": "Abstract",
                    "text": self._to_text(abstract.get("abstract_text")) if abstract else None,
                    "language_code": self._to_text(abstract.get("language_code")) if abstract else None,
                    "source": "PATSTAT_ABSTRACT",
                    "available": bool(self._to_text(abstract.get("abstract_text")) if abstract else None),
                },
                {
                    "panel_key": "claim_1",
                    "label": "Claim 1",
                    "text": self._to_text(claim.get("claim_text")) if claim else None,
                    "language_code": self._to_text(claim.get("language_code")) if claim else None,
                    "source": "EPAB_CLAIM",
                    "available": bool(self._to_text(claim.get("claim_text")) if claim else None),
                },
            ]
            summary = {
                "title_available": rows[0]["available"],
                "abstract_available": rows[1]["available"],
                "claim_1_available": rows[2]["available"],
                "claim_source_mode": "epab_claim_1" if self._to_text(member.get("publn_auth")) == "EP" else "not_supported",
            }
            caveats = [
                Caveat(
                    code="publication_serving_text_source",
                    title="Title and abstract come from publication serving",
                    detail="These text panels read the publication serving snapshot, which is derived from PATSTAT application text and keeps the exact provenance visible.",
                ),
                Caveat(
                    code="claim_scope",
                    title="Claim coverage is narrower than abstract coverage",
                    detail="Only EPAB-backed English Claim 1 rows are currently projected into publication serving, so claims may be blank even when title and abstract are available.",
                ),
            ]
        elif section == "legal_timeline":
            register = self.repository.get_register_evidence(appln_id) if appln_id is not None and self._to_text(member.get("publn_auth")) == "EP" else {}
            rows = self._timeline_rows(member=member, register=register)
            summary = {
                "latest_event_date": rows[-1]["event_date"] if rows else None,
                "latest_event_type": rows[-1]["event_type"] if rows else None,
                "event_count": len(rows),
                "register_record_present": self._to_bool(register.get("register_record_present")),
            }
            support_level = SupportLevel.strong if rows else SupportLevel.limited
            caveats = [
                Caveat(
                    code="timeline_scope",
                    title="Timeline is milestone-first",
                    detail="This first V2 chronology surfaces publication, register, and major prosecution milestones. It is not yet a full prosecution event ledger.",
                )
            ]
        elif section == "register_evidence":
            register = self.repository.get_register_evidence(appln_id) if appln_id is not None and self._to_text(member.get("publn_auth")) == "EP" else {}
            register_present = self._to_bool(register.get("register_record_present"))
            rows = [
                {
                    "label": "Register record present",
                    "value": "Yes" if register_present else "No",
                    "detail": self._to_text(register.get("register_snapshot_date")) or "No register snapshot recorded.",
                },
                {
                    "label": "Display status",
                    "value": self._to_text(register.get("ep_display_status_text")) or "—",
                    "detail": self._to_text(register.get("status_source")) or "No display status source recorded.",
                },
                {
                    "label": "Registered license flag",
                    "value": "Yes" if self._to_bool(register.get("ep_registered_license_flag")) else "No",
                    "detail": self._to_text(register.get("ep_licensee_names")) or "No licensee names observed.",
                },
                {
                    "label": "Search report mailed",
                    "value": self._to_text(register.get("ep_search_report_mailed_date")) or "—",
                    "detail": self._to_text(register.get("ep_latest_proc_phase_code")) or "No latest procedure phase recorded.",
                },
                {
                    "label": "Latest procedure result",
                    "value": self._to_text(register.get("ep_latest_proc_result_code")) or "—",
                    "detail": self._format_optional_number(register.get("ep_proc_step_maturity_score"), 2) or "No maturity score recorded.",
                },
                {
                    "label": "Unitary patent status",
                    "value": self._to_text(register.get("ep_register_up_status_text")) or ("Yes" if self._to_bool(register.get("ep_register_is_unitary_patent")) else "—"),
                    "detail": self._to_text(register.get("ep_register_up_event_latest_date")) or "No UP event date recorded.",
                },
                {
                    "label": "Opposition status",
                    "value": self._to_text(register.get("ep_opposition_status_text")) or ("Active" if self._to_bool(register.get("ep_opposition_active")) else "—"),
                    "detail": self._to_text(register.get("ep_opponent_names")) or "No opponent names observed.",
                },
                {
                    "label": "Lead agent",
                    "value": self._to_text(register.get("ep_register_lead_agent_name")) or "—",
                    "detail": self._to_text(register.get("ep_register_lead_agent_country")) or "No agent country recorded.",
                },
            ]
            summary = {
                "register_record_present": register_present,
                "register_snapshot_date": self._to_text(register.get("register_snapshot_date")),
                "license_flag": self._to_bool(register.get("ep_registered_license_flag")),
                "unitary_patent": self._to_bool(register.get("ep_register_is_unitary_patent")),
                "opposition_active": self._to_bool(register.get("ep_opposition_active")),
            }
            support_level = SupportLevel.strong if register_present else (
                SupportLevel.limited if self._to_text(member.get("publn_auth")) == "EP" else SupportLevel.candidate_only
            )
            caveats = [
                Caveat(
                    code="ep_register_only",
                    title="Register evidence is EP-specific",
                    detail="This section is populated from publication serving fields derived from EP Register. Non-EP publications will usually show factual blanks rather than inferred legal evidence.",
                )
            ]
        else:
            rows = []

        return PublicationSectionResponse(
            publication_id=normalized_publication_id,
            summary=summary,
            rows=rows,
            meta=ResponseMeta(
                page=f"publication.{section}",
                artifact_sources=[str(path) for path in self.repository.artifacts()],
                support_level=support_level,
                caveats=caveats,
            ),
        )

    def _normalize_publication_id(self, publication_id: str) -> str:
        return publication_id.strip().upper()

    def _stage_label(self, row: dict[str, object]) -> str:
        if self._to_bool(row.get("is_grant_stage")):
            return "Grant"
        if self._to_bool(row.get("is_application_stage")):
            return "Application"
        if self._to_bool(row.get("is_modifier_stage")):
            return "Post-grant modifier"
        return "Other"

    def _text_coverage_label(self, has_title: bool, has_abstract: bool) -> str:
        if has_title and has_abstract:
            return "Title + abstract"
        if has_title:
            return "Title only"
        if has_abstract:
            return "Abstract only"
        return "Metadata only"

    def _timeline_rows(self, member: dict[str, object], register: dict[str, object]) -> list[dict[str, object]]:
        rows: list[dict[str, object]] = []
        publication_date = self._to_text(member.get("publn_date"))
        if publication_date:
            rows.append(
                {
                    "event_date": publication_date,
                    "event_type": "Publication",
                    "detail": f"{self._normalize_publication_id(self._to_text(member.get('publication_number_full')) or '')} published in {self._to_text(member.get('publn_auth')) or 'its office'}.",
                    "source": "PATSTAT_PUBLICATION",
                }
            )

        search_report_date = self._to_text(register.get("ep_search_report_mailed_date"))
        if search_report_date:
            rows.append(
                {
                    "event_date": search_report_date,
                    "event_type": "Search report mailed",
                    "detail": self._to_text(register.get("ep_latest_proc_phase_code")) or "EP Register procedure milestone.",
                    "source": "EP_REGISTER_PROC",
                }
            )

        up_event_date = self._to_text(register.get("ep_register_up_event_latest_date"))
        if up_event_date:
            rows.append(
                {
                    "event_date": up_event_date,
                    "event_type": "Unitary patent status",
                    "detail": self._to_text(register.get("ep_register_up_status_text")) or "UP status observed in EP Register.",
                    "source": "EP_REGISTER_UP",
                }
            )

        register_snapshot_date = self._to_text(register.get("register_snapshot_date")) or self._to_text(register.get("display_snapshot_date"))
        if register_snapshot_date and self._to_bool(register.get("register_record_present")):
            rows.append(
                {
                    "event_date": register_snapshot_date,
                    "event_type": "Register snapshot",
                    "detail": self._to_text(register.get("ep_display_status_text")) or "EP Register record observed.",
                    "source": self._to_text(register.get("status_source")) or "EP_REGISTER_CORE",
                }
            )

        rows.sort(key=lambda row: self._parse_date(row.get("event_date")))
        return rows

    def _parse_date(self, value: object) -> tuple[int, date]:
        text = self._to_text(value)
        if not text:
            return (1, date.min)
        try:
            return (0, date.fromisoformat(text))
        except ValueError:
            return (1, date.min)

    def _format_optional_number(self, value: object, digits: int) -> str | None:
        number = self._to_float(value)
        if number is None:
            return None
        return f"{number:.{digits}f}"

    def _to_text(self, value: object) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    def _to_bool(self, value: object) -> bool:
        if isinstance(value, bool):
            return value
        if value is None:
            return False
        if isinstance(value, (int, float)):
            return bool(value)
        return str(value).strip().lower() in {"true", "1", "yes", "y"}

    def _to_int(self, value: object) -> int | None:
        if value is None:
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def _to_float(self, value: object) -> float | None:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
