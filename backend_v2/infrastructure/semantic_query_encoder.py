from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import sys
from functools import lru_cache
from pathlib import Path
from threading import Lock

from config.settings import get_settings

FALLBACK_DIMS = 32
_TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")


def _hash_slot(token: str, seed: str = "") -> tuple[int, float]:
    digest = hashlib.sha256(f"{seed}{token}".encode("utf-8")).digest()
    slot = int.from_bytes(digest[:4], "little") % FALLBACK_DIMS
    sign = 1.0 if digest[4] % 2 == 0 else -1.0
    return slot, sign


def _lexical_hash_embedding(text: str) -> list[float]:
    vector = [0.0] * FALLBACK_DIMS
    tokens = _TOKEN_RE.findall(text.lower())
    for token in tokens:
        slot, sign = _hash_slot(token)
        vector[slot] += sign * (1.0 + min(len(token), 20) / 20.0)
        if len(token) >= 4:
            for trigram_idx in range(min(len(token) - 2, 3)):
                trigram = token[trigram_idx : trigram_idx + 3]
                tri_slot, tri_sign = _hash_slot(trigram, "tri:")
                vector[tri_slot] += tri_sign * 0.2
    norm = sum(value * value for value in vector) ** 0.5
    if norm == 0.0:
        return [0.0] * FALLBACK_DIMS
    return [round(float(value / norm), 6) for value in vector]


class SemanticQueryEncoder:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.manifest_path = self.settings.etl_data_root / "vectors" / "vec_embedding_manifest.json"
        self._manifest = self._load_manifest()
        self._model_cache: dict[str, object] = {}
        self._model_lock = Lock()

    def encode_text(self, query_text: str, vector_space: str) -> list[float]:
        normalized_space = self._normalize_vector_space(vector_space)
        normalized_text = self._normalize_query_text(query_text)
        model_id = self._model_id_for_space(normalized_space)
        if model_id == "lexical_hash_embedding_v1":
            return _lexical_hash_embedding(normalized_text)

        model = self._get_model(normalized_space, model_id)
        dense = model.encode(
            [normalized_text],
            batch_size=1,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        if getattr(dense, "shape", None) is None or len(dense) == 0:
            raise RuntimeError("Semantic query encoder returned no embedding.")
        return [float(value) for value in dense[0].tolist()]

    def _get_model(self, vector_space: str, model_id: str):
        cached = self._model_cache.get(vector_space)
        if cached is not None:
            return cached

        with self._model_lock:
            cached = self._model_cache.get(vector_space)
            if cached is not None:
                return cached

            self._ensure_etl_site_packages()
            os.environ.setdefault("HF_HUB_OFFLINE", "1")
            os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
            from sentence_transformers import SentenceTransformer

            model = SentenceTransformer(
                self._resolve_local_model_path(model_id),
                device=self._resolve_device(),
                local_files_only=True,
            )
            self._model_cache[vector_space] = model
            return model

    def _load_manifest(self) -> dict[str, object]:
        if not self.manifest_path.exists():
            return {}
        try:
            return json.loads(self.manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}

    def _model_id_for_space(self, vector_space: str) -> str:
        normalized_space = self._normalize_vector_space(vector_space)
        if normalized_space == "claims":
            return str(self._manifest.get("claim_model_id") or "AI-Growth-Lab/PatentSBERTa")
        return str(self._manifest.get("abstract_model_id") or "BAAI/bge-m3")

    def _resolve_local_model_path(self, model_id: str) -> str:
        prefetched_model_dir = self._resolve_prefetched_model_dir(model_id)
        if prefetched_model_dir.exists():
            return str(prefetched_model_dir)

        hub_root = self._resolve_hf_hub_root()
        repo_dir = hub_root / f"models--{model_id.replace('/', '--')}"
        snapshots_dir = repo_dir / "snapshots"
        if snapshots_dir.exists():
            candidates = sorted((path for path in snapshots_dir.iterdir() if path.is_dir()), key=lambda path: path.name, reverse=True)
            if candidates:
                return str(candidates[0])
        return model_id

    def _resolve_prefetched_model_dir(self, model_id: str) -> Path:
        hf_home = os.environ.get("HF_HOME")
        if not hf_home:
            return Path.home() / ".cache" / "huggingface" / "models" / model_id.replace("/", "--")
        return Path(hf_home).expanduser() / "models" / model_id.replace("/", "--")

    def _resolve_hf_hub_root(self) -> Path:
        explicit_hub_cache = os.environ.get("HF_HUB_CACHE")
        if explicit_hub_cache:
            return Path(explicit_hub_cache).expanduser()
        hf_home = os.environ.get("HF_HOME")
        if hf_home:
            return Path(hf_home).expanduser() / "hub"
        return Path.home() / ".cache" / "huggingface" / "hub"

    def _ensure_etl_site_packages(self) -> None:
        if all(importlib.util.find_spec(module_name) is not None for module_name in ("huggingface_hub", "transformers", "sentence_transformers", "torch")):
            return

        candidates = [
            self.settings.repo_root / "etl" / ".venv",
            self.settings.repo_root / "etl" / ".venv-seed-backfill",
        ]
        version = f"python{sys.version_info.major}.{sys.version_info.minor}"

        resolved_site_packages: list[Path] = []
        for root in candidates:
            preferred = root / "lib" / version / "site-packages"
            if preferred.exists():
                resolved_site_packages.append(preferred)
                continue

            fallback_matches = sorted((root / "lib").glob("python*/site-packages"))
            resolved_site_packages.extend(path for path in fallback_matches if path.exists())

        for site_packages in resolved_site_packages:
            site_packages_str = str(site_packages)
            if site_packages_str not in sys.path:
                sys.path.insert(0, site_packages_str)

    def _resolve_device(self) -> str:
        self._ensure_etl_site_packages()
        try:
            import torch
        except Exception:
            return "cpu"

        try:
            if getattr(torch.backends, "mps", None) is not None and torch.backends.mps.is_available():
                return "mps"
        except Exception:
            pass
        try:
            if torch.cuda.is_available():
                return "cuda"
        except Exception:
            pass
        return "cpu"

    def _normalize_query_text(self, query_text: str) -> str:
        return " ".join(str(query_text or "").split()).strip()

    def _normalize_vector_space(self, vector_space: str | None) -> str:
        normalized = str(vector_space or "abstract").strip().lower()
        if normalized in {"claims", "vector_claims", "claim"}:
            return "claims"
        return "abstract"


@lru_cache(maxsize=1)
def get_semantic_query_encoder() -> SemanticQueryEncoder:
    return SemanticQueryEncoder()
