"use client"

import { TremorMetricCard } from "@/components/tremor-metric-card"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { TrendingUp, Shield, Clock, Calendar, Leaf, Award } from "lucide-react"

export interface LifecycleMetrics {
    trajectory: {
        score: number
        percentile: number
        label: "Rising" | "Flat" | "Falling"
    }
    durability: {
        score: number
        percentile: number
        spanYears: number
    }
    sustainability: {
        score: number
        percentile: number
        isSustaining: boolean
    }
    timing: {
        score: number
        percentile: number
        class: "EARLY" | "MID" | "LATE"
    }
    peakAge: number
    totalCitations: number
}

interface TrajectoryLifecycleCardsProps {
    metrics: LifecycleMetrics
}

export function TrajectoryLifecycleCards({ metrics }: TrajectoryLifecycleCardsProps) {
    const getTrajectoryColor = (label: string): string => {
        switch (label) {
            case "Rising": return "emerald"
            case "Falling": return "rose"
            default: return "gray"
        }
    }

    return (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            {/* 1. Trajectory Score */}
            <TooltipProvider>
                <Tooltip>
                    <TooltipTrigger asChild>
                        <div>
                            <TremorMetricCard
                                title="Trajectory"
                                metric={`${metrics.trajectory.percentile}/100`}
                                subtext={`Avg: ${metrics.trajectory.score}`}
                                icon={TrendingUp}
                                progress={{ value: metrics.trajectory.percentile, color: "blue", label: `${metrics.trajectory.percentile}/100` }}
                                status={{
                                    label: metrics.trajectory.label,
                                    color: getTrajectoryColor(metrics.trajectory.label) as any
                                }}
                                decorationColor={getTrajectoryColor(metrics.trajectory.label) as any}
                                className="h-full cursor-help"
                            />
                        </div>
                    </TooltipTrigger>
                    <TooltipContent side="top">
                        Citation growth momentum (0-100). Indicates if interest is rising, flat, or falling.
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
                                metric={`${metrics.durability.percentile}/100`}
                                subtext={`Avg: ${metrics.durability.score}`}
                                icon={Shield}
                                progress={{ value: metrics.durability.percentile, color: "violet", label: `${metrics.durability.percentile}/100` }}
                                decorationColor="violet"
                                className="h-full cursor-help"
                            />
                        </div>
                    </TooltipTrigger>
                    <TooltipContent side="top">
                        Longevity of citation interest. Higher scores indicate long-lasting relevance.
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
                                metric={`${metrics.sustainability.percentile}/100`}
                                subtext={`Avg: ${metrics.sustainability.score}`}
                                icon={Leaf}
                                progress={{ value: metrics.sustainability.percentile, color: "green", label: `${metrics.sustainability.percentile}/100` }}
                                status={{
                                    label: metrics.sustainability.isSustaining ? "Sustaining" : "Normal",
                                    color: metrics.sustainability.isSustaining ? "green" : "gray"
                                }}
                                decorationColor="green"
                                className="h-full cursor-help"
                            />
                        </div>
                    </TooltipTrigger>
                    <TooltipContent side="top">
                        Stability of citation inflow over time.
                    </TooltipContent>
                </Tooltip>
            </TooltipProvider>

            {/* 4. Strategic Timing */}
            <TooltipProvider>
                <Tooltip>
                    <TooltipTrigger asChild>
                        <div>
                            <TremorMetricCard
                                title="Strat. Timing"
                                metric={`${metrics.timing.percentile}/100`}
                                subtext={`Avg: ${metrics.timing.score}`}
                                icon={Clock}
                                progress={{ value: metrics.timing.percentile, color: "amber", label: `${metrics.timing.percentile}/100` }}
                                status={{ label: metrics.timing.class, color: "amber" }}
                                decorationColor="amber"
                                className="h-full cursor-help"
                            />
                        </div>
                    </TooltipTrigger>
                    <TooltipContent side="top">
                        Timing of citations relative to technology cycle (Early, Mid, Late).
                    </TooltipContent>
                </Tooltip>
            </TooltipProvider>

            {/* 5. Peak Age */}
            <TooltipProvider>
                <Tooltip>
                    <TooltipTrigger asChild>
                        <div>
                            <TremorMetricCard
                                title="Peak Age"
                                metric={metrics.peakAge}
                                subtext="years post-filing"
                                icon={Calendar}
                                decorationColor="indigo"
                                className="h-full cursor-help"
                            />
                        </div>
                    </TooltipTrigger>
                    <TooltipContent side="top">
                        Years after filing when citations peaked.
                    </TooltipContent>
                </Tooltip>
            </TooltipProvider>

            {/* 6. Total Citations */}
            <TooltipProvider>
                <Tooltip>
                    <TooltipTrigger asChild>
                        <div>
                            <TremorMetricCard
                                title="Total Cites"
                                metric={metrics.totalCitations}
                                subtext="Lifetime citations"
                                icon={Award}
                                decorationColor="blue"
                                className="h-full cursor-help"
                            />
                        </div>
                    </TooltipTrigger>
                    <TooltipContent side="top">
                        Total forward citations count.
                    </TooltipContent>
                </Tooltip>
            </TooltipProvider>
        </div>
    )
}
