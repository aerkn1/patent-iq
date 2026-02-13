"""
Single-patent citation forecast service.
Implements the full inference pipeline: feature loading → LightGBM prediction →
conformal interval → difficulty bucket → response assembly.
"""
import logging
from math import expm1
from typing import Optional

import numpy as np

from domain.errors import NotFoundError, ValidationError
from domain.schemas.forecast import (
    PatentForecastResponse,
    PatentPrediction,
    Interval80,
    ForecastMeta,
)
from infrastructure.ml.model_registry import ModelRegistry
from infrastructure.repositories.forecast_feature_repo import ForecastFeatureRepository

logger = logging.getLogger(__name__)

_VALID_HORIZONS = {"3y", "5y"}

# Boolean columns that must be cast to 0/1 for the model
_BOOL_FEATURES = {"has_us_grant", "has_cn_grant", "has_jp_grant", "has_kr_grant"}


class PatentForecastService:

    def __init__(self):
        self.feature_repo = ForecastFeatureRepository()
        self.registry = ModelRegistry.get()

    async def get_forecast(self, appln_id: int, horizon: str) -> dict:
        if horizon not in _VALID_HORIZONS:
            raise ValidationError(f"horizon must be one of {_VALID_HORIZONS}")

        row = self.feature_repo.get_features(appln_id)
        if row is None:
            raise NotFoundError(f"No inference features for appln_id={appln_id}")

        feature_list = self.registry.MODEL_FEATURES
        x = np.array(
            [_cast_feature(row[f], f) for f in feature_list],
            dtype=np.float64,
        ).reshape(1, -1)

        y_pred_log: float = float(self.registry.models[horizon].predict(x)[0])

        expected = max(0.0, expm1(y_pred_log))

        calib = self.registry.calib[horizon]
        cutpoints = calib["difficulty_cutpoints"]
        bucket, bucket_idx = _assign_bucket(y_pred_log, cutpoints)

        qhat = calib["bucket_qhats"][str(bucket_idx)]["qhat_abs_log"]
        low_log = y_pred_log - qhat
        high_log = y_pred_log + qhat
        low = max(0.0, expm1(low_log))
        high = max(low, expm1(high_log))

        response = PatentForecastResponse(
            appln_id=appln_id,
            horizon=horizon,
            filing_date=str(row.get("filing_date", "")),
            as_of_date=str(row.get("as_of_date", "")),
            prediction=PatentPrediction(
                expected_citations=round(expected, 4),
                interval_80=Interval80(low=round(low, 4), high=round(high, 4)),
                difficulty_bucket=bucket,
            ),
            features_used={f: row[f] for f in feature_list},
            meta=ForecastMeta(
                model_version=self.registry.meta.get("lightgbm", "unknown"),
            ),
        )
        return response.model_dump()


# ── helpers ─────────────────────────────────────────────────────────────────

def _cast_feature(value, name: str) -> float:
    """Cast a single feature to float, handling booleans."""
    if name in _BOOL_FEATURES:
        if isinstance(value, bool):
            return 1.0 if value else 0.0
        return float(value)
    if value is None:
        return 0.0
    return float(value)


def _assign_bucket(y_pred_log: float, cutpoints: dict) -> tuple[str, int]:
    """Return (bucket_name, bucket_index) based on prediction vs cutpoints."""
    q33 = cutpoints["q33"]
    q66 = cutpoints["q66"]
    if y_pred_log <= q33:
        return "LOW", 0
    elif y_pred_log <= q66:
        return "MID", 1
    else:
        return "HIGH", 2
