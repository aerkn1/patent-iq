""" 
Portfolio-level citation forecast service.
Aggregates patent-level predictions weighted by owner share.
"""

import logging
from math import expm1

import numpy as np

from domain.errors import NotFoundError, ValidationError
from domain.schemas.forecast import (
    PortfolioForecastResponse,
    PortfolioPrediction,
    Interval80,
    DifficultyMix,
    TopContributor,
    ForecastMeta,
    SegmentItem,
    SegmentsMeta,
    PortfolioForecastSegments,
)
from infrastructure.ml.model_registry import ModelRegistry
from infrastructure.repositories.forecast_feature_repo import ForecastFeatureRepository

logger = logging.getLogger(__name__)

_VALID_HORIZONS = {"3y", "5y"}
_BOOL_FEATURES = {"has_us_grant", "has_cn_grant", "has_jp_grant", "has_kr_grant"}

_OTHER = "OTHER"
_UNKNOWN = "UNKNOWN"


class PortfolioForecastService:

    def __init__(self):
        self.feature_repo = ForecastFeatureRepository()
        self.registry = ModelRegistry.get()

    async def get_forecast(
        self,
        owner_id: int,
        horizon: str,
        segments: bool = True,
        segments_top_k: int = 10,
        cpc_top_n_per_patent: int = 5,
    ) -> dict:
        if horizon not in _VALID_HORIZONS:
            raise ValidationError(f"horizon must be one of {_VALID_HORIZONS}")

        appln_ids = self.feature_repo.get_portfolio_appln_ids(owner_id)
        if not appln_ids:
            raise NotFoundError(f"No portfolio found for owner_id={owner_id}")

        owner_shares = self.feature_repo.get_owner_shares(appln_ids)

        df = self.feature_repo.get_features_batch(appln_ids)
        if df.empty:
            raise NotFoundError(f"No inference features for owner_id={owner_id}")

        # Drop patents missing from features table
        available_ids = set(df["appln_id"].tolist())
        missing = set(appln_ids) - available_ids
        if missing:
            logger.warning(
                f"Portfolio {owner_id}: {len(missing)} patents missing from feature table, skipped"
            )

        feature_list = self.registry.MODEL_FEATURES
        X = np.zeros((len(df), len(feature_list)), dtype=np.float64)
        for j, f in enumerate(feature_list):
            col = df[f].values
            if f in _BOOL_FEATURES:
                X[:, j] = np.where(col.astype(bool), 1.0, 0.0)
            else:
                X[:, j] = np.nan_to_num(col.astype(np.float64), nan=0.0)

        # Batch predict
        y_pred_log = self.registry.models[horizon].predict(X)

        calib = self.registry.calib[horizon]
        cutpoints = calib["difficulty_cutpoints"]
        q33, q66 = cutpoints["q33"], cutpoints["q66"]
        bucket_qhats = calib["bucket_qhats"]

        df_by_id = df.set_index("appln_id", drop=False)

        patent_results: list[dict] = []
        for i, row in df.iterrows():
            aid = int(row["appln_id"])
            ylog = float(y_pred_log[i])
            expected_i = max(0.0, expm1(ylog))

            # bucket
            if ylog <= q33:
                bucket, bidx = "LOW", 0
            elif ylog <= q66:
                bucket, bidx = "MID", 1
            else:
                bucket, bidx = "HIGH", 2

            # interval
            qhat = bucket_qhats[str(bidx)]["qhat_abs_log"]
            low_i = max(0.0, expm1(ylog - qhat))
            high_i = max(low_i, expm1(ylog + qhat))

            share = float(owner_shares.get(aid, 1.0))

            patent_results.append({
                "appln_id": aid,
                "owner_share": share,
                "expected": expected_i,
                "low": low_i,
                "high": high_i,
                "bucket": bucket,
                "contribution": share * expected_i,
            })

        expected_total = sum(p["owner_share"] * p["expected"] for p in patent_results)
        low_total = sum(p["owner_share"] * p["low"] for p in patent_results)
        high_total = sum(p["owner_share"] * p["high"] for p in patent_results)
        n_patents_effective = sum(p["owner_share"] for p in patent_results)
        expected_per_eff = expected_total / n_patents_effective if n_patents_effective > 0 else 0.0

        bucket_weights = {"LOW": 0.0, "MID": 0.0, "HIGH": 0.0}
        for p in patent_results:
            bucket_weights[p["bucket"]] += p["owner_share"]
        if n_patents_effective > 0:
            for k in bucket_weights:
                bucket_weights[k] /= n_patents_effective

        patent_results.sort(key=lambda p: p["contribution"], reverse=True)
        top_10 = patent_results[:10]

        # Portfolio-level as_of_date = latest as_of_date
        as_of_dates = df["as_of_date"].dropna()
        portfolio_as_of = str(as_of_dates.max()) if not as_of_dates.empty else ""

        segments_payload = None
        if segments:
            try:
                segments_payload = _compute_segments(
                    owner_id=owner_id,
                    df_by_id=df_by_id,
                    patent_results=patent_results,
                    expected_total=float(expected_total),
                    segments_top_k=int(segments_top_k),
                    cpc_top_n_per_patent=int(cpc_top_n_per_patent),
                    feature_repo=self.feature_repo,
                )
            except Exception:
                logger.exception(
                    "Failed to compute portfolio forecast segments",
                    extra={"owner_id": owner_id},
                )
                segments_payload = None

        response = PortfolioForecastResponse(
            owner_id=owner_id,
            horizon=horizon,
            as_of_date=portfolio_as_of,
            portfolio_prediction=PortfolioPrediction(
                expected_citations_total=round(expected_total, 4),
                interval_80_total=Interval80(
                    low=round(low_total, 4),
                    high=round(high_total, 4),
                ),
                n_patents_effective=round(n_patents_effective, 4),
                expected_per_effective_patent=round(expected_per_eff, 4),
            ),
            difficulty_mix=DifficultyMix(
                LOW=round(bucket_weights["LOW"], 4),
                MID=round(bucket_weights["MID"], 4),
                HIGH=round(bucket_weights["HIGH"], 4),
            ),
            top_contributors=[
                TopContributor(
                    appln_id=p["appln_id"],
                    owner_share=round(p["owner_share"], 4),
                    expected=round(p["expected"], 4),
                    interval_80=Interval80(
                        low=round(p["low"], 4),
                        high=round(p["high"], 4),
                    ),
                    contribution=round(p["contribution"], 4),
                    difficulty_bucket=p["bucket"],
                )
                for p in top_10
            ],
            segments=segments_payload,
            meta=ForecastMeta(
                model_version=self.registry.meta.get("lightgbm", "unknown"),
                calibration="bucketed_conformal_80",
                as_of_definition="filing_plus_2y",
            ),
        )
        return response.model_dump()


def _bucket_jurisdiction_coverage(value) -> str:
    try:
        if value is None or (isinstance(value, float) and np.isnan(value)):
            return _UNKNOWN
        v = int(value)
    except Exception:
        return _UNKNOWN

    if v <= 0:
        return _UNKNOWN
    if v == 1:
        return "1"
    if 2 <= v <= 3:
        return "2-3"
    if 4 <= v <= 6:
        return "4-6"
    return "7+"


def _bucket_major_office_grants(value) -> str:
    try:
        if value is None or (isinstance(value, float) and np.isnan(value)):
            return _UNKNOWN
        v = int(value)
    except Exception:
        return _UNKNOWN

    if v < 0:
        return _UNKNOWN
    if v == 0:
        return "0"
    if v == 1:
        return "1"
    if 2 <= v <= 3:
        return "2-3"
    return "4-5"


def _bucket_as_of_year(value) -> str:
    try:
        if value is None or (isinstance(value, float) and np.isnan(value)):
            return _UNKNOWN
        y = int(value)
    except Exception:
        return _UNKNOWN

    if y <= 0:
        return _UNKNOWN
    if y <= 2014:
        return "<=2014"
    if 2015 <= y <= 2018:
        return "2015-2018"
    if 2019 <= y <= 2021:
        return "2019-2021"
    return ">=2022"


def _add_totals(totals: dict[str, dict[str, float]], key: str, expected: float, low: float, high: float) -> None:
    if key not in totals:
        totals[key] = {"expected": 0.0, "low": 0.0, "high": 0.0}
    totals[key]["expected"] += expected
    totals[key]["low"] += low
    totals[key]["high"] += high


def _to_segment_items(
    totals: dict[str, dict[str, float]],
    expected_total: float,
    order: list[str] | None = None,
) -> list[SegmentItem]:
    items: list[SegmentItem] = []

    keys: list[str]
    if order:
        keys = [k for k in order if k in totals] + [k for k in totals.keys() if k not in order]
    else:
        keys = list(totals.keys())

    for key in keys:
        exp = float(totals[key]["expected"])
        low = float(totals[key]["low"])
        high = float(totals[key]["high"])
        if exp <= 0 and low <= 0 and high <= 0:
            continue
        share = (exp / expected_total) if expected_total > 0 else 0.0
        items.append(
            SegmentItem(
                key=str(key),
                expected=round(exp, 4),
                interval_80=Interval80(low=round(low, 4), high=round(high, 4)),
                share=round(share, 4),
            )
        )

    return items


def _compute_segments(
    owner_id: int,
    df_by_id,
    patent_results: list[dict],
    expected_total: float,
    segments_top_k: int,
    cpc_top_n_per_patent: int,
    feature_repo: ForecastFeatureRepository,
) -> PortfolioForecastSegments:
    # Bucket-based segments
    juris_totals: dict[str, dict[str, float]] = {}
    grant_totals: dict[str, dict[str, float]] = {}
    year_totals: dict[str, dict[str, float]] = {}

    for p in patent_results:
        aid = p["appln_id"]
        row = df_by_id.loc[aid] if aid in df_by_id.index else None

        expected_c = float(p["owner_share"] * p["expected"])
        low_c = float(p["owner_share"] * p["low"])
        high_c = float(p["owner_share"] * p["high"])

        juris_key = _bucket_jurisdiction_coverage(None if row is None else row.get("family_jurisdiction_count"))
        grant_key = _bucket_major_office_grants(None if row is None else row.get("major_office_grant_auth_count"))
        year_key = _bucket_as_of_year(None if row is None else row.get("as_of_year"))

        _add_totals(juris_totals, juris_key, expected_c, low_c, high_c)
        _add_totals(grant_totals, grant_key, expected_c, low_c, high_c)
        _add_totals(year_totals, year_key, expected_c, low_c, high_c)

    # CPC segmentation
    cpc_totals: dict[str, dict[str, float]] = {}
    cpc_df = feature_repo.get_portfolio_cpc_top_n_per_patent(owner_id, cpc_top_n_per_patent)

    cpc_by_patent: dict[int, list[tuple[str, float]]] = {}
    if not cpc_df.empty:
        for _, r in cpc_df.iterrows():
            aid = int(r["appln_id"])
            code = str(r["cpc_subclass"])
            try:
                freq = float(r["cpc_freq"])
            except Exception:
                continue
            if freq <= 0 or np.isnan(freq):
                continue
            cpc_by_patent.setdefault(aid, []).append((code, freq))

    for p in patent_results:
        aid = p["appln_id"]
        expected_c = float(p["owner_share"] * p["expected"])
        low_c = float(p["owner_share"] * p["low"])
        high_c = float(p["owner_share"] * p["high"])

        weights = cpc_by_patent.get(aid)
        if not weights:
            _add_totals(cpc_totals, _OTHER, expected_c, low_c, high_c)
            continue

        sum_top = sum(w for _, w in weights if w > 0)
        if sum_top <= 0:
            _add_totals(cpc_totals, _OTHER, expected_c, low_c, high_c)
            continue

        remainder = max(0.0, 1.0 - sum_top)
        renorm = 1.0
        if sum_top > 1.0:
            remainder = 0.0
            renorm = sum_top

        for code, w in weights:
            ww = w / renorm
            if ww <= 0:
                continue
            _add_totals(cpc_totals, code, expected_c * ww, low_c * ww, high_c * ww)

        if remainder > 0:
            _add_totals(cpc_totals, _OTHER, expected_c * remainder, low_c * remainder, high_c * remainder)

    # Keep top-K CPC codes and fold the rest into OTHER
    other = cpc_totals.pop(_OTHER, {"expected": 0.0, "low": 0.0, "high": 0.0})
    sorted_codes = sorted(cpc_totals.items(), key=lambda kv: float(kv[1]["expected"]), reverse=True)
    top_items = sorted_codes[: max(0, segments_top_k)]
    tail_items = sorted_codes[max(0, segments_top_k):]

    for _, t in tail_items:
        other["expected"] += float(t["expected"])
        other["low"] += float(t["low"])
        other["high"] += float(t["high"])

    top_cpc_totals: dict[str, dict[str, float]] = {k: v for k, v in top_items}
    if other["expected"] > 0 or other["low"] > 0 or other["high"] > 0:
        top_cpc_totals[_OTHER] = other

    segments_meta = SegmentsMeta(
        top_k=int(segments_top_k),
        cpc_top_n_per_patent=int(cpc_top_n_per_patent),
        allocation="owner_share * (expected/low/high) weighted by cpc_freq",
        other_bucket_label=_OTHER,
    )

    return PortfolioForecastSegments(
        meta=segments_meta,
        by_cpc_subclass=_to_segment_items(top_cpc_totals, expected_total),
        by_jurisdiction_coverage_bucket=_to_segment_items(
            juris_totals,
            expected_total,
            order=["1", "2-3", "4-6", "7+", _UNKNOWN],
        ),
        by_major_office_grant_bucket=_to_segment_items(
            grant_totals,
            expected_total,
            order=["0", "1", "2-3", "4-5", _UNKNOWN],
        ),
        by_as_of_year_bucket=_to_segment_items(
            year_totals,
            expected_total,
            order=["<=2014", "2015-2018", "2019-2021", ">=2022", _UNKNOWN],
        ),
    )
