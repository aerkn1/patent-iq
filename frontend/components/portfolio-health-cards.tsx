"use client"

import {
    TrendingUp,
    TrendingDown,
    Minus,
    Shield,
    Clock,
    Zap,
    Leaf,
    Info,
    Activity,
    BarChart3
} from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
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
        by_phase: {
            early: number
            mid: number
            late: number
        }
    }
}

interface PortfolioHealthCardsProps {
    metrics: PortfolioLifecycleMetrics
}

export function PortfolioHealthCards({ metrics }: PortfolioHealthCardsProps) {
    const getTrajectoryIcon = (label: string) => {
        switch (label) {
            case "Rising":
                return <TrendingUp className="h-4 w-4 mr-1" />
            case "Falling":
                return <TrendingDown className="h-4 w-4 mr-1" />
            default:
                return <Minus className="h-4 w-4 mr-1" />
        }
    }

    const getTrajectoryColor = (label: string) => {
        switch (label) {
            case "Rising":
                return "bg-green-100 text-green-700 border-green-200"
            case "Falling":
                return "bg-red-100 text-red-700 border-red-200"
            default:
                return "bg-gray-100 text-gray-700 border-gray-200"
        }
    }

    const getTimingColor = (mode: string) => {
        switch (mode) {
            case "EARLY":
                return "bg-green-100 text-green-700 border-green-200"
            case "MID":
                return "bg-blue-100 text-blue-700 border-blue-200"
            case "LATE":
                return "bg-orange-100 text-orange-700 border-orange-200"
            default:
                return "bg-gray-100 text-gray-700 border-gray-200"
        }
    }

    return (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            {/* 1. Trajectory (Avg + Percentile) */}
            <TooltipProvider>
                <Card>
                    <CardContent className="p-4 flex flex-col justify-between h-full">
                        <div className="space-y-2">
                            <div className="flex items-center justify-between text-muted-foreground">
                                <span className="text-xs font-medium flex items-center gap-1">
                                    <TrendingUp className="h-3 w-3" /> Trajectory
                                </span>
                                <Tooltip>
                                    <TooltipTrigger>
                                        <Info className="h-3 w-3 cursor-help" />
                                    </TooltipTrigger>
                                    <TooltipContent>
                                        <p className="max-w-xs text-xs">
                                            Average citation growth velocity across the portfolio.
                                            Percentile compares to global portfolios.
                                        </p>
                                    </TooltipContent>
                                </Tooltip>
                            </div>
                            <div className="flex flex-col gap-1">
                                <div className="flex items-center gap-2">
                                    <span className="text-2xl font-bold">{metrics.trajectory.score_avg}</span>
                                    <Badge variant="outline" className={`text-[10px] px-1.5 py-0 h-5 ${getTrajectoryColor(metrics.trajectory.label)}`}>
                                        {getTrajectoryIcon(metrics.trajectory.label)}
                                        {metrics.trajectory.label}
                                    </Badge>
                                </div>
                                <span className="text-xs text-muted-foreground">{metrics.trajectory.score_pct}th percentile</span>
                            </div>
                        </div>
                        <Progress value={metrics.trajectory.score_pct} className="h-1 mt-3" />
                    </CardContent>
                </Card>
            </TooltipProvider>

            {/* 2. Durability (Avg + Percentile) */}
            <TooltipProvider>
                <Card>
                    <CardContent className="p-4 flex flex-col justify-between h-full">
                        <div className="space-y-2">
                            <div className="flex items-center justify-between text-muted-foreground">
                                <span className="text-xs font-medium flex items-center gap-1">
                                    <Shield className="h-3 w-3" /> Durability
                                </span>
                                <Tooltip>
                                    <TooltipTrigger>
                                        <Info className="h-3 w-3 cursor-help" />
                                    </TooltipTrigger>
                                    <TooltipContent>
                                        <p className="max-w-xs text-xs">
                                            Measure of citation longevity. Higher scores indicate patents that remain relevant for longer periods.
                                        </p>
                                    </TooltipContent>
                                </Tooltip>
                            </div>
                            <div className="flex flex-col gap-1">
                                <span className="text-2xl font-bold">{metrics.durability.score_avg}</span>
                                <span className="text-xs text-muted-foreground">Avg Score</span>
                                <span className="text-xs font-medium text-green-600">Top {100 - metrics.durability.score_pct}%</span>
                            </div>
                        </div>
                        <Progress value={metrics.durability.score_pct} className="h-1 mt-3" />
                    </CardContent>
                </Card>
            </TooltipProvider>

            {/* 3. Sustainability (Avg + Share) */}
            <TooltipProvider>
                <Card>
                    <CardContent className="p-4 flex flex-col justify-between h-full">
                        <div className="space-y-2">
                            <div className="flex items-center justify-between text-muted-foreground">
                                <span className="text-xs font-medium flex items-center gap-1">
                                    <Leaf className="h-3 w-3" /> Sustainability
                                </span>
                                <Tooltip>
                                    <TooltipTrigger>
                                        <Info className="h-3 w-3 cursor-help" />
                                    </TooltipTrigger>
                                    <TooltipContent>
                                        <p className="max-w-xs text-xs">
                                            Share of patents exhibiting steady, long-term citation interest vs flashy short-term spikes.
                                        </p>
                                    </TooltipContent>
                                </Tooltip>
                            </div>
                            <div className="flex flex-col gap-1">
                                <div className="flex items-center gap-2">
                                    <span className="text-2xl font-bold">{metrics.sustainability.score_avg}</span>
                                </div>
                                <Badge variant="secondary" className="w-fit text-[10px] px-1.5 h-5">
                                    {(metrics.sustainability.sustaining_share * 100).toFixed(0)}% Sustaining
                                </Badge>
                            </div>
                        </div>
                        <Progress value={metrics.sustainability.score_avg} className="h-1 mt-3" />
                    </CardContent>
                </Card>
            </TooltipProvider>

            {/* 4. Strategic Timing (Mode + Score) */}
            <TooltipProvider>
                <Card>
                    <CardContent className="p-4 flex flex-col justify-between h-full">
                        <div className="space-y-2">
                            <div className="flex items-center justify-between text-muted-foreground">
                                <span className="text-xs font-medium flex items-center gap-1">
                                    <Clock className="h-3 w-3" /> Timing
                                </span>
                                <Tooltip>
                                    <TooltipTrigger>
                                        <Info className="h-3 w-3 cursor-help" />
                                    </TooltipTrigger>
                                    <TooltipContent>
                                        <p className="max-w-xs text-xs">
                                            Dominant strategic timing (Early/Mid/Late) relative to technology waves.
                                        </p>
                                    </TooltipContent>
                                </Tooltip>
                            </div>
                            <div className="flex flex-col gap-1">
                                <Badge variant="outline" className={`w-fit mb-1 ${getTimingColor(metrics.timing.mode)}`}>
                                    {metrics.timing.mode} MOVER
                                </Badge>
                                <span className="text-xs text-muted-foreground">Score: {metrics.timing.score_avg}</span>
                            </div>
                        </div>
                        <Progress value={metrics.timing.score_pct} className="h-1 mt-3" />
                    </CardContent>
                </Card>
            </TooltipProvider>

            {/* 5. Early-Signal Share */}
            <TooltipProvider>
                <Card>
                    <CardContent className="p-4 flex flex-col justify-between h-full">
                        <div className="space-y-2">
                            <div className="flex items-center justify-between text-muted-foreground">
                                <span className="text-xs font-medium flex items-center gap-1">
                                    <Zap className="h-3 w-3" /> Early Signal
                                </span>
                                <Tooltip>
                                    <TooltipTrigger>
                                        <Info className="h-3 w-3 cursor-help" />
                                    </TooltipTrigger>
                                    <TooltipContent>
                                        <p className="max-w-xs text-xs">
                                            Percentage of citations received within the first 3 years of publication.
                                            High values indicate immediate industry relevance.
                                        </p>
                                    </TooltipContent>
                                </Tooltip>
                            </div>
                            <div className="flex flex-col gap-1">
                                <span className="text-2xl font-bold">{(metrics.early_signal.share * 100).toFixed(1)}%</span>
                                <span className="text-xs text-muted-foreground">of total citations</span>
                            </div>
                        </div>
                        <Progress value={metrics.early_signal.share * 100} className="h-1 mt-3" />
                    </CardContent>
                </Card>
            </TooltipProvider>

            {/* 6. Cites per Patent (Overall + Mini Bar) */}
            <TooltipProvider>
                <Card>
                    <CardContent className="p-4 flex flex-col justify-between h-full">
                        <div className="space-y-2">
                            <div className="flex items-center justify-between text-muted-foreground">
                                <span className="text-xs font-medium flex items-center gap-1">
                                    <BarChart3 className="h-3 w-3" /> Citations/Pat
                                </span>
                                <Tooltip>
                                    <TooltipTrigger>
                                        <Info className="h-3 w-3 cursor-help" />
                                    </TooltipTrigger>
                                    <TooltipContent>
                                        <p className="max-w-xs text-xs">
                                            Average citations per patent. The bar shows the distribution of Early/Mid/Late phase citations.
                                        </p>
                                    </TooltipContent>
                                </Tooltip>
                            </div>
                            <div className="flex flex-col gap-1">
                                <span className="text-2xl font-bold">{metrics.cites_per_patent.overall_avg.toFixed(1)}</span>
                                <div className="flex h-2 w-full mt-2 rounded-full overflow-hidden">
                                    <div
                                        className="bg-emerald-500 h-full"
                                        style={{ width: `${(metrics.cites_per_patent.by_phase.early / metrics.cites_per_patent.overall_avg) * 100}%` }}
                                        title="Early"
                                    />
                                    <div
                                        className="bg-blue-500 h-full"
                                        style={{ width: `${(metrics.cites_per_patent.by_phase.mid / metrics.cites_per_patent.overall_avg) * 100}%` }}
                                        title="Mid"
                                    />
                                    <div
                                        className="bg-amber-500 h-full"
                                        style={{ width: `${(metrics.cites_per_patent.by_phase.late / metrics.cites_per_patent.overall_avg) * 100}%` }}
                                        title="Late"
                                    />
                                </div>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </TooltipProvider>
        </div>
    )
}
