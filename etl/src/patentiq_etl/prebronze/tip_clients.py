from __future__ import annotations

from collections.abc import Iterable
import logging
from pathlib import Path
from typing import Any

import duckdb

from patentiq_etl.common.io import ensure_dir


LOGGER = logging.getLogger(__name__)


PATSTAT_MODEL_CANDIDATES = {
    "bronze_patstat_appln": ["TLS201_APPLN"],
    "bronze_patstat_appln_title": ["TLS202_APPLN_TITLE"],
    "bronze_patstat_appln_abstr": ["TLS203_APPLN_ABSTR"],
    "bronze_patstat_appln_prior": ["TLS204_APPLN_PRIOR"],
    "bronze_patstat_person": ["TLS206_PERSON"],
    "bronze_patstat_pers_appln": ["TLS207_PERS_APPLN"],
    "bronze_patstat_appln_ipc": ["TLS209_APPLN_IPC"],
    "bronze_patstat_pat_publn": ["TLS211_PAT_PUBLN"],
    "bronze_patstat_citation": ["TLS212_CITATION"],
    "bronze_patstat_npl_publn": ["TLS214_NPL_PUBLN"],
    "bronze_patstat_appln_contn": ["TLS216_APPLN_CONTN"],
    "bronze_patstat_appln_cpc": ["TLS224_APPLN_CPC"],
    "bronze_patstat_docdb_fam_citn": ["TLS228_DOCDB_FAM_CITN"],
    "bronze_patstat_appln_techn_field": ["TLS230_APPLN_TECHN_FIELD", "TLS230_APPLN_TECHNFLD"],
    "bronze_patstat_inpadoc_legal_event": ["TLS231_INPADOC_LEGAL_EVENT"],
    "bronze_ref_legal_event_code": ["TLS803_LEGAL_EVENT_CODE"],
    "bronze_ref_techn_field_ipc": ["TLS901_TECHN_FIELD_IPC"],
}


REGISTER_MODEL_CANDIDATES = {
    "bronze_reg101_appln": ["REG101_APPLN"],
    "bronze_reg403_appln_status": ["REG403_APPLN_STATUS"],
    "bronze_reg107_parties": ["REG107_PARTIES"],
    "bronze_reg111_licensee": ["REG111_LICENSEE"],
    "bronze_reg125_appeal": ["REG125_APPEAL"],
    "bronze_reg130_opponent": ["REG130_OPPONENT"],
    "bronze_reg201_proc_step": ["REG201_PROC_STEP"],
    "bronze_reg202_proc_step_text": ["REG202_PROC_STEP_TEXT"],
    "bronze_reg203_proc_step_date": ["REG203_PROC_STEP_DATE"],
    "bronze_reg301_event_data": ["REG301_EVENT_DATA"],
    "bronze_reg402_event_text": ["REG402_EVENT_TEXT"],
    "bronze_reg701_appln": ["REG701_APPLN"],
    "bronze_reg731_event_data": ["REG731_EVENT_DATA"],
    "bronze_reg741_appln_status": ["REG741_APPLN_STATUS"],
    "bronze_reg742_event_text": ["REG742_EVENT_TEXT"],
}


def get_patstat_client(env: str):
    """Return a TIP PATSTAT client and ORM handle."""
    from epo.tipdata.patstat import PatstatClient

    patstat = PatstatClient(env=env)
    return patstat, patstat.orm()


def get_epab_client(env: str):
    """Return a TIP EPAB client."""
    from epo.tipdata.epab import EPABClient

    return EPABClient(env=env)


def close_tip_client(client) -> None:
    """Close one TIP client safely when the client exposes an explicit close method."""
    if client is None:
        return
    for method_name in ("close_session", "close"):
        method = getattr(client, method_name, None)
        if callable(method):
            try:
                method()
            except Exception:
                LOGGER.debug("Ignoring TIP client close failure for %s.%s", type(client).__name__, method_name, exc_info=True)
            return


def get_patstat_database_module():
    """Return the TIP PATSTAT database/model module."""
    from epo.tipdata.patstat import database as patstat_database

    return patstat_database


def resolve_model(database_module, candidates: Iterable[str]):
    """Resolve the first available ORM model from a candidate name list."""
    for name in candidates:
        model = getattr(database_module, name, None)
        if model is not None:
            return model
    return None


def resolve_patstat_model(database_module, logical_name: str):
    """Resolve one PATSTAT ORM model by logical Bronze table name."""
    return resolve_model(database_module, PATSTAT_MODEL_CANDIDATES.get(logical_name, []))


def resolve_register_model(database_module, logical_name: str):
    """Resolve one Register ORM model by logical Bronze table name."""
    return resolve_model(database_module, REGISTER_MODEL_CANDIDATES.get(logical_name, []))


def query_to_dataframe(client, query):
    """Materialize a TIP PATSTAT ORM query as a pandas DataFrame."""
    return client.df(query)


def result_to_dataframe(payload):
    """Normalize a TIP EPAB result payload into a pandas DataFrame."""
    import pandas as pd

    if hasattr(payload, "to_dict") and hasattr(payload, "columns"):
        return payload.copy()
    if isinstance(payload, list):
        return pd.DataFrame(payload)
    if payload is None:
        return pd.DataFrame()
    return pd.DataFrame(list(payload))


def write_dataframe_parquet(df, out_path: Path) -> int:
    """Write a pandas DataFrame to parquet with zstd compression."""
    ensure_dir(out_path.parent)
    df.to_parquet(out_path, index=False, compression="zstd")
    return len(df.index)


def parquet_row_count(path: Path) -> int:
    """Return the row count of a parquet artifact."""
    con = duckdb.connect()
    return int(con.execute("select count(*) from read_parquet(?)", [str(path)]).fetchone()[0])
