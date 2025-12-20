# tests/test_demo_v2.py
#
# Run:
#   python -m tests.test_demo_v2
#
# Goal:
#   - More single EP tests
#   - More portfolio tests
#   - More invariants + edge cases
#   - A “graph-ready” (X,Y,alive) point for each patent
#
# NOTE:
#   This assumes you already applied the two tweaks:
#     (1) Module 3: `from datetime import date`
#     (2) Legal summary: keep note OUT of `summary` (optional) and expose in `notes`
#
# If you haven't done (2), this file still works; legal_notes will just be empty.

from __future__ import annotations

from datetime import date
from pprint import pprint
from typing import Any, Dict, List, Optional

from main_pipeline import (
    get_patstat,
    build_patent_report,
    build_portfolio_report,
    score_v0,
    choose_main_publication,  # unit tests
)


# ======================================================================================
# HELPERS
# ======================================================================================

def _pub_brief(p: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Compact publication descriptor for logs."""
    if not p:
        return None
    return {
        "publn_auth": p.get("publn_auth"),
        "publn_nr": p.get("publn_nr"),
        "publn_kind": p.get("publn_kind"),
        "publn_date": p.get("publn_date"),
        "pat_publn_id": p.get("pat_publn_id"),
        "forward_citations": p.get("forward_citations"),
    }


def compute_plot_point(report: Dict[str, Any]) -> Dict[str, Any]:
    """
    Minimal "graph point" for the future scatter plot:
      X = max forward citations across EP publications
      Y = DOCDB family size
      alive = latest fee payment within 3y (proxy)
    """
    fam_size = int((report.get("family_docdb") or {}).get("family_size") or 0)

    robust_max = (report.get("citations_robust") or {}).get("max_any_publn") or {}
    x_cit = int(robust_max.get("forward_citations") or 0)

    legal = ((report.get("legal_events") or {}).get("summary") or {})
    latest_fee = legal.get("latest_fee_payment") or {}
    latest_fee_date = latest_fee.get("fee_payment_date")

    alive = False
    if latest_fee_date:
        alive = (date.today() - latest_fee_date).days <= 3 * 365

    return {
        "x_max_citations": x_cit,
        "y_family_size": fam_size,
        "alive_proxy": alive,
    }


def _safe_get(d: Dict[str, Any], path: List[str], default=None):
    cur = d
    for k in path:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur


# ======================================================================================
# SINGLE PATENT TESTS
# ======================================================================================

def test_single(ep: str, patstat_env: str = "PROD") -> Dict[str, Any]:
    patstat = get_patstat(patstat_env)
    report = build_patent_report(patstat, ep)
    score = score_v0(report, today=date.today())

    main_publn = report.get("main_publn")
    robust_max = (report.get("citations_robust") or {}).get("max_any_publn")

    legal_summary_obj = ((report.get("legal_events") or {}).get("summary") or {})
    legal_summary = legal_summary_obj.get("summary")
    legal_notes = legal_summary_obj.get("notes", [])  # only exists if you implemented tweak (2)

    # Pretty print
    print("\n" + "=" * 98)
    print(f"SINGLE PATENT TEST — EP{ep}")
    print("=" * 98)

    payload = {
        "ep": ep,
        "title": _safe_get(report, ["text", "title"]),
        "granted": _safe_get(report, ["core", "granted"]),
        "filing_date": _safe_get(report, ["core", "appln_filing_date"]),

        "family_size": _safe_get(report, ["family_docdb", "family_size"]),
        "family_by_auth": _safe_get(report, ["family_docdb", "by_authority"]),

        "main_publn": _pub_brief(main_publn),
        "main_publn_reason": report.get("main_publn_reason"),

        "robust_max_publn": _pub_brief(robust_max),
        "citations_main": _safe_get(report, ["citations", "forward_citations"]),
        "citations_max_any": (robust_max or {}).get("forward_citations"),

        "legal_summary": legal_summary,
        "legal_notes": legal_notes,

        "score_total": score["score_total"],
        "score_components": score["score_components"],
        "explanation": score["explanation"],

        "plot_point": compute_plot_point(report),
        "cpc_head": (_safe_get(report, ["cpc", "symbols"], []) or [])[:10],
        "n_cpc": _safe_get(report, ["cpc", "n_cpc"]),
    }
    pprint(payload)
    return {"report": report, "score": score, "payload": payload}


def test_single_batch(ep_list: List[str], patstat_env: str = "PROD") -> List[Dict[str, Any]]:
    """
    Runs multiple single patents, returns compact table-like summary.
    """
    results = []
    for ep in ep_list:
        try:
            out = test_single(ep, patstat_env=patstat_env)
            rep = out["report"]
            robust_max = (rep.get("citations_robust") or {}).get("max_any_publn") or {}
            legal = ((rep.get("legal_events") or {}).get("summary") or {})
            results.append({
                "ep": ep,
                "ok": True,
                "title": _safe_get(rep, ["text", "title"]),
                "granted": _safe_get(rep, ["core", "granted"]),
                "family_size": _safe_get(rep, ["family_docdb", "family_size"]),
                "max_cit": int(robust_max.get("forward_citations") or 0),
                "max_cit_kind": robust_max.get("publn_kind"),
                "latest_fee": (legal.get("latest_fee_payment") or {}).get("fee_payment_date"),
                "score": out["score"]["score_total"],
            })
        except Exception as e:
            results.append({"ep": ep, "ok": False, "error": str(e)})

    print("\n" + "=" * 98)
    print("SINGLE BATCH SUMMARY")
    print("=" * 98)
    pprint(results)
    return results


# ======================================================================================
# PORTFOLIO TESTS
# ======================================================================================

def test_portfolio(ep_list: List[str], patstat_env: str = "PROD") -> Dict[str, Any]:
    patstat = get_patstat(patstat_env)
    pr = build_portfolio_report(patstat, ep_list)

    print("\n" + "=" * 98)
    print(f"PORTFOLIO TEST — {ep_list}")
    print("=" * 98)
    pprint(pr["portfolio"]["aggregates"])

    scored = []
    for rep in pr["reports"]:
        if "error" in rep:
            scored.append({"ep": rep["input"]["ep_nr"], "error": rep["error"]})
            continue

        sc = score_v0(rep, today=date.today())
        robust_max = (rep.get("citations_robust") or {}).get("max_any_publn") or {}
        legal = ((rep.get("legal_events") or {}).get("summary") or {})

        scored.append({
            "ep": rep["core"]["appln_nr"],
            "score": sc["score_total"],
            "max_cit": int(robust_max.get("forward_citations") or 0),
            "max_cit_pub_kind": robust_max.get("publn_kind"),
            "max_cit_pub_date": robust_max.get("publn_date"),
            "family_size": rep["family_docdb"]["family_size"],
            "latest_fee": (legal.get("latest_fee_payment") or {}).get("fee_payment_date"),
            "plot_point": compute_plot_point(rep),
        })

    pprint(scored)
    return {"portfolio": pr, "scored": scored}


def test_portfolio_suite(patstat_env: str = "PROD"):
    """
    Runs multiple portfolios:
      - demo portfolio (yours)
      - mix with a bogus EP to confirm error handling
      - larger portfolio = stress test of wrapper & aggregation
    """
    portfolios = [
        ("DEMO_CORE", ["15860005", "13849544", "07740080", "11835510"]),
        ("MIX_WITH_ERROR", ["15860005", "00000000", "13849544"]),  # should create 1 error
        ("BIGGER_MIX", ["15860005", "13849544", "07740080", "11835510", "12761442"]),
    ]

    for name, eps in portfolios:
        print("\n" + "#" * 98)
        print(f"PORTFOLIO SUITE — {name}")
        print("#" * 98)
        test_portfolio(eps, patstat_env=patstat_env)


# ======================================================================================
# INVARIANTS (HARD CORRECTNESS CHECKS)
# ======================================================================================

def test_invariants(ep: str, patstat_env: str = "PROD"):
    """
    Hard validation checks for demo correctness.
    If these fail, something is broken or PATSTAT schema changed.
    """
    patstat = get_patstat(patstat_env)
    r = build_patent_report(patstat, ep)

    # Invariant 1: appln_id exists
    assert r["core"]["appln_id"] is not None

    # Invariant 2: family_docdb is present
    assert "family_docdb" in r and r["family_docdb"]["family_size"] >= 1

    # Invariant 3: citations robust list includes all EP publications
    ep_pubs = [p for p in r["publications"] if p.get("publn_auth") == "EP"]
    robust_pubs = r["citations_robust"]["per_publication"]
    assert len(robust_pubs) == len(ep_pubs), f"robust pubs {len(robust_pubs)} != EP pubs {len(ep_pubs)}"

    # Invariant 4: if main_publn is EP B*, reason should be prefer_EP_B
    mp = r.get("main_publn")
    if mp and mp.get("publn_auth") == "EP" and str(mp.get("publn_kind", "")).startswith("B"):
        assert r.get("main_publn_reason") == "prefer_EP_B"

    # Invariant 5: robust max citations must be >= main citations
    main_cit = int((r.get("citations") or {}).get("forward_citations") or 0)
    max_any = int(((r.get("citations_robust") or {}).get("max_any_publn") or {}).get("forward_citations") or 0)
    assert max_any >= main_cit, f"Expected robust max >= main, got {max_any} < {main_cit}"

    # Invariant 6: plot point is numeric and non-negative
    pt = compute_plot_point(r)
    assert pt["x_max_citations"] >= 0
    assert pt["y_family_size"] >= 0

    print("\n" + "=" * 98)
    print(f"INVARIANTS OK — EP{ep}")
    print("=" * 98)


def test_invariants_batch(ep_list: List[str], patstat_env: str = "PROD"):
    print("\n" + "#" * 98)
    print("INVARIANTS BATCH")
    print("#" * 98)
    for ep in ep_list:
        try:
            test_invariants(ep, patstat_env=patstat_env)
        except Exception as e:
            if "No application found" in str(e):
                print(f"[SKIP] invariants for EP{ep}: not found in PATSTAT")
            else:
                print(f"[FAILED] invariants for EP{ep}: {e}")



# ======================================================================================
# UNIT TESTS (PURE LOGIC, NO PATSTAT DEPENDENCY)
# ======================================================================================

def test_choose_main_publication_empty():
    out = choose_main_publication([])
    assert out["main_publn"] is None
    assert out["reason"] == "no_publications"
    print("\n" + "=" * 98)
    print("UNIT OK — choose_main_publication handles empty list")
    print("=" * 98)


def test_choose_main_publication_prefers_B():
    pubs = [
        {"pat_publn_id": 1, "publn_auth": "EP", "publn_kind": "A1", "publn_date": date(2020, 1, 1)},
        {"pat_publn_id": 2, "publn_auth": "EP", "publn_kind": "B1", "publn_date": date(2022, 1, 1)},
        {"pat_publn_id": 3, "publn_auth": "EP", "publn_kind": "A2", "publn_date": date(2021, 1, 1)},
    ]
    out = choose_main_publication(pubs)
    assert out["reason"] == "prefer_EP_B"
    assert out["main_publn"]["pat_publn_id"] == 2
    print("\n" + "=" * 98)
    print("UNIT OK — choose_main_publication prefers EP B*")
    print("=" * 98)


# ======================================================================================
# INPUT HARDENING TEST (DEPENDS ON YOUR DIGIT-ONLY GUARD)
# ======================================================================================

def test_bad_input_rejected(patstat_env: str = "PROD"):
    patstat = get_patstat(patstat_env)
    bad = "EP 15 86 0005; DROP tls201_appln;"
    try:
        build_patent_report(patstat, bad)
        raise AssertionError("Expected ValueError for non-digit EP number")
    except ValueError:
        print("\n" + "=" * 98)
        print("SECURITY OK — bad EP input rejected (digits-only sanitizer)")
        print("=" * 98)


# ======================================================================================
# RUNNER
# ======================================================================================

if __name__ == "__main__":
    ENV = "PROD"

    # ----------------------------------------------------------------------
    # 1) Baseline singles (yours)
    # ----------------------------------------------------------------------
    test_single("15860005", patstat_env=ENV)

    # ----------------------------------------------------------------------
    # 2) More singles (expand demo coverage)
    #     - includes your earlier example list
    # ----------------------------------------------------------------------
    more_singles = [
        "15860005",
        "13849544",
        "07740080",
        "11835510",
        "12761442",
    ]
    test_single_batch(more_singles, patstat_env=ENV)

    # ----------------------------------------------------------------------
    # 3) Portfolios suite
    # ----------------------------------------------------------------------
    test_portfolio_suite(patstat_env=ENV)

    # ----------------------------------------------------------------------
    # 4) Invariants on multiple EPs (catches schema changes / weird cases)
    # ----------------------------------------------------------------------
    test_invariants_batch(more_singles, patstat_env=ENV)

    # ----------------------------------------------------------------------
    # 5) Pure unit tests
    # ----------------------------------------------------------------------
    test_choose_main_publication_empty()
    test_choose_main_publication_prefers_B()

    # ----------------------------------------------------------------------
    # 6) Security / input hardening test
    # ----------------------------------------------------------------------
    test_bad_input_rejected(patstat_env=ENV)
