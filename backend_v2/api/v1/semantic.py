from fastapi import APIRouter

from application.services.semantic import SemanticService
from domain.schemas.semantic import SemanticCompareResponse, SemanticFamilySuggestionResponse, SemanticSearchResponse

router = APIRouter(prefix="/semantic", tags=["semantic"])
service = SemanticService()


@router.get("/families/search", response_model=SemanticSearchResponse)
def get_family_anchor_search(
    family_id: str,
    vector_space: str = "abstract",
    limit: int = 12,
    offset: int = 0,
    same_field_only: bool = False,
    exclude_same_owner: bool = False,
    selected_family_id: str | None = None,
) -> SemanticSearchResponse:
    return service.get_family_anchor_search(
        family_id=family_id,
        vector_space=vector_space,
        limit=limit,
        offset=offset,
        same_field_only=same_field_only,
        exclude_same_owner=exclude_same_owner,
        selected_family_id=selected_family_id,
    )


@router.get("/text/search", response_model=SemanticSearchResponse)
def get_text_discovery_search(
    q: str,
    vector_space: str = "abstract",
    limit: int = 12,
    offset: int = 0,
) -> SemanticSearchResponse:
    return service.get_text_discovery_search(
        query_text=q,
        vector_space=vector_space,
        limit=limit,
        offset=offset,
    )


@router.get("/families/suggestions", response_model=SemanticFamilySuggestionResponse)
def get_family_anchor_suggestions(
    q: str,
    vector_space: str = "abstract",
    limit: int = 8,
) -> SemanticFamilySuggestionResponse:
    return service.get_family_anchor_suggestions(
        query=q,
        vector_space=vector_space,
        limit=limit,
    )


@router.get("/families/compare", response_model=SemanticCompareResponse)
def get_family_semantic_compare(left_family_id: str, right_family_id: str) -> SemanticCompareResponse:
    return service.get_family_semantic_compare(left_family_id=left_family_id, right_family_id=right_family_id)
