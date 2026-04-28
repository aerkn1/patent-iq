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
import { Info, TrendingUp, Loader2, HelpCircle } from "lucide-react"
import { UncertaintyBar } from "@/components/uncertainty-bar"
import { CitationForecastChart } from "@/components/citation-forecast-chart"
import { ModelTransparencyAccordion } from "@/components/model-transparency-accordion"
import { fetchJson, getPatentForecastUrl } from "@/lib/api"
import type { PatentForecastResponse, DifficultyBucket } from "@/lib/types/forecast"

const BUCKET_STYLES: Record<DifficultyBucket, string> = {
    LOW: "bg-emerald-100 text-emerald-700 border-emerald-200",
    MID: "bg-amber-100 text-amber-700 border-amber-200",
    HIGH: "bg-rose-100 text-rose-700 border-rose-200",
}

const BUCKET_LABELS: Record<DifficultyBucket, string> = {
    LOW: "Easy to predict",
    MID: "Moderate",
    HIGH: "Hard to predict",
}

interface ForecastCardProps {
    applnId: number
}

export function ForecastCard({ applnId }: ForecastCardProps) {
    const [horizon, setHorizon] = useState<"3y" | "5y">("3y")
    const [data, setData] = useState<PatentForecastResponse | null>(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        let cancelled = false
        setLoading(true)
        setError(null)

        fetchJson<PatentForecastResponse>(getPatentForecastUrl(applnId, horizon))
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
    }, [applnId, horizon])

    return (
        <Card className="relative overflow-hidden">
            <CardContent className="p-5 space-y-4">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <TrendingUp className="h-4 w-4 text-muted-foreground" />
                        <TooltipProvider>
                            <span className="text-sm font-semibold text-muted-foreground flex items-center gap-1.5">
                                Patent Global Forward Citation Prediction
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
                        </TooltipProvider>
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
                    <div className="space-y-4">
                        <div className="flex items-end gap-3">
                            <div className="flex items-center gap-1">
                                <span className="text-4xl font-bold tracking-tight">
                                    {data.prediction.expected_citations.toFixed(1)}
                                </span>
                                <TooltipProvider>
                                    <Tooltip>
                                        <TooltipTrigger className="cursor-help mb-1">
                                            <HelpCircle className="h-4 w-4 text-muted-foreground" />
                                        </TooltipTrigger>
                                        <TooltipContent>Expected number of future citations.</TooltipContent>
                                    </Tooltip>
                                </TooltipProvider>
                            </div>
                            <span className="text-sm text-muted-foreground mb-1">
                                expected citations
                            </span>
                        </div>


                        <TooltipProvider>
                            <Tooltip>
                                <TooltipTrigger>
                                    <Badge
                                        variant="outline"
                                        className={`text-xs ${BUCKET_STYLES[data.prediction.difficulty_bucket]}`}
                                    >
                                        {data.prediction.difficulty_bucket} — {BUCKET_LABELS[data.prediction.difficulty_bucket]}
                                    </Badge>
                                </TooltipTrigger>
                                <TooltipContent>
                                    <p className="max-w-xs text-xs">
                                        Difficulty bucket indicates how predictable this patent&apos;s citations are.
                                        LOW = narrow confidence interval, HIGH = wider interval.
                                    </p>
                                </TooltipContent>
                            </Tooltip>
                        </TooltipProvider>


                        <TooltipProvider>
                            <Tooltip>
                                <TooltipTrigger className="w-full cursor-help">
                                    <UncertaintyBar
                                        low={data.prediction.interval_80.low}
                                        expected={data.prediction.expected_citations}
                                        high={data.prediction.interval_80.high}
                                        bucket={data.prediction.difficulty_bucket}
                                    />
                                </TooltipTrigger>
                                <TooltipContent>
                                    <p className="text-xs">
                                        80% prediction interval: [{data.prediction.interval_80.low.toFixed(1)}, {data.prediction.interval_80.high.toFixed(1)}]
                                    </p>
                                </TooltipContent>
                            </Tooltip>
                        </TooltipProvider>


                        <div className="flex items-center gap-4 text-xs text-muted-foreground">
                            <TooltipProvider>
                                <Tooltip>
                                    <TooltipTrigger className="flex items-center gap-1">
                                        <Info className="h-3 w-3" />
                                        <span>as-of: {data.as_of_date}</span>
                                    </TooltipTrigger>
                                    <TooltipContent>
                                        <p className="max-w-xs text-xs">
                                            Forecast baseline date (filing + 2 years). Only citations before
                                            this date are used as features.
                                        </p>
                                    </TooltipContent>
                                </Tooltip>
                            </TooltipProvider>
                            <span>filed: {data.filing_date}</span>
                        </div>

                        <div className="pt-4 border-t">
                            <h4 className="text-sm font-semibold mb-4 text-muted-foreground">Projected Growth</h4>
                            <CitationForecastChart
                                entityId={applnId}
                                entityType="patent"
                                embedded={true}
                                horizon={horizon}
                            />
                        </div>

                        {/* Model transparency */}
                        <ModelTransparencyAccordion
                            featuresUsed={data.features_used}
                            meta={data.meta}
                        />
                    </div>
                ) : null}
            </CardContent>
        </Card>
    )
}
