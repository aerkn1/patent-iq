from domain.errors import NotFoundError
from infrastructure.repositories.portfolio_citations_repo import PortfolioCitationsRepository
from domain.schemas.portfolio_citation import PortfolioCitationMetricsResponse, PortfolioCitationTimeSeriesResponse

class PortfolioCitationService:
    def __init__(self):
        self.repo = PortfolioCitationsRepository()

    def get_citation_metrics(self, owner_id: int) -> dict:
        data = self.repo.get_citation_metrics(owner_id)
        if not data:
            raise NotFoundError(f"Citation metrics not found for portfolio {owner_id}")
        
        # Transform flat structure to nested structure required by schema
        return {
            "owner_id": data["owner_id"],
            "portfolio_size": {
                "n_patents_effective": data["n_patents_effective"]
            },
            "citation_volume": {
                "early_cites_total": data["early_cites_total"],
                "mid_cites_total": data["mid_cites_total"],
                "late_cites_total": data["late_cites_total"],
                "early_cites_per_patent": data["early_cites_per_patent"],
                "mid_cites_per_patent": data["mid_cites_per_patent"],
                "late_cites_per_patent": data["late_cites_per_patent"],
                "cites_per_patent": data["cites_per_patent"]
            },
            "citation_quality_raw": {
                "trajectory_score_avg": data["trajectory_score_avg"],
                "durability_score_avg": data["durability_score_avg"],
                "sustainability_score_avg": data["sustainability_score_ui_avg"],  # Map from db column
                "timing_score_avg": data["timing_score_avg"]
            },
            "citation_quality_percentile": {
                "trajectory_score_pct": data["trajectory_score_pct"],
                "durability_score_pct": data["durability_score_pct"],
                "sustainability_score_pct": data["sustainability_score_pct"],
                "timing_score_pct": data["timing_score_pct"]
            },
            "portfolio_behavior": {
                "timing_class_mode": data["timing_class_mode"],
                "early_signal_share": data["early_signal_share"],
                "sustaining_share": data["sustaining_share"]
            }
        }

    def get_citation_timeseries(self, owner_id: int) -> dict:
        series = self.repo.get_citation_timeseries(owner_id)
        
        import math
        cleaned_series = []
        for row in series:
            cleaned_row = {}
            for k, v in row.items():
                if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                    cleaned_row[k] = 0.0
                else:
                    cleaned_row[k] = v
            cleaned_series.append(cleaned_row)

        return {
            "owner_id": owner_id,
            "series": cleaned_series
        }
