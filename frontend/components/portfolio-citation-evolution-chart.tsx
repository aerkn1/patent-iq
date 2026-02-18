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
import { Badge } from "@/components/ui/badge"
import { TrendingUp, Layers } from "lucide-react"

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

const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
        return (
            <div className="bg-white p-3 border rounded shadow-lg text-sm">
                <p className="font-bold mb-2">{label}</p>
                {payload.map((entry: any, index: number) => (
                    <div key={index} className="flex items-center gap-2 mb-1">
                        <div
                            className="w-3 h-3 rounded-full"
                            style={{ backgroundColor: entry.color }}
                        />
                        <span className="text-gray-600 capitalize">
                            {entry.name.replace(/_/g, ' ')}:
                        </span>
                        <span className="font-mono font-medium">
                            {entry.value !== null ?
                                (entry.name === "yoy_growth" ? `${entry.value.toFixed(1)}%` : entry.value.toFixed(2))
                                : "N/A"}
                        </span>
                    </div>
                ))}
            </div>
        )
    }
    return null
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
                                <linearGradient id="colorTotal" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#8884d8" stopOpacity={0.8} />
                                    <stop offset="95%" stopColor="#8884d8" stopOpacity={0.1} />
                                </linearGradient>
                                <linearGradient id="colorEarly" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.8} />
                                    <stop offset="95%" stopColor="#10b981" stopOpacity={0.1} />
                                </linearGradient>
                                <linearGradient id="colorMid" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8} />
                                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.1} />
                                </linearGradient>
                                <linearGradient id="colorLate" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.8} />
                                    <stop offset="95%" stopColor="#f59e0b" stopOpacity={0.1} />
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} />
                            <XAxis
                                dataKey="year"
                                tick={{ fontSize: 12, fill: "#6b7280" }}
                                axisLine={false}
                                tickLine={false}
                            />
                            <YAxis
                                yAxisId="left"
                                tick={{ fontSize: 12, fill: "#6b7280" }}
                                axisLine={false}
                                tickLine={false}
                                label={{ value: 'Citations per Patent', angle: -90, position: 'insideLeft', style: { textAnchor: 'middle', fill: '#6b7280', fontSize: 12 } }}
                            />
                            {showYoY && (
                                <YAxis
                                    yAxisId="right"
                                    orientation="right"
                                    tick={{ fontSize: 12, fill: "#ef4444" }}
                                    axisLine={false}
                                    tickLine={false}
                                    unit="%"
                                    label={{ value: 'YoY Growth', angle: 90, position: 'insideRight', style: { textAnchor: 'middle', fill: '#ef4444', fontSize: 12 } }}
                                />
                            )}
                            <Tooltip content={<CustomTooltip />} />
                            <Legend verticalAlign="top" height={36} />

                            <Area
                                yAxisId="left"
                                type="monotone"
                                dataKey="avg_cites_per_patent"
                                name="Avg. Cites/Patent"
                                stroke="#8884d8"
                                fill="url(#colorTotal)"
                                strokeWidth={2}
                            />

                            {showYoY && (
                                <Line
                                    yAxisId="right"
                                    type="monotone"
                                    dataKey="yoy_growth"
                                    name="YoY Growth"
                                    stroke="#ef4444"
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
