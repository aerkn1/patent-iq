"use client"

import { Badge } from "@/components/ui/badge"
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
    const getColorClass = (color: string) => {
        switch (color) {
            case "emerald": return "bg-emerald-500"
            case "rose": return "bg-rose-500"
            case "blue": return "bg-blue-500"
            case "amber": return "bg-amber-500"
            case "violet": return "bg-violet-500"
            case "indigo": return "bg-indigo-500"
            default: return "bg-slate-500"
        }
    }

    const MetricItem = ({
        title,
        icon: Icon,
        value,
        label,
        color,
        progressValue,
        description
    }: {
        title: string
        icon: any
        value: string | number
        label?: string
        color: string
        progressValue?: number
        description: string
    }) => (
        <TooltipProvider>
            <Tooltip>
                <TooltipTrigger asChild>
                    <div className="space-y-3 p-4 border rounded-lg bg-card hover:bg-muted/30 transition-colors cursor-help h-full flex flex-col justify-between">
                        <div>
                            <div className="flex items-center justify-between mb-2">
                                <span className="text-sm font-medium text-muted-foreground">{title}</span>
                                <Icon className="h-4 w-4 text-muted-foreground" />
                            </div>
                            <div className="flex items-baseline gap-2 mb-3">
                                <span className="text-2xl font-bold tracking-tight">{value}</span>
                                {label && (
                                    <Badge variant="secondary" className="text-xs font-normal bg-muted">
                                        {label}
                                    </Badge>
                                )}
                            </div>
                        </div>

                        <div className="space-y-2">
                            {/* Custom Progress Bar */}
                            {typeof progressValue === 'number' && (
                                <div className="h-1.5 w-full bg-secondary rounded-full overflow-hidden">
                                    <div
                                        className={`h-full ${getColorClass(color)} transition-all duration-500 ease-out`}
                                        style={{ width: `${Math.min(100, Math.max(0, progressValue))}%` }}
                                    />
                                </div>
                            )}
                        </div>
                    </div>
                </TooltipTrigger>
                <TooltipContent side="top">
                    <p className="max-w-xs text-xs">
                        {description}
                    </p>
                </TooltipContent>
            </Tooltip>
        </TooltipProvider>
    )

    return (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            {/* 1. Trajectory Score */}
            <MetricItem
                title="Trajectory"
                icon={TrendingUp}
                value={`${metrics.trajectory.percentile}/100`}
                label={metrics.trajectory.label}
                progressValue={metrics.trajectory.percentile}
                color={metrics.trajectory.label === "Rising" ? "emerald" : (metrics.trajectory.label === "Falling" ? "rose" : "slate")}
                description="Percentile (0-100) compares overall trajectory strength. Label (Rising/Falling) describes the current trend direction."
            />

            {/* 2. Durability */}
            <MetricItem
                title="Durability"
                icon={Shield}
                value={`${metrics.durability.percentile}/100`}
                label={`Avg: ${metrics.durability.score}`}
                progressValue={metrics.durability.percentile}
                color="violet"
                description="Longevity of citation interest. Higher scores indicate long-lasting relevance."
            />

            {/* 3. Sustainability */}
            <MetricItem
                title="Sustainability"
                icon={Leaf}
                value={`${metrics.sustainability.percentile}/100`}
                label={metrics.sustainability.isSustaining ? "Sustaining" : "Normal"}
                progressValue={metrics.sustainability.percentile}
                color="emerald"
                description="Stability of citation inflow over time."
            />

            {/* 4. Strategic Timing */}
            <MetricItem
                title="Strat. Timing"
                icon={Clock}
                value={`${metrics.timing.percentile}/100`}
                label={metrics.timing.class}
                progressValue={metrics.timing.percentile}
                color="amber"
                description="Timing of citations relative to technology cycle (Early, Mid, Late)."
            />

            {/* 5. Peak Age */}
            <MetricItem
                title="Peak Age"
                icon={Calendar}
                value={metrics.peakAge}
                label="years post-filing"
                progressValue={0} // No bar for non-percentile
                color="indigo"
                description="Years after filing when citations peaked."
            />

            {/* 6. Total Citations */}
            <MetricItem
                title="Total Cites"
                icon={Award}
                value={metrics.totalCitations}
                label="Lifetime"
                progressValue={0} // No bar
                color="blue"
                description="Total forward citations count."
            />
        </div>
    )
}
