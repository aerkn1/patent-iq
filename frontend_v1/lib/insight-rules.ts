import type { TechnologyProfile, MarketProfile, PeerPositioning } from "@/lib/types/patent"

export function getTechnologyInsights(profile: TechnologyProfile): string[] {
    const insights: string[] = []
    const { diversification, axis_score } = profile
    const { entropy_norm, top_k_share, long_tail_share } = diversification

    // 1. Diversification Pattern
    if (entropy_norm > 0.75) {
        insights.push("Highly diversified technology portfolio covering a broad range of technical domains.")
    } else if (entropy_norm < 0.4) {
        insights.push("Specialized portfolio with high concentration in specific technical areas.")
    } else {
        insights.push("Balanced portfolio with a mix of core technologies and adjacent areas.")
    }

    // 2. Focus & Concentration
    if (top_k_share > 0.8) {
        insights.push("Primary focus is heavily consolidated within top technical categories.")
    } else if (top_k_share < 0.5) {
        insights.push("Investment is distributed evenly across multiple technology sectors.")
    }

    // 3. Exploration / Innovation
    if (long_tail_share > 0.15) {
        insights.push("Shows active exploration into emerging or niche technology fields (strong 'long tail').")
    }

    // 4. Axis Score (Tech Leadership)
    if (axis_score > 0.8) {
        insights.push("Demonstrates strong leadership and technological depth in its primary fields.")
    }

    return insights
}

export function getMarketInsights(profile: MarketProfile): string[] {
    const insights: string[] = []
    const { diversification, axis_score } = profile
    const { entropy_norm, top_k_share, long_tail_share } = diversification

    // 1. Market Spread
    if (entropy_norm > 0.75) {
        insights.push("Broad market applicability across diverse industry sectors.")
    } else if (entropy_norm < 0.4) {
        insights.push("Targeted market focus on specific industries.")
    } else {
        insights.push("Presence across several related market sectors.")
    }

    // 2. Industry Concentration
    if (top_k_share > 0.8) {
        insights.push("Revenue potential is strongly tied to a few key industries.")
    }

    // 3. Niche Markets
    if (long_tail_share > 0.15) {
        insights.push("Significant potential applications in niche or specialized market segments.")
    }

    if (axis_score > 0.8) {
        insights.push("High market relevance and potential dominance in target industries.")
    }

    return insights
}

export function getPeerPositioningInsights(positioning: PeerPositioning): string[] {
    const insights: string[] = []
    const { peer_percentile, peer_class, n_peers, peer_group_id } = positioning

    // 1. Overall Performance
    if (peer_percentile > 75) {
        insights.push("Outperforms the majority of peers in the reference group.")
    } else if (peer_percentile < 25) {
        insights.push("Performance is currently lagging behind industry benchmarks.")
    } else {
        insights.push("Performance is consistent with industry standards.")
    }

    // 2. Peer Class
    if (peer_class === "HIGH" || peer_class === "ABOVE_AVERAGE") {
        insights.push("Classified as a top-tier portfolio within its cohort.")
    } else if (peer_class === "LOW" || peer_class === "BELOW_AVERAGE") {
        insights.push("Identify opportunities to improve portfolio quality relative to peers.")
    }

    // 3. Comparison Context
    insights.push(`Benchmarked against ${n_peers.toLocaleString()} similar portfolios in the "${peer_group_id}" group.`)

    return insights
}
