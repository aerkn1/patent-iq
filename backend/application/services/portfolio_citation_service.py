from domain.errors import NotFoundError, ValidationError
from infrastructure.repositories.portfolio_citations_repo import PortfolioCitationsRepository
from domain.schemas.portfolio_citation import PortfolioCitationMetricsResponse, PortfolioCitationTimeSeriesResponse
from application.services.portfolio_forecast_service import PortfolioForecastService
import logging

logger = logging.getLogger(__name__)

class PortfolioCitationService:
    def __init__(self):
        self.repo = PortfolioCitationsRepository()
        self.forecast_service = PortfolioForecastService()

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

    async def get_citation_forecast_ts(self, owner_id: int, horizon: str) -> dict:
        if owner_id <= 0:
            raise ValidationError("owner_id must be positive")

        # 1. Get historical cumulative timeseries from repo
        hist_series = self.repo.get_cumulative_timeseries(owner_id)
        
        if not hist_series:
            # If no history, we can't project properly or return empty
            raise NotFoundError(f"No citation history found for portfolio {owner_id}")

        last_observed = hist_series[-1]
        last_year = int(last_observed["year"])
        last_cum = float(last_observed["cum_cites"])

        # 2. Get ML forecast (portfolio level)
        # We don't need segmentation here, just total numbers
        try:
            forecast_raw = await self.forecast_service.get_forecast(
                owner_id, 
                horizon, 
                segments=False
            )
            pred = forecast_raw["portfolio_prediction"]
            expected_add = pred["expected_citations_total"]
            low_add = pred["interval_80_total"]["low"]
            high_add = pred["interval_80_total"]["high"]
        except Exception as e:
            logger.warning(f"Portfolio forecast failed for {owner_id}: {e}")
            expected_add = 0.0
            low_add = 0.0
            high_add = 0.0
            pred = {
                "expected_citations_total": 0.0,
                "interval_80_total": {"low": 0.0, "high": 0.0},
                "n_patents_effective": 0.0,
                "expected_per_effective_patent": 0.0
            }

        # 3. Project forecast linearly
        horizon_years = 3 if horizon == "3y" else 5
        forecast_series = []

        # Continuity point
        forecast_series.append({
            "year": last_year,
            "cum_cites": last_cum,
            "low": last_cum,
            "high": last_cum
        })

        for i in range(1, horizon_years + 1):
            fraction = i / horizon_years
            
            proj_expected = last_cum + (expected_add * fraction)
            proj_low = last_cum + (low_add * fraction)
            proj_high = last_cum + (high_add * fraction)
            
            forecast_series.append({
                "year": last_year + i,
                "cum_cites": round(proj_expected, 1),
                "low": round(proj_low, 1),
                "high": round(proj_high, 1)
            })

        return {
            "owner_id": owner_id,
            "horizon": horizon,
            "last_observed_year": last_year,
            "historical": hist_series,
            "forecast": forecast_series,
            "prediction_summary": {
                "expected_additional": round(expected_add, 1),
                "interval_80": {
                    "low": round(low_add, 1),
                    "high": round(high_add, 1)
                },
                "difficulty_bucket": "N/A" # Portfolio doesn't have single difficulty
            }
        }
