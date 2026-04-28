"use client"

import { useEffect, useState } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from "@/components/ui/tooltip"
import { Info, TrendingUp, Loader2, Users, HelpCircle } from "lucide-react"
import { DifficultyMixBar } from "@/components/difficulty-mix-bar"
import { CitationForecastChart } from "@/components/citation-forecast-chart"
import { ForecastSegmentPanel } from "@/components/forecast-segment-panel"
import { TopContributorsTable } from "@/components/top-contributors-table"
import { fetchJson, getPortfolioForecastUrl } from "@/lib/api"
import type { PortfolioForecastResponse } from "@/lib/types/forecast"

interface PortfolioForecastCardProps {
    ownerId: number
}

export function PortfolioForecastCard({ ownerId }: PortfolioForecastCardProps) {
    const [horizon, setHorizon] = useState<"3y" | "5y">("3y")
    const [data, setData] = useState<PortfolioForecastResponse | null>(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        let cancelled = false
        setLoading(true)
        setError(null)

        fetchJson<PortfolioForecastResponse>(
            getPortfolioForecastUrl(ownerId, horizon, { segments: true })
        )
            .then((res) => {
                if (!cancelled) setData(res)
            })
            .catch((err) => {
                if (!cancelled) setError(err.message || "Failed to load forecast")
            })
            .finally(() => {
                if (!cancelled) setLoading(false)
            })

        return () => { cancelled = true }
    }, [ownerId, horizon])

    return (
        <div className="space-y-4">
            <Card className="relative overflow-hidden">
                <CardContent className="p-5 space-y-4">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <TrendingUp className="h-4 w-4 text-muted-foreground" />
                            <span className="text-sm font-semibold text-muted-foreground flex items-center gap-1.5">
                                Portfolio Global Forward Citation Prediction
                                <Tooltip>
                                    <TooltipTrigger className="cursor-help">
                                        <HelpCircle className="h-4 w-4" />
                                    </TooltipTrigger>
                                    <TooltipContent className="max-w-sm">
                                        The model predicts the expected number of global forward citations
                                        that a patent (or patent family) will receive within a 3-year or 5-year horizon,
                                        measured from an as-of date defined as filing date + 2 years.
                                    </TooltipContent>
                                </Tooltip>
                            </span>
                        </div>

                        <Tabs value={horizon} onValueChange={(v) => setHorizon(v as "3y" | "5y")}>
                            <TabsList className="h-7">
                                <TabsTrigger value="3y" className="text-xs px-3 h-6">3 Year</TabsTrigger>
                                <TabsTrigger value="5y" className="text-xs px-3 h-6">5 Year</TabsTrigger>
                            </TabsList>
                        </Tabs>
                    </div>

                    {loading ? (
                        <div className="flex items-center justify-center py-8">
                            <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
                        </div>
                    ) : error ? (
                        <div className="text-sm text-destructive py-4">{error}</div>
                    ) : data ? (
                        <div className="space-y-5">
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                <div className="space-y-1">
                                    <div className="flex items-center gap-1 text-xs text-muted-foreground">
                                        Expected Total
                                        <TooltipProvider>
                                            <Tooltip>
                                                <TooltipTrigger className="cursor-help">
                                                    <HelpCircle className="h-3 w-3" />
                                                </TooltipTrigger>
                                                <TooltipContent>Total expected citations for all patents in the portfolio.</TooltipContent>
                                            </Tooltip>
                                        </TooltipProvider>
                                    </div>
                                    <div className="text-3xl font-bold tracking-tight">
                                        {data.portfolio_prediction.expected_citations_total.toFixed(1)}
                                    </div>
                                </div>

                                <div className="space-y-1">
                                    <div className="flex items-center gap-1 text-xs text-muted-foreground">
                                        Per Eff. Patent
                                        <TooltipProvider>
                                            <Tooltip>
                                                <TooltipTrigger className="cursor-help">
                                                    <HelpCircle className="h-3 w-3" />
                                                </TooltipTrigger>
                                                <TooltipContent>Average expected citations per effective patent (weighted by ownership share).</TooltipContent>
                                            </Tooltip>
                                        </TooltipProvider>
                                    </div>
                                    <div className="text-3xl font-bold tracking-tight">
                                        {data.portfolio_prediction.expected_per_effective_patent.toFixed(2)}
                                    </div>
                                </div>

                                <div className="space-y-1">
                                    <div className="flex items-center gap-1">
                                        <Users className="h-3 w-3 text-muted-foreground" />
                                        <span className="text-xs text-muted-foreground">Eff. Patents</span>
                                        <TooltipProvider>
                                            <Tooltip>
                                                <TooltipTrigger className="cursor-help">
                                                    <HelpCircle className="h-3 w-3 text-muted-foreground" />
                                                </TooltipTrigger>
                                                <TooltipContent>Sum of ownership shares across all patents in the portfolio.</TooltipContent>
                                            </Tooltip>
                                        </TooltipProvider>
                                    </div>
                                    <div className="text-3xl font-bold tracking-tight">
                                        {data.portfolio_prediction.n_patents_effective.toFixed(1)}
                                    </div>
                                </div>

                                <div className="space-y-1">
                                    <div className="flex items-center gap-1 text-xs text-muted-foreground">
                                        80% Interval
                                        <TooltipProvider>
                                            <Tooltip>
                                                <TooltipTrigger className="cursor-help">
                                                    <HelpCircle className="h-3 w-3" />
                                                </TooltipTrigger>
                                                <TooltipContent>Range within which the true citation count is expected to fall with 80% probability.</TooltipContent>
                                            </Tooltip>
                                        </TooltipProvider>
                                    </div>
                                    <div className="text-lg font-semibold">
                                        {data.portfolio_prediction.interval_80_total.low.toFixed(1)} — {data.portfolio_prediction.interval_80_total.high.toFixed(1)}
                                    </div>
                                </div>
                            </div>

                            <div className="flex items-center gap-4 text-xs text-muted-foreground">
                                <TooltipProvider>
                                    <Tooltip>
                                        <TooltipTrigger className="flex items-center gap-1">
                                            <Info className="h-3 w-3" />
                                            <span>as-of: {data.as_of_date}</span>
                                        </TooltipTrigger>
                                        <TooltipContent>
                                            <p className="max-w-xs text-xs">
                                                Latest as-of date among portfolio patents (filing + 2 years).
                                            </p>
                                        </TooltipContent>
                                    </Tooltip>
                                </TooltipProvider>
                                <Badge variant="secondary" className="text-[10px]">
                                    {data.meta.calibration}
                                </Badge>
                            </div>

                            <DifficultyMixBar mix={data.difficulty_mix} />

                            <div className="pt-4 border-t">
                                <h4 className="text-sm font-semibold mb-4 text-muted-foreground">Projected Growth</h4>
                                <CitationForecastChart
                                    entityId={ownerId}
                                    entityType="portfolio"
                                    embedded={true}
                                    horizon={horizon}
                                />
                            </div>
                        </div>
                    ) : null}
                </CardContent>
            </Card>

            {data && !loading && !error && (
                <>
                    <ForecastSegmentPanel segments={data.segments} />
                    <TopContributorsTable contributors={data.top_contributors} />
                </>
            )}
        </div>
    )
}
