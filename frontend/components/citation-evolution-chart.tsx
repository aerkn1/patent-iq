"use client"

import { useState } from "react"
import { Area, ComposedChart, Line, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import { TrendingUp } from "lucide-react"

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

    // Custom tooltip
    const CustomTooltip = ({ active, payload, label }: any) => {
        if (active && payload && payload.length) {
            return (
                <div className="bg-background border border-border p-3 rounded-lg shadow-lg text-sm">
                    <div className="font-bold mb-2">{label}</div>
                    {showSplit ? (
                        <>
                            <div className="flex items-center gap-2 mb-1">
                                <div className="w-2 h-2 rounded-full bg-emerald-500" />
                                <span className="text-muted-foreground">Early:</span>
                                <span className="font-mono font-medium">{payload.find((p: any) => p.dataKey === "early")?.value || 0}</span>
                            </div>
                            <div className="flex items-center gap-2 mb-1">
                                <div className="w-2 h-2 rounded-full bg-blue-500" />
                                <span className="text-muted-foreground">Mid:</span>
                                <span className="font-mono font-medium">{payload.find((p: any) => p.dataKey === "mid")?.value || 0}</span>
                            </div>
                            <div className="flex items-center gap-2 mb-1">
                                <div className="w-2 h-2 rounded-full bg-amber-500" />
                                <span className="text-muted-foreground">Late:</span>
                                <span className="font-mono font-medium">{payload.find((p: any) => p.dataKey === "late")?.value || 0}</span>
                            </div>
                        </>
                    ) : (
                        <div className="flex items-center gap-2 mb-1">
                            <div className="w-2 h-2 rounded-full" style={{ backgroundColor: payload[0].color }} />
                            <span className="text-muted-foreground">Citations:</span>
                            <span className="font-mono font-medium">{payload.find((p: any) => p.dataKey === "total")?.value || 0}</span>
                        </div>
                    )}
                    {showYoY && (
                        <div className="flex items-center gap-2 mt-2 pt-2 border-t border-border">
                            <div className="w-2 h-2 rounded-full bg-red-500" />
                            <span className="text-muted-foreground">YoY Growth:</span>
                            <span className="font-mono font-medium">
                                {payload.find((p: any) => p.dataKey === "yoy_growth")?.value?.toFixed(1) || "0.0"}%
                            </span>
                        </div>
                    )}
                </div>
            )
        }
        return null
    }

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
                                label={{ value: 'Annual Citations', angle: -90, position: 'insideLeft', style: { textAnchor: 'middle', fill: '#6b7280', fontSize: 12 } }}
                            />
                            {showYoY && (
                                <YAxis
                                    yAxisId="right"
                                    orientation="right"
                                    tick={{ fontSize: 12, fill: "#ef4444" }}
                                    axisLine={false}
                                    tickLine={false}
                                    unit="%"
                                    domain={['auto', 'auto']}
                                />
                            )}
                            <Tooltip content={<CustomTooltip />} />

                            {showSplit ? (
                                <>
                                    <Area yAxisId="left" type="monotone" dataKey="late" stackId="1" stroke="#f59e0b" fill="url(#colorLate)" />
                                    <Area yAxisId="left" type="monotone" dataKey="mid" stackId="1" stroke="#3b82f6" fill="url(#colorMid)" />
                                    <Area yAxisId="left" type="monotone" dataKey="early" stackId="1" stroke="#10b981" fill="url(#colorEarly)" />
                                </>
                            ) : (
                                <Area yAxisId="left" type="monotone" dataKey="total" stroke="#8884d8" fill="url(#colorTotal)" strokeWidth={2} />
                            )}

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
