"use client"

import { useState, useEffect } from "react"
import {
    Area,
    ComposedChart,
    CartesianGrid,
    Line,
    ResponsiveContainer,
    Tooltip,
    XAxis,
    YAxis,
    Legend,
    ReferenceLine
} from "recharts"
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

interface CitationForecastChartProps {
    entityId: number
    entityType: "patent" | "portfolio"
    embedded?: boolean
    horizon?: "3y" | "5y"
}

const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
        const isForecast = payload.some((p: any) => p.dataKey === "low")
        const mainValue = payload.find((p: any) => p.dataKey === "cum_cites")

        return (
            <div className="bg-white p-3 border rounded shadow-lg text-sm z-50">
                <p className="font-bold mb-2">{label} {isForecast ? "(Forecast)" : "(Historical)"}</p>

                {mainValue && (
                    <div className="flex items-center gap-2 mb-1">
                        <div
                            className="w-3 h-3 rounded-full"
                            style={{ backgroundColor: mainValue.color }}
                        />
                        <span className="text-gray-600">Cumulative:</span>
                        <span className="font-mono font-medium">
                            {mainValue.value.toFixed(1)}
                        </span>
                    </div>
                )}

                {isForecast && payload[0].payload.low != null && (
                    <div className="mt-2 pt-2 border-t border-gray-100">
                        <p className="text-xs text-muted-foreground mb-1">80% Prediction Interval:</p>
                        <div className="font-mono font-medium text-xs">
                            {payload[0].payload.low.toFixed(1)} - {payload[0].payload.high?.toFixed(1)}
                        </div>
                    </div>
                )}
            </div>
        )
    }
    return null
}

export function CitationForecastChart({ entityId, entityType, embedded = false, horizon: controlledHorizon }: CitationForecastChartProps) {
    const [localHorizon, setLocalHorizon] = useState<"3y" | "5y">("3y")
    // Use controlled horizon if provided, otherwise local
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

    // Combine historical and forecast for rendering
    const chartData = [
        ...data.historical.map(d => ({ ...d, type: 'historical' })),
        // Skip the first forecast point if it overlaps exactly with last historical
        ...data.forecast.slice(1).map(d => ({ ...d, type: 'forecast' }))
    ]

    const historicalData = data.historical
    const forecastData = data.forecast
    const lastObservedYear = data.last_observed_year

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
                        {typeof data.prediction_summary.difficulty_bucket === 'string' && (
                            <Badge variant="outline" className="ml-auto">
                                {data.prediction_summary.difficulty_bucket} DIFFICULTY
                            </Badge>
                        )}
                    </div>
                )}

                <div className="h-[300px] w-full">
                    <ResponsiveContainer width="100%" height="100%">
                        <ComposedChart margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                            <defs>
                                <linearGradient id="colorHist" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#8884d8" stopOpacity={0.8} />
                                    <stop offset="95%" stopColor="#8884d8" stopOpacity={0.1} />
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} />
                            <XAxis
                                dataKey="year"
                                type="number"
                                domain={['auto', 'auto']}
                                tick={{ fontSize: 12, fill: "#6b7280" }}
                                tickCount={8}
                                axisLine={false}
                                tickLine={false}
                                allowDuplicatedCategory={false}
                            />
                            <YAxis
                                tick={{ fontSize: 12, fill: "#6b7280" }}
                                axisLine={false}
                                tickLine={false}
                            />
                            <Tooltip content={<CustomTooltip />} />
                            <Legend verticalAlign="top" height={36} />

                            {/* Historical Area */}
                            <Area
                                data={historicalData}
                                type="monotone"
                                dataKey="cum_cites"
                                name="Historical"
                                stroke="#8884d8"
                                fill="url(#colorHist)"
                                strokeWidth={2}
                            />

                            {/* Reference line for today */}
                            <ReferenceLine x={lastObservedYear} stroke="#666" strokeDasharray="3 3" label="Now" />

                            {/* Forecast Line */}
                            <Line
                                data={forecastData}
                                type="monotone"
                                dataKey="cum_cites"
                                name="Forecast (Exp)"
                                stroke="#10b981"
                                strokeWidth={2}
                                strokeDasharray="5 5"
                                dot={{ r: 3 }}
                            />

                            {/* Confidence Interval Lines (simplified visualization) */}
                            <Line
                                data={forecastData}
                                type="monotone"
                                dataKey="low"
                                name="Lower 80%"
                                stroke="#10b981"
                                strokeWidth={1}
                                strokeOpacity={0.5}
                                strokeDasharray="3 3"
                                dot={false}
                            />
                            <Line
                                data={forecastData}
                                type="monotone"
                                dataKey="high"
                                name="Upper 80%"
                                stroke="#10b981"
                                strokeWidth={1}
                                strokeOpacity={0.5}
                                strokeDasharray="3 3"
                                dot={false}
                            />
                        </ComposedChart>
                    </ResponsiveContainer>
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
