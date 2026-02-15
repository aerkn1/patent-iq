"use client"

import { useMemo } from "react"
import {
    Area,
    AreaChart,
    CartesianGrid,
    ResponsiveContainer,
    Tooltip,
    XAxis,
    YAxis,
    ReferenceLine,
    Label,
} from "recharts"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

interface DistributionChartProps {
    zScore: number
    percentile: number
    title?: string
    description?: string
}

export function DistributionChart({
    zScore,
    percentile,
    title = "Peer Group Distribution",
    description = "Your portfolio vs. peer group (Normal Distribution)",
}: DistributionChartProps) {
    // Generate data points for a standard normal distribution (mean=0, std=1)
    const data = useMemo(() => {
        const points = []
        // Range from -3.5 to +3.5 covers 99.9% of the distribution
        for (let x = -3.5; x <= 3.5; x += 0.1) {
            // Normal distribution PDF formula: (1 / sqrt(2*pi)) * e^(-0.5 * x^2)
            // We scale it for better visualization
            const y = (1 / Math.sqrt(2 * Math.PI)) * Math.exp(-0.5 * x * x)
            points.push({ x, y })
        }
        return points
    }, [])

    // Clamp zScore to visible range for the chart, but display real value
    const clampedZScore = Math.max(-3.5, Math.min(3.5, zScore))

    return (
        <Card>
            <CardHeader>
                <CardTitle>{title}</CardTitle>
                <CardDescription>{description}</CardDescription>
            </CardHeader>
            <CardContent>
                <div className="h-[250px] w-full">
                    <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={data} margin={{ top: 20, right: 20, left: 20, bottom: 20 }}>
                            <defs>
                                <linearGradient id="colorY" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#8884d8" stopOpacity={0.8} />
                                    <stop offset="95%" stopColor="#8884d8" stopOpacity={0} />
                                </linearGradient>
                            </defs>
                            <XAxis
                                dataKey="x"
                                type="number"
                                domain={[-3.5, 3.5]}
                                tickFormatter={(val) => {
                                    if (val === 0) return "Avg"
                                    return val > 0 ? `+${val}σ` : `${val}σ`
                                }}
                                tickCount={7}
                            />
                            <YAxis hide />
                            <Tooltip
                                cursor={{ strokeDasharray: "3 3" }}
                                content={({ active, payload }) => {
                                    if (active && payload && payload.length) {
                                        const dataPoint = payload[0].payload
                                        return (
                                            <div className="rounded-lg border bg-background p-2 shadow-sm">
                                                <div className="grid grid-cols-2 gap-2">
                                                    <span className="font-medium">Deviation:</span>
                                                    <span className="text-muted-foreground">
                                                        {dataPoint.x > 0 ? "+" : ""}
                                                        {dataPoint.x.toFixed(1)}σ
                                                    </span>
                                                </div>
                                            </div>
                                        )
                                    }
                                    return null
                                }}
                            />
                            <Area
                                type="monotone"
                                dataKey="y"
                                stroke="#8884d8"
                                fillOpacity={1}
                                fill="url(#colorY)"
                                isAnimationActive={false}
                            />
                            {/* Mean Line */}
                            <ReferenceLine x={0} stroke="#666" strokeDasharray="3 3">
                                <Label value="Peer Avg" position="top" offset={10} fontSize={12} fill="#666" />
                            </ReferenceLine>

                            {/* Portfolio Position Line */}
                            <ReferenceLine x={clampedZScore} stroke="#ef4444" strokeWidth={2}>
                                <Label
                                    value="You"
                                    position="top"
                                    offset={10}
                                    fontSize={12}
                                    fill="#ef4444"
                                    fontWeight="bold"
                                />
                            </ReferenceLine>
                        </AreaChart>
                    </ResponsiveContainer>
                </div>
                <div className="mt-4 flex items-center justify-between text-sm">
                    <div className="flex gap-4">
                        <div>
                            <span className="text-muted-foreground block">Your Z-Score</span>
                            <span className="font-bold text-lg">{zScore > 0 ? "+" : ""}{zScore.toFixed(2)}</span>
                        </div>
                        <div>
                            <span className="text-muted-foreground block">Percentile</span>
                            <span className="font-bold text-lg">{percentile.toFixed(1)}%</span>
                        </div>
                    </div>
                    <div className="text-right text-xs text-muted-foreground max-w-[200px]">
                        Values &gt; 0 indicate above-average performance relative to peers.
                    </div>
                </div>
            </CardContent>
        </Card>
    )
}
