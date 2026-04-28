from infrastructure.semantic_query_encoder import SemanticQueryEncoder


def test_resolve_local_model_path_prefers_prefetched_model_dir(monkeypatch, tmp_path):
    hf_home = tmp_path / "hf-home"
    model_dir = hf_home / "models" / "BAAI--bge-m3"
    model_dir.mkdir(parents=True)

    monkeypatch.delenv("HF_HUB_CACHE", raising=False)
    monkeypatch.setenv("HF_HOME", str(hf_home))

    encoder = SemanticQueryEncoder()

    assert encoder._resolve_local_model_path("BAAI/bge-m3") == str(model_dir)


def test_resolve_local_model_path_prefers_hf_hub_cache_env(monkeypatch, tmp_path):
    hub_root = tmp_path / "custom-hub"
    snapshot_dir = hub_root / "models--BAAI--bge-m3" / "snapshots" / "20260426"
    snapshot_dir.mkdir(parents=True)

    monkeypatch.setenv("HF_HUB_CACHE", str(hub_root))
    monkeypatch.delenv("HF_HOME", raising=False)

    encoder = SemanticQueryEncoder()

    assert encoder._resolve_local_model_path("BAAI/bge-m3") == str(snapshot_dir)


def test_resolve_local_model_path_falls_back_to_hf_home(monkeypatch, tmp_path):
    hf_home = tmp_path / "hf-home"
    snapshot_dir = hf_home / "hub" / "models--AI-Growth-Lab--PatentSBERTa" / "snapshots" / "20260426"
    snapshot_dir.mkdir(parents=True)

    monkeypatch.delenv("HF_HUB_CACHE", raising=False)
    monkeypatch.setenv("HF_HOME", str(hf_home))

    encoder = SemanticQueryEncoder()

    assert encoder._resolve_local_model_path("AI-Growth-Lab/PatentSBERTa") == str(snapshot_dir)
