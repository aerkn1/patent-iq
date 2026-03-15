"use client"

import { useMemo } from "react"
import { ResponsiveLine } from "@nivo/line"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { getNivoTheme } from "@/lib/nivo-theme"

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
    const generatedData = useMemo(() => {
        const points = []
        for (let x = -3.5; x <= 3.5; x += 0.1) {
            const y = (1 / Math.sqrt(2 * Math.PI)) * Math.exp(-0.5 * x * x)
            points.push({ x: Math.round(x * 10) / 10, y })
        }
        return points
    }, [])

    const clampedZScore = Math.max(-3.5, Math.min(3.5, zScore))

    const nivoData = [{ id: "distribution", color: "#8884d8", data: generatedData }]

    const RefLinesLayer = ({ xScale, innerHeight }: any) => (
        <g>
            <line
                x1={xScale(0)} x2={xScale(0)}
                y1={0} y2={innerHeight}
                stroke="#888" strokeDasharray="3 3"
            />
            <text x={xScale(0) + 4} y={-6} fontSize={11} fill="#888">Peer Avg</text>
            <line
                x1={xScale(clampedZScore)} x2={xScale(clampedZScore)}
                y1={0} y2={innerHeight}
                stroke="#ef4444" strokeWidth={2}
            />
            <text x={xScale(clampedZScore) + 4} y={-6} fontSize={11} fill="#ef4444" fontWeight="bold">You</text>
        </g>
    )

    return (
        <Card>
            <CardHeader>
                <CardTitle>{title}</CardTitle>
                <CardDescription>{description}</CardDescription>
            </CardHeader>
            <CardContent>
                <div className="h-[250px] w-full">
                    <ResponsiveLine
                        data={nivoData}
                        theme={getNivoTheme()}
                        colors={["#8884d8"]}
                        margin={{ top: 20, right: 20, bottom: 40, left: 20 }}
                        xScale={{ type: "linear", min: -3.5, max: 3.5 }}
                        yScale={{ type: "linear", min: 0, max: "auto" }}
                        enableArea={true}
                        areaOpacity={0.4}
                        axisLeft={null}
                        axisBottom={{
                            tickSize: 0,
                            tickPadding: 8,
                            tickValues: [-3, -2, -1, 0, 1, 2, 3],
                            format: (v: number) => v === 0 ? "Avg" : v > 0 ? `+${v}σ` : `${v}σ`,
                        }}
                        enablePoints={false}
                        enableGridX={false}
                        curve="natural"
                        layers={["grid", "axes", "areas", "lines", RefLinesLayer, "points", "slices", "mesh", "legends"]}
                        tooltip={({ point }) => (
                            <div className="bg-background border border-border p-2 rounded-lg text-xs shadow">
                                <span>Deviation: {Number(point.data.x) > 0 ? "+" : ""}{Number(point.data.x).toFixed(1)}σ</span>
                            </div>
                        )}
                    />
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
