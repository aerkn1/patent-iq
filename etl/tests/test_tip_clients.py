from __future__ import annotations

import pandas as pd

from patentiq_etl.prebronze.tip_clients import query_to_dataframe


class _FakeOrmRow:
    def __init__(self, appln_id: int, publn_auth: str) -> None:
        self.appln_id = appln_id
        self.publn_auth = publn_auth


class _FakeClient:
    def __init__(self, frame: pd.DataFrame) -> None:
        self._frame = frame

    def df(self, query):
        return self._frame.copy()


def test_query_to_dataframe_flattens_single_orm_object_column() -> None:
    frame = pd.DataFrame({"TLS201_APPLN": [_FakeOrmRow(1, "EP"), _FakeOrmRow(2, "US")]})

    result = query_to_dataframe(_FakeClient(frame), query=object())

    assert list(result.columns) == ["appln_id", "publn_auth"]
    assert result.to_dict(orient="records") == [
        {"appln_id": 1, "publn_auth": "EP"},
        {"appln_id": 2, "publn_auth": "US"},
    ]


def test_query_to_dataframe_keeps_normal_tabular_frames_unchanged() -> None:
    frame = pd.DataFrame({"appln_id": [1], "publn_auth": ["EP"]})

    result = query_to_dataframe(_FakeClient(frame), query=object())

    assert result.equals(frame)
