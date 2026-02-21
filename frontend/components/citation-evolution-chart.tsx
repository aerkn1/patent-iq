"use client"

import { useState } from "react"
import { Area, ComposedChart, Line, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import { TrendingUp } from "lucide-react"
import { ChartTooltip } from "@/components/charts/ChartTooltip"
import { CHART_COLORS } from "@/lib/chart-config"

export interface CitationYearData {
    year: number
    total: number
    early: number
    mid: number
    late: number
}

interface CitationEvolutionChartProps {
    data: CitationYearData[]
}

export function CitationEvolutionChart({ data }: CitationEvolutionChartProps) {
    const [showYoY, setShowYoY] = useState(false)
    const [showSplit, setShowSplit] = useState(false)

    // Enrich data with YoY growth
    const enrichedData = data.map((item, index) => {
        const prev = data[index - 1]
        let yoy_growth = null
        if (prev && prev.total > 0) {
            yoy_growth = ((item.total - prev.total) / prev.total) * 100
        } else if (prev && prev.total === 0 && item.total > 0) {
            yoy_growth = 100 // Treat 0 to >0 as 100% growth for visualization cap
        }
        return { ...item, yoy_growth }
    })

    return (
        <Card>
            <CardHeader>
                <div className="flex items-center justify-between">
                    <div>
                        <CardTitle className="flex items-center gap-2">
                            <TrendingUp className="h-5 w-5 text-primary" />
                            Global Citation Dynamics
                        </CardTitle>
                        <CardDescription>
                            Annual citation impact and growth trajectory
                        </CardDescription>
                    </div>
                    <div className="flex items-center gap-4">
                        <div className="flex items-center gap-2">
                            <Switch id="split-mode" checked={showSplit} onCheckedChange={setShowSplit} />
                            <Label htmlFor="split-mode" className="text-xs">Split View</Label>
                        </div>
                        <div className="flex items-center gap-2">
                            <Switch id="show-yoy" checked={showYoY} onCheckedChange={setShowYoY} />
                            <Label htmlFor="show-yoy" className="text-xs">YoY %</Label>
                        </div>
                    </div>
                </div>
            </CardHeader>
            <CardContent>
                <div className="h-[350px] w-full">
                    <ResponsiveContainer width="100%" height="100%">
                        <ComposedChart data={enrichedData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                            <defs>
                                <linearGradient id="citationColorTotal" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor={CHART_COLORS.indigo} stopOpacity={0.8} />
                                    <stop offset="95%" stopColor={CHART_COLORS.indigo} stopOpacity={0.1} />
                                </linearGradient>
                                <linearGradient id="citationColorEarly" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor={CHART_COLORS.green} stopOpacity={0.8} />
                                    <stop offset="95%" stopColor={CHART_COLORS.green} stopOpacity={0.1} />
                                </linearGradient>
                                <linearGradient id="citationColorMid" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor={CHART_COLORS.blue} stopOpacity={0.8} />
                                    <stop offset="95%" stopColor={CHART_COLORS.blue} stopOpacity={0.1} />
                                </linearGradient>
                                <linearGradient id="citationColorLate" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor={CHART_COLORS.amber} stopOpacity={0.8} />
                                    <stop offset="95%" stopColor={CHART_COLORS.amber} stopOpacity={0.1} />
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} />
                            <XAxis
                                dataKey="year"
                                tick={{ fontSize: 12, fill: CHART_COLORS.gray }}
                                axisLine={false}
                                tickLine={false}
                            />
                            <YAxis
                                yAxisId="left"
                                tick={{ fontSize: 12, fill: CHART_COLORS.gray }}
                                axisLine={false}
                                tickLine={false}
                                label={{ value: 'Annual Citations', angle: -90, position: 'insideLeft', style: { textAnchor: 'middle', fill: CHART_COLORS.gray, fontSize: 12 } }}
                            />
                            {showYoY && (
                                <YAxis
                                    yAxisId="right"
                                    orientation="right"
                                    tick={{ fontSize: 12, fill: CHART_COLORS.red }}
                                    axisLine={false}
                                    tickLine={false}
                                    unit="%"
                                    domain={['auto', 'auto']}
                                />
                            )}
                            <Tooltip content={<ChartTooltip formatYoY />} />

                            {showSplit ? (
                                <>
                                    <Area yAxisId="left" type="monotone" dataKey="late" stackId="1" stroke={CHART_COLORS.amber} fill="url(#citationColorLate)" />
                                    <Area yAxisId="left" type="monotone" dataKey="mid" stackId="1" stroke={CHART_COLORS.blue} fill="url(#citationColorMid)" />
                                    <Area yAxisId="left" type="monotone" dataKey="early" stackId="1" stroke={CHART_COLORS.green} fill="url(#citationColorEarly)" />
                                </>
                            ) : (
                                <Area yAxisId="left" type="monotone" dataKey="total" stroke={CHART_COLORS.indigo} fill="url(#citationColorTotal)" strokeWidth={2} />
                            )}

                            {showYoY && (
                                <Line
                                    yAxisId="right"
                                    type="monotone"
                                    dataKey="yoy_growth"
                                    name="YoY Growth"
                                    stroke={CHART_COLORS.red}
                                    strokeWidth={2}
                                    dot={{ r: 3 }}
                                    strokeDasharray="5 5"
                                />
                            )}
                        </ComposedChart>
                    </ResponsiveContainer>
                </div>
            </CardContent>
        </Card>
    )
}
