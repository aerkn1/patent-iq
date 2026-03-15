from __future__ import annotations

from patentiq_etl.common.io import stable_hash_embedding


def test_stable_hash_embedding_dimension() -> None:
    vector = stable_hash_embedding("A motor capable of rotating an axle", dims=16)
    assert len(vector) == 16
    assert round(sum(vector), 6) == 1.0
