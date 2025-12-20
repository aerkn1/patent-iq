# ======================================================================================
#  PATENT VALUATION / PORTFOLIO COMPARISON — PATSTAT-ONLY v1 SKELETON (EXPLAINABLE)
# ======================================================================================
#
#  WHAT THIS FILE IS:
#  ------------------
#  A fully working end-to-end pipeline that takes:
#    - 1 EP application number (e.g., "15860005")
#    - OR a list of EP application numbers (portfolio)
#
#  ...and returns a structured report (dict) based ONLY on PATSTAT data:
#    - core application identifiers (appln_id, family ids, grant flag, filing date)
#    - title + abstract
#    - applicant(s)
#    - publications (A/B kinds)
#    - CPC tech classification
#    - DOCDB family footprint (jurisdictions, family size)
#    - forward citations (publication-level, robust across A/B)
#    - legal event signals (fees paid, lapses, reinstatements)
#    - simple explainable score v0 (0–100) + justification
#
#
#  WHY THIS EXISTS:
#  ---------------
#  We need a demo-ready "skeleton" that already works on real PATSTAT,
#  even before adding advanced AI / ML / LLM components.
#
#  The philosophy is:
#    - PATSTAT first (ground truth-ish bibliographic + legal signals)
#    - Explainable features (no black box)
#    - Portfolio comparison by default
#    - Add AI later ONLY where it adds value (e.g., claim breadth, novelty, X/Y, etc.)
#
#
#  HIGH-LEVEL PIPELINE DIAGRAM:
#  ----------------------------
#
#      INPUT
#      -----
#      EP application number(s)
#       - Single: "15860005"
#       - Portfolio: ["15860005", "13849544", ...]
#
#          |
#          v
#
#      MODULE 0 — RESOLUTION (EP → appln_id)
#      -------------------------------------
#      tls201_appln:
#        - appln_id
#        - filing date/year
#        - granted flag
#        - docdb_family_id, inpadoc_family_id
#
#          |
#          v
#
#      MODULE 1 — CORE PATENT CARD
#      ---------------------------
#      tls202_appln_title  -> title
#      tls203_appln_abstr  -> abstract
#      tls206_person + tls207_pers_appln -> applicants
#      tls211_pat_publn    -> publications list (A1/A2/A3/A4/B1...)
#
#          |
#          v
#
#      MODULE 2 — TECH + FAMILY FOOTPRINT
#      ----------------------------------
#      tls224_appln_cpc    -> CPC symbols (tech field proxy)
#      tls201_appln (docdb_family_id filter) -> family members + geo footprint
#
#          |
#          v
#
#      MODULE 3 — CITATIONS (MAIN PUBLICATION)
#      ---------------------------------------
#      Choose main publication:
#        - Prefer EP B* (grant publication)
#        - Else EP A*
#      tls212_citation + tls211_pat_publn -> forward citations + citations-by-year curve
#
#          |
#          v
#
#      MODULE 4 — LEGAL SIGNALS + ROBUST CITATIONS
#      -------------------------------------------
#      tls231_inpadoc_legal_event -> fee payments, lapses, reinstates
#      AND robust citation metrics across ALL EP publications:
#        - citations_main_publn
#        - citations_max_any_publn (important!)
#
#          |
#          v
#
#      MODULE 5 — BUILD REPORT(S)
#      --------------------------
#      build_patent_report()    -> report dict for one EP number
#      build_portfolio_report() -> list of reports + aggregate stats
#
#          |
#          v
#
#      MODULE 6 — SCORE v0 (EXPLAINABLE)
#      ---------------------------------
#      A simple transparent baseline score:
#        - citations (max_any_publn) [0..40]
#        - family breadth (size + US/JP/KR/WO) [0..25]
#        - legal maintenance / lapse recency [0..20]
#        - remaining term (20y baseline) [0..15]
#
#
#  IMPORTANT LIMITATIONS (KNOWN GAPS / FUTURE WORK):
#  ------------------------------------------------
#  This v1 does NOT attempt:
#    - claim breadth analysis (independent claims count, claim length, etc.)
#    - examiner X/Y evidence (search report, blocking power)  <-- big future piece
#    - "hidden gem" detection using ML/LLM embeddings
#    - field-normalized citation scoring (citations vary by tech domain)
#    - economic valuation models (DCF, royalty relief, option pricing, etc.)
#
#  But it DOES give us a working platform with real data, explainable outputs,
#  and clear insertion points for advanced methods later.
#
# ======================================================================================


from epo.tipdata.patstat import PatstatClient
from datetime import date

def get_patstat(env: str = "PROD") -> PatstatClient:
    return PatstatClient(env)



# ======================================================================================
# MODULE 0 + 1 — INPUT → appln_id → CORE PATENT CARD
# ======================================================================================
# Goal:
#   Convert an EP application number into a structured "patent card".
#
# Inputs:
#   - EP application number (no "EP" prefix required)
#
# Outputs (card):
#   - core identifiers (tls201_appln)
#   - title/abstract (tls202/tls203)
#   - applicants (tls206/tls207)
#   - publications list (tls211)
#
# Typical usage:
#   card = build_patent_card(patstat, "15860005")
#
# Notes:
#   - Language handling is simplified (we take first row if multiple exist).
#   - Future: support EP publication number input (EP0404097) directly.
# ======================================================================================


#module 0 - 1


from typing import Any, Dict, List, Optional, Tuple

EP_AUTH_DEFAULT = "EP"


def resolve_ep_application(
    patstat,
    ep_nr: str,
    ep_auth: str = EP_AUTH_DEFAULT,
) -> Dict[str, Any]:
    """
    Module 0:
    Resolve an EP application number (e.g. '15860005') to appln_id + core identifiers.
    """
    ep_nr_clean = ep_nr.strip().upper().replace("EP", "").replace(" ", "")

    # --- Input hardening (v1 safety) -----------------------------------------
    # We only accept digits for EP application numbers in this skeleton.
    # This avoids accidental weird input and prevents SQL injection via string interpolation.
    # If later we support other formats, replace this with a proper parser.
    if not ep_nr_clean.isdigit():
        raise ValueError(
            f"Invalid EP application number '{ep_nr}'. "
            f"After cleaning it became '{ep_nr_clean}', but we only accept digits."
        )
    # -------------------------------------------------------------------------

    res = patstat.sql_query(f"""
    SELECT appln_id, appln_auth, appln_nr, appln_kind,
           appln_filing_date, appln_filing_year,
           granted, docdb_family_id, inpadoc_family_id
    FROM tls201_appln
    WHERE appln_auth = '{ep_auth}'
      AND appln_nr = '{ep_nr_clean}'
    """, use_legacy_sql=False)

    if not res:
        raise ValueError(f"No application found for {ep_auth}{ep_nr_clean}")

    out = dict(res[0])
    out["input_ep_nr"] = ep_nr
    out["ep_nr_clean"] = ep_nr_clean
    out["multiple_matches"] = (len(res) > 1)
    return out



def get_patent_text(
    patstat,
    appln_id: int,
) -> Dict[str, Optional[str]]:
    """
    Module 1a:
    Title + abstract for appln_id.
    Note: if multiple languages exist, this may return multiple rows in raw PATSTAT,
    but in your sample it returned a single row. For v1 we take the first.
    """
    res = patstat.sql_query(f"""
    SELECT
      t.appln_title,
      ab.appln_abstract
    FROM tls201_appln a
    LEFT JOIN tls202_appln_title t ON a.appln_id = t.appln_id
    LEFT JOIN tls203_appln_abstr ab ON a.appln_id = ab.appln_id
    WHERE a.appln_id = {appln_id}
    """, use_legacy_sql=False)

    if not res:
        return {"title": None, "abstract": None}

    row = res[0]
    return {"title": row.get("appln_title"), "abstract": row.get("appln_abstract")}


def get_patent_applicants(
    patstat,
    appln_id: int,
) -> List[Dict[str, Any]]:
    """
    Module 1b:
    Applicants ordered by applt_seq_nr (exclude inventors).
    """
    res = patstat.sql_query(f"""
    SELECT
      p.psn_name, p.person_name, p.person_ctry_code,
      pa.applt_seq_nr
    FROM tls207_pers_appln pa
    JOIN tls206_person p ON pa.person_id = p.person_id
    WHERE pa.appln_id = {appln_id}
      AND pa.applt_seq_nr > 0
    ORDER BY pa.applt_seq_nr
    """, use_legacy_sql=False)

    # Normalize keys
    out = []
    for r in res:
        out.append({
            "applt_seq_nr": r.get("applt_seq_nr"),
            "psn_name": r.get("psn_name"),
            "person_name": r.get("person_name"),
            "person_ctry_code": r.get("person_ctry_code"),
        })
    return out


def get_patent_publications(
    patstat,
    appln_id: int,
) -> List[Dict[str, Any]]:
    """
    Module 1c:
    Publications for appln_id (EP A1/A2/A4/B1 etc), ordered by publn_date.
    """
    res = patstat.sql_query(f"""
    SELECT
      pat_publn_id,
      publn_auth, publn_nr, publn_kind, publn_date
    FROM tls211_pat_publn
    WHERE appln_id = {appln_id}
    ORDER BY publn_date
    """, use_legacy_sql=False)

    return [dict(r) for r in res]


def build_patent_card(
    patstat,
    ep_nr: str,
    ep_auth: str = EP_AUTH_DEFAULT,
) -> Dict[str, Any]:
    """
    Module 0 + Module 1:
    Full 'patent card' from EP number.
    """
    core = resolve_ep_application(patstat, ep_nr=ep_nr, ep_auth=ep_auth)
    appln_id = int(core["appln_id"])

    text = get_patent_text(patstat, appln_id=appln_id)
    applicants = get_patent_applicants(patstat, appln_id=appln_id)
    publications = get_patent_publications(patstat, appln_id=appln_id)

    card = {
        "input": {"ep_auth": ep_auth, "ep_nr": ep_nr, "ep_nr_clean": core["ep_nr_clean"]},
        "core": core,
        "text": text,
        "applicants": applicants,
        "publications": publications,
    }
    return card


# ======================================================================================
# MODULE 2 — TECH CLASSIFICATION + DOCDB FAMILY FOOTPRINT
# ======================================================================================
# Goal:
#   Enrich the patent card with:
#     - CPC symbols (tech proxy)
#     - DOCDB family members and geographic footprint
#
# Why it matters:
#   - CPC tells us "what field" the invention is in.
#   - Family footprint is a strong commercial proxy:
#       bigger / broader family often implies higher value or expected value.
#
# Outputs added to card:
#   card["cpc"] = {symbols, n_cpc}
#   card["family_docdb"] = {
#      docdb_family_id,
#      members (list of applications),
#      family_size,
#      by_authority counts (geo footprint),
#      flags has_US/JP/KR/WO...
#   }
# ======================================================================================



#module 2

from typing import Any, Dict, List, Optional


def get_cpc_list(patstat, appln_id: int, limit: int = 500) -> List[str]:
    """
    Module 2A:
    CPC symbols for appln_id.
    """
    res = patstat.sql_query(f"""
    SELECT cpc_class_symbol
    FROM tls224_appln_cpc
    WHERE appln_id = {appln_id}
    LIMIT {limit}
    """, use_legacy_sql=False)

    # keep order as returned; you can sort later if you want
    return [r["cpc_class_symbol"] for r in res if r.get("cpc_class_symbol")]


def get_docdb_family_members(patstat, docdb_family_id: int, limit: int = 5000) -> List[Dict[str, Any]]:
    """
    Module 2B:
    Family members for docdb_family_id using tls201_appln.
    """
    res = patstat.sql_query(f"""
    SELECT
      appln_id, appln_auth, appln_nr, appln_kind,
      appln_filing_date, appln_filing_year,
      granted
    FROM tls201_appln
    WHERE docdb_family_id = {docdb_family_id}
    ORDER BY appln_filing_date
    LIMIT {limit}
    """, use_legacy_sql=False)
    return [dict(r) for r in res]


def summarize_family_geo(members: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Module 2B summary:
    Counts by appln_auth + derived flags.
    """
    counts: Dict[str, int] = {}
    for m in members:
        auth = (m.get("appln_auth") or "").strip()
        if not auth:
            continue
        counts[auth] = counts.get(auth, 0) + 1

    authorities_sorted = sorted(counts.keys(), key=lambda k: (-counts[k], k))

    def has(auth: str) -> bool:
        return counts.get(auth, 0) > 0

    return {
        "family_size": len(members),
        "by_authority": counts,
        "authorities": authorities_sorted,
        "flags": {
            "has_EP": has("EP"),
            "has_WO": has("WO"),
            "has_US": has("US"),
            "has_CN": has("CN"),
            "has_JP": has("JP"),
            "has_KR": has("KR"),
        }
    }


def enrich_card_with_family_and_cpc(patstat, card: Dict[str, Any]) -> Dict[str, Any]:
    """
    Module 2 wrapper:
    Adds CPC list + DOCDB family members + geo summary to an existing card.
    """
    appln_id = int(card["core"]["appln_id"])
    docdb_family_id = int(card["core"]["docdb_family_id"])

    cpc_list = get_cpc_list(patstat, appln_id=appln_id)
    family_members = get_docdb_family_members(patstat, docdb_family_id=docdb_family_id)
    family_summary = summarize_family_geo(family_members)

    card2 = dict(card)  # shallow copy
    card2["cpc"] = {
        "symbols": cpc_list,
        "n_cpc": len(cpc_list),
    }
    card2["family_docdb"] = {
        "docdb_family_id": docdb_family_id,
        "members": family_members,
        **family_summary,
    }
    return card2


# ======================================================================================
# MODULE 3 — MAIN PUBLICATION + CITATION METRICS
# ======================================================================================
# Goal:
#   Choose a "main publication" for citation analysis and compute:
#     - forward citations count
#     - citations-by-year histogram
#
# Important nuance:
#   - For some patents (especially older ones), citations concentrate on A-publications
#     rather than B-publications.
#   - That is why Module 4 also computes robust citations across all EP publications.
#
# Outputs added to card:
#   card["main_publn"] + reason
#   card["citations"] = {
#       cited_pat_publn_id,
#       forward_citations,
#       citations_by_year
#   }
# ======================================================================================


#module 3

from typing import Dict, Any, List, Optional


def choose_main_publication(publications: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Prefer EP B* > EP A* > anything else.
    Returns: {"main_publn": {...} or None, "reason": str}
    """
    if not publications:
        return {"main_publn": None, "reason": "no_publications"}

    # Normalize a bit
    pubs = [dict(p) for p in publications if p.get("pat_publn_id")]

    # 1) EP B*
    ep_b = [p for p in pubs if p.get("publn_auth") == "EP" and str(p.get("publn_kind","")).startswith("B")]
    if ep_b:
        # if multiple, pick latest date (often B1 is later), else first
        #ep_b_sorted = sorted(ep_b, key=lambda p: (p.get("publn_date") or "0000-00-00"))
        ep_b_sorted = sorted(ep_b, key=lambda p: (p.get("publn_date") or date(1,1,1)))
        return {"main_publn": ep_b_sorted[-1], "reason": "prefer_EP_B"}

    # 2) EP A*
    ep_a = [p for p in pubs if p.get("publn_auth") == "EP" and str(p.get("publn_kind","")).startswith("A")]
    if ep_a:
        #ep_a_sorted = sorted(ep_a, key=lambda p: (p.get("publn_date") or "0000-00-00"))
        ep_a_sorted = sorted(ep_a, key=lambda p: (p.get("publn_date") or date(1,1,1)))
        return {"main_publn": ep_a_sorted[-1], "reason": "prefer_EP_A"}

    # 3) fallback: latest dated publn overall
    #pubs_sorted = sorted(pubs, key=lambda p: (p.get("publn_date") or "0000-00-00"))
    pubs_sorted = sorted(pubs, key=lambda p: (p.get("publn_date") or date(1,1,1)))
    return {"main_publn": pubs_sorted[-1], "reason": "fallback_latest_publn"}


def count_forward_citations(patstat, cited_pat_publn_id: int) -> int:
    res = patstat.sql_query(f"""
    SELECT COUNT(*) AS forward_citations
    FROM tls212_citation
    WHERE cited_pat_publn_id = {cited_pat_publn_id}
    """, use_legacy_sql=False)
    return int(res[0]["forward_citations"]) if res else 0


def citations_by_year(patstat, cited_pat_publn_id: int, limit: int = 5000) -> List[Dict[str, Any]]:
    """
    Year histogram of citing publications.
    """
    res = patstat.sql_query(f"""
    SELECT EXTRACT(YEAR FROM p.publn_date) AS y, COUNT(*) AS n
    FROM tls212_citation c
    JOIN tls211_pat_publn p ON p.pat_publn_id = c.pat_publn_id
    WHERE c.cited_pat_publn_id = {cited_pat_publn_id}
      AND p.publn_date IS NOT NULL
    GROUP BY y
    ORDER BY y
    LIMIT {limit}
    """, use_legacy_sql=False)
    return [dict(r) for r in res]


def enrich_card_with_citations(patstat, card: Dict[str, Any]) -> Dict[str, Any]:
    """
    Module 3 wrapper: adds main publication + citation metrics.
    """
    pick = choose_main_publication(card.get("publications", []))
    main_publn = pick["main_publn"]

    card3 = dict(card)
    card3["main_publn"] = main_publn
    card3["main_publn_reason"] = pick["reason"]

    if not main_publn:
        card3["citations"] = {"forward_citations": None, "citations_by_year": []}
        return card3

    cited_id = int(main_publn["pat_publn_id"])
    fwd = count_forward_citations(patstat, cited_id)
    by_year = citations_by_year(patstat, cited_id)

    card3["citations"] = {
        "cited_pat_publn_id": cited_id,
        "forward_citations": fwd,
        "citations_by_year": by_year,
    }
    return card3

# ======================================================================================
# MODULE 4 — LEGAL EVENTS (MAINTENANCE / LAPSE SIGNALS) + ROBUST CITATIONS
# ======================================================================================
# Goal:
#   Add two "business reality" dimensions:
#
#   (1) Legal / maintenance signals (tls231_inpadoc_legal_event)
#       - renewal fee payments (fee_payment_date)
#       - lapses (lapse_date)
#       - reinstatements (reinstate_date)
#       - handle PATSTAT sentinel dates (9999-12-31) as NULL
#
#   (2) Robust citations across ALL EP publications (A/B kinds)
#       - max_any_publn forward citations
#       - per_publication list (A2, A3, B1...) with citation counts
#
# Why it matters:
#   - A patent with renewals paid recently is usually more "alive".
#   - Using only B1 citations can undercount; max-any-publication fixes that.
#
# Outputs added to card:
#   card["legal_events"] = {raw_head, summary}
#   card["citations_robust"] = {per_publication, max_any_publn, sum_all_ep_pubs}
# ======================================================================================


#module 4
from datetime import date
from typing import Any, Dict, List, Optional, Tuple


SENTINEL_DATE = date(9999, 12, 31)


def _clean_date(d: Optional[date]) -> Optional[date]:
    if d is None:
        return None
    return None if d == SENTINEL_DATE else d


def get_legal_events(patstat, appln_id: int, limit: int = 5000) -> List[Dict[str, Any]]:
    """
    Raw legal events from tls231_inpadoc_legal_event, cleaned for sentinel dates.
    """
    res = patstat.sql_query(f"""
    SELECT
      event_auth, event_code,
      event_filing_date, event_publn_date, event_effective_date,
      fee_country, fee_payment_date, fee_renewal_year,
      lapse_country, lapse_date,
      reinstate_country, reinstate_date,
      event_descr, event_text
    FROM tls231_inpadoc_legal_event
    WHERE appln_id = {appln_id}
    ORDER BY COALESCE(event_effective_date, event_publn_date, fee_payment_date, lapse_date) DESC
    LIMIT {limit}
    """, use_legacy_sql=False)

    out = []
    for r in res:
        rr = dict(r)
        # Clean key dates
        for k in ["event_filing_date", "event_publn_date", "event_effective_date",
                  "fee_payment_date", "lapse_date", "reinstate_date"]:
            rr[k] = _clean_date(rr.get(k))
        # Normalize blank country codes
        for k in ["fee_country", "lapse_country", "reinstate_country", "event_auth"]:
            if rr.get(k) is not None:
                rr[k] = str(rr[k]).strip()
        out.append(rr)
    return out


def summarize_legal_status(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Produces simple, explainable legal signals:
    - latest renewal fee payment (any country)
    - lapse events list
    - reinstatements list
    - narrative summary string
    """
    fee_payments = []
    lapses = []
    reinstates = []

    for e in events:
        if e.get("fee_payment_date"):
            fee_payments.append({
                "fee_country": e.get("fee_country"),
                "fee_payment_date": e.get("fee_payment_date"),
                "fee_renewal_year": e.get("fee_renewal_year"),
                "event_code": e.get("event_code"),
                "event_auth": e.get("event_auth"),
            })
        if e.get("lapse_date"):
            lapses.append({
                "lapse_country": e.get("lapse_country"),
                "lapse_date": e.get("lapse_date"),
                "event_code": e.get("event_code"),
                "event_auth": e.get("event_auth"),
            })
        if e.get("reinstate_date"):
            reinstates.append({
                "reinstate_country": e.get("reinstate_country"),
                "reinstate_date": e.get("reinstate_date"),
                "event_code": e.get("event_code"),
                "event_auth": e.get("event_auth"),
            })

    fee_payments_sorted = sorted(
        fee_payments,
        key=lambda x: (x["fee_payment_date"] or date(1, 1, 1)),
        reverse=True,
    )
    lapses_sorted = sorted(
        lapses,
        key=lambda x: (x["lapse_date"] or date(1, 1, 1)),
        reverse=True,
    )
    reinstates_sorted = sorted(
        reinstates,
        key=lambda x: (x["reinstate_date"] or date(1, 1, 1)),
        reverse=True,
    )

    latest_fee = fee_payments_sorted[0] if fee_payments_sorted else None
    latest_lapse = lapses_sorted[0] if lapses_sorted else None
    latest_reinstate = reinstates_sorted[0] if reinstates_sorted else None
    parts = []
    notes = []
    
    if latest_fee:
        notes.append("fee_country is the designated/validation state where a post-grant fee/renewal-type payment is observed (not an EPO renewal fee).")
        fee_ctry = latest_fee.get("fee_country") or "unknown country"
        parts.append(f"Latest fee payment observed: {latest_fee['fee_payment_date']} ({fee_ctry})")
    
    if latest_lapse:
        lapse_ctry = latest_lapse.get("lapse_country") or "unknown country"
        parts.append(f"Latest lapse observed: {latest_lapse['lapse_date']} ({lapse_ctry})")
    
    if latest_reinstate:
        rein_ctry = latest_reinstate.get("reinstate_country") or "unknown country"
        parts.append(f"Latest reinstatement observed: {latest_reinstate['reinstate_date']} ({rein_ctry})")


    summary = " | ".join(parts) if parts else "No renewal/lapse/reinstatement signals found in tls231 (PATSTAT)."

    return {
        "n_events": len(events),
        "latest_fee_payment": latest_fee,
        "latest_lapse": latest_lapse,
        "latest_reinstate": latest_reinstate,
        "fee_payments": fee_payments_sorted[:50],   # keep top 50 for safety
        "lapses": lapses_sorted[:50],
        "reinstatements": reinstates_sorted[:50],
        "summary": summary,
        "notes": notes,
    }


def citations_across_publications(patstat, publications: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Robust citation metrics across all EP publications in the card.
    Returns:
      - per_publn list with counts
      - max citations + which publn
      - sum citations across pubs (note: may double count in edge cases)
    """
    per = []
    total = 0
    best = None

    for p in publications:
        if p.get("publn_auth") != "EP":
            continue
        pid = int(p["pat_publn_id"])
        n = count_forward_citations(patstat, pid)
        row = {**p, "forward_citations": n}
        per.append(row)
        total += n
        if best is None or n > best["forward_citations"]:
            best = row

    # sort by citations desc, then date
    per_sorted = sorted(per, key=lambda r: (-r["forward_citations"], r.get("publn_date") or date(1, 1, 1)))
    return {
        "per_publication": per_sorted,
        "max_any_publn": best,
        "sum_all_ep_pubs": total,
    }


def enrich_card_with_legal_and_robust_citations(patstat, card: Dict[str, Any]) -> Dict[str, Any]:
    """
    Module 4 wrapper:
    - Adds legal events summary
    - Adds robust citations across all EP publications
    """
    appln_id = int(card["core"]["appln_id"])

    # Legal
    events = get_legal_events(patstat, appln_id=appln_id)
    legal = summarize_legal_status(events)

    # Robust citations across pubs
    pubs = card.get("publications", [])
    robust = citations_across_publications(patstat, pubs)

    card4 = dict(card)
    card4["legal_events"] = {
        "raw_head": events[:30],   # keep a preview
        "summary": legal,
    }
    card4["citations_robust"] = robust
    return card4


# ======================================================================================
# MODULE 5 — END-TO-END REPORT BUILDERS (SINGLE + PORTFOLIO)
# ======================================================================================
# Goal:
#   Provide clean entry points for downstream usage:
#
#   - build_patent_report(patstat, ep_nr) -> full enriched report dict
#   - build_portfolio_report(patstat, [ep1, ep2, ...]) -> list of reports + aggregates
#
# Portfolio aggregates (v1):
#   - avg family size
#   - avg max forward citations (max_any_publn)
#   - granted ratio
#
# Future portfolio additions:
#   - portfolio-level scatter plot coordinates
#   - portfolio concentration risk (one patent dominates)
#   - tech clustering (CPC-based) and diversity score
# ======================================================================================

#module 5

from datetime import date
from typing import Any, Dict, List, Optional, Tuple


def build_patent_report(patstat, ep_nr: str, ep_auth: str = "EP") -> Dict[str, Any]:
    """
    End-to-end v1 report for ONE EP application number.
    """
    # Modules 0-1
    card = build_patent_card(patstat, ep_nr, ep_auth=ep_auth)

    # Module 2
    card2 = enrich_card_with_family_and_cpc(patstat, card)

    # Module 3
    card3 = enrich_card_with_citations(patstat, card2)

    # Module 4
    card4 = enrich_card_with_legal_and_robust_citations(patstat, card3)

    return card4


def build_portfolio_report(patstat, ep_list: List[str], ep_auth: str = "EP") -> Dict[str, Any]:
    """
    End-to-end v1 report for a portfolio of EP application numbers.
    Returns per-patent reports + lightweight aggregates.
    """
    reports = []
    for ep in ep_list:
        try:
            reports.append(build_patent_report(patstat, ep, ep_auth=ep_auth))
        except Exception as e:
            reports.append({
                "input": {"ep_auth": ep_auth, "ep_nr": ep},
                "error": str(e),
            })

    # Aggregates (ignore errored items)
    ok = [r for r in reports if "error" not in r and r.get("core")]
    n_ok = len(ok)

    def safe_int(x, default=0):
        try:
            return int(x)
        except Exception:
            return default

    family_sizes = [safe_int(r["family_docdb"]["family_size"]) for r in ok]
    max_citations = [
        safe_int((r.get("citations_robust", {}).get("max_any_publn") or {}).get("forward_citations"), 0)
        for r in ok
    ]
    granted_flags = [1 if r["core"].get("granted") == "Y" else 0 for r in ok]

    agg = {
        "n_input": len(ep_list),
        "n_ok": n_ok,
        "n_errors": len(reports) - n_ok,
        "avg_family_size": (sum(family_sizes) / n_ok) if n_ok else None,
        "avg_max_forward_citations": (sum(max_citations) / n_ok) if n_ok else None,
        "granted_ratio": (sum(granted_flags) / n_ok) if n_ok else None,
    }

    return {"portfolio": {"ep_list": ep_list, "aggregates": agg}, "reports": reports}

# ======================================================================================
# MODULE 6 — SCORE v0 (EXPLAINABLE BASELINE)
# ======================================================================================
# Goal:
#   Provide a transparent baseline score (0..100) with justification.
#
# This is NOT "true monetary valuation" — it is a prioritization / comparison signal.
#
# Score components:
#   - Citations (max_any_publn)  -> proxy for technological impact / relevance [0..40]
#   - Family breadth            -> proxy for market interest / protection effort [0..25]
#   - Legal activity            -> proxy for ongoing maintenance / alive status [0..20]
#   - Term remaining (20y)      -> proxy for remaining exclusive window [0..15]
#
# Future scoring upgrades:
#   - Field-normalized citations (CPC cohort normalization)
#   - Claim breadth / independent claims / claim length
#   - Examiner X/Y evidence (blocking power)  <-- big missing piece
#   - ML / embeddings / LLM scoring, only when justified
# ======================================================================================

    
#module 6

def years_remaining_20y(filing_date: Optional[date], today: Optional[date] = None) -> Optional[float]:
    if filing_date is None:
        return None
    if today is None:
        today = date.today()
    # approx; good enough for v1
    years_passed = (today - filing_date).days / 365.25
    return max(0.0, 20.0 - years_passed)


def score_v0(report: Dict[str, Any], today: Optional[date] = None) -> Dict[str, Any]:
    """
    Explainable score (0-100) based on:
      - max citations across EP publications
      - family breadth (size + key jurisdictions)
      - legal activity (latest renewal vs lapse)
      - remaining term estimate
    """
    if today is None:
        today = date.today()

    core = report.get("core") or {}
    fam = report.get("family_docdb") or {}
    legal = (report.get("legal_events") or {}).get("summary") or {}
    robust = report.get("citations_robust") or {}
    max_pub = robust.get("max_any_publn") or {}

    # --- Citations bucket (0-40)
    max_cit = int(max_pub.get("forward_citations") or 0)
    # simple saturation: 0 -> 0, 50 -> ~20, 200 -> ~30, 1000+ -> 40
    cit_score = min(40, int(10 * (max_cit ** 0.5)))  # sqrt curve

    # --- Family bucket (0-25)
    family_size = int(fam.get("family_size") or 0)
    flags = (fam.get("flags") or {})
    breadth_score = 0
    breadth_score += min(10, family_size)  # up to 10
    # key jurisdictions bonus
    if flags.get("has_US"): breadth_score += 6
    if flags.get("has_JP"): breadth_score += 4
    if flags.get("has_KR"): breadth_score += 3
    if flags.get("has_WO"): breadth_score += 2
    # cap
    family_score = min(25, breadth_score)

    # --- Legal activity bucket (0-20)
    latest_fee = legal.get("latest_fee_payment")  # dict or None
    latest_lapse = legal.get("latest_lapse")      # dict or None
    legal_score = 0
    if latest_fee and latest_fee.get("fee_payment_date"):
        # more recent -> better
        days = (today - latest_fee["fee_payment_date"]).days
        if days <= 365: legal_score = 20
        elif days <= 3 * 365: legal_score = 14
        elif days <= 7 * 365: legal_score = 8
        else: legal_score = 4
    if latest_lapse and latest_lapse.get("lapse_date"):
        # penalize if lapse is recent
        days = (today - latest_lapse["lapse_date"]).days
        if days <= 365: legal_score = max(0, legal_score - 10)
        elif days <= 3 * 365: legal_score = max(0, legal_score - 6)

    # --- Remaining term bucket (0-15)
    yrem = years_remaining_20y(core.get("appln_filing_date"), today=today)
    if yrem is None:
        term_score = 0
    else:
        if yrem >= 10: term_score = 15
        elif yrem >= 5: term_score = 10
        elif yrem > 0: term_score = 5
        else: term_score = 0

    total = int(min(100, cit_score + family_score + legal_score + term_score))

    explanation = []
    explanation.append(f"Max forward citations across EP publications: {max_cit} (drives citation score).")
    explanation.append(f"DOCDB family size: {family_size} | footprint: {fam.get('by_authority')}.")
    explanation.append(f"Legal signals (designated-state fee/lapse proxies): {legal.get('summary')}.")
    

    if yrem is not None:
        explanation.append(f"Estimated years remaining (20y baseline): {yrem:.1f}.")

    return {
        "score_total": total,
        "score_components": {
            "citations": cit_score,
            "family": family_score,
            "legal_activity": legal_score,
            "term_remaining": term_score,
        },
        "explanation": explanation,
        "raw": {
            "max_citations": max_cit,
            "family_size": family_size,
            "years_remaining_est": yrem,
        }
    }

# ======================================================================================
# TODO RADAR — "ORIGINAL IDEA" VS "CURRENT PATSTAT-ONLY SKELETON"
# ======================================================================================
#
# ✅ IMPLEMENTED IN v1 (THIS FILE):
#   [x] EP application number → appln_id resolution
#   [x] Title + abstract
#   [x] Applicant(s)
#   [x] Publications
#   [x] CPC tech field proxy
#   [x] DOCDB family footprint (geo breadth)
#   [x] Forward citations (main publication)
#   [x] Robust citations (max across EP publications)
#   [x] Legal renewal/lapse signals (PATSTAT INPADOC events)
#   [x] Portfolio comparison + aggregates
#   [x] Explainable score v0 + textual justification
#
# ⚠️ PARTIALLY ADDRESSED (NEEDS IMPROVEMENT):
#   [~] "Alive" status: we only use fee/lapse signals; needs country-level validity logic
#   [~] Citation meaning: citations are not field-normalized yet
#   [~] Portfolio visualization: data exists, chart not implemented here
#
# ❌ NOT IMPLEMENTED YET (MAJOR FUTURE WORK):
#   [ ] Input types beyond EP nr:
#       - EP publication number (EP0404097) direct input mode
#       - PDF upload parsing (extract EP nr / title / claims)
#       - Patent title search / similarity search
#       - Company name input → portfolio extraction (entity resolution)
#
#   [ ] Claim / scope features (NOT in PATSTAT):
#       - independent claims count
#       - claim length proxy (short/broad vs long/narrow)
#       - claim dependency tree
#       - "patent block" / "hidden gem" concepts need definitions + features
#
#   [ ] Examiner evidence / blocking power:
#       - X/Y category citations from search report (EPO-specific)
#       - Opposition / litigation risk signals
#
#   [ ] Economic valuation:
#       - royalty relief / DCF / option-like valuation models
#       - firm profitability / market signals (external data)
#
#   [ ] ML / AI:
#       - embeddings for semantic similarity and novelty
#       - LLM summaries, keyword extraction, claim interpretation
#       - predictive models (citation growth, survival/maintenance prediction)
#
# ======================================================================================

