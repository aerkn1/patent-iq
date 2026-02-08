from pathlib import Path

BASE = "https://huggingface.co/datasets/ardae1/analytics-parquets/resolve/main/patent-iq"

PARQUETS = {
    "patent_core": f"{BASE}/patent_core.parquet",
    "patent_core_w_ranks": f"{BASE}/patent_core_with_ranks.parquet",

    "patent_tech_market_axes": f"{BASE}/patent_tech_market_axes.parquet",

    "patent_tech_lens_presence": f"{BASE}/patent_tech_lens_presence.parquet",
    "patent_tech_lens_freq": f"{BASE}/patent_tech_lens_freq_v3.parquet",

    "patent_industry_presence": f"{BASE}/patent_industry_presence.parquet",
    "patent_industry_freq": f"{BASE}/patent_industry_freq.parquet",

    "patent_portfolio_map": f"{BASE}/patent_portfolio_map.parquet",

    "patent_frequency_scores": f"{BASE}/patent_frequency_scores.parquet",
    "patent_final_decision_scores": f"{BASE}/patent_final_decision_scores.parquet",
    "patent_final_decision_scores_ui": f"{BASE}/patent_final_decision_scores_ui.parquet",

    "patent_rank_global": f"{BASE}/patent_rank_global.parquet",
    "patent_rank_in_tech": f"{BASE}/patent_rank_in_tech.parquet",

    "patent_citation_events_core": f"{BASE}/patent_citation_events_core.parquet",
    "patent_citation_events_yearly": f"{BASE}/patent_citation_events_yearly.parquet",
    "patent_citation_metrics": f"{BASE}/patent_citation_metrics.parquet",

    "portfolio_citation_timeseries": f"{BASE}/portfolio_citation_timeseries.parquet",
    "portfolio_citation_metrics": f"{BASE}/portfolio_citation_metrics.parquet",

    # portfolio
    "portfolio_axis_scores": f"{BASE}/portfolio_axis_scores.parquet",
    "portfolio_master": f"{BASE}/portfolio_master.parquet",
    "portfolio_peer_benchmark": f"{BASE}/portfolio_peer_benchmark.parquet",
    "portfolio_ranking_final": f"{BASE}/portfolio_ranking_final.parquet",
    "portfolio_size_reference": f"{BASE}/portfolio_size_reference.parquet",
    "owner_reference": f"{BASE}/owner_reference.parquet",
    "portfolio_final": f"{BASE}/portfolio_final.parquet",
    "portfolio_cpc_stats": f"{BASE}/portfolio_cpc_distribution_stats.parquet",
    "portfolio_industry_stats": f"{BASE}/portfolio_industry_distribution_stats.parquet",
    "portfolio_cpc": f"{BASE}/portfolio_cpc_distribution.parquet",
    "portfolio_industry": f"{BASE}/portfolio_industry_distribution.parquet",
    "portfolio_licensing": f"{BASE}/portfolio_licensing_final.parquet",

    # family
    "family_members": f"{BASE}/family_members.parquet",
    "raw_family_grants": f"{BASE}/raw_family_grants.parquet",
    "family_grants": f"{BASE}/family_grants.parquet",
    "raw_family_cpc": f"{BASE}/raw_family_cpc.parquet",
    "family_cpc": f"{BASE}/family_cpc.parquet",
    "family_members_metrics": f"{BASE}/family_members_metrics.parquet",
    "family_grant_metrics": f"{BASE}/family_grant_metrics.parquet",
    "family_cpc_metrics": f"{BASE}/family_cpc_metrics.parquet",
    "patent_family_enriched": f"{BASE}/patent_family_enriched.parquet",
    "portfolio_family_metrics": f"{BASE}/portfolio_family_metrics.parquet",
    "portfolio_family_grant_mix": f"{BASE}/portfolio_family_grant_mix.parquet",
    "portfolio_family_top_cpcs": f"{BASE}/portfolio_family_top_cpcs.parquet",
    "portfolio_family_assets": f"{BASE}/portfolio_family_assets.parquet",
}