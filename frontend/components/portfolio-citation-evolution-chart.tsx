"use client"

import { useState } from "react"
import {
    Area,
    AreaChart,
    CartesianGrid,
    ComposedChart,
    Line,
    ResponsiveContainer,
    Tooltip,
    XAxis,
    YAxis,
    Legend
} from "recharts"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import { TrendingUp } from "lucide-react"
import { ChartTooltip } from "@/components/charts/ChartTooltip"
import { CHART_COLORS } from "@/lib/chart-config"

export interface PortfolioCitationYearData {
    year: string
    total_cites: number
    avg_cites_per_patent: number
    early_cites: number
    mid_cites: number
    late_cites: number
    yoy_growth: number | null
}

interface PortfolioCitationEvolutionChartProps {
    data: PortfolioCitationYearData[]
}


export function PortfolioCitationEvolutionChart({ data }: PortfolioCitationEvolutionChartProps) {
    const [showYoY, setShowYoY] = useState(false)

    // Calculate some summary stats for the header
    const latestYear = data[data.length - 1]
    const trend = data.length > 2
        ? (data[data.length - 1].avg_cites_per_patent - data[data.length - 2].avg_cites_per_patent)
        : 0

    return (
        <Card>
            <CardHeader>
                <div className="flex items-center justify-between">
                    <div>
                        <CardTitle className="flex items-center gap-2">
                            <TrendingUp className="h-5 w-5 text-primary" />
                            Global Portfolio Citation Evolution
                        </CardTitle>
                        <CardDescription>
                            Average citations per patent over time
                        </CardDescription>
                    </div>
                    <div className="flex items-center gap-6">
                        <div className="flex items-center gap-2">
                            <Switch
                                id="show-yoy"
                                checked={showYoY}
                                onCheckedChange={setShowYoY}
                            />
                            <Label htmlFor="show-yoy" className="text-sm font-medium">
                                Show YoY %
                            </Label>
                        </div>
                    </div>
                </div>
            </CardHeader>
            <CardContent>
                <div className="h-[350px] w-full">
                    <ResponsiveContainer width="100%" height="100%">
                        <ComposedChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                            <defs>
                                <linearGradient id="portfolioColorTotal" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor={CHART_COLORS.indigo} stopOpacity={0.8} />
                                    <stop offset="95%" stopColor={CHART_COLORS.indigo} stopOpacity={0.1} />
                                </linearGradient>
                                <linearGradient id="portfolioColorEarly" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor={CHART_COLORS.green} stopOpacity={0.8} />
                                    <stop offset="95%" stopColor={CHART_COLORS.green} stopOpacity={0.1} />
                                </linearGradient>
                                <linearGradient id="portfolioColorMid" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor={CHART_COLORS.blue} stopOpacity={0.8} />
                                    <stop offset="95%" stopColor={CHART_COLORS.blue} stopOpacity={0.1} />
                                </linearGradient>
                                <linearGradient id="portfolioColorLate" x1="0" y1="0" x2="0" y2="1">
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
                                label={{ value: 'Citations per Patent', angle: -90, position: 'insideLeft', style: { textAnchor: 'middle', fill: CHART_COLORS.gray, fontSize: 12 } }}
                            />
                            {showYoY && (
                                <YAxis
                                    yAxisId="right"
                                    orientation="right"
                                    tick={{ fontSize: 12, fill: CHART_COLORS.red }}
                                    axisLine={false}
                                    tickLine={false}
                                    unit="%"
                                    label={{ value: 'YoY Growth', angle: 90, position: 'insideRight', style: { textAnchor: 'middle', fill: CHART_COLORS.red, fontSize: 12 } }}
                                />
                            )}
                            <Tooltip content={<ChartTooltip formatYoY />} />
                            <Legend verticalAlign="top" height={36} />

                            <Area
                                yAxisId="left"
                                type="monotone"
                                dataKey="avg_cites_per_patent"
                                name="Avg. Cites/Patent"
                                stroke={CHART_COLORS.indigo}
                                fill="url(#portfolioColorTotal)"
                                strokeWidth={2}
                            />

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
