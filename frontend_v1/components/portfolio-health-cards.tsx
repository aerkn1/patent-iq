"use client"

import {
    TrendingUp,
    Shield,
    Clock,
    Zap,
    Leaf,
    BarChart3
} from "lucide-react"
import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
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
    const getColorClass = (color: string) => {
        switch (color) {
            case "emerald": return "bg-emerald-500"
            case "rose": return "bg-rose-500"
            case "blue": return "bg-blue-500"
            case "amber": return "bg-amber-500"
            case "violet": return "bg-violet-500"
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
                    <div className="space-y-3 p-4 border rounded-lg bg-card hover:bg-muted/30 transition-[box-shadow,background-color] duration-150 cursor-help h-full flex flex-col justify-between">
                        <div>
                            <div className="flex items-center justify-between mb-2">
                                <span className="text-sm font-medium text-muted-foreground">{title}</span>
                                <Icon className="h-4 w-4 text-muted-foreground" />
                            </div>
                            <div className="flex items-baseline gap-2 mb-3">
                                <span className="metric-value text-2xl">{value}</span>
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
                            {/* Description for context */}
                            {/* <p className="text-xs text-muted-foreground line-clamp-2">
                                {description}
                            </p> */}
                        </div>
                    </div>
                </TooltipTrigger>
                <TooltipContent>
                    <p className="max-w-xs text-xs">
                        {description}
                    </p>
                </TooltipContent>
            </Tooltip>
        </TooltipProvider>
    )

    return (
        <Card>
            <CardHeader>
                <div className="flex items-center gap-2">
                    <TrendingUp className="h-5 w-5 text-primary" />
                    <div>
                        <CardTitle className="text-lg">Global Portfolio Citation Dynamics</CardTitle>
                        <CardDescription>Performance indicators relative to global benchmarks</CardDescription>
                    </div>
                </div>
            </CardHeader>
            <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 items-stretch">
                    {/* 1. Trajectory */}
                    <MetricItem
                        title="Trajectory"
                        icon={TrendingUp}
                        value={`${metrics.trajectory.score_pct}/100`}
                        label={metrics.trajectory.label}
                        progressValue={metrics.trajectory.score_pct}
                        color={metrics.trajectory.label === "Rising" ? "emerald" : (metrics.trajectory.label === "Falling" ? "rose" : "slate")}
                        description="Average citation growth velocity across the portfolio. Percentile compares to global portfolios."
                    />

                    {/* 2. Durability */}
                    <MetricItem
                        title="Durability"
                        icon={Shield}
                        value={`${metrics.durability.score_pct}/100`}
                        label={`Top ${Math.max(1, 100 - metrics.durability.score_pct)}%`}
                        progressValue={metrics.durability.score_pct}
                        color="blue"
                        description="Measure of citation longevity. Higher scores indicate patents that remain relevant for longer periods."
                    />

                    {/* 3. Sustainability */}
                    <MetricItem
                        title="Sustainability"
                        icon={Leaf}
                        value={`${metrics.sustainability.score_pct}/100`}
                        label={`${(metrics.sustainability.sustaining_share * 100).toFixed(0)}% Sustaining`}
                        progressValue={metrics.sustainability.score_pct}
                        color="emerald"
                        description="Share of patents exhibiting steady, long-term citation interest vs flashy short-term spikes."
                    />

                    {/* 4. Strategic Timing */}
                    <MetricItem
                        title="Timing"
                        icon={Clock}
                        value={`${metrics.timing.score_pct}/100`}
                        label={`${metrics.timing.mode} MOVER`}
                        progressValue={metrics.timing.score_pct}
                        color={metrics.timing.mode === "EARLY" ? "emerald" : (metrics.timing.mode === "MID" ? "blue" : "amber")}
                        description="Dominant strategic timing (Early/Mid/Late) relative to technology waves."
                    />

                    {/* 5. Early Signal */}
                    <MetricItem
                        title="Early Signal"
                        icon={Zap}
                        value={`${(metrics.early_signal.share * 100).toFixed(1)}%`}
                        label="3-Year Impact"
                        progressValue={metrics.early_signal.share * 100}
                        color="amber"
                        description="Percentage of citations received within the first 3 years of publication. High values indicate immediate industry relevance."
                    />

                    {/* 6. Cite/Patent */}
                    <MetricItem
                        title="Cite/Patent"
                        icon={BarChart3}
                        value={metrics.cites_per_patent.overall_avg.toFixed(1)}
                        label="Per Patent"
                        progressValue={0} // No progress bar for raw number? Or maybe scale it? Leaving 0 hides it effectively if I add check, but here I rendered bar always.
                        // I will pass undefined to hide bar.
                        color="blue"
                        description="Average citations per patent."
                    />
                </div>
            </CardContent>
        </Card>
    )
}
