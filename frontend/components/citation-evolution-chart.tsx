"use client"

import { useState } from "react"
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import { Activity } from "lucide-react"

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
    const [showSplit, setShowSplit] = useState(false)

    // Custom tooltip to show breakdown
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
                            <div className="border-t border-border mt-2 pt-2 flex items-center justify-between gap-4">
                                <span className="font-semibold">Total:</span>
                                <span className="font-bold">
                                    {(payload.find((p: any) => p.dataKey === "early")?.value || 0) +
                                        (payload.find((p: any) => p.dataKey === "mid")?.value || 0) +
                                        (payload.find((p: any) => p.dataKey === "late")?.value || 0)}
                                </span>
                            </div>
                        </>
                    ) : (
                        <div className="flex items-center gap-2">
                            <span className="text-muted-foreground">Citations:</span>
                            <span className="font-bold">{payload[0].value}</span>
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
                            <Activity className="h-5 w-5 text-primary" />
                            Citation Evolution
                        </CardTitle>
                        <CardDescription>Yearly citation growth over patent lifecycle</CardDescription>
                    </div>
                    <div className="flex items-center space-x-2">
                        <Switch id="split-mode" checked={showSplit} onCheckedChange={setShowSplit} />
                        <Label htmlFor="split-mode">Split View</Label>
                    </div>
                </div>
            </CardHeader>
            <CardContent>
                <div className="h-[300px] w-full">
                    <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                            <defs>
                                <linearGradient id="colorTotal" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.3} />
                                    <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0} />
                                </linearGradient>
                                <linearGradient id="colorEarly" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                                    <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                                </linearGradient>
                                <linearGradient id="colorMid" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                                </linearGradient>
                                <linearGradient id="colorLate" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.3} />
                                    <stop offset="95%" stopColor="#f59e0b" stopOpacity={0} />
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} className="stroke-muted" />
                            <XAxis
                                dataKey="year"
                                tickLine={false}
                                axisLine={false}
                                tick={{ fontSize: 12 }}
                                tickMargin={10}
                            />
                            <YAxis
                                tickLine={false}
                                axisLine={false}
                                tick={{ fontSize: 12 }}
                                tickFormatter={(value) => `${value}`}
                            />
                            <Tooltip content={<CustomTooltip />} />

                            {showSplit ? (
                                <>
                                    <Area
                                        type="monotone"
                                        dataKey="late"
                                        stackId="1"
                                        stroke="#f59e0b"
                                        fill="url(#colorLate)"
                                        name="Late"
                                    />
                                    <Area
                                        type="monotone"
                                        dataKey="mid"
                                        stackId="1"
                                        stroke="#3b82f6"
                                        fill="url(#colorMid)"
                                        name="Mid"
                                    />
                                    <Area
                                        type="monotone"
                                        dataKey="early"
                                        stackId="1"
                                        stroke="#10b981"
                                        fill="url(#colorEarly)"
                                        name="Early"
                                    />
                                </>
                            ) : (
                                <Area
                                    type="monotone"
                                    dataKey="total"
                                    stroke="hsl(var(--primary))"
                                    fill="url(#colorTotal)"
                                    name="Total Citations"
                                    strokeWidth={2}
                                />
                            )}
                        </AreaChart>
                    </ResponsiveContainer>
                </div>
            </CardContent>
        </Card>
    )
}
