"use client"

import {
    TrendingUp,
    Shield,
    Clock,
    Zap,
    Leaf,
    BarChart3
} from "lucide-react"
import { TremorMetricCard } from "@/components/tremor-metric-card"
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from "@/components/ui/tooltip"

export interface PortfolioLifecycleMetrics {
    trajectory: {
        score_avg: number
        score_pct: number
        label: "Rising" | "Flat" | "Falling"
    }
    durability: {
        score_avg: number
        score_pct: number
    }
    sustainability: {
        score_avg: number
        score_pct: number
        sustaining_share: number
    }
    timing: {
        mode: "EARLY" | "MID" | "LATE"
        score_avg: number
        score_pct: number
    }
    early_signal: {
        share: number
    }
    cites_per_patent: {
        overall_avg: number
    }
}

interface PortfolioHealthCardsProps {
    metrics: PortfolioLifecycleMetrics
}

export function PortfolioHealthCards({ metrics }: PortfolioHealthCardsProps) {
    const getTrajectoryColor = (label: string): string => {
        switch (label) {
            case "Rising": return "emerald"
            case "Falling": return "rose"
            default: return "gray"
        }
    }

    const getTimingColor = (mode: string): string => {
        switch (mode) {
            case "EARLY": return "emerald"
            case "MID": return "blue"
            case "LATE": return "orange"
            default: return "gray"
        }
    }

    return (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            {/* 1. Trajectory */}
            <TooltipProvider>
                <Tooltip>
                    <TooltipTrigger asChild>
                        <div>
                            <TremorMetricCard
                                title="Trajectory"
                                metric={`${metrics.trajectory.score_pct}/100`}
                                subtext={`Avg: ${metrics.trajectory.score_avg}`}
                                icon={TrendingUp}
                                progress={{ value: metrics.trajectory.score_pct, color: "blue", label: `${metrics.trajectory.score_pct}/100` }}
                                status={{
                                    label: metrics.trajectory.label,
                                    color: getTrajectoryColor(metrics.trajectory.label) as any
                                }}
                                decorationColor={getTrajectoryColor(metrics.trajectory.label) as any}
                                className="h-full cursor-help"
                            />
                        </div>
                    </TooltipTrigger>
                    <TooltipContent>
                        <p className="max-w-xs text-xs">
                            Average citation growth velocity across the portfolio.
                            Percentile compares to global portfolios.
                        </p>
                    </TooltipContent>
                </Tooltip>
            </TooltipProvider>

            {/* 2. Durability */}
            <TooltipProvider>
                <Tooltip>
                    <TooltipTrigger asChild>
                        <div>
                            <TremorMetricCard
                                title="Durability"
                                metric={`${metrics.durability.score_pct}/100`}
                                subtext={`Avg: ${metrics.durability.score_avg}`}
                                icon={Shield}
                                progress={{ value: metrics.durability.score_pct, color: "violet", label: `${metrics.durability.score_pct}/100` }}
                                trend={{
                                    value: `Top ${100 - metrics.durability.score_pct}%`,
                                    direction: "up",
                                    label: "Global Rank"
                                }}
                                decorationColor="violet"
                                className="h-full cursor-help"
                            />
                        </div>
                    </TooltipTrigger>
                    <TooltipContent>
                        <p className="max-w-xs text-xs">
                            Measure of citation longevity. Higher scores indicate patents that remain relevant for longer periods.
                        </p>
                    </TooltipContent>
                </Tooltip>
            </TooltipProvider>

            {/* 3. Sustainability */}
            <TooltipProvider>
                <Tooltip>
                    <TooltipTrigger asChild>
                        <div>
                            <TremorMetricCard
                                title="Sustainability"
                                metric={`${metrics.sustainability.score_pct}/100`}
                                subtext={`Avg: ${metrics.sustainability.score_avg}`}
                                icon={Leaf}
                                progress={{ value: metrics.sustainability.score_pct, color: "green", label: `${metrics.sustainability.score_pct}/100` }}
                                status={{
                                    label: `${(metrics.sustainability.sustaining_share * 100).toFixed(0)}% Sustaining`,
                                    color: "green"
                                }}
                                decorationColor="green"
                                className="h-full cursor-help"
                            />
                        </div>
                    </TooltipTrigger>
                    <TooltipContent>
                        <p className="max-w-xs text-xs">
                            Share of patents exhibiting steady, long-term citation interest vs flashy short-term spikes.
                        </p>
                    </TooltipContent>
                </Tooltip>
            </TooltipProvider>

            {/* 4. Strategic Timing */}
            <TooltipProvider>
                <Tooltip>
                    <TooltipTrigger asChild>
                        <div>
                            <TremorMetricCard
                                title="Timing"
                                metric={`${metrics.timing.score_pct}/100`}
                                subtext={`Avg: ${metrics.timing.score_avg}`}
                                icon={Clock}
                                progress={{ value: metrics.timing.score_pct, color: getTimingColor(metrics.timing.mode) as any, label: `${metrics.timing.score_pct}/100` }}
                                status={{
                                    label: `${metrics.timing.mode} MOVER`,
                                    color: getTimingColor(metrics.timing.mode) as any
                                }}
                                decorationColor={getTimingColor(metrics.timing.mode) as any}
                                className="h-full cursor-help"
                            />
                        </div>
                    </TooltipTrigger>
                    <TooltipContent>
                        <p className="max-w-xs text-xs">
                            Dominant strategic timing (Early/Mid/Late) relative to technology waves.
                        </p>
                    </TooltipContent>
                </Tooltip>
            </TooltipProvider>

            {/* 5. Early Signal */}
            <TooltipProvider>
                <Tooltip>
                    <TooltipTrigger asChild>
                        <div>
                            <TremorMetricCard
                                title="Early Signal"
                                metric={`${(metrics.early_signal.share * 100).toFixed(1)}%`}
                                subtext="of total citations"
                                icon={Zap}
                                progress={{ value: metrics.early_signal.share * 100, color: "amber" }}
                                decorationColor="amber"
                                className="h-full cursor-help"
                            />
                        </div>
                    </TooltipTrigger>
                    <TooltipContent>
                        <p className="max-w-xs text-xs">
                            Percentage of citations received within the first 3 years of publication.
                            High values indicate immediate industry relevance.
                        </p>
                    </TooltipContent>
                </Tooltip>
            </TooltipProvider>

            {/* 6. Cite/Patent */}
            <TooltipProvider>
                <Tooltip>
                    <TooltipTrigger asChild>
                        <div>
                            <TremorMetricCard
                                title="Cite/Patent"
                                metric={metrics.cites_per_patent.overall_avg.toFixed(1)}
                                subtext="Avg per patent"
                                icon={BarChart3}
                                decorationColor="blue"
                                className="h-full cursor-help"
                            />
                        </div>
                    </TooltipTrigger>
                    <TooltipContent>
                        <p className="max-w-xs text-xs">
                            Average citations per patent.
                        </p>
                    </TooltipContent>
                </Tooltip>
            </TooltipProvider>
        </div>
    )
}
