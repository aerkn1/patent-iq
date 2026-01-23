from infrastructure.repositories.portfolio_patent_repo import PortfolioPatentRepository

class PortfolioPatentsService:
    def __init__(self):
        self.patent_repo = PortfolioPatentRepository()

    def get_patents(
        self,
        owner_id: int,
        filters: dict,
        sort: str,
        order: str,
        limit: int,
        offset: int,
    ) -> dict:
        rows, total = self.patent_repo.fetch_patents(
            owner_id=owner_id,
            filters=filters,
            sort=sort,
            order=order,
            limit=limit,
            offset=offset,
        )

        return {
            "portfolio": {"owner_id": owner_id},
            "pagination": {
                "total": total,
                "limit": limit,
                "offset": offset,
            },
            "patents": rows,
            "metadata": {
                "contract_version": "v1",
                "data_snapshot": "2025-01-31",
            },
        }