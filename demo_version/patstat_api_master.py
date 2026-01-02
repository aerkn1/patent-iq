"""
====================================================================================================
====================================================================================================
====================  PATSTAT PATENT VALUATION / PORTFOLIO API  (ENRICHED v1.1)  ===================
====================================================================================================
====================================================================================================

WHAT THIS FILE IS
----------------------------------------------------------------------------------------------------
A single-file FastAPI service that exposes a PATSTAT-only “patent card + analytics” pipeline as a
REST API. It is meant to be:

  - Demo-ready (runs locally / on TIP via uvicorn)
  - Explainable (features are transparent, no black-box valuation)
  - Modular (clear “MODULE” sections separated by very visible separators)
  - Extensible (clear TODO radar and upgrade hooks)

CONTEXT / GOAL
----------------------------------------------------------------------------------------------------
You currently have:
  1) A PATSTAT-only valuation skeleton script (working pipeline + score v0)
  2) A working FastAPI version (same pipeline exposed as endpoints)
  3) A PATSTAT primer notebook (same core tables used)
  4) A “product idea” PDF that hints at richer directions (X/Y evidence, opposition, BPI, AI, etc.)

This file extends the API script WITHOUT pretending we can finish the full product.
We keep PATSTAT-only as the ground truth, but we add more PATSTAT signals and structure so we can
iterate.

IMPORTANT: Some “idea PDF” features (X/Y categories, opposition, litigation, BPI, AI embeddings, etc.)
are NOT implementable via PATSTAT alone in TIP without additional datasets/APIs. Those are captured
explicitly in the TODO / FUTURE EXTENSIONS section at the end.

Swagger / OpenAPI behind TIP proxy
----------------------------------------------------------------------------------------------------
TIP proxy paths often look like:
  /user/<token>/proxy/<port>/

Swagger failing with:
  "Fetch error response status is 404 /openapi.json"

Usually this means: the Swagger UI (served at /docs) is requesting /openapi.json at the wrong base
path because the upstream proxy is not passing root_path correctly.

This file fixes it by:
  - using a middleware that reads X-Forwarded-Prefix and sets request.scope["root_path"]
  - generating OpenAPI "servers" dynamically from the same prefix
  - keeping openapi_url="/openapi.json" and docs_url="/docs" stable

Run (local):
  uvicorn patstat_api_enriched:app --host 0.0.0.0 --port 8000

Run (TIP proxy-friendly):
  uvicorn patstat_api_enriched:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips="*"

====================================================================================================
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple

from fastapi import Body, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# PATSTAT client available in TIP environment
from epo.tipdata.patstat import PatstatClient


# ====================================================================================================
# ====================================================================================================
# ==========================================  MODULE 00  ============================================
# ================================  CONFIG / ENV / RUNTIME HELPERS  ==================================
# ====================================================================================================
# ====================================================================================================

EP_AUTH_DEFAULT = os.getenv("EP_AUTH_DEFAULT", "EP")

# If you are behind TIP proxy, you can set this, but we ALSO dynamically override root_path from headers.
DEFAULT_ROOT_PATH = os.getenv("ROOT_PATH", "/user/oB3q2LPSPjmZn99ghZ4vQ7/proxy/8000")  # e.g. "/user/<token>/proxy/8000"

PATSTAT_ENV = os.getenv("PATSTAT_ENV", "PROD")  # "PROD" in TIP
API_TITLE = os.getenv("API_TITLE", "Patent Value Estimator (PATSTAT-only, enriched)")
API_VERSION = os.getenv("API_VERSION", "1.1.0")

# Safety / performance knobs
DEFAULT_LIMIT = int(os.getenv("DEFAULT_LIMIT", "200"))
MAX_LIMIT = int(os.getenv("MAX_LIMIT", "2000"))

# Cohort normalization can be expensive, keep bounded.
MAX_COHORT_SIZE = int(os.getenv("MAX_COHORT_SIZE", "2000"))
DEFAULT_COHORT_SAMPLE = int(os.getenv("DEFAULT_COHORT_SAMPLE", "500"))

# Simple in-memory cache (per-process). Good enough for demo; replace with Redis later.
@dataclass
class CacheEntry:
    expires_at: float
    value: Any


_CACHE: Dict[str, CacheEntry] = {}
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "900"))  # 15 min

def cache_get_many(prefix: str, keys: List[int]) -> Dict[int, Any]:
    out: Dict[int, Any] = {}
    for k in keys:
        v = cache_get(f"{prefix}:{k}")
        if v is not None:
            out[int(k)] = v
    return out

def cache_set_many(prefix: str, mapping: Dict[int, Any], ttl_seconds: Optional[int] = None) -> None:
    if ttl_seconds is None:
        ttl_seconds = CACHE_TTL_SECONDS
    for k, v in mapping.items():
        cache_set(f"{prefix}:{int(k)}", v, ttl_seconds=ttl_seconds)

        
def cache_get(key: str) -> Optional[Any]:
    ent = _CACHE.get(key)
    if not ent:
        return None
    if ent.expires_at < time.time():
        _CACHE.pop(key, None)
        return None
    return ent.value


def cache_set(key: str, value: Any, ttl_seconds: int = CACHE_TTL_SECONDS) -> None:
    _CACHE[key] = CacheEntry(expires_at=time.time() + ttl_seconds, value=value)


def clamp_limit(x: int) -> int:
    return max(1, min(int(x), MAX_LIMIT))


def now_utc_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def _jsonable(obj: Any) -> Any:
    """FastAPI JSON helper: PATSTAT returns date/datetime objects inside dicts."""
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {k: _jsonable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_jsonable(v) for v in obj]
    return obj


def get_patstat(env: str = PATSTAT_ENV) -> PatstatClient:
    """Create a PATSTAT client. In TIP this is typically just PatstatClient("PROD")."""
    return PatstatClient(env)


patstat = get_patstat(PATSTAT_ENV)


# ====================================================================================================
# ====================================================================================================
# ==========================================  MODULE 01  ============================================
# =====================================  INPUT NORMALIZATION  =======================================
# ====================================================================================================
# ====================================================================================================

def clean_ep_application_number(ep_nr: str) -> str:
    """
    Clean EP application number input.

    Current accepted format:
      - digits only (after removing 'EP' and spaces), e.g. "15860005"

    Future:
      - support EP publication numbers (EP0404097...) and map to appln_id
      - support WO/PCT resolution paths
    """
    ep_nr_clean = ep_nr.strip().upper().replace("EP", "").replace(" ", "")
    if not ep_nr_clean.isdigit():
        raise ValueError(
            f"Invalid EP application number '{ep_nr}'. "
            f"After cleaning it became '{ep_nr_clean}', but we only accept digits for now."
        )
    return ep_nr_clean


# ====================================================================================================
# ====================================================================================================
# ==========================================  MODULE 02  ============================================
# ================================  CORE RESOLUTION (EP NR -> appln_id)  =============================
# ====================================================================================================
# ====================================================================================================

def resolve_ep_application(
    patstat: PatstatClient,
    ep_nr: str,
    ep_auth: str = EP_AUTH_DEFAULT,
) -> Dict[str, Any]:
    """
    Resolve an EP application number (e.g. '15860005') to:
      - appln_id
      - filing date/year
      - granted flag
      - docdb_family_id, inpadoc_family_id

    PATSTAT table:
      - tls201_appln
    """
    ep_nr_clean = clean_ep_application_number(ep_nr)

    res = patstat.sql_query(
        f"""
        SELECT appln_id, appln_auth, appln_nr, appln_kind,
               appln_filing_date, appln_filing_year,
               granted, docdb_family_id, inpadoc_family_id
        FROM tls201_appln
        WHERE appln_auth = '{ep_auth}'
          AND appln_nr = '{ep_nr_clean}'
        """,
        use_legacy_sql=False,
    )

    if not res:
        raise ValueError(f"No application found for {ep_auth}{ep_nr_clean}")

    out = dict(res[0])
    out["input_ep_nr"] = ep_nr
    out["ep_nr_clean"] = ep_nr_clean
    out["multiple_matches"] = (len(res) > 1)
    return out

# =============================================================================
# Module 2B — PRIORITY (tls204_appln_prior) + earliest priority date
# =============================================================================

def get_priority_links(patstat: PatstatClient, appln_id: int, limit: int = 5000) -> List[Dict[str, Any]]:
    """
    Returns priority links for appln_id.

    PATSTAT:
      - tls204_appln_prior: appln_id -> prior_appln_id (+ sequence)
      - tls201_appln: prior_appln_id -> prior filing date/auth/nr

    Output:
      - list of priority applications with their filing date, auth, nr, kind
    """
    limit = int(limit)

    res = patstat.sql_query(
        f"""
        SELECT
          pr.prior_appln_seq_nr,
          pr.prior_appln_id,
          a.appln_auth AS prior_appln_auth,
          a.appln_nr   AS prior_appln_nr,
          a.appln_kind AS prior_appln_kind,
          a.appln_filing_date AS prior_appln_filing_date,
          a.appln_filing_year AS prior_appln_filing_year
        FROM tls204_appln_prior pr
        JOIN tls201_appln a ON a.appln_id = pr.prior_appln_id
        WHERE pr.appln_id = {int(appln_id)}
        ORDER BY pr.prior_appln_seq_nr
        LIMIT {limit}
        """,
        use_legacy_sql=False,
    )
    return [dict(r) for r in res]


def summarize_priorities(priority_rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Explainable priority summary:
      - earliest priority filing date
      - priority count
      - priority countries (by appln_auth)
      - age delta (filing_date - earliest_priority_date) computed later in report builder
    """
    if not priority_rows:
        return {
            "n_priorities": 0,
            "earliest_priority_date": None,
            "priority_authorities": [],
            "by_authority": {},
        }

    # Earliest priority filing date
    dates = [r.get("prior_appln_filing_date") for r in priority_rows if r.get("prior_appln_filing_date")]
    earliest = min(dates) if dates else None

    # Authority mix
    by_auth: Dict[str, int] = {}
    for r in priority_rows:
        auth = (r.get("prior_appln_auth") or "").strip() or "UNK"
        by_auth[auth] = by_auth.get(auth, 0) + 1

    auth_sorted = sorted(by_auth.keys(), key=lambda k: (-by_auth[k], k))

    return {
        "n_priorities": len(priority_rows),
        "earliest_priority_date": earliest,
        "priority_authorities": auth_sorted,
        "by_authority": by_auth,
    }


# =============================================================================
# Module 2C — IPC (tls209_appln_ipc) + coarse buckets
# =============================================================================

def get_ipc_list(patstat: PatstatClient, appln_id: int, limit: int = 2000) -> List[Dict[str, Any]]:
    """
    Raw IPC rows for appln_id.

    PATSTAT:
      - tls209_appln_ipc
        fields you observed: ipc_class_symbol, ipc_class_level, ipc_version, ipc_value, ipc_position, ipc_gener_auth

    Note:
      - ipc_class_symbol often has extra spaces. We'll normalize in summarizer.
    """
    limit = int(limit)
    res = patstat.sql_query(
        f"""
        SELECT
          ipc_class_symbol,
          ipc_class_level,
          ipc_version,
          ipc_value,
          ipc_position,
          ipc_gener_auth
        FROM tls209_appln_ipc
        WHERE appln_id = {int(appln_id)}
        LIMIT {limit}
        """,
        use_legacy_sql=False,
    )
    return [dict(r) for r in res]


def ipc_coarse_buckets(ipc_rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Derive coarse IPC buckets:
      - section (1st char)
      - class (first 3, e.g. H01)
      - subclass (first 4, e.g. H01S)
    """
    sec: Dict[str, int] = {}
    cls: Dict[str, int] = {}
    sub: Dict[str, int] = {}

    cleaned_symbols: List[str] = []
    for r in ipc_rows:
        sym_raw = (r.get("ipc_class_symbol") or "")
        # normalize multi-spaces and remove spaces for slicing
        sym = " ".join(sym_raw.split()).strip()
        sym_nospace = sym.replace(" ", "")
        if len(sym_nospace) < 4:
            continue
        cleaned_symbols.append(sym)

        sec_k = sym_nospace[0]
        cls_k = sym_nospace[:3]
        sub_k = sym_nospace[:4]

        sec[sec_k] = sec.get(sec_k, 0) + 1
        cls[cls_k] = cls.get(cls_k, 0) + 1
        sub[sub_k] = sub.get(sub_k, 0) + 1

    def topk(d: Dict[str, int], k: int = 10) -> List[Dict[str, Any]]:
        items = sorted(d.items(), key=lambda kv: (-kv[1], kv[0]))
        return [{"key": a, "n": b} for a, b in items[:k]]

    return {
        "symbols_cleaned": cleaned_symbols,
        "counts_section": sec,
        "counts_class": cls,
        "counts_subclass": sub,
        "top_sections": topk(sec, 10),
        "top_classes": topk(cls, 15),
        "top_subclasses": topk(sub, 15),
    }

def priority_age_days(core_filing_date: Optional[date], earliest_priority_date: Optional[date]) -> Optional[int]:
    if not core_filing_date or not earliest_priority_date:
        return None
    return (core_filing_date - earliest_priority_date).days


def enrich_card_with_priority_and_ipc(patstat: PatstatClient, card: Dict[str, Any]) -> Dict[str, Any]:
    """
    Wrapper: add priority + IPC info to an existing card.
    """
    appln_id = int(card["core"]["appln_id"])

    # Priority
    pr_rows = get_priority_links(patstat, appln_id=appln_id)
    pr_summary = summarize_priorities(pr_rows)
    filing_date = card["core"].get("appln_filing_date")
    age_days = priority_age_days(filing_date, pr_summary.get("earliest_priority_date"))
    pr_summary["priority_age_days"] = age_days


    # IPC
    ipc_rows = get_ipc_list(patstat, appln_id=appln_id)
    ipc_summary = ipc_coarse_buckets(ipc_rows)

    out = dict(card)
    out["priorities"] = {
        "raw": pr_rows[:200],          # preview
        "summary": pr_summary,
    }
    out["ipc"] = {
        "raw": ipc_rows[:200],         # preview
        "coarse": ipc_summary,
        "n_ipc_rows": len(ipc_rows),
    }
    return out



# ====================================================================================================
# ====================================================================================================
# ==========================================  MODULE 03  ============================================
# ======================================  CORE PATENT CARD  =========================================
# ====================================================================================================
# ====================================================================================================
#
# Goal:
#   Build a core “patent card” that downstream analytics can enrich.
#
# Includes (PATSTAT):
#   - Title + abstract: tls202_appln_title, tls203_appln_abstr
#   - Applicants + Inventors: tls206_person, tls207_pers_appln
#   - Publications: tls211_pat_publn
#
# Notes:
#   - Language handling: still simplified. We provide:
#       * best-effort English preference if available, else first row.
#   - Applicants vs Inventors:
#       * Applicants: applt_seq_nr > 0
#       * Inventors: invt_seq_nr > 0
# ----------------------------------------------------------------------------------------------------

def _pick_lang_pref(rows: List[Dict[str, Any]], lang_key: str, prefer: str = "en") -> Optional[Dict[str, Any]]:
    """Pick a row preferring a language code (best-effort). If not possible, return first row."""
    if not rows:
        return None
    prefer = (prefer or "").lower()
    for r in rows:
        v = (r.get(lang_key) or "").lower()
        if v == prefer:
            return r
    return rows[0]


def get_patent_text(patstat: PatstatClient, appln_id: int) -> Dict[str, Optional[str]]:
    """
    Title + abstract for appln_id.

    PATSTAT:
      - tls202_appln_title (appln_title + appln_title_lg)
      - tls203_appln_abstr (appln_abstract + appln_abstract_lg)

    We return:
      - title
      - abstract
      - title_lang
      - abstract_lang
      - raw_rows_n (so you can see if multiple languages exist)
    """
    res = patstat.sql_query(
        f"""
        SELECT
          t.appln_title,
          t.appln_title_lg,
          ab.appln_abstract,
          ab.appln_abstract_lg
        FROM tls201_appln a
        LEFT JOIN tls202_appln_title t ON a.appln_id = t.appln_id
        LEFT JOIN tls203_appln_abstr ab ON a.appln_id = ab.appln_id
        WHERE a.appln_id = {appln_id}
        """,
        use_legacy_sql=False,
    )

    if not res:
        return {"title": None, "abstract": None, "title_lang": None, "abstract_lang": None, "raw_rows_n": 0}

    # Best-effort: prefer EN if present
    picked = _pick_lang_pref([dict(r) for r in res], "appln_title_lg", prefer="en") or dict(res[0])
    return {
        "title": picked.get("appln_title"),
        "abstract": picked.get("appln_abstract"),
        "title_lang": picked.get("appln_title_lg"),
        "abstract_lang": picked.get("appln_abstract_lg"),
        "raw_rows_n": len(res),
    }


def get_patent_applicants(patstat: PatstatClient, appln_id: int) -> List[Dict[str, Any]]:
    """
    Applicants ordered by applt_seq_nr (exclude inventors).
    PATSTAT:
      - tls207_pers_appln (role sequencing)
      - tls206_person (names, country)
    """
    res = patstat.sql_query(
        f"""
        SELECT
          p.person_id,
          p.psn_name, p.person_name, p.person_ctry_code,
          pa.applt_seq_nr
        FROM tls207_pers_appln pa
        JOIN tls206_person p ON pa.person_id = p.person_id
        WHERE pa.appln_id = {appln_id}
          AND pa.applt_seq_nr > 0
        ORDER BY pa.applt_seq_nr
        """,
        use_legacy_sql=False,
    )

    out: List[Dict[str, Any]] = []
    for r in res:
        out.append(
            {
                "applt_seq_nr": r.get("applt_seq_nr"),
                "person_id": r.get("person_id"),
                "psn_name": r.get("psn_name"),
                "person_name": r.get("person_name"),
                "person_ctry_code": r.get("person_ctry_code"),
            }
        )
    return out


def get_patent_inventors(patstat: PatstatClient, appln_id: int) -> List[Dict[str, Any]]:
    """
    Inventors ordered by invt_seq_nr.

    PATSTAT:
      - tls207_pers_appln has invt_seq_nr for inventors
      - tls206_person for name/country
    """
    res = patstat.sql_query(
        f"""
        SELECT
          p.person_id,
          p.psn_name, p.person_name, p.person_ctry_code,
          pa.invt_seq_nr
        FROM tls207_pers_appln pa
        JOIN tls206_person p ON pa.person_id = p.person_id
        WHERE pa.appln_id = {appln_id}
          AND pa.invt_seq_nr > 0
        ORDER BY pa.invt_seq_nr
        """,
        use_legacy_sql=False,
    )

    out: List[Dict[str, Any]] = []
    for r in res:
        out.append(
            {
                "invt_seq_nr": r.get("invt_seq_nr"),
                "person_id": r.get("person_id"),
                "psn_name": r.get("psn_name"),
                "person_name": r.get("person_name"),
                "person_ctry_code": r.get("person_ctry_code"),
            }
        )
    return out


def get_patent_publications(patstat: PatstatClient, appln_id: int) -> List[Dict[str, Any]]:
    """
    Publications for appln_id (EP A1/A2/A4/B1 etc), ordered by publn_date.

    PATSTAT:
      - tls211_pat_publn
    """
    res = patstat.sql_query(
        f"""
        SELECT
          pat_publn_id,
          publn_auth, publn_nr, publn_kind, publn_date
        FROM tls211_pat_publn
        WHERE appln_id = {appln_id}
        ORDER BY publn_date
        """,
        use_legacy_sql=False,
    )
    return [dict(r) for r in res]


def build_patent_card(
    patstat: PatstatClient,
    ep_nr: str,
    ep_auth: str = EP_AUTH_DEFAULT,
    include_inventors: bool = True,
) -> Dict[str, Any]:
    """
    Full 'patent card' from EP application number.

    Output structure is intentionally stable and explicit:
      - input
      - core (tls201)
      - text (title/abstract)
      - applicants
      - inventors (optional)
      - publications
    """
    core = resolve_ep_application(patstat, ep_nr=ep_nr, ep_auth=ep_auth)
    appln_id = int(core["appln_id"])

    text = get_patent_text(patstat, appln_id=appln_id)
    applicants = get_patent_applicants(patstat, appln_id=appln_id)
    inventors = get_patent_inventors(patstat, appln_id=appln_id) if include_inventors else []
    publications = get_patent_publications(patstat, appln_id=appln_id)

    return {
        "input": {"ep_auth": ep_auth, "ep_nr": ep_nr, "ep_nr_clean": core["ep_nr_clean"]},
        "core": core,
        "text": text,
        "applicants": applicants,
        "inventors": inventors if include_inventors else None,
        "publications": publications,
    }


# ====================================================================================================
# ====================================================================================================
# ==========================================  MODULE 04  ============================================
# ================================  TECH CLASSIFICATION + FAMILY FOOTPRINT  =========================
# ====================================================================================================
# ====================================================================================================
#
# PATSTAT:
#   - CPC: tls224_appln_cpc
#   - DOCDB family members: tls201_appln filtered by docdb_family_id
#
# Extensions (vs your current script):
#   - Provide CPC “coarse buckets” (section / class / subclass) for analytics
#   - Add INPADOC family size (count only) using tls201_appln filtered by inpadoc_family_id
#   - Provide applicant country mix summary (helps portfolio visuals later)
# ----------------------------------------------------------------------------------------------------

def get_cpc_list(patstat: PatstatClient, appln_id: int, limit: int = 500) -> List[str]:
    res = patstat.sql_query(
        f"""
        SELECT cpc_class_symbol
        FROM tls224_appln_cpc
        WHERE appln_id = {appln_id}
        LIMIT {int(limit)}
        """,
        use_legacy_sql=False,
    )
    return [r["cpc_class_symbol"] for r in res if r.get("cpc_class_symbol")]


def cpc_coarse_buckets(cpc_symbols: List[str]) -> Dict[str, Any]:
    """
    Turn CPC symbols into coarse groupings useful for:
      - portfolio tech distribution charts
      - cohort normalization (later)
      - comparisons

    CPC format examples:
      - "H04L 29/08"
      - "A61K 31/00"

    We derive:
      - section (first char): H, A, G...
      - class (first 3): H04, A61...
      - subclass (first 4): H04L, A61K...
    """
    sec: Dict[str, int] = {}
    cls: Dict[str, int] = {}
    sub: Dict[str, int] = {}
    for sym in cpc_symbols:
        s = (sym or "").strip().replace(" ", "")
        if len(s) < 4:
            continue
        sec_k = s[0]
        cls_k = s[:3]
        sub_k = s[:4]
        sec[sec_k] = sec.get(sec_k, 0) + 1
        cls[cls_k] = cls.get(cls_k, 0) + 1
        sub[sub_k] = sub.get(sub_k, 0) + 1

    def topk(d: Dict[str, int], k: int = 10) -> List[Dict[str, Any]]:
        items = sorted(d.items(), key=lambda kv: (-kv[1], kv[0]))
        return [{"key": a, "n": b} for a, b in items[:k]]

    return {
        "counts_section": sec,
        "counts_class": cls,
        "counts_subclass": sub,
        "top_sections": topk(sec, 10),
        "top_classes": topk(cls, 15),
        "top_subclasses": topk(sub, 15),
    }


def get_docdb_family_members(patstat: PatstatClient, docdb_family_id: int, limit: int = 5000) -> List[Dict[str, Any]]:
    res = patstat.sql_query(
        f"""
        SELECT
          appln_id, appln_auth, appln_nr, appln_kind,
          appln_filing_date, appln_filing_year,
          granted
        FROM tls201_appln
        WHERE docdb_family_id = {int(docdb_family_id)}
        ORDER BY appln_filing_date
        LIMIT {int(limit)}
        """,
        use_legacy_sql=False,
    )
    return [dict(r) for r in res]


def count_inpadoc_family_size(patstat: PatstatClient, inpadoc_family_id: int) -> Optional[int]:
    """
    INPADOC family can be large. For now we compute only the size (count of applications in tls201).
    """
    if not inpadoc_family_id:
        return None
    res = patstat.sql_query(
        f"""
        SELECT COUNT(*) AS n
        FROM tls201_appln
        WHERE inpadoc_family_id = {int(inpadoc_family_id)}
        """,
        use_legacy_sql=False,
    )
    return int(res[0]["n"]) if res else None


def summarize_family_geo(members: List[Dict[str, Any]]) -> Dict[str, Any]:
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
        },
    }


def summarize_applicant_countries(applicants: List[Dict[str, Any]]) -> Dict[str, Any]:
    counts: Dict[str, int] = {}
    for a in applicants:
        c = (a.get("person_ctry_code") or "").strip()
        if not c:
            c = "UNKNOWN"
        counts[c] = counts.get(c, 0) + 1
    top = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return {"by_country": counts, "top": [{"ctry": k, "n": v} for k, v in top[:10]]}


def enrich_card_with_family_and_cpc(patstat: PatstatClient, card: Dict[str, Any]) -> Dict[str, Any]:
    appln_id = int(card["core"]["appln_id"])
    docdb_family_id = int(card["core"]["docdb_family_id"])
    inpadoc_family_id = int(card["core"].get("inpadoc_family_id") or 0)

    cpc_list = get_cpc_list(patstat, appln_id=appln_id)
    family_members = get_docdb_family_members(patstat, docdb_family_id=docdb_family_id)
    family_summary = summarize_family_geo(family_members)

    inpadoc_size = count_inpadoc_family_size(patstat, inpadoc_family_id) if inpadoc_family_id else None
    applicant_ctry = summarize_applicant_countries(card.get("applicants", []))

    out = dict(card)
    out["cpc"] = {
        "symbols": cpc_list,
        "n_cpc": len(cpc_list),
        "coarse": cpc_coarse_buckets(cpc_list),
    }
    out["family_docdb"] = {"docdb_family_id": docdb_family_id, "members": family_members, **family_summary}
    out["family_inpadoc"] = {"inpadoc_family_id": inpadoc_family_id or None, "family_size": inpadoc_size}
    out["applicant_countries"] = applicant_ctry
    return out


# ====================================================================================================
# ====================================================================================================
# ==========================================  MODULE 05  ============================================
# ===============================  PUBLICATION SELECTION + CITATIONS  ===============================
# ====================================================================================================
# ====================================================================================================
#
# We keep your "main publication" heuristic (prefer EP B* then EP A*).
#
# Extensions:
#   - Provide backward citations (what this publication cites) via tls212_citation
#   - Provide "top citing publications" (sample) for network graphs later
#   - Provide citation velocity proxies (recent citations in last N years)
# ----------------------------------------------------------------------------------------------------

def choose_main_publication(publications: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not publications:
        return {"main_publn": None, "reason": "no_publications"}

    pubs = [dict(p) for p in publications if p.get("pat_publn_id")]

    ep_b = [p for p in pubs if p.get("publn_auth") == "EP" and str(p.get("publn_kind", "")).startswith("B")]
    if ep_b:
        ep_b_sorted = sorted(ep_b, key=lambda p: (p.get("publn_date") or date(1, 1, 1)))
        return {"main_publn": ep_b_sorted[-1], "reason": "prefer_EP_B"}

    ep_a = [p for p in pubs if p.get("publn_auth") == "EP" and str(p.get("publn_kind", "")).startswith("A")]
    if ep_a:
        ep_a_sorted = sorted(ep_a, key=lambda p: (p.get("publn_date") or date(1, 1, 1)))
        return {"main_publn": ep_a_sorted[-1], "reason": "prefer_EP_A"}

    pubs_sorted = sorted(pubs, key=lambda p: (p.get("publn_date") or date(1, 1, 1)))
    return {"main_publn": pubs_sorted[-1], "reason": "fallback_latest_publn"}


def count_forward_citations(patstat: PatstatClient, cited_pat_publn_id: int) -> int:
    res = patstat.sql_query(
        f"""
        SELECT COUNT(*) AS forward_citations
        FROM tls212_citation
        WHERE cited_pat_publn_id = {int(cited_pat_publn_id)}
        """,
        use_legacy_sql=False,
    )
    return int(res[0]["forward_citations"]) if res else 0


def count_backward_citations(patstat: PatstatClient, pat_publn_id: int) -> int:
    """
    Backward citations = references made BY this publication to other publications.
    In tls212_citation:
      - pat_publn_id = citing publication
      - cited_pat_publn_id = cited publication
    """
    res = patstat.sql_query(
        f"""
        SELECT COUNT(*) AS backward_citations
        FROM tls212_citation
        WHERE pat_publn_id = {int(pat_publn_id)}
        """,
        use_legacy_sql=False,
    )
    return int(res[0]["backward_citations"]) if res else 0


def citations_by_year(patstat: PatstatClient, cited_pat_publn_id: int, limit: int = 5000) -> List[Dict[str, Any]]:
    res = patstat.sql_query(
        f"""
        SELECT EXTRACT(YEAR FROM p.publn_date) AS y, COUNT(*) AS n
        FROM tls212_citation c
        JOIN tls211_pat_publn p ON p.pat_publn_id = c.pat_publn_id
        WHERE c.cited_pat_publn_id = {int(cited_pat_publn_id)}
          AND p.publn_date IS NOT NULL
        GROUP BY y
        ORDER BY y
        LIMIT {int(limit)}
        """,
        use_legacy_sql=False,
    )
    return [dict(r) for r in res]


def top_citing_publications(
    patstat: PatstatClient,
    cited_pat_publn_id: int,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """
    Returns a sample list of citing publications (useful later for network graphs).
    """
    limit = clamp_limit(limit)
    res = patstat.sql_query(
        f"""
        SELECT
          c.pat_publn_id AS citing_pat_publn_id,
          p.publn_auth AS citing_publn_auth,
          p.publn_nr   AS citing_publn_nr,
          p.publn_kind AS citing_publn_kind,
          p.publn_date AS citing_publn_date
        FROM tls212_citation c
        JOIN tls211_pat_publn p ON p.pat_publn_id = c.pat_publn_id
        WHERE c.cited_pat_publn_id = {int(cited_pat_publn_id)}
        ORDER BY p.publn_date DESC
        LIMIT {int(limit)}
        """,
        use_legacy_sql=False,
    )
    return [dict(r) for r in res]


def recent_citation_counts(by_year: List[Dict[str, Any]], windows: List[int] = [3, 5, 10]) -> Dict[str, Any]:
    """
    Simple velocity proxy:
      - citations in last N years (relative to current year)
    """
    if not by_year:
        return {f"last_{w}y": 0 for w in windows}

    current_year = date.today().year
    yr_map = {int(r["y"]): int(r["n"]) for r in by_year if r.get("y") is not None}
    out = {}
    for w in windows:
        s = 0
        for y in range(current_year - w + 1, current_year + 1):
            s += yr_map.get(y, 0)
        out[f"last_{w}y"] = s
    return out


def enrich_card_with_citations(
    patstat: PatstatClient,
    card: Dict[str, Any],
    include_top_citers: bool = False,
    top_citers_limit: int = 30,
) -> Dict[str, Any]:
    pick = choose_main_publication(card.get("publications", []))
    main_publn = pick["main_publn"]

    out = dict(card)
    out["main_publn"] = main_publn
    out["main_publn_reason"] = pick["reason"]

    if not main_publn:
        out["citations"] = {"forward_citations": None, "backward_citations": None, "citations_by_year": [], "velocity": {}}
        return out

    cited_id = int(main_publn["pat_publn_id"])
    fwd = count_forward_citations(patstat, cited_id)
    bwd = count_backward_citations(patstat, cited_id)
    by_year = citations_by_year(patstat, cited_id)
    velocity = recent_citation_counts(by_year)

    block: Dict[str, Any] = {
        "cited_pat_publn_id": cited_id,
        "forward_citations": fwd,
        "backward_citations": bwd,
        "citations_by_year": by_year,
        "velocity": velocity,
    }

    if include_top_citers:
        block["top_citing_publications"] = top_citing_publications(patstat, cited_id, limit=top_citers_limit)

    out["citations"] = block
    return out


def citations_across_publications(patstat: PatstatClient, publications: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Robust citation metrics across all EP publications in the card.
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

    per_sorted = sorted(per, key=lambda r: (-r["forward_citations"], r.get("publn_date") or date(1, 1, 1)))
    return {"per_publication": per_sorted, "max_any_publn": best, "sum_all_ep_pubs": total}


# ====================================================================================================
# ====================================================================================================
# ==========================================  MODULE 06  ============================================
# ===============================  LEGAL EVENTS (INPADOC) + STATUS  =================================
# ====================================================================================================
# ====================================================================================================

SENTINEL_DATE = date(9999, 12, 31)


def _clean_date(d: Optional[date]) -> Optional[date]:
    if d is None:
        return None
    return None if d == SENTINEL_DATE else d


def get_legal_events(patstat: PatstatClient, appln_id: int, limit: int = 5000) -> List[Dict[str, Any]]:
    res = patstat.sql_query(
        f"""
        SELECT
          event_auth, event_code,
          event_filing_date, event_publn_date, event_effective_date,
          fee_country, fee_payment_date, fee_renewal_year,
          lapse_country, lapse_date,
          reinstate_country, reinstate_date,
          event_descr, event_text
        FROM tls231_inpadoc_legal_event
        WHERE appln_id = {int(appln_id)}
        ORDER BY COALESCE(event_effective_date, event_publn_date, fee_payment_date, lapse_date) DESC
        LIMIT {int(limit)}
        """,
        use_legacy_sql=False,
    )

    out = []
    for r in res:
        rr = dict(r)
        for k in [
            "event_filing_date",
            "event_publn_date",
            "event_effective_date",
            "fee_payment_date",
            "lapse_date",
            "reinstate_date",
        ]:
            rr[k] = _clean_date(rr.get(k))
        for k in ["fee_country", "lapse_country", "reinstate_country", "event_auth"]:
            if rr.get(k) is not None:
                rr[k] = str(rr[k]).strip()
        out.append(rr)
    return out


def summarize_legal_status(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    fee_payments = []
    lapses = []
    reinstates = []

    for e in events:
        if e.get("fee_payment_date"):
            fee_payments.append(
                {
                    "fee_country": e.get("fee_country"),
                    "fee_payment_date": e.get("fee_payment_date"),
                    "fee_renewal_year": e.get("fee_renewal_year"),
                    "event_code": e.get("event_code"),
                    "event_auth": e.get("event_auth"),
                }
            )
        if e.get("lapse_date"):
            lapses.append(
                {
                    "lapse_country": e.get("lapse_country"),
                    "lapse_date": e.get("lapse_date"),
                    "event_code": e.get("event_code"),
                    "event_auth": e.get("event_auth"),
                }
            )
        if e.get("reinstate_date"):
            reinstates.append(
                {
                    "reinstate_country": e.get("reinstate_country"),
                    "reinstate_date": e.get("reinstate_date"),
                    "event_code": e.get("event_code"),
                    "event_auth": e.get("event_auth"),
                }
            )

    fee_payments_sorted = sorted(fee_payments, key=lambda x: (x["fee_payment_date"] or date(1, 1, 1)), reverse=True)
    lapses_sorted = sorted(lapses, key=lambda x: (x["lapse_date"] or date(1, 1, 1)), reverse=True)
    reinstates_sorted = sorted(reinstates, key=lambda x: (x["reinstate_date"] or date(1, 1, 1)), reverse=True)

    latest_fee = fee_payments_sorted[0] if fee_payments_sorted else None
    latest_lapse = lapses_sorted[0] if lapses_sorted else None
    latest_reinstate = reinstates_sorted[0] if reinstates_sorted else None

    parts = []
    notes = []

    if latest_fee:
        notes.append(
            "fee_country is a designated/validation state where a post-grant fee/renewal-type payment is observed "
            "(not necessarily an EPO renewal fee). Interpretation requires care."
        )
        parts.append(f"Latest fee payment: {latest_fee['fee_payment_date']} ({latest_fee.get('fee_country')})")

    if latest_lapse:
        parts.append(f"Latest lapse: {latest_lapse['lapse_date']} ({latest_lapse.get('lapse_country')})")

    if latest_reinstate:
        parts.append(
            f"Latest reinstatement: {latest_reinstate['reinstate_date']} ({latest_reinstate.get('reinstate_country')})"
        )

    summary = " | ".join(parts) if parts else "No renewal/lapse/reinstatement signals found in tls231 (PATSTAT)."

    # A coarse “alive-ish” heuristic (still not “legal status truth”):
    alive_hint = None
    if latest_fee and latest_fee.get("fee_payment_date"):
        days = (date.today() - latest_fee["fee_payment_date"]).days
        alive_hint = "likely_alive" if days <= 3 * 365 else "unknown"
    if latest_lapse and latest_lapse.get("lapse_date"):
        days = (date.today() - latest_lapse["lapse_date"]).days
        if days <= 3 * 365:
            alive_hint = "possible_lapse_recent"

    return {
        "n_events": len(events),
        "latest_fee_payment": latest_fee,
        "latest_lapse": latest_lapse,
        "latest_reinstate": latest_reinstate,
        "fee_payments": fee_payments_sorted[:50],
        "lapses": lapses_sorted[:50],
        "reinstatements": reinstates_sorted[:50],
        "summary": summary,
        "notes": notes,
        "alive_hint": alive_hint,
    }


def enrich_card_with_legal_and_robust_citations(patstat: PatstatClient, card: Dict[str, Any]) -> Dict[str, Any]:
    appln_id = int(card["core"]["appln_id"])
    events = get_legal_events(patstat, appln_id=appln_id)
    legal = summarize_legal_status(events)
    robust = citations_across_publications(patstat, card.get("publications", []))

    out = dict(card)
    out["legal_events"] = {"raw_head": events[:30], "summary": legal}
    out["citations_robust"] = robust
    return out


# ====================================================================================================
# ====================================================================================================
# ==========================================  MODULE 07  ============================================
# ============================  FIELD NORMALIZATION (COHORT-BASED, OPTIONAL)  =======================
# ====================================================================================================
# ====================================================================================================
#
# “Field-normalized citations” was a known gap in your v1 skeleton and is mentioned in the product
# direction. We *can* approximate a normalization in PATSTAT-only terms, but it can be expensive.
#
# Approach (simple, explainable):
#   - define a cohort of “similar” applications by:
#       * same filing year
#       * same CPC subclass (first 4 chars), using tls224_appln_cpc
#   - compute robust max_any_publn citations for a sample of that cohort
#   - compute percentile-ish metrics: p50 / p75 / p90 (approx) and z-score-like ratio
#
# We keep it bounded:
#   - cap cohort size and sampling
#   - cache results for 15 minutes
# ----------------------------------------------------------------------------------------------------

def _primary_cpc_subclass(cpc_symbols: List[str]) -> Optional[str]:
    for sym in cpc_symbols or []:
        s = (sym or "").strip().replace(" ", "")
        if len(s) >= 4:
            return s[:4]
    return None


def _cohort_appln_ids_for_year_and_cpc_subclass(
    patstat: PatstatClient,
    filing_year: int,
    cpc_subclass: str,
    limit: int = MAX_COHORT_SIZE,
) -> List[int]:
    limit = min(int(limit), MAX_COHORT_SIZE)
    res = patstat.sql_query(
        f"""
        SELECT a.appln_id
        FROM tls201_appln a
        JOIN tls224_appln_cpc c ON a.appln_id = c.appln_id
        WHERE a.appln_filing_year = {int(filing_year)}
          AND SUBSTR(REPLACE(c.cpc_class_symbol, ' ', ''), 1, 4) = '{cpc_subclass}'
        LIMIT {int(limit)}
        """,
        use_legacy_sql=False,
    )
    return [int(r["appln_id"]) for r in res if r.get("appln_id") is not None]


def _ep_publn_ids_for_appln(patstat: PatstatClient, appln_id: int, limit: int = 50) -> List[int]:
    res = patstat.sql_query(
        f"""
        SELECT pat_publn_id
        FROM tls211_pat_publn
        WHERE appln_id = {int(appln_id)}
          AND publn_auth = 'EP'
        LIMIT {int(limit)}
        """,
        use_legacy_sql=False,
    )
    return [int(r["pat_publn_id"]) for r in res if r.get("pat_publn_id") is not None]


def _max_forward_citations_for_appln(patstat: PatstatClient, appln_id: int) -> int:
    publn_ids = _ep_publn_ids_for_appln(patstat, appln_id)
    if not publn_ids:
        return 0
    best = 0
    for pid in publn_ids:
        n = count_forward_citations(patstat, pid)
        if n > best:
            best = n
    return best


def cohort_normalization(
    patstat: PatstatClient,
    report: Dict[str, Any],
    sample_size: int = DEFAULT_COHORT_SAMPLE,
) -> Dict[str, Any]:
    """
    Returns a coarse normalization block for citations:
      - cohort definition
      - sample stats
      - position of the patent within the cohort (approx)
    """
    core = report.get("core") or {}
    filing_year = int(core.get("appln_filing_year") or 0)
    if not filing_year:
        return {"enabled": False, "reason": "missing_filing_year"}

    cpc_symbols = ((report.get("cpc") or {}).get("symbols") or [])
    cpc_sub = _primary_cpc_subclass(cpc_symbols)
    if not cpc_sub:
        return {"enabled": False, "reason": "missing_cpc_subclass"}

    cache_key = f"cohort:{filing_year}:{cpc_sub}:{sample_size}"
    cached = cache_get(cache_key)
    if cached is not None:
        return cached

    appln_ids = _cohort_appln_ids_for_year_and_cpc_subclass(patstat, filing_year, cpc_sub, limit=MAX_COHORT_SIZE)
    if not appln_ids:
        out = {"enabled": False, "reason": "empty_cohort", "cohort": {"filing_year": filing_year, "cpc_subclass": cpc_sub}}
        cache_set(cache_key, out)
        return out

    # Sample deterministically for demo (first N). Later: random, stratified, etc.
    sample_size = min(int(sample_size), len(appln_ids), MAX_COHORT_SIZE)
    sample_ids = appln_ids[:sample_size]

    values: List[int] = []
    for aid in sample_ids:
        values.append(_max_forward_citations_for_appln(patstat, aid))

    values_sorted = sorted(values)

    def pct(p: float) -> int:
        if not values_sorted:
            return 0
        idx = int(round((len(values_sorted) - 1) * p))
        return int(values_sorted[max(0, min(idx, len(values_sorted) - 1))])

    p50 = pct(0.50)
    p75 = pct(0.75)
    p90 = pct(0.90)

    my_max_cit = int(((report.get("citations_robust") or {}).get("max_any_publn") or {}).get("forward_citations") or 0)

    # “Percentile-ish” position: proportion of values <= my_max_cit (within sample)
    le = sum(1 for v in values_sorted if v <= my_max_cit)
    approx_percentile = le / len(values_sorted) if values_sorted else None

    out = {
        "enabled": True,
        "cohort": {"filing_year": filing_year, "cpc_subclass": cpc_sub, "cohort_size_cap": len(appln_ids), "sample_size": sample_size},
        "stats": {"p50": p50, "p75": p75, "p90": p90, "sample_min": values_sorted[0], "sample_max": values_sorted[-1]},
        "position": {"my_max_citations": my_max_cit, "approx_percentile_in_sample": approx_percentile},
        "notes": [
            "This is a bounded, approximate normalization based on filing year + CPC subclass. It is meant for dashboards, not legal/financial truth.",
            "Sampling strategy is naive (first N). Replace with better sampling for production.",
        ],
    }
    cache_set(cache_key, out)
    return out


# ====================================================================================================
# ====================================================================================================
# ==========================================  MODULE 08  ============================================
# =============================  END-TO-END REPORT BUILDERS (SINGLE + PORTFOLIO)  ====================
# ====================================================================================================
# ====================================================================================================

def build_patent_report(
    patstat: PatstatClient,
    ep_nr: str,
    ep_auth: str = EP_AUTH_DEFAULT,
    include_inventors: bool = True,
    include_top_citers: bool = False,
) -> Dict[str, Any]:
    """
    End-to-end enriched report for ONE EP application number.
    """
    card = build_patent_card(patstat, ep_nr, ep_auth=ep_auth, include_inventors=include_inventors)
    card2 = enrich_card_with_family_and_cpc(patstat, card)
    # NEW: Module 2B/2C
    card2b = enrich_card_with_priority_and_ipc(patstat, card2)

    card3 = enrich_card_with_citations(
    patstat,
    card2b,
    include_top_citers=include_top_citers,
    top_citers_limit=30,
    )

    card4 = enrich_card_with_legal_and_robust_citations(patstat, card3)
    return card4


def build_portfolio_report(
    patstat: PatstatClient,
    ep_list: List[str],
    ep_auth: str = EP_AUTH_DEFAULT,
    include_inventors: bool = False,
) -> Dict[str, Any]:
    """
    End-to-end report for a portfolio.
    Returns:
      - per-patent reports
      - aggregates for charts / dashboard
    """
    reports = []
    for ep in ep_list:
        try:
            reports.append(build_patent_report(patstat, ep, ep_auth=ep_auth, include_inventors=include_inventors))
        except Exception as e:
            reports.append({"input": {"ep_auth": ep_auth, "ep_nr": ep}, "error": str(e)})

    ok = [r for r in reports if "error" not in r and r.get("core")]
    n_ok = len(ok)

    def safe_int(x: Any, default: int = 0) -> int:
        try:
            return int(x)
        except Exception:
            return default

    family_sizes = [safe_int(r.get("family_docdb", {}).get("family_size")) for r in ok]
    max_citations = [
        safe_int((r.get("citations_robust", {}).get("max_any_publn") or {}).get("forward_citations"), 0)
        for r in ok
    ]
    granted_flags = [1 if (r.get("core", {}) or {}).get("granted") == "Y" else 0 for r in ok]

    # Tech distribution (CPC section)
    cpc_sections: Dict[str, int] = {}
    for r in ok:
        coarse = ((r.get("cpc") or {}).get("coarse") or {}).get("counts_section") or {}
        for k, v in coarse.items():
            cpc_sections[k] = cpc_sections.get(k, 0) + int(v)

    agg = {
        "n_input": len(ep_list),
        "n_ok": n_ok,
        "n_errors": len(reports) - n_ok,
        "avg_family_size": (sum(family_sizes) / n_ok) if n_ok else None,
        "avg_max_forward_citations": (sum(max_citations) / n_ok) if n_ok else None,
        "granted_ratio": (sum(granted_flags) / n_ok) if n_ok else None,
        "tech_cpc_section_counts": cpc_sections,
    }

    return {"portfolio": {"ep_list": ep_list, "aggregates": agg}, "reports": reports}

# ====================================================================================================
# ====================================================================================================
# ==========================================  MODULE 09A  ===========================================
# ==========================  "SIMILAR PATENTS" VIA CPC/IPC NEIGHBORHOODS  ==========================
# ====================================================================================================
# ====================================================================================================
#
# Goal:
#   For demo / explainability, fetch 2 "peer" EP applications that are likely in the same tech space
#   based on CPC/IPC overlap. Then score them too so we can compare.
#
# Important:
#   - This is NOT semantic similarity. It's classification-neighborhood similarity.
#   - It is good enough for a v1.1 demo because CPC/IPC are curated tech taxonomy signals.
#
# Strategy:
#   1) Build candidate pool from CPC/IPC matches (strict -> relaxed).
#   2) Rank by overlap count.
#   3) Return top K EP appln_nr (digits) excluding the input appln_id.
#
# Performance:
#   - bounded limits
#   - cached per appln_id
# ----------------------------------------------------------------------------------------------------

  
SIMILAR_RETURN_K = int(os.getenv("SIMILAR_RETURN_K", "2"))               # how many peers we return
       
SIMILAR_MAX_CANDIDATES = int(os.getenv("SIMILAR_MAX_CANDIDATES", "80"))# cap candidate pool size
SIMILAR_MIN_OVERLAP = int(os.getenv("SIMILAR_MIN_OVERLAP", "1"))# try to find >=2 overlaps first

def _cpc_subclass(sym: str) -> Optional[str]:
    s = (sym or "").strip().replace(" ", "")
    return s[:4] if len(s) >= 4 else None

def _cpc_class(sym: str) -> Optional[str]:
    s = (sym or "").strip().replace(" ", "")
    return s[:3] if len(s) >= 3 else None

def _ipc_subclass(sym: str) -> Optional[str]:
    # IPC strings often have spaces; normalize then remove spaces for slicing
    s = " ".join((sym or "").split()).strip().replace(" ", "")
    return s[:4] if len(s) >= 4 else None

def _ipc_class(sym: str) -> Optional[str]:
    s = " ".join((sym or "").split()).strip().replace(" ", "")
    return s[:3] if len(s) >= 3 else None

def _ep_nrs_for_appln_ids(patstat: PatstatClient, appln_ids: List[int]) -> Dict[int, str]:
    """
    Batch fetch appln_nr for many appln_id in ONE query.
    Returns: {appln_id: appln_nr}
    """
    ids = [int(x) for x in appln_ids if x is not None]
    if not ids:
        return {}

    # Keep the IN list bounded (safety). We only need the top few anyway.
    ids = ids[:200]

    ids_sql = ",".join(str(i) for i in ids)
    res = patstat.sql_query(
        f"""
        SELECT appln_id, appln_nr
        FROM tls201_appln
        WHERE appln_auth = 'EP'
          AND appln_id IN ({ids_sql})
        """,
        use_legacy_sql=False,
    )
    out = {}
    for r in res:
        aid = int(r["appln_id"])
        nr = (r.get("appln_nr") or "").strip()
        if nr:
            out[aid] = nr
    return out


def _rank_candidates_by_overlap(
    candidates: Dict[int, Dict[str, Any]],
    required_min_overlap: int = 1,
) -> List[Dict[str, Any]]:
    """
    candidates: appln_id -> {
        "cpc_overlap": int,
        "ipc_overlap": int,
        "score": int  (combined)
        "reasons": {..}
    }
    """
    rows = []
    for appln_id, info in candidates.items():
        combined = int(info.get("score") or 0)
        if combined < required_min_overlap:
            continue
        rows.append({"appln_id": appln_id, **info})
    rows.sort(key=lambda r: (-int(r.get("score") or 0), -int(r.get("cpc_overlap") or 0), -int(r.get("ipc_overlap") or 0), r["appln_id"]))
    return rows

def _candidate_pool_from_cpc_subclasses(
    patstat: PatstatClient,
    cpc_subs: List[str],
    exclude_appln_id: int,
    limit: int = SIMILAR_MAX_CANDIDATES,
) -> Dict[int, int]:
    """
    Return appln_id -> overlap_count (count of matching CPC subclasses)
    """
    if not cpc_subs:
        return {}
    # Use IN ('AAAA','BBBB',...) style
    subs_sql = ",".join([f"'{s}'" for s in sorted(set(cpc_subs)) if s])
    res = patstat.sql_query(
        f"""
        SELECT c.appln_id, COUNT(DISTINCT SUBSTR(REPLACE(c.cpc_class_symbol,' ',''), 1, 4)) AS n_match
        FROM tls224_appln_cpc c
        WHERE SUBSTR(REPLACE(c.cpc_class_symbol,' ',''), 1, 4) IN ({subs_sql})
          AND c.appln_id <> {int(exclude_appln_id)}
        GROUP BY c.appln_id
        ORDER BY n_match DESC
        LIMIT {int(limit)}
        """,
        use_legacy_sql=False,
    )
    return {int(r["appln_id"]): int(r["n_match"]) for r in res if r.get("appln_id") is not None}

def _candidate_pool_from_ipc_subclasses(
    patstat: PatstatClient,
    ipc_subs: List[str],
    exclude_appln_id: int,
    limit: int = SIMILAR_MAX_CANDIDATES,
) -> Dict[int, int]:
    """
    Return appln_id -> overlap_count (count of matching IPC subclasses)
    """
    if not ipc_subs:
        return {}
    subs_sql = ",".join([f"'{s}'" for s in sorted(set(ipc_subs)) if s])
    res = patstat.sql_query(
        f"""
        SELECT i.appln_id, COUNT(DISTINCT SUBSTR(REPLACE(i.ipc_class_symbol,' ',''), 1, 4)) AS n_match
        FROM tls209_appln_ipc i
        WHERE SUBSTR(REPLACE(i.ipc_class_symbol,' ',''), 1, 4) IN ({subs_sql})
          AND i.appln_id <> {int(exclude_appln_id)}
        GROUP BY i.appln_id
        ORDER BY n_match DESC
        LIMIT {int(limit)}
        """,
        use_legacy_sql=False,
    )
    return {int(r["appln_id"]): int(r["n_match"]) for r in res if r.get("appln_id") is not None}

def find_similar_ep_peers(
    patstat: PatstatClient,
    report: Dict[str, Any],
    k: int = SIMILAR_RETURN_K,
) -> Dict[str, Any]:
    """
    Returns:
      {
        "method": "...",
        "peers": [{"ep_nr": "...", "overlap": {...}}, ...],
        "notes": [...]
      }
    """
    core = report.get("core") or {}
    my_appln_id = int(core.get("appln_id") or 0)
    if not my_appln_id:
        return {"enabled": False, "reason": "missing_appln_id"}

    cache_key = f"similar:{my_appln_id}:{k}"
    cached = cache_get(cache_key)
    if cached is not None:
        return cached

    # Extract CPC + IPC from report (already computed in your pipeline)
    cpc_syms = ((report.get("cpc") or {}).get("symbols") or [])
    ipc_syms = (((report.get("ipc") or {}).get("coarse") or {}).get("symbols_cleaned") or [])

    cpc_subs = [x for x in (_cpc_subclass(s) for s in cpc_syms) if x]
    ipc_subs = [x for x in (_ipc_subclass(s) for s in ipc_syms) if x]

    candidates: Dict[int, Dict[str, Any]] = {}

    # -------------------------------
    # Pass 1 (strict): CPC subclass + IPC subclass overlaps
    # -------------------------------
    cpc_pool = _candidate_pool_from_cpc_subclasses(patstat, cpc_subs, my_appln_id)
    ipc_pool = {}

    # Only query IPC if CPC didn't find enough candidates
    if len(cpc_pool) < 50:
        ipc_pool = _candidate_pool_from_ipc_subclasses(patstat, ipc_subs, my_appln_id)


    # Merge pools into candidate dict
    for aid, n in cpc_pool.items():
        candidates.setdefault(aid, {"cpc_overlap": 0, "ipc_overlap": 0, "reasons": {}})
        candidates[aid]["cpc_overlap"] = int(n)
        candidates[aid]["reasons"]["cpc_subclass_overlap"] = int(n)

    for aid, n in ipc_pool.items():
        candidates.setdefault(aid, {"cpc_overlap": 0, "ipc_overlap": 0, "reasons": {}})
        candidates[aid]["ipc_overlap"] = int(n)
        candidates[aid]["reasons"]["ipc_subclass_overlap"] = int(n)

    # combined score (weighted: CPC slightly stronger signal than IPC for EPO context)
    for aid in candidates:
        c = int(candidates[aid].get("cpc_overlap") or 0)
        i = int(candidates[aid].get("ipc_overlap") or 0)
        candidates[aid]["score"] = 2 * c + 1 * i

    ranked = _rank_candidates_by_overlap(candidates, required_min_overlap=SIMILAR_MIN_OVERLAP)

    # If not enough, relax overlap threshold
    if len(ranked) < k:
        ranked = _rank_candidates_by_overlap(candidates, required_min_overlap=1)

    # Convert to EP numbers (filter to those that are EP applications)
    # ---- FAST PATH: batch fetch EP numbers for top-ranked candidates (avoid N+1 queries)
    top_ids = [int(r["appln_id"]) for r in ranked[:30]] # 30 is plenty to find 2 EP peers
    id_to_ep = _ep_nrs_for_appln_ids(patstat, top_ids)

    peers: List[Dict[str, Any]] = []
    for row in ranked:
        if len(peers) >= k:
            break
        aid = int(row["appln_id"])
        ep_nr = id_to_ep.get(aid)
        if not ep_nr:
            continue
        peers.append({
            "ep_nr": ep_nr,
            "appln_id": aid,  # <--- keep it; we’ll use it for fast peer score
            "overlap": {
                "cpc_subclass_matches": int(row.get("cpc_overlap") or 0),
                "ipc_subclass_matches": int(row.get("ipc_overlap") or 0),
                "combined_score": int(row.get("score") or 0),
            },
            "reasons": row.get("reasons") or {},
        })


    out = {
        "enabled": True,
        "method": "CPC/IPC subclass overlap (strict->relaxed)",
        "k": k,
        "peers": peers,
        "notes": [
            "Peers are selected by overlap in CPC/IPC subclasses (taxonomy neighborhood).",
            "This is suitable for a demo/comparison baseline, not semantic similarity.",
        ],
    }
    cache_set(cache_key, out)
    return out

def fast_docdb_family_size_for_appln_ids(patstat: PatstatClient, appln_ids: List[int]) -> Dict[int, int]:
    """
    Returns {appln_id: docdb_family_size} with:
      - per-appln_id cache
      - single SQL query for missing ids
    """
    ids = [int(x) for x in appln_ids if x is not None]
    if not ids:
        return {}

    ids = ids[:200]

    cached = cache_get_many("fam_sz", ids)
    missing = [i for i in ids if i not in cached]

    out: Dict[int, int] = {int(k): int(v) for k, v in cached.items()}

    if missing:
        ids_sql = ",".join(str(i) for i in missing)
        res = patstat.sql_query(
            f"""
            SELECT a.appln_id, COUNT(b.appln_id) AS fam_size
            FROM tls201_appln a
            JOIN tls201_appln b
              ON a.docdb_family_id = b.docdb_family_id
            WHERE a.appln_id IN ({ids_sql})
            GROUP BY a.appln_id
            """,
            use_legacy_sql=False,
        )
        fresh = {int(r["appln_id"]): int(r["fam_size"] or 0) for r in res}
        # ensure zeros for anything not returned
        for i in missing:
            fresh.setdefault(int(i), 0)

        cache_set_many("fam_sz", fresh)
        out.update(fresh)

    # keep ordering irrelevant but ensure all ids included
    for i in ids:
        out.setdefault(int(i), 0)
    return out

def fast_max_forward_citations_for_appln_ids(patstat: PatstatClient, appln_ids: List[int]) -> Dict[int, int]:
    """
    Returns {appln_id: max_forward_citations_across_EP_pubs}, optimized:
      - cache per appln_id
      - restrict citation counting to the small set of EP pat_publn_id
    """
    ids = [int(x) for x in appln_ids if x is not None]
    if not ids:
        return {}

    ids = ids[:200]

    cached = cache_get_many("max_fwd", ids)
    missing = [i for i in ids if i not in cached]

    out: Dict[int, int] = {int(k): int(v) for k, v in cached.items()}

    if missing:
        ids_sql = ",".join(str(i) for i in missing)

        # Step: pubs -> cit counts only for those pubs -> max per appln
        res = patstat.sql_query(
            f"""
            WITH pubs AS (
              SELECT appln_id, pat_publn_id
              FROM tls211_pat_publn
              WHERE appln_id IN ({ids_sql})
                AND publn_auth = 'EP'
            ),
            cit AS (
              SELECT cited_pat_publn_id, COUNT(*) AS fwd
              FROM tls212_citation
              WHERE cited_pat_publn_id IN (SELECT pat_publn_id FROM pubs)
              GROUP BY cited_pat_publn_id
            )
            SELECT
              p.appln_id,
              MAX(COALESCE(c.fwd, 0)) AS max_fwd
            FROM pubs p
            LEFT JOIN cit c
              ON c.cited_pat_publn_id = p.pat_publn_id
            GROUP BY p.appln_id
            """,
            use_legacy_sql=False,
        )

        fresh = {int(r["appln_id"]): int(r["max_fwd"] or 0) for r in res}
        # missing ids might have zero EP pubs => not returned
        for i in missing:
            fresh.setdefault(int(i), 0)

        cache_set_many("max_fwd", fresh)
        out.update(fresh)

    for i in ids:
        out.setdefault(int(i), 0)
    return out

def fast_titles_for_appln_ids(patstat: PatstatClient, appln_ids: List[int]) -> Dict[int, Dict[str, Any]]:
    """
    Returns {appln_id: {"title": str|None, "title_lang": str|None}}
    Prefers EN if present, else first available.
    Cached per appln_id.
    """
    ids = [int(x) for x in appln_ids if x is not None][:200]
    if not ids:
        return {}

    cached = cache_get_many("ttl", ids)
    missing = [i for i in ids if i not in cached]

    out: Dict[int, Dict[str, Any]] = {int(k): v for k, v in cached.items()}

    if missing:
        ids_sql = ",".join(str(i) for i in missing)
        res = patstat.sql_query(
            f"""
            SELECT appln_id, appln_title, appln_title_lg
            FROM tls202_appln_title
            WHERE appln_id IN ({ids_sql})
            """,
            use_legacy_sql=False,
        )

        # group rows per appln_id and pick EN if possible
        grouped: Dict[int, List[Dict[str, Any]]] = {}
        for r in res:
            aid = int(r["appln_id"])
            grouped.setdefault(aid, []).append(dict(r))

        fresh: Dict[int, Dict[str, Any]] = {}
        for aid in missing:
            rows = grouped.get(int(aid), [])
            picked = None
            for rr in rows:
                if (rr.get("appln_title_lg") or "").lower() == "en":
                    picked = rr
                    break
            if picked is None and rows:
                picked = rows[0]
            fresh[int(aid)] = {
                "title": picked.get("appln_title") if picked else None,
                "title_lang": picked.get("appln_title_lg") if picked else None,
            }

        cache_set_many("ttl", fresh)
        out.update(fresh)

    for i in ids:
        out.setdefault(int(i), {"title": None, "title_lang": None})
    return out

def fast_main_applicant_for_appln_ids(patstat: PatstatClient, appln_ids: List[int]) -> Dict[int, Dict[str, Any]]:
    """
    Returns {appln_id: {"person_name": str|None, "person_ctry_code": str|None}}
    Uses applt_seq_nr = 1 as main applicant.
    Cached per appln_id.
    """
    ids = [int(x) for x in appln_ids if x is not None][:200]
    if not ids:
        return {}

    cached = cache_get_many("appl1", ids)
    missing = [i for i in ids if i not in cached]

    out: Dict[int, Dict[str, Any]] = {int(k): v for k, v in cached.items()}

    if missing:
        ids_sql = ",".join(str(i) for i in missing)
        res = patstat.sql_query(
            f"""
            SELECT
              pa.appln_id,
              p.person_name,
              p.psn_name,
              p.person_ctry_code
            FROM tls207_pers_appln pa
            JOIN tls206_person p ON p.person_id = pa.person_id
            WHERE pa.appln_id IN ({ids_sql})
              AND pa.applt_seq_nr = 1
            """,
            use_legacy_sql=False,
        )

        fresh: Dict[int, Dict[str, Any]] = {}
        for r in res:
            aid = int(r["appln_id"])
            fresh[aid] = {
                "person_name": (r.get("person_name") or r.get("psn_name")),
                "person_ctry_code": r.get("person_ctry_code"),
            }

        # ensure missing ids get defaults
        for i in missing:
            fresh.setdefault(int(i), {"person_name": None, "person_ctry_code": None})

        cache_set_many("appl1", fresh)
        out.update(fresh)

    for i in ids:
        out.setdefault(int(i), {"person_name": None, "person_ctry_code": None})
    return out

def cheap_peer_score_from_xy(x_max_forward_citations: int, y_docdb_family_size: int) -> Dict[str, Any]:
    """
    SUPER CHEAP peer score based ONLY on:
      X = max forward citations (EP pubs)
      Y = DOCDB family size

    No legal status, no term remaining, no flags (US/WO/etc).
    This is for quick peer ranking / chart labels only.
    """
    import math

    x = max(0, int(x_max_forward_citations or 0))
    y = max(0, int(y_docdb_family_size or 0))

    # Saturating transforms (cheap + stable)
    # - citations saturate around ~50
    # - family size saturates around ~50
    x_norm = math.log1p(min(x, 50)) / math.log1p(50)   # 0..1
    y_norm = math.log1p(min(y, 50)) / math.log1p(50)   # 0..1

    # Weight citations a bit more than family
    total = int(round(100.0 * (0.65 * x_norm + 0.35 * y_norm)))

    return {
        "total": total,
        "components": {
            "x_citations_norm": round(x_norm, 4),
            "y_family_norm": round(y_norm, 4),
        },
        "notes": [
            "XY-only cheap score (log-saturated). Not comparable to score_v0.",
            "Use for peer ranking/labels only.",
        ],
    }


def fast_peer_reference_xy(patstat: PatstatClient, peers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Build minimal payload for X/Y chart + human-readable labels.
    Uses cached/batched:
      - max_fwd citations
      - docdb family size
      - title (pref EN)
      - main applicant (seq 1)
    """
    appln_ids = [int(p["appln_id"]) for p in peers if p.get("appln_id")]
    appln_ids = appln_ids[:50]  # safety; k is tiny anyway

    max_cit = fast_max_forward_citations_for_appln_ids(patstat, appln_ids)
    fam_sz  = fast_docdb_family_size_for_appln_ids(patstat, appln_ids)
    titles  = fast_titles_for_appln_ids(patstat, appln_ids)
    appl1   = fast_main_applicant_for_appln_ids(patstat, appln_ids)

    out = []
    for p in peers:
        aid = int(p["appln_id"])
        t = titles.get(aid, {}) or {}
        a = appl1.get(aid, {}) or {}

        x_val = int(max_cit.get(aid, 0))
        y_val = int(fam_sz.get(aid, 0))

        out.append({
            "ep_nr": p["ep_nr"],
            "appln_id": aid,

            "title": t.get("title"),
            "title_lang": t.get("title_lang"),
            "main_applicant": a.get("person_name"),
            "main_applicant_ctry": a.get("person_ctry_code"),

            "x_max_forward_citations": x_val,
            "y_docdb_family_size": y_val,

            # ✅ NEW: super-cheap peer score
            "cheap_peer_score": cheap_peer_score_from_xy(x_val, y_val),

            "overlap": p.get("overlap"),
        })
    return out






#helper for less strict year analysis
import math

def legal_activity_score_from_days(days_since_fee: Optional[int]) -> int:
    """
    Smooth decay from 20 down to ~0 as days increase.
    Tuned so:
      - ~20 around 0-1y
      - ~14 around 3y
      - ~8 around 7y
    """
    if days_since_fee is None:
        return 0
    if days_since_fee < 0:
        days_since_fee = 0

    # Half-life-ish decay. You can tweak 900–1400 to shift curve.
    decay = math.exp(-days_since_fee / 1200.0)
    score = 20.0 * decay + 2.0  # small floor bump so “some activity” still counts
    return int(max(0, min(20, round(score))))


# ====================================================================================================
# ====================================================================================================
# ==========================================  MODULE 09  ============================================
# ======================================  SCORE v0 (EXPLAINABLE)  ===================================
# ====================================================================================================
# ====================================================================================================

def years_remaining_20y(filing_date: Optional[date], today: Optional[date] = None) -> Optional[float]:
    if filing_date is None:
        return None
    if today is None:
        today = date.today()
    years_passed = (today - filing_date).days / 365.25
    return max(0.0, 20.0 - years_passed)


def score_v0(report: Dict[str, Any], today: Optional[date] = None, include_peers: bool = True) -> Dict[str, Any]:
    """
    Explainable score (0-100) based on:
      - max citations across EP publications
      - family breadth (size + key jurisdictions)
      - legal activity (latest renewal vs lapse)
      - remaining term estimate

    Extensions (small):
      - include a velocity note (recent citations) from Module 05 if present
    """
    if today is None:
        today = date.today()

    core = report.get("core") or {}
    fam = report.get("family_docdb") or {}
    legal = (report.get("legal_events") or {}).get("summary") or {}
    robust = report.get("citations_robust") or {}
    max_pub = robust.get("max_any_publn") or {}

    max_cit = int(max_pub.get("forward_citations") or 0)
    #cit_score = min(40, int(10 * (max_cit ** 0.5)))
    cit_score = min(40, int(8 * (max_cit ** 0.5)) + (2 if max_cit > 0 else 0))


    family_size = int(fam.get("family_size") or 0)
    flags = (fam.get("flags") or {})
    breadth_score = min(10, family_size)
    if flags.get("has_US"):
        breadth_score += 6
    if flags.get("has_JP"):
        breadth_score += 4
    if flags.get("has_KR"):
        breadth_score += 3
    if flags.get("has_WO"):
        breadth_score += 2
    family_score = min(25, breadth_score)

    latest_fee = legal.get("latest_fee_payment")
    latest_lapse = legal.get("latest_lapse")
    
    legal_score = 0
    
    # Fee-based “alive-ish” signal
    if latest_fee and latest_fee.get("fee_payment_date"):
        days = (today - latest_fee["fee_payment_date"]).days
        legal_score = legal_activity_score_from_days(days)
    
    # Lapse penalty (still bucketed; keep it simple)
    if latest_lapse and latest_lapse.get("lapse_date"):
        days = (today - latest_lapse["lapse_date"]).days
        if days <= 365:
            legal_score = max(0, legal_score - 10)
        elif days <= 3 * 365:
            legal_score = max(0, legal_score - 6)


    yrem = years_remaining_20y(core.get("appln_filing_date"), today=today)
    if yrem is None:
        term_score = 0
    elif yrem >= 10:
        term_score = 15
    elif yrem >= 5:
        term_score = 10
    elif yrem > 0:
        term_score = 5
    else:
        term_score = 0

    total = int(min(100, cit_score + family_score + legal_score + term_score))

    explanation = [
        f"Max forward citations across EP publications: {max_cit} (citation score uses sqrt curve).",
        f"DOCDB family size: {family_size} | footprint: {fam.get('by_authority')}.",
        f"Legal signals (designated-state fee/lapse proxies): {legal.get('summary')}.",
    ]

    velocity = ((report.get("citations") or {}).get("velocity") or {})
    if velocity:
        explanation.append(f"Citation velocity proxy: {velocity} (recent citations in last N years).")

    if yrem is not None:
        explanation.append(f"Estimated years remaining (20y baseline): {yrem:.1f}.")

    # --------------------------------------------------------------------------------
    # v1.1 ADD-ON: compare vs 2 "similar patents" selected by CPC/IPC overlap
    # --------------------------------------------------------------------------------
    peer_comparison = None
    if include_peers:
        peer_block = find_similar_ep_peers(patstat, report, k=2)

        peer_xy = []
        if peer_block.get("enabled") and peer_block.get("peers"):
            # FAST: reference X/Y only (no build_patent_report, no score_v0 on peers)
            peer_xy = fast_peer_reference_xy(patstat, peer_block["peers"])
        my_xy_cheap = cheap_peer_score_from_xy(max_cit, family_size)
        peer_comparison = {
            "my_cheap_xy_score": my_xy_cheap,
            "peer_selection": peer_block,
            "peer_reference_xy": peer_xy,
            "notes": [
                "Peers use fast reference values for charting (no full report build).",
                "X=max forward citations (EP pubs), Y=DOCDB family size.",
            ],
        }



    # IMPORTANT: prevent recursion explosion
    # We do NOT want peer scores to include their own peers, etc.
    #debug = {
    #    "latest_fee_payment": legal.get("latest_fee_payment"),
    #    "latest_lapse": legal.get("latest_lapse"),
    #    "today": today,
    #}
    

    return {
        "score_total": total,
        "score_components": {
            "citations": cit_score,
            "family": family_score,
            "legal_activity": legal_score,
            "term_remaining": term_score,
        },
        "explanation": explanation,
        "raw": {"max_citations": max_cit, "family_size": family_size, "years_remaining_est": yrem},
        "peer_comparison": peer_comparison,
        #"_debug": debug,  # 👈 TEMPORARY
    }


# ====================================================================================================
# ====================================================================================================
# ==========================================  MODULE 10  ============================================
# ======================================  API MODELS / SCHEMAS  =====================================
# ====================================================================================================
# ====================================================================================================

class PortfolioRequest(BaseModel):
    ep_nrs: List[str] = Field(..., min_length=1, examples=[["15860005", "13849544"]])
    include_inventors: bool = Field(False, description="Include inventors in each report (can be heavier).")
    include_peers: bool = Field(False, description="Also compute peers (CPC/IPC-based) and quick comparison points (X/Y) for the top-ranked patents only (see /portfolio/score behavior).")


class NormalizationRequest(BaseModel):
    ep_nr: str = Field(..., examples=["15860005"])
    sample_size: int = Field(DEFAULT_COHORT_SAMPLE, ge=50, le=MAX_COHORT_SIZE)


class ApiError(BaseModel):
    error: str
    detail: Optional[str] = None


# ====================================================================================================
# ====================================================================================================
# ==========================================  MODULE 11  ============================================
# =========================================  FASTAPI APP SETUP  =====================================
# ====================================================================================================
# ====================================================================================================

app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    description="Explainable patent scoring + report generation using PATSTAT signals only (enriched).",
    root_path=DEFAULT_ROOT_PATH,          # will be overridden per-request if X-Forwarded-Prefix exists
    docs_url="/docs",
    openapi_url="/openapi.json",
    redoc_url=None,
    root_path_in_servers=False,          # IMPORTANT: we manage servers ourselves
)


@app.middleware("http")
async def set_root_path_from_forwarded_prefix(request: Request, call_next):
    """
    TIP / reverse proxies commonly set X-Forwarded-Prefix.
    We inject it into request.scope["root_path"] so routing + swagger behave.
    """
    prefix = request.headers.get("x-forwarded-prefix")
    if prefix:
        request.scope["root_path"] = prefix
    return await call_next(request)


def custom_openapi():
    """
    Generate OpenAPI schema with a server base URL that matches the proxy prefix.
    This helps Swagger request the correct /openapi.json (and all endpoints) under TIP proxy paths.
    """
    from fastapi.openapi.utils import get_openapi

    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    # Provide a neutral server; actual routing uses root_path at runtime.
    # Swagger UI usually resolves relative paths correctly with root_path,
    # but adding servers is a helpful belt-and-suspenders.
    schema["servers"] = [{"url": DEFAULT_ROOT_PATH or "/"}]
    return schema


app.openapi = custom_openapi

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,   # MUST be False when allow_origins=["*"]
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=86400,
)



# ====================================================================================================
# ====================================================================================================
# ==========================================  MODULE 12  ============================================
# ============================================  API ENDPOINTS  ======================================
# ====================================================================================================
# ====================================================================================================

@app.get("/health", summary="Health check")
def health() -> Dict[str, Any]:
    return {"status": "ok", "time": now_utc_iso(), "patstat_env": PATSTAT_ENV, "version": API_VERSION}


@app.get("/report", summary="Get full enriched PATSTAT report for one EP application number")
def api_report(
    ep_nr: str = Query(..., description="EP application number, e.g. 15860005", examples=["15860005"]),
    include_inventors: bool = Query(True, description="Include inventor list (may increase payload)."),
    include_top_citers: bool = Query(False, description="Include sample of top citing publications (network use)."),
) -> Dict[str, Any]:
    try:
        report = build_patent_report(
            patstat,
            ep_nr,
            include_inventors=include_inventors,
            include_top_citers=include_top_citers,
        )
        return {"input": {"ep_nr": ep_nr, "ep_nr_clean": report["core"]["ep_nr_clean"]}, "report": _jsonable(report)}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error while building report: {e}")


@app.get("/score", summary="Get explainable score for one EP application number")
def api_score(
    ep_nr: str = Query(..., description="EP application number, e.g. 15860005", examples=["15860005"]),
    include_peers: bool = Query(True, description="Also compute 2 similar patents (CPC/IPC peers) and quick comparison points (X/Y).")
) -> Dict[str, Any]:
    try:
        report = build_patent_report(patstat, ep_nr, include_inventors=False, include_top_citers=False)
        s = score_v0(report, include_peers=include_peers)
        return {"input": {"ep_nr": ep_nr, "ep_nr_clean": report["core"]["ep_nr_clean"]}, "score": _jsonable(s)}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error while building score: {e}")


@app.post("/portfolio/report", summary="Get full enriched PATSTAT reports + aggregates for a portfolio")
def api_portfolio_report(req: PortfolioRequest) -> Dict[str, Any]:
    try:
        out = build_portfolio_report(patstat, req.ep_nrs, include_inventors=req.include_inventors)
        return _jsonable(out)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error while building portfolio report: {e}")


@app.post("/portfolio/score", summary="Get scores for a portfolio (plus portfolio aggregates)")
def api_portfolio_score(req: PortfolioRequest) -> Dict[str, Any]:
    try:
        portfolio = build_portfolio_report(patstat, req.ep_nrs, include_inventors=False)
        reports = portfolio.get("reports", [])

        scored = []
        for r in reports:
            if "error" in r:
                scored.append({"input": r.get("input"), "error": r.get("error")})
            else:
                # First pass: base score WITHOUT peers (fast, stable)
                scored.append({"input": r.get("input"), "score": score_v0(r, include_peers=False)})
        
        # Optional: recompute peers only for top N
        if req.include_peers:
            top_n = 3  # or make it an env var / request field
            ok_scored = [x for x in scored if x.get("score") and "score_total" in x["score"]]
            ok_scored.sort(key=lambda x: x["score"]["score_total"], reverse=True)
        
            # Map ep_nr -> report for quick lookup
            report_by_ep = {}
            for r in reports:
                ep = (r.get("input") or {}).get("ep_nr")
                if ep and "error" not in r:
                    report_by_ep[ep] = r
        
            for x in ok_scored[:top_n]:
                ep = (x.get("input") or {}).get("ep_nr")
                rep = report_by_ep.get(ep)
                if rep:
                    # Recompute INCLUDING peers (but score_v0 already prevents recursion explosion)
                    x["score"] = score_v0(rep, include_peers=True)


        return _jsonable({"portfolio": portfolio.get("portfolio"), "scores": scored})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error while building portfolio score: {e}")



@app.post("/normalize/citations", summary="Compute optional cohort-based field-normalized citation position")
def api_normalize_citations(req: NormalizationRequest = Body(...)) -> Dict[str, Any]:
    """
    This endpoint is intentionally separate because it can be more expensive.

    It:
      1) builds a report (light)
      2) computes cohort normalization stats
      3) returns normalization block
    """
    try:
        report = build_patent_report(patstat, req.ep_nr, include_inventors=False, include_top_citers=False)
        norm = cohort_normalization(patstat, report, sample_size=req.sample_size)
        return _jsonable({"input": {"ep_nr": req.ep_nr, "ep_nr_clean": report["core"]["ep_nr_clean"]}, "normalization": norm})
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error while computing normalization: {e}")


# ====================================================================================================
# ====================================================================================================
# ==============================  MODULE 13  |  TODO / FUTURE EXTENSIONS  =============================
# ====================================================================================================
# ====================================================================================================
#
# The following items are explicitly not implemented yet, either because:
#   - they require extra PATSTAT tables not confirmed in TIP environment, or
#   - they require non-PATSTAT datasets/APIs, or
#   - they require product design decisions (how to define the metric)
#
# ---------------------------
# A) PATSTAT EXTENSIONS (LIKELY DOABLE IF TABLES ARE AVAILABLE)
# ---------------------------
#  [x] Priority claims + earliest priority date (IMPLEMENTED in v1.1: Module 2B via tls204_appln_prior)
#        - See: get_priority_links(), summarize_priorities(), enrich_card_with_priority_and_ipc()
#
#  [x] IPC classification (IMPLEMENTED in v1.1: Module 2C via tls209_appln_ipc)
#        - See: get_ipc_list(), ipc_coarse_buckets(), enrich_card_with_priority_and_ipc()
#
#  [ ] PCT / international phase markers:
#        - Might require specific patterns on publication/auth or priority links
#
#  [ ] Applicant harmonization / name cleaning:
#        - PATSTAT has person_id/psn_name but corporate group harmonization needs rules + maybe external.
#
# ---------------------------
# B) PRODUCT IDEA FEATURES (NOT PATSTAT-ONLY)
# ---------------------------
#  [ ] Examiner X/Y evidence (search report, blocking power):
#        - Not in vanilla PATSTAT bibliographic/citation tables.
#        - Requires EPO internal sources or specific datasets.
#
#  [ ] Opposition / litigation risk signals:
#        - Requires EPO opposition data and/or court/litigation datasets.
#
#  [ ] BPI / IPscore / other value indices:
#        - Requires external model/dataset definitions.
#
#  [ ] Claims / scope features:
#        - Not in PATSTAT. Need full text / claims parsing pipelines.
#
#  [ ] AI / embeddings / novelty / similarity:
#        - Needs text sources + embedding store + retrieval.
#
# ---------------------------
# C) API / ARCHITECTURE IMPROVEMENTS
# ---------------------------
#  [ ] Split into package modules (patstat_queries.py, scoring.py, api.py, etc.)
#  [ ] Add persistent cache (Redis) + async query execution
#  [ ] Add rate limiting and API keys (if exposed publicly)
#  [ ] Add structured logging + tracing
#  [ ] Add “batch” endpoints returning minimal payload for dashboards
#


