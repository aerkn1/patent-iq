from __future__ import annotations

from math import sqrt
from pathlib import Path
from typing import Any

import duckdb

from config.settings import get_settings
from infrastructure.artifacts import ArtifactLocator
from infrastructure.duckdb import DuckDbProvider
from infrastructure.repositories.publication_repository import PublicationRepository


class SemanticRepository:
    def __init__(self) -> None:
        settings = get_settings()
        self.settings = settings
        self.vector_abstract_path = settings.etl_data_root / "vectors" / "vec_family_embeddings_abstracts.parquet"
        self.vector_claims_path = settings.etl_data_root / "vectors" / "vec_family_embeddings_claims.parquet"
        self.artifact_locator = ArtifactLocator(settings=settings)
        self.duckdb_provider = DuckDbProvider()
        self.publication_repository = PublicationRepository()

    def artifacts(self) -> list[Path]:
        semantic_serving_path = self.artifact_locator.resolve_semantic_serving_duckdb()
        artifacts = [self.vector_abstract_path, self.vector_claims_path]
        if semantic_serving_path is not None:
            return [semantic_serving_path, *artifacts]
        return artifacts

    def get_space_summary(self, vector_space: str) -> dict[str, object]:
        normalized_space = self._normalize_vector_space(vector_space)
        vector_path = self._vector_path(normalized_space)
        semantic_serving_path = self.artifact_locator.resolve_semantic_serving_duckdb()

        with self.duckdb_provider.connect() as con:
            vector_row = self._query_single_row(
                con,
                f"""
                select
                    count(*) as searchable_family_count,
                    sum(case when is_abstract_fallback then 1 else 0 end) as abstract_fallback_count,
                    sum(case when coalesce(is_abstract_fallback, false) = false then 1 else 0 end) as claim_backed_count
                from read_parquet('{vector_path}')
                """,
                [],
            )
            total_context_family_count = None
            if semantic_serving_path is not None and semantic_serving_path.exists():
                self._attach_semantic_serving(con, semantic_serving_path)
                if self._semantic_table_exists(con, "semantic_match_context"):
                    row = con.execute("select count(*) from semantic_db.semantic_match_context").fetchone()
                    if row is not None:
                        total_context_family_count = int(row[0])

        searchable_count = self._to_int(vector_row.get("searchable_family_count"))
        fallback_count = self._to_int(vector_row.get("abstract_fallback_count"))
        claim_backed_count = self._to_int(vector_row.get("claim_backed_count"))
        coverage_pct = None
        if searchable_count is not None and total_context_family_count:
            coverage_pct = searchable_count / total_context_family_count
        return {
            "vector_space": normalized_space,
            "searchable_family_count": searchable_count,
            "total_context_family_count": total_context_family_count,
            "vector_coverage_pct": coverage_pct,
            "abstract_fallback_count": fallback_count,
            "claim_backed_count": claim_backed_count,
        }

    def get_family_vector_support(self, family_id: str | int) -> dict[str, bool]:
        normalized_family_id = self._normalize_family_id(family_id)
        if normalized_family_id is None:
            return {"abstract": False, "claims": False}

        with self.duckdb_provider.connect() as con:
            abstract_exists = con.execute(
                f"select 1 from read_parquet('{self.vector_abstract_path}') where docdb_family_id = ? limit 1",
                [normalized_family_id],
            ).fetchone() is not None
            claims_exists = con.execute(
                f"select 1 from read_parquet('{self.vector_claims_path}') where docdb_family_id = ? limit 1",
                [normalized_family_id],
            ).fetchone() is not None
        return {"abstract": abstract_exists, "claims": claims_exists}

    def get_anchor_row(self, family_id: str | int, vector_space: str) -> dict[str, object]:
        normalized_family_id = self._normalize_family_id(family_id)
        if normalized_family_id is None:
            return {}

        with self.duckdb_provider.connect() as con:
            return self._query_single_row(
                con,
                f"""
                select
                    docdb_family_id,
                    representative_appln_id,
                    vector_space,
                    representative_stage,
                    queryable_text,
                    token_count,
                    text_provenance,
                    text_source_type,
                    is_abstract_fallback,
                    family_earliest_priority_date,
                    primary_wipo_field,
                    owner_name_harmonized,
                    family_ui_blocking_power_score,
                    oecd_quality_percentile,
                    family_composite_status,
                    embedding
                from read_parquet('{self._vector_path(vector_space)}')
                where docdb_family_id = ?
                limit 1
                """,
                [normalized_family_id],
            )

    def get_family_anchor_suggestions(
        self,
        query: str,
        vector_space: str,
        *,
        limit: int = 8,
    ) -> list[dict[str, object]]:
        normalized_query = str(query).strip()
        if len(normalized_query) < 1:
            return []

        safe_limit = max(1, min(int(limit), 20))
        upper_query = normalized_query.upper()
        id_prefix = f"{normalized_query}%"
        text_like = f"%{upper_query}%"
        vector_path = self._vector_path(vector_space)

        with self.duckdb_provider.connect() as con:
            return self._query_rows(
                con,
                f"""
                select
                    cast(docdb_family_id as varchar) as family_id,
                    cast(docdb_family_id as varchar) as label,
                    owner_name_harmonized,
                    primary_wipo_field,
                    family_composite_status
                from read_parquet('{vector_path}')
                where cast(docdb_family_id as varchar) like ?
                   or upper(coalesce(owner_name_harmonized, '')) like ?
                   or upper(coalesce(primary_wipo_field, '')) like ?
                order by
                    case
                        when cast(docdb_family_id as varchar) = ? then 0
                        when cast(docdb_family_id as varchar) like ? then 1
                        when upper(coalesce(owner_name_harmonized, '')) like ? then 2
                        else 3
                    end,
                    cast(docdb_family_id as varchar) asc
                limit ?
                """,
                [
                    id_prefix,
                    text_like,
                    text_like,
                    normalized_query,
                    id_prefix,
                    text_like,
                    safe_limit,
                ],
            )

    def get_anchor_search_results(
        self,
        family_id: str | int,
        vector_space: str,
        *,
        limit: int = 12,
        offset: int = 0,
        same_field_only: bool = False,
        exclude_same_owner: bool = False,
    ) -> tuple[list[dict[str, object]], int]:
        anchor = self.get_anchor_row(family_id, vector_space)
        anchor_embedding = anchor.get("embedding")
        if not isinstance(anchor_embedding, list):
            return [], 0

        normalized_family_id = self._normalize_family_id(family_id)
        if normalized_family_id is None:
            return [], 0

        filters = ["docdb_family_id <> ?"]
        count_parameters: list[object] = [normalized_family_id]
        if same_field_only and anchor.get("primary_wipo_field"):
            filters.append("primary_wipo_field = ?")
            count_parameters.append(anchor["primary_wipo_field"])
        if exclude_same_owner and anchor.get("owner_name_harmonized"):
            filters.append("coalesce(owner_name_harmonized, '') <> ?")
            count_parameters.append(anchor["owner_name_harmonized"])

        where_clause = " and ".join(filters)
        vector_path = self._vector_path(vector_space)

        return self._search_results_for_embedding(
            anchor_embedding,
            vector_space,
            limit=limit,
            offset=offset,
            where_clause=where_clause,
            where_parameters=count_parameters,
        )

    def get_text_query_search_results(
        self,
        query_embedding: list[float],
        vector_space: str,
        *,
        limit: int = 12,
        offset: int = 0,
    ) -> tuple[list[dict[str, object]], int]:
        if not query_embedding:
            return [], 0
        return self._search_results_for_embedding(
            query_embedding,
            vector_space,
            limit=limit,
            offset=offset,
            where_clause="true",
            where_parameters=[],
        )

    def get_family_compare_context(self, family_id: str | int) -> dict[str, object]:
        normalized_family_id = self._normalize_family_id(family_id)
        if normalized_family_id is None:
            return {}
        support = self.get_family_vector_support(normalized_family_id)
        preferred_space = "claims" if support["claims"] else "abstract"
        if not support["claims"] and not support["abstract"]:
            return {}
        row = self.get_anchor_row(normalized_family_id, preferred_space)
        return {
            "docdb_family_id": row.get("docdb_family_id"),
            "label": str(normalized_family_id),
            "owner_name_harmonized": row.get("owner_name_harmonized"),
            "primary_wipo_field": row.get("primary_wipo_field"),
            "family_composite_status": row.get("family_composite_status"),
            "family_ui_blocking_power_score": row.get("family_ui_blocking_power_score"),
            "oecd_quality_percentile": row.get("oecd_quality_percentile"),
            "representative_stage": row.get("representative_stage"),
            "text_provenance": row.get("text_provenance"),
            "family_earliest_priority_date": row.get("family_earliest_priority_date"),
            "abstract_supported": support["abstract"],
            "claims_supported": support["claims"],
            "text_excerpt": self._excerpt(row.get("queryable_text")),
        }

    def get_pair_similarity(self, left_family_id: str | int, right_family_id: str | int, vector_space: str) -> float | None:
        left = self.get_anchor_row(left_family_id, vector_space)
        right = self.get_anchor_row(right_family_id, vector_space)
        left_embedding = left.get("embedding")
        right_embedding = right.get("embedding")
        if not isinstance(left_embedding, list) or not isinstance(right_embedding, list):
            return None
        return self._cosine_similarity(left_embedding, right_embedding)

    def _cosine_similarity(self, left_embedding: list[float], right_embedding: list[float]) -> float | None:
        if len(left_embedding) != len(right_embedding) or not left_embedding:
            return None
        left_norm = sqrt(sum(float(value) * float(value) for value in left_embedding))
        right_norm = sqrt(sum(float(value) * float(value) for value in right_embedding))
        if left_norm == 0 or right_norm == 0:
            return None
        numerator = sum(float(left_value) * float(right_value) for left_value, right_value in zip(left_embedding, right_embedding, strict=False))
        return numerator / (left_norm * right_norm)

    def _normalize_family_id(self, family_id: str | int | None) -> int | None:
        if family_id is None:
            return None
        try:
            return int(str(family_id).strip())
        except (TypeError, ValueError):
            return None

    def _normalize_vector_space(self, vector_space: str | None) -> str:
        normalized = str(vector_space or "abstract").strip().lower()
        if normalized in {"claims", "vector_claims", "claim"}:
            return "claims"
        return "abstract"

    def _search_results_for_embedding(
        self,
        query_embedding: list[float],
        vector_space: str,
        *,
        limit: int,
        offset: int,
        where_clause: str,
        where_parameters: list[object],
    ) -> tuple[list[dict[str, object]], int]:
        vector_path = self._vector_path(vector_space)

        with self.duckdb_provider.connect() as con:
            total_row = con.execute(
                f"select count(*) from read_parquet('{vector_path}') where {where_clause}",
                where_parameters,
            ).fetchone()
            total_count = int(total_row[0]) if total_row is not None else 0

            cursor = con.execute(
                f"""
                select
                    docdb_family_id,
                    representative_appln_id,
                    primary_wipo_field,
                    owner_name_harmonized,
                    family_ui_blocking_power_score,
                    oecd_quality_percentile,
                    family_composite_status,
                    representative_stage,
                    text_provenance,
                    text_source_type,
                    is_abstract_fallback,
                    family_earliest_priority_date,
                    substr(queryable_text, 1, 480) as text_excerpt,
                    list_cosine_similarity(embedding, ?) as semantic_similarity
                from read_parquet('{vector_path}')
                where {where_clause}
                order by semantic_similarity desc, docdb_family_id asc
                limit ?
                offset ?
                """,
                [query_embedding, *where_parameters, limit, offset],
            )
            columns = [column[0] for column in cursor.description]
            rows = [self._to_dict(columns, row) for row in cursor.fetchall()]
        return self._attach_family_titles(rows), total_count

    def _vector_path(self, vector_space: str) -> Path:
        normalized_space = self._normalize_vector_space(vector_space)
        return self.vector_claims_path if normalized_space == "claims" else self.vector_abstract_path

    def _attach_semantic_serving(self, con: duckdb.DuckDBPyConnection, semantic_serving_path: Path) -> None:
        attached = con.execute("pragma database_list").fetchall()
        if any(str(row[1]) == "semantic_db" for row in attached):
            return
        con.execute(f"ATTACH '{semantic_serving_path}' AS semantic_db (READ_ONLY)")

    def _semantic_table_exists(self, con: duckdb.DuckDBPyConnection, table_name: str) -> bool:
        row = con.execute(
            """
            select 1
            from information_schema.tables
            where table_catalog = 'semantic_db'
              and table_schema = 'main'
              and table_name = ?
            limit 1
            """,
            [table_name],
        ).fetchone()
        return row is not None

    def _query_single_row(
        self,
        con: duckdb.DuckDBPyConnection,
        query: str,
        parameters: list[object] | tuple[object, ...],
    ) -> dict[str, object]:
        cursor = con.execute(query, parameters)
        row = cursor.fetchone()
        if row is None:
            return {}
        columns = [col[0] for col in cursor.description]
        return self._to_dict(columns, row)

    def _query_rows(
        self,
        con: duckdb.DuckDBPyConnection,
        query: str,
        parameters: list[object] | tuple[object, ...],
    ) -> list[dict[str, object]]:
        cursor = con.execute(query, parameters)
        columns = [col[0] for col in cursor.description]
        return [self._to_dict(columns, row) for row in cursor.fetchall()]

    def _to_dict(self, columns: list[str], row: Any) -> dict[str, object]:
        if row is None:
            return {}
        return dict(zip(columns, row, strict=False))

    def _to_int(self, value: object | None) -> int | None:
        try:
            if value is None:
                return None
            return int(value)
        except (TypeError, ValueError):
            return None

    def _to_text(self, value: object | None) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    def _attach_family_titles(self, rows: list[dict[str, object]]) -> list[dict[str, object]]:
        for row in rows:
            appln_id = self._to_int(row.get("representative_appln_id"))
            if appln_id is None:
                row["family_title"] = None
                continue
            title_row = self.publication_repository.get_title_for_application(appln_id)
            row["family_title"] = self._to_text(title_row.get("title_text")) if title_row else None
        return rows

    def _excerpt(self, value: object | None, limit: int = 480) -> str | None:
        if not isinstance(value, str):
            return None
        trimmed = " ".join(value.split())
        if not trimmed:
            return None
        if len(trimmed) <= limit:
            return trimmed
        return f"{trimmed[:limit].rstrip()}…"
