from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from infrastructure.duckdb.connection import DuckDBConnection


CACHE_TABLE = "llm_advisory_cache"


@dataclass(frozen=True)
class AdvisoryCacheEntry:
    cache_key: str
    analysis_type: str
    entity_id: int
    snapshot_date: str
    parquet_version_hash: str
    model: str
    payload: dict[str, Any]
    created_at: datetime
    expires_at: datetime


class AdvisoryCacheRepository:
    def __init__(self) -> None:
        self.conn = DuckDBConnection.get_connection()
        self._ensure_table()

    def _ensure_table(self) -> None:
        self.conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {CACHE_TABLE} (
                cache_key VARCHAR PRIMARY KEY,
                analysis_type VARCHAR NOT NULL,
                entity_id BIGINT NOT NULL,
                snapshot_date VARCHAR NOT NULL,
                parquet_version_hash VARCHAR NOT NULL,
                model VARCHAR NOT NULL,
                payload_json VARCHAR NOT NULL,
                created_at TIMESTAMP NOT NULL,
                expires_at TIMESTAMP NOT NULL
            )
            """
        )

        # Helpful index for cleanup queries
        self.conn.execute(
            f"CREATE INDEX IF NOT EXISTS idx_{CACHE_TABLE}_expires_at ON {CACHE_TABLE}(expires_at)"
        )

    def get(self, *, cache_key: str) -> Optional[AdvisoryCacheEntry]:
        q = f"""
        SELECT
            cache_key,
            analysis_type,
            entity_id,
            snapshot_date,
            parquet_version_hash,
            model,
            payload_json,
            created_at,
            expires_at
        FROM {CACHE_TABLE}
        WHERE cache_key = ?
          AND expires_at > CURRENT_TIMESTAMP
        LIMIT 1
        """
        df = self.conn.execute(q, [cache_key]).fetchdf()
        if df.empty:
            return None

        r = df.iloc[0]
        payload = json.loads(r["payload_json"])

        created_at = _ensure_datetime(r["created_at"])
        expires_at = _ensure_datetime(r["expires_at"])

        return AdvisoryCacheEntry(
            cache_key=str(r["cache_key"]),
            analysis_type=str(r["analysis_type"]),
            entity_id=int(r["entity_id"]),
            snapshot_date=str(r["snapshot_date"]),
            parquet_version_hash=str(r["parquet_version_hash"]),
            model=str(r["model"]),
            payload=payload,
            created_at=created_at,
            expires_at=expires_at,
        )

    def set(
        self,
        *,
        cache_key: str,
        analysis_type: str,
        entity_id: int,
        snapshot_date: str,
        parquet_version_hash: str,
        model: str,
        payload: dict[str, Any],
        ttl_days: int = 30,
    ) -> None:
        created_at = datetime.now(timezone.utc)
        expires_at = created_at + timedelta(days=ttl_days)

        q = f"""
        INSERT OR REPLACE INTO {CACHE_TABLE} (
            cache_key,
            analysis_type,
            entity_id,
            snapshot_date,
            parquet_version_hash,
            model,
            payload_json,
            created_at,
            expires_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.conn.execute(
            q,
            [
                cache_key,
                analysis_type,
                int(entity_id),
                snapshot_date,
                parquet_version_hash,
                model,
                json.dumps(payload, separators=(",", ":")),
                created_at.isoformat(),
                expires_at.isoformat(),
            ],
        )

    def delete_expired(self, *, limit: int = 5000) -> int:
        q = f"""
        DELETE FROM {CACHE_TABLE}
        WHERE cache_key IN (
            SELECT cache_key
            FROM {CACHE_TABLE}
            WHERE expires_at <= CURRENT_TIMESTAMP
            LIMIT ?
        )
        """
        self.conn.execute(q, [int(limit)])
        # DuckDB python API doesn't reliably expose affected rows; return 0 for now.
        return 0


def _ensure_datetime(v: Any) -> datetime:
    # DuckDB/pandas may return Timestamp-like objects.
    if isinstance(v, datetime):
        return v if v.tzinfo else v.replace(tzinfo=timezone.utc)
    try:
        # pandas Timestamp
        return v.to_pydatetime().replace(tzinfo=timezone.utc)
    except Exception:
        return datetime.now(timezone.utc)
