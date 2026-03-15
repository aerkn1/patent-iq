"use client"

import { useState, useEffect } from "react"
import { ResponsiveLine } from "@nivo/line"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import { Loader2, TrendingUp, AlertCircle } from "lucide-react"
import {
    getPatentCitationForecastTsUrl,
    getPortfolioCitationForecastTsUrl,
    fetchJson
} from "@/lib/api"
import { CitationForecastTimeSeriesResponse } from "@/lib/types/forecast"
import { getNivoTheme } from "@/lib/nivo-theme"

interface CitationForecastChartProps {
    entityId: number
    entityType: "patent" | "portfolio"
    embedded?: boolean
    horizon?: "3y" | "5y"
}

export function CitationForecastChart({ entityId, entityType, embedded = false, horizon: controlledHorizon }: CitationForecastChartProps) {
    const [localHorizon, setLocalHorizon] = useState<"3y" | "5y">("3y")
    const horizon = controlledHorizon ?? localHorizon

    const [data, setData] = useState<CitationForecastTimeSeriesResponse | null>(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        let mounted = true

        async function load() {
            try {
                setLoading(true)
                setError(null)

                const url = entityType === "patent"
                    ? getPatentCitationForecastTsUrl(entityId, horizon)
                    : getPortfolioCitationForecastTsUrl(entityId, horizon)

                const res = await fetchJson<CitationForecastTimeSeriesResponse>(url)

                if (mounted) {
                    setData(res)
                }
            } catch (err) {
                if (mounted) {
                    console.error("Failed to load forecast timeseries", err)
                    setError("Failed to load forecast data")
                }
            } finally {
                if (mounted) {
                    setLoading(false)
                }
            }
        }

        load()

        return () => {
            mounted = false
        }
    }, [entityId, entityType, horizon])

    if (error) {
        if (embedded) {
            return <div className="p-4 text-center text-sm text-destructive">{error}</div>
        }
        return (
            <Card>
                <CardContent className="flex flex-col items-center justify-center py-10 text-muted-foreground">
                    <AlertCircle className="h-8 w-8 mb-2 opacity-50" />
                    <p>{error}</p>
                </CardContent>
            </Card>
        )
    }

    if (loading && !data) {
        if (embedded) {
            return (
                <div className="flex items-center justify-center py-12">
                    <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                </div>
            )
        }
        return (
            <Card>
                <CardContent className="flex items-center justify-center py-20">
                    <Loader2 className="h-8 w-8 animate-spin text-primary" />
                </CardContent>
            </Card>
        )
    }

    if (!data) return null

    const historicalData = data.historical
    const forecastData = data.forecast
    const lastObservedYear = data.last_observed_year

    const nivoSeries = [
        {
            id: "Historical",
            color: "#8884d8",
            data: historicalData.map((d) => ({ x: d.year, y: d.cum_cites })),
        },
        {
            id: "Forecast",
            color: "#10b981",
            data: forecastData.map((d) => ({ x: d.year, y: d.cum_cites })),
        },
        {
            id: "Upper 80%",
            color: "#10b981",
            data: forecastData.map((d) => ({ x: d.year, y: d.high ?? d.cum_cites })),
        },
        {
            id: "Lower 80%",
            color: "#10b981",
            data: forecastData.map((d) => ({ x: d.year, y: d.low ?? d.cum_cites })),
        },
    ]

    const ConfidenceBandLayer = ({ series, xScale, yScale }: any) => {
        const upper = series.find((s: any) => s.id === "Upper 80%")?.data ?? []
        const lower = series.find((s: any) => s.id === "Lower 80%")?.data ?? []
        if (!upper.length || !lower.length) return null
        const points = [
            ...upper.map((d: any) => `${xScale(d.data.x)},${yScale(d.data.y)}`),
            ...lower.slice().reverse().map((d: any) => `${xScale(d.data.x)},${yScale(d.data.y)}`),
        ]
        return <polygon points={points.join(" ")} fill="#10b981" fillOpacity={0.1} />
    }

    const ForecastLinesLayer = ({ series, lineGenerator, xScale, yScale }: any) => (
        <g>
            {series
                .map((s: any) => (
                    <path
                        key={s.id}
                        d={lineGenerator(
                            s.data.map((d: any) => ({ x: xScale(d.data.x), y: yScale(d.data.y) }))
                        )}
                        fill="none"
                        stroke={s.color}
                        strokeWidth={s.id === "Historical" || s.id === "Forecast" ? 2 : 1}
                        strokeOpacity={s.id === "Historical" || s.id === "Forecast" ? 1 : 0.4}
                        strokeDasharray={s.id === "Historical" ? undefined : "5 5"}
                    />
                ))}
        </g>
    )

    const NowLineLayer = ({ xScale, innerHeight }: any) => (
        <g>
            <line
                x1={xScale(lastObservedYear)} x2={xScale(lastObservedYear)}
                y1={0} y2={innerHeight}
                stroke="#666" strokeDasharray="3 3"
            />
            <text x={xScale(lastObservedYear) + 4} y={-6} fontSize={11} fill="#666">Now</text>
        </g>
    )

    const Content = (
        <>
            {!embedded && (
                <CardHeader>
                    <div className="flex items-center justify-between">
                        <div>
                            <CardTitle className="flex items-center gap-2">
                                <TrendingUp className="h-5 w-5 text-primary" />
                                Citation Forecast
                            </CardTitle>
                            <CardDescription>
                                Projected cumulative growth ({horizon} horizon)
                            </CardDescription>
                        </div>
                        <Tabs value={horizon} onValueChange={(v) => setLocalHorizon(v as "3y" | "5y")}>
                            <TabsList>
                                <TabsTrigger value="3y">3 Years</TabsTrigger>
                                <TabsTrigger value="5y">5 Years</TabsTrigger>
                            </TabsList>
                        </Tabs>
                    </div>
                </CardHeader>
            )}
            <div className={embedded ? "mt-6" : "p-6 pt-0"}>
                {!embedded && (
                    <div className="mb-6 flex items-center gap-4 text-sm">
                        <div className="flex items-baseline gap-2">
                            <span className="text-muted-foreground">Expected Additional:</span>
                            <span className="font-bold text-lg">
                                +{data.prediction_summary.expected_additional.toFixed(1)}
                            </span>
                        </div>
                        <div className="hidden sm:flex items-baseline gap-2">
                            <span className="text-muted-foreground">80% Interval:</span>
                            <span className="font-mono">
                                [{data.prediction_summary.interval_80.low.toFixed(1)} - {data.prediction_summary.interval_80.high.toFixed(1)}]
                            </span>
                        </div>
                        {typeof data.prediction_summary.difficulty_bucket === "string" && (
                            <Badge variant="outline" className="ml-auto">
                                {data.prediction_summary.difficulty_bucket} DIFFICULTY
                            </Badge>
                        )}
                    </div>
                )}

                <div className="h-[300px] w-full">
                    <ResponsiveLine
                        data={nivoSeries}
                        theme={getNivoTheme()}
                        colors={["#8884d8", "#10b981", "#10b981", "#10b981"]}
                        margin={{ top: 20, right: 10, bottom: 40, left: 45 }}
                        xScale={{ type: "linear", min: "auto", max: "auto" }}
                        yScale={{ type: "linear", min: 0, max: "auto" }}
                        enableArea={false}
                        axisBottom={{
                            tickSize: 0,
                            tickPadding: 8,
                        }}
                        axisLeft={{
                            tickSize: 0,
                            tickPadding: 8,
                        }}
                        enablePoints={false}
                        enableGridX={false}
                        curve="monotoneX"
                        layers={[
                            "grid",
                            "axes",
                            "areas",
                            ConfidenceBandLayer,
                            ForecastLinesLayer,
                            NowLineLayer,
                            "points",
                            "slices",
                            "mesh",
                            "legends",
                        ]}
                        tooltip={({ point }) => (
                            <div className="bg-background border border-border p-2 rounded-lg text-xs shadow">
                                <span className="font-semibold">{point.seriesId}</span>
                                {" · "}
                                <span>{String(point.data.x)}: {Number(point.data.y).toFixed(1)}</span>
                            </div>
                        )}
                    />
                </div>
            </div>
        </>
    )

    if (embedded) {
        return Content
    }

    return (
        <Card>
            {Content}
        </Card>
    )
}
