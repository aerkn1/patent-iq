import logging
from typing import Optional, Union

from domain.errors import ValidationError, NotFoundError, InternalServerError
from infrastructure.repositories import (
    PatentCoreRepository,
    PatentRanksRepository,
    PatentClassificationRepository,
    PatentCitationsRepository,
    OwnerRepository,
    PatentCpcFrequencyRepository,
    PatentIndustryFrequencyRepository,
    PatentDiversificationRepository,
    PatentFamilyRepository
)
from application.services.patent_forecast_service import PatentForecastService

logger = logging.getLogger(__name__)


class PatentPageService:

    def __init__(self):
        self.core_repo = PatentCoreRepository()
        self.ranks_repo = PatentRanksRepository()
        self.class_repo = PatentClassificationRepository()
        self.citations_repo = PatentCitationsRepository()
        self.owner_repo = OwnerRepository()
        self.cpc_repo = PatentCpcFrequencyRepository()
        self.ind_repo = PatentIndustryFrequencyRepository()
        self.div_repo = PatentDiversificationRepository()
        self.family_repo = PatentFamilyRepository()
        self.forecast_service = PatentForecastService()


    async def get_patent_page(self, appln_id: int) -> dict:
        if appln_id <= 0:
            raise ValidationError("appln_id must be positive")

        core = self.core_repo.get_core(appln_id)
        if core is None:
            raise NotFoundError(f"Patent {appln_id} not found")

        scores = self.scores_repo.get_scores(appln_id)
        classification = self.class_repo.get_classification(appln_id)
        citations = self.citations_repo.get_citations(appln_id)
        owners = self.owner_repo.get_owners(appln_id)

        return {
            "patent": {
                **core,
                "owners": owners,
            },
            "scores": scores["scores"],
            "technology": scores["technology"],
            "market": scores["market"],
            "citations": citations,
            "legal": scores["legal"],
            "classification": classification,
            "similarity": {
                "similar_patents_available": True,
                "similarity_vector_id": f"pat_{appln_id}",
            },
            "metadata": {
                "contract_version": "v1",
                "data_snapshot": "2025-01-31",
                "confidence": "HIGH",
            },
        }

    async def get_overview(self, appln_id: int) -> dict[str, any]:
        if appln_id <= 0:
            raise ValidationError("appln_id must be positive")

        core = self.core_repo.get_core(appln_id)
        if core is None:
            raise NotFoundError(f"Patent {appln_id} not found")

        ranks = self.ranks_repo.get_ranks_row(appln_id)
        if ranks is None:
            raise NotFoundError(f"Patent ranks not found for {appln_id}")

        owners = self.owner_repo.get_owners(appln_id)
        citations = self.citations_repo.get_citations(appln_id)
        family_data = self.family_repo.get_family_data(appln_id)

        # Locked v1 contract
        return {
            "patent": {
                "appln_id": int(core["appln_id"]),
                "title": core["appln_title"],
                "application_date": str(core["filing_date"]) if core["filing_date"] else None,
                "publication_date": str(core["publn_date"]) if core["publn_date"] else None,
                "grant_date": str(core["grant_date"]) if core["grant_date"] else None,
                "patent_age_years": int(core["patent_age_years"]) if core["patent_age_years"] is not None else None,
                "jurisdiction": core["publn_auth"],
                "family_id": int(core["docdb_family_id"]) if core["docdb_family_id"] is not None else None,
                "status": core["status"],
                "owners": owners,
                "patent_category": core["patent_category"]
            },
            "family": {
                "family_members_count": family_data.get("family_members_count") if family_data else None,
                "family_jurisdiction_count": family_data.get("family_jurisdiction_count") if family_data else None,
                "major_office_grant_auths": family_data.get("major_office_grant_auths") if family_data else None,
                "family_cpc_subclass_count": family_data.get("family_cpc_subclass_count") if family_data else None,
            },

            "scores": {
                "blocking_power": {
                    "raw": self.round3(ranks["blocking_power_index"]),
                    "percentile": self.round3(ranks["blocking_power_pct"]),
                    "tier": ranks["blocking_power_tier"],  # already computed in parquet
                },
                "licensing_readiness": {
                    "raw": self.round3(ranks["licensing_readiness_score"]),
                    "percentile": self.round3(ranks["licensing_readiness_pct"]),
                    "tier": ranks["licensing_readiness_tier"],  # already computed in parquet
                },
                "legal_strength": {
                    "raw": self.round3(ranks.get("legal_strength_score", None) or None),  # optional if you have it
                    "percentile": self.round3(ranks["legal_strength_score_pct_global"]),
                },
            },

            "technology": {
                "axis_score": self.round3(ranks["tech_axis_score"]),
                "percentile_global": self.round3(ranks["tech_axis_score_pct_global"]),
                "tier": self.tier_from_percentile(float(ranks["tech_axis_score_pct_global"])),
            },

            "market": {
                "axis_score": self.round3(ranks["market_axis_score"]),
                "percentile_global": self.round3(ranks["market_axis_score_pct_global"]),
                "tier": self.tier_from_percentile(float(ranks["market_axis_score_pct_global"])),
            },

            "citations": citations,

            "relative_positioning": {
                "blocking_power": {
                    "percentile_global": self.round3(ranks["blocking_power_index_pct_global"]),
                    "tier": self.tier_from_percentile(float(ranks["blocking_power_index_pct_global"])),
                },
                "licensing_readiness": {
                    "percentile_global": self.round3(ranks["licensing_readiness_pct"]),
                    "tier": self.tier_from_percentile(float(ranks["licensing_readiness_pct"])),
                },
            },

            "radar": {
                "axes": [
                    {
                        "key": "technology",
                        "label": "Technology Strength",
                        "value": self.pct(ranks["tech_axis_score_pct_global"]),
                    },
                    {
                        "key": "market",
                        "label": "Market Reach",
                        "value": self.pct(ranks["market_axis_score_pct_global"]),
                    },
                    {
                        "key": "blocking",
                        "label": "Blocking Power",
                        "value": self.pct(ranks["blocking_power_pct"]),
                    },
                    {
                        "key": "licensing",
                        "label": "Licensing Readiness",
                        "value": self.pct(ranks["licensing_readiness_pct"]),
                    },
                    {
                        "key": "legal",
                        "label": "Legal Strength",
                        "value": self.pct(ranks["legal_strength_score_pct_global"]),
                    },
                ]
            },

            "similarity": {
                "similar_patents_available": True,
                "similarity_vector_id": f"pat_{appln_id}",
            },

            "metadata": {
                "contract_version": "v1",
                "data_snapshot": "2025-01-31",
                "confidence": "HIGH",
            },
        }

    async def get_patent_analysis(self, appln_id: int) -> dict:
        if appln_id is None or appln_id <= 0:
            raise ValidationError("appln_id must be a positive integer")

        try:
            if not self.core_repo.exists(appln_id):
                raise NotFoundError(f"Patent {appln_id} not found")

            core = self.core_repo.get_core_metrics(appln_id)
            if core is None:
                raise NotFoundError(f"Patent {appln_id} not found")

            cpc_dist = self.cpc_repo.get_cpc_distribution(appln_id, top_n=20)
            ind_dist = self.ind_repo.get_industry_distribution(appln_id, top_n=20)
            div = self.div_repo.get_diversification(appln_id)

            tech_entropy = div["tech"]["entropy"]
            tech_norm = div["tech"]["norm"]
            market_entropy = div["market"]["entropy"]
            market_norm = div["market"]["norm"]

            return {
                "appln_id": appln_id,

                "technology_analysis": {
                    "cpc_distribution": cpc_dist,
                    "technology_concentration": {
                        "entropy": tech_entropy,
                        "normalized_entropy": tech_norm,
                        "interpretation": self._interpret_entropy(tech_norm),
                    },
                },

                "market_analysis": {
                    "industry_distribution": ind_dist,
                    "market_concentration": {
                        "entropy": market_entropy,
                        "normalized_entropy": market_norm,
                        "interpretation": self._interpret_entropy(market_norm),
                    },
                },

                "citation_analysis": {
                    "backward": {
                        "total": core["backward"]["total"],
                        "self_citations": core["backward"]["self_citations"],
                        "x_patent": core["backward"]["x_patent"],
                        "y_patent": core["backward"]["y_patent"],
                        "npl": core["backward"]["npl"],
                    },
                    "forward": {
                        "total": core["forward"]["total"],
                        "self_citations": core["forward"]["self_citations"],
                        "x_patent": core["forward"]["x_patent"],
                        "y_patent": core["forward"]["y_patent"],
                        "npl": core["forward"]["npl"],
                    },
                    "field_normalization": {
                        "avg_fw": core["field_norm"]["avg_fw"],
                        "field_normalized_citations": core["field_norm"]["field_normalized_citations"],
                        "h_index_proxy": core["field_norm"]["h_index_proxy"],
                    },
                },

                "family_analysis": {
                    "family_size": core["family"]["family_size"],
                    "family_breadth": core["family"]["family_breadth"],
                    "geographic_scope": core["family"]["geographic_scope"],
                },

                "legal_event_analysis": {
                    "oppositions": core["legal_events"]["oppositions"],
                    "renewals_paid": core["legal_events"]["renewals_paid"],
                    "lapses": core["legal_events"]["lapses"],
                    "maintenance_status": self._maintenance_status(
                        is_unknown=core["legal_events"]["is_legal_unknown"],
                        is_maintained=core["legal_events"]["is_maintained"],
                    ),
                },

                "metadata": {
                    "contract_version": "v1",
                    "data_snapshot": "2025-01-31",
                    "confidence": "HIGH",
                },
            }

        except (ValidationError, NotFoundError):
            raise
        except Exception as e:
            logger.exception("Unhandled error in PatentAnalysisService appln_id=%s", appln_id)
            raise InternalServerError() from e

            

    async def get_analysis_2(self, appln_id: int) -> dict[str, any]:
        if appln_id <= 0:
            raise ValidationError("appln_id must be positive")

        core_metrics = self.core_repo.get_core_metrics(appln_id)
        if core_metrics is None:
            raise NotFoundError(f"Patent {appln_id} not found")

        ranks = self.ranks_repo.get_ranks_row(appln_id)
        if ranks is None:
            raise NotFoundError(f"Patent ranks not found for {appln_id}")

        cpc_dist = self.cpc_repo.get_cpc_distribution(appln_id, top_n=20)
        ind_dist = self.ind_repo.get_industry_distribution(appln_id, top_n=20)
        div = self.div_repo.get_diversification(appln_id)

        backward_total = int(core_metrics["X_backward_patent_count"] + core_metrics["Y_backward_patent_count"]
                             + core_metrics["X_backward_npl_count"] + core_metrics["Y_backward_npl_count"])
        forward_total = int(core_metrics["forward_patent_citation_count"])

        return {
            "technology": {
                "distribution": {
                    "cpc_subclasses": [
                        {"code": i["cpc_subclass"], "weight": i["frequency"]}
                        for i in cpc_dist["top_cpcs"]
                    ]
                },
                "diversification": {
                    "entropy": div["tech_entropy"],
                    "normalized": div["tech_norm"],
                    "interpretation": self._interpret_entropy(div["tech_norm"]),
                },
            },

            "market": {
                "distribution": {
                    "industries": [
                        {"code": i["industry_code"], "weight": i["frequency"]}
                        for i in ind_dist["top_industries"]
                    ]
                },
                "diversification": {
                    "entropy": div["market_entropy"],
                    "normalized": div["market_norm"],
                    "interpretation": self._interpret_entropy(div["market_norm"]),
                },
            },
            
            "citations": {
                "backward": {
                    "total": backward_total,
                    "x_patent": int(core_metrics["X_backward_patent_count"]),
                    "y_patent": int(core_metrics["Y_backward_patent_count"]),
                    "x_npl": int(core_metrics["X_backward_npl_count"]),
                    "y_npl": int(core_metrics["Y_backward_npl_count"]),
                },
                "forward": {
                    "total": forward_total,
                    "x_patent": int(core_metrics["X_forward_patent_count"]),
                    "y_patent": int(core_metrics["Y_forward_patent_count"]),
                },
                "self_citations": {
                    "forward": int(core_metrics["self_forward_citation_count"]),
                    "backward": int(core_metrics["self_backward_patent_count"]),
                    "self_forward_rate": self.round3(core_metrics["self_forward_rate"]),
                    "self_blocking_rate": self.round3(core_metrics["self_blocking_rate"]),
                },
            },

            "blocking_power_breakdown": {
                "dimensions": {
                    "technology": {
                        "axis_score": self.round3(ranks["tech_axis_score"]),
                    },
                    "market": {
                        "axis_score": self.round3(ranks["market_axis_score"]),
                    },
                    "legal": {
                        "legal_strength_score": self.round3(core_metrics["legal_strength_score"]),
                    }
                },
                "diagnostics": {
                    "forward_impact_score": self.round3(core_metrics["forward_impact_score"]),
                    "family_breadth_normalized": self.round3(core_metrics["family_breadth_normalized"]),
                    "tech_breadth_penalty": self.round3(core_metrics["tech_breadth_penalty"]),
                    "self_blocking_rate": self.round3(core_metrics["self_blocking_rate"]),
                }
            },

            "licensing_readiness_breakdown": {
                "forward_impact_score": self.round3(core_metrics["forward_impact_score"]),
                "claim_chartability_score": self.round3(core_metrics["claim_chartability_score"]),
                "market_relevance_score": self.round3(ranks["market_axis_score_pct_global"]),
                "legal_confidence_score": self.round3(core_metrics["legal_confidence_score"]),
                "final_readiness_score": self.round3(ranks["licensing_readiness_pct"]),
            },

            "legal": {
                "opposition_count": int(core_metrics["opposition_count"]),
                "lapse_count": int(core_metrics["lapse_count"]),
                "renewal_payment_count": int(core_metrics["renewal_payment_count"]),
                "legal_uncertainty": bool(core_metrics["is_legal_unknown"]),
            },

            "innovation": {
                "innovation_score": self.round3(core_metrics["innovation_score"]),
                "tech_field_influence": int(core_metrics["h_index_proxy"]),
                "field_attention": self.round3(core_metrics["field_normalized_citations"]),
            },

            "rankings": {
                "blocking_power": {
                    "rank_global": int(ranks["blocking_power_index_rank_global"]),
                    "percentile_global": self.round3(ranks["blocking_power_index_pct_global"]),
                },
                "technology_axis": {
                    "rank_global": int(ranks["tech_axis_score_rank_global"]),
                    "percentile_global": self.round3(ranks["tech_axis_score_pct_global"]),
                },
                "market_axis": {
                    "rank_global": int(ranks["market_axis_score_rank_global"]),
                    "percentile_global": self.round3(ranks["market_axis_score_pct_global"]),
                },
            },

            "metadata": {
                "contract_version": "v1",
                "confidence": "HIGH",
            },
        }


    @staticmethod
    def _interpret_entropy(norm: float) -> str:
        if norm < 0.30:
            return "HIGHLY_CONCENTRATED"
        if norm < 0.60:
            return "MODERATE"
        return "DIVERSIFIED"

    @staticmethod
    def _maintenance_status(is_unknown: bool, is_maintained: Optional[bool]) -> str:
        if is_unknown:
            return "UNKNOWN"
        return "MAINTAINED" if is_maintained else "NOT_MAINTAINED"

    @staticmethod
    def round3(value: Optional[float]) -> Optional[float]:
        if value is None:
            return None
        return round(float(value), 3)

    @staticmethod
    def tier_from_percentile(p: float) -> str:
        """
        Generic percentile-to-tier used for technology/market axis tiers and relative_positioning tiers.
        Percentile is 0..100 where higher is better.
        """
        if p >= 90:
            return "TOP_10_PERCENT"
        if p >= 75:
            return "TOP_25_PERCENT"
        if p >= 60:
            return "ABOVE_AVERAGE"
        if p >= 40:
            return "AVERAGE"
        if p >= 25:
            return "BELOW_AVERAGE"
        return "BOTTOM_25_PERCENT"

    @staticmethod
    def diversification_label(norm: float) -> str:
        """
        normalized diversification score (0..1). Higher means broader.
        """
        if norm >= 0.75:
            return "WELL_DIVERSIFIED"
        if norm >= 0.55:
            return "MODERATELY_DIVERSIFIED"
        if norm >= 0.35:
            return "NARROWLY_DIVERSIFIED"
        return "HIGHLY_CONCENTRATED"

    @staticmethod
    def pct(v: Optional[float]) -> Optional[float]:
        if v is None:
            return None
        return round(float(v), 1)

    async def get_citation_metrics(self, appln_id: int) -> dict:
        if appln_id <= 0:
            raise ValidationError("appln_id must be positive")

        metrics = self.citations_repo.get_citation_metrics(appln_id)
        if metrics is None:
            raise NotFoundError(f"Citation metrics not found for {appln_id}")

        return metrics

    async def get_citation_timeseries(self, appln_id: int) -> dict:
        if appln_id <= 0:
            raise ValidationError("appln_id must be positive")
            
        data = self.citations_repo.get_citation_timeseries(appln_id)
        if data is None:
             raise NotFoundError(f"Citation timeseries not found for {appln_id}")
             
        return data

    async def get_citation_forecast_ts(self, appln_id: int, horizon: str) -> dict:
        if appln_id <= 0:
            raise ValidationError("appln_id must be positive")

        # 1. Get historical cumulative timeseries
        hist_data = self.citations_repo.get_cumulative_timeseries(appln_id)
        if not hist_data or not hist_data["series"]:
            raise NotFoundError(f"Citation timeseries not found for {appln_id}")
            
        series = hist_data["series"]
        last_observed = series[-1]
        last_year = last_observed["year"]
        last_cum = last_observed["cum_cites"]

        # 2. Get ML forecast
        try:
            forecast_raw = await self.forecast_service.get_forecast(appln_id, horizon)
            pred = forecast_raw["prediction"]
            expected_add = pred["expected_citations"]
            low_add = pred["interval_80"]["low"]
            high_add = pred["interval_80"]["high"]
        except Exception as e:
            logger.warning(f"Forecast failed for {appln_id}: {e}")
            expected_add = 0.0
            low_add = 0.0
            high_add = 0.0
            pred = {
                "expected_citations": 0.0,
                "interval_80": {"low": 0.0, "high": 0.0},
                "difficulty_bucket": "UNKNOWN"
            }

        # 3. Project forecast linearly over horizon
        horizon_years = 3 if horizon == "3y" else 5
        forecast_series = []
        
        # Start forecast from the last observed point to ensure continuity
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
            "appln_id": appln_id,
            "filing_year": int(hist_data["filing_year"]),
            "horizon": horizon,
            "last_observed_year": last_year,
            "historical": series,
            "forecast": forecast_series,
            "prediction_summary": {
                "expected_additional": round(expected_add, 1),
                "interval_80": pred["interval_80"],
                "difficulty_bucket": pred.get("difficulty_bucket", "UNKNOWN")
            }
        }


    async def get_patent_forecast(self, appln_id: int, horizon: str) -> dict:
        if appln_id <= 0:
            raise ValidationError("appln_id must be positive")
        return await self.forecast_service.get_forecast(appln_id, horizon)

    async def search_patents(self, query: str, limit: int = 10) -> dict:
        if not query or len(query.strip()) < 2:
            return {"results": []}

        results = self.core_repo.search_by_publn_id(query, limit=limit)
        return {
            "query": query,
            "results": results
        }
