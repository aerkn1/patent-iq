"""
Singleton registry that downloads and holds LightGBM models, calibration
data, and metadata for the citation forecast system.
"""
import json
import logging
from pathlib import Path
from typing import Optional

import lightgbm as lgb
from huggingface_hub import hf_hub_download

from config.settings import get_settings

logger = logging.getLogger("uvicorn")

_ARTIFACTS = {
    "model_3y": "model_3y.txt",
    "model_5y": "model_5y.txt",
    "calibration": "calibration_bucketed.json",
    "metadata": "metadata.json",
}


class ModelRegistry:
    """Singleton holding loaded LightGBM boosters + calibration + metadata."""

    _instance: Optional["ModelRegistry"] = None

    def __init__(self):
        self.models: dict[str, lgb.Booster] = {}
        self.calib: dict[str, dict] = {}
        self.meta: dict[str, dict] = {}

    # The model expects these features in this exact order
    MODEL_FEATURES = [
        "cites_pre_asof",
        "family_members_count",
        "family_jurisdiction_count",
        "major_office_grant_auth_count",
        "family_cpc_subclass_count",
        "has_us_grant",
        "has_cn_grant",
        "has_jp_grant",
        "has_kr_grant",
        "as_of_year",
    ]

    # ── public API ──────────────────────────────────────────────────────

    @classmethod
    def initialize(cls) -> None:
        """Download HF artifacts and load models into memory. Call once at startup."""
        inst = cls()
        settings = get_settings()
        token = settings.hf_token
        if not token:
            raise RuntimeError("HF_TOKEN environment variable is required for model download")

        local_paths: dict[str, Path] = {}
        for key, filename in _ARTIFACTS.items():
            path = hf_hub_download(
                repo_id=settings.hf_model_repo,
                filename=filename,
                subfolder=settings.hf_model_subfolder,
                repo_type="model",
                token=token,
            )
            local_paths[key] = Path(path)

        for horizon in ("3y", "5y"):
            model_path = local_paths[f"model_{horizon}"]
            inst.models[horizon] = lgb.Booster(model_file=str(model_path))
            logger.info(f"Loaded LightGBM model for {horizon} from {model_path}")

        with open(local_paths["calibration"]) as f:
            calib_raw = json.load(f)
        for horizon in ("3y", "5y"):
            if horizon not in calib_raw:
                raise ValueError(f"Calibration JSON missing key '{horizon}'")
            inst.calib[horizon] = calib_raw[horizon]

        with open(local_paths["metadata"]) as f:
            inst.meta = json.load(f)

        cls._health_check(inst)

        cls._instance = inst
        logger.info("ModelRegistry initialized successfully")

    @classmethod
    def get(cls) -> "ModelRegistry":
        if cls._instance is None:
            raise RuntimeError(
                "ModelRegistry not initialized — call ModelRegistry.initialize() at startup"
            )
        return cls._instance

    # ── health checks ───────────────────────────────────────────────────

    @staticmethod
    def _health_check(inst: "ModelRegistry") -> None:
        expected_n_features = len(inst.MODEL_FEATURES)
        for horizon in ("3y", "5y"):
            # Feature count check
            model_n_features = inst.models[horizon].num_feature()
            if expected_n_features != model_n_features:
                raise ValueError(
                    f"[{horizon}] defines {expected_n_features} features "
                    f"but model expects {model_n_features}"
                )

            # Calibration schema check
            calib = inst.calib[horizon]
            if "difficulty_cutpoints" not in calib:
                raise ValueError(f"[{horizon}] calibration missing 'difficulty_cutpoints'")
            cutpoints = calib["difficulty_cutpoints"]
            if "q33" not in cutpoints or "q66" not in cutpoints:
                raise ValueError(f"[{horizon}] difficulty_cutpoints missing q33/q66")
            if "bucket_qhats" not in calib:
                raise ValueError(f"[{horizon}] calibration missing 'bucket_qhats'")
            
            # bucket_qhats is a dict with keys "0", "1", "2", each containing "qhat_abs_log"
            bq = calib["bucket_qhats"]
            if not all(k in bq for k in ("0", "1", "2")):
                 raise ValueError(f"[{horizon}] bucket_qhats must have keys '0', '1', '2'")

        logger.info("Model health checks passed ✓")
