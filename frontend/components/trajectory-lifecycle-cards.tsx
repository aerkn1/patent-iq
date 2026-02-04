"use client"

import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { Progress } from "@/components/ui/progress"
import { Info, TrendingUp, TrendingDown, Minus, Clock, Calendar, Leaf, Zap, Award } from "lucide-react"

export interface LifecycleMetrics {
    trajectory: {
        score: number
        label: "Rising" | "Flat" | "Falling"
    }
    durability: {
        score: number
        spanYears: number
    }
    sustainability: {
        score: number
        isSustaining: boolean
    }
    timing: {
        score: number
        class: "EARLY" | "MID" | "LATE"
    }
    peakAge: number
    totalCitations: number
}

interface TrajectoryLifecycleCardsProps {
    metrics: LifecycleMetrics
}

export function TrajectoryLifecycleCards({ metrics }: TrajectoryLifecycleCardsProps) {
    const getTrajectoryIcon = (label: string) => {
        switch (label) {
            case "Rising": return <TrendingUp className="h-4 w-4 text-emerald-500" />
            case "Falling": return <TrendingDown className="h-4 w-4 text-rose-500" />
            default: return <Minus className="h-4 w-4 text-gray-500" />
        }
    }

    const getTrajectoryColor = (label: string) => {
        switch (label) {
            case "Rising": return "text-emerald-500 bg-emerald-50 border-emerald-200"
            case "Falling": return "text-rose-500 bg-rose-50 border-rose-200"
            default: return "text-gray-500 bg-gray-50 border-gray-200"
        }
    }

    return (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            {/* 1. Trajectory Score */}
            <TooltipProvider>
                <Card>
                    <CardContent className="p-4 flex flex-col justify-between h-full">
                        <div className="space-y-2">
                            <div className="flex items-center justify-between text-muted-foreground">
                                <span className="text-xs font-medium">Trajectory</span>
                                <Tooltip>
                                    <TooltipTrigger>
                                        <Info className="h-3.5 w-3.5 cursor-help" />
                                    </TooltipTrigger>
                                    <TooltipContent side="top">
                                        Citation growth momentum (0-100). Indicates if interest is rising, flat, or falling.
                                    </TooltipContent>
                                </Tooltip>
                            </div>
                            <div className="flex items-center gap-2">
                                <span className="text-2xl font-bold">{metrics.trajectory.score}</span>
                                <Badge variant="outline" className={`text-[10px] px-1 py-0 h-5 gap-1 ${getTrajectoryColor(metrics.trajectory.label)}`}>
                                    {getTrajectoryIcon(metrics.trajectory.label)}
                                    {metrics.trajectory.label}
                                </Badge>
                            </div>
                        </div>
                        <Progress value={metrics.trajectory.score} className="h-1 mt-3" />
                    </CardContent>
                </Card>
            </TooltipProvider>

            {/* 2. Durability */}
            <TooltipProvider>
                <Card>
                    <CardContent className="p-4 flex flex-col justify-between h-full">
                        <div className="space-y-2">
                            <div className="flex items-center justify-between text-muted-foreground">
                                <span className="text-xs font-medium">Durability</span>
                                <Tooltip>
                                    <TooltipTrigger>
                                        <Info className="h-3.5 w-3.5 cursor-help" />
                                    </TooltipTrigger>
                                    <TooltipContent side="top">
                                        Longevity of citation interest. Higher scores indicate long-lasting relevance.
                                    </TooltipContent>
                                </Tooltip>
                            </div>
                            <div className="flex items-center gap-2">
                                <span className="text-2xl font-bold">{metrics.durability.score}</span>
                            </div>
                            <div className="flex items-center gap-1 text-xs text-muted-foreground">
                                <Clock className="h-3 w-3" />
                                <span>{metrics.durability.spanYears} year span</span>
                            </div>
                        </div>
                        <Progress value={metrics.durability.score} className="h-1 mt-3" />
                    </CardContent>
                </Card>
            </TooltipProvider>

            {/* 3. Sustainability */}
            <TooltipProvider>
                <Card>
                    <CardContent className="p-4 flex flex-col justify-between h-full">
                        <div className="space-y-2">
                            <div className="flex items-center justify-between text-muted-foreground">
                                <span className="text-xs font-medium">Sustainability</span>
                                <Tooltip>
                                    <TooltipTrigger>
                                        <Info className="h-3.5 w-3.5 cursor-help" />
                                    </TooltipTrigger>
                                    <TooltipContent side="top">
                                        Stability of citation inflow over time.
                                    </TooltipContent>
                                </Tooltip>
                            </div>
                            <div className="flex items-center gap-2">
                                <span className="text-2xl font-bold">{metrics.sustainability.score}</span>
                                {metrics.sustainability.isSustaining ? (
                                    <Badge variant="outline" className="text-[10px] px-1 py-0 h-5 bg-green-50 text-green-700 border-green-200">
                                        Sustaining
                                    </Badge>
                                ) : (
                                    <Badge variant="outline" className="text-[10px] px-1 py-0 h-5 bg-gray-50 text-gray-700 border-gray-200">
                                        Normal
                                    </Badge>
                                )}
                            </div>
                        </div>
                        <Progress value={metrics.sustainability.score} className="h-1 mt-3" />
                    </CardContent>
                </Card>
            </TooltipProvider>

            {/* 4. Strategic Timing */}
            <TooltipProvider>
                <Card>
                    <CardContent className="p-4 flex flex-col justify-between h-full">
                        <div className="space-y-2">
                            <div className="flex items-center justify-between text-muted-foreground">
                                <span className="text-xs font-medium">Strat. Timing</span>
                                <Tooltip>
                                    <TooltipTrigger>
                                        <Info className="h-3.5 w-3.5 cursor-help" />
                                    </TooltipTrigger>
                                    <TooltipContent side="top">
                                        Timing of citations relative to technology cycle (Early, Mid, Late).
                                    </TooltipContent>
                                </Tooltip>
                            </div>
                            <div className="flex items-center gap-2">
                                <span className="text-2xl font-bold">{metrics.timing.score}</span>
                                <Badge variant="outline" className="text-[10px] px-1 py-0 h-5">
                                    {metrics.timing.class}
                                </Badge>
                            </div>
                        </div>
                        <Progress value={metrics.timing.score} className="h-1 mt-3" />
                    </CardContent>
                </Card>
            </TooltipProvider>

            {/* 5. Peak Age */}
            <TooltipProvider>
                <Card>
                    <CardContent className="p-4 flex flex-col justify-between h-full">
                        <div className="space-y-2">
                            <div className="flex items-center justify-between text-muted-foreground">
                                <span className="text-xs font-medium">Peak Age</span>
                                <Tooltip>
                                    <TooltipTrigger>
                                        <Info className="h-3.5 w-3.5 cursor-help" />
                                    </TooltipTrigger>
                                    <TooltipContent side="top">
                                        Years after filing when citations peaked.
                                    </TooltipContent>
                                </Tooltip>
                            </div>
                            <div className="flex items-center gap-2">
                                <span className="text-2xl font-bold">{metrics.peakAge}</span>
                                <span className="text-sm text-muted-foreground">years</span>
                            </div>
                            <div className="flex items-center gap-1 text-xs text-muted-foreground">
                                <Calendar className="h-3 w-3" />
                                <span>Post-filing</span>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </TooltipProvider>

            {/* 6. Total Citations */}
            <TooltipProvider>
                <Card>
                    <CardContent className="p-4 flex flex-col justify-between h-full">
                        <div className="space-y-2">
                            <div className="flex items-center justify-between text-muted-foreground">
                                <span className="text-xs font-medium">Total Cites</span>
                                <Tooltip>
                                    <TooltipTrigger>
                                        <Info className="h-3.5 w-3.5 cursor-help" />
                                    </TooltipTrigger>
                                    <TooltipContent side="top">
                                        Total forward citations count.
                                    </TooltipContent>
                                </Tooltip>
                            </div>
                            <div className="text-2xl font-bold text-primary">{metrics.totalCitations}</div>
                            <div className="flex items-center gap-1 text-xs text-muted-foreground">
                                <Award className="h-3 w-3" />
                                <span>Lifetime</span>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </TooltipProvider>
        </div>
    )
}
