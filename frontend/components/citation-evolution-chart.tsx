"use client"

import { useMemo, useState } from "react"
import { ResponsiveLine } from "@nivo/line"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import { TrendingUp, BarChart3 } from "lucide-react"
import { CHART_COLORS } from "@/lib/chart-config"
import { getNivoTheme } from "@/lib/nivo-theme"

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

    const nivoData = useMemo(
        () =>
            showSplit
                ? [
                      { id: "early", data: data.map((d) => ({ x: d.year, y: d.early })) },
                      { id: "mid", data: data.map((d) => ({ x: d.year, y: d.mid })) },
                      { id: "late", data: data.map((d) => ({ x: d.year, y: d.late })) },
                  ]
                : [{ id: "total", data: data.map((d) => ({ x: d.year, y: d.total })) }],
        [data, showSplit]
    )

    const colors = showSplit
        ? [CHART_COLORS.green, CHART_COLORS.blue, CHART_COLORS.amber]
        : [CHART_COLORS.indigo]

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
                            Annual citations — split by citation age cohort
                        </CardDescription>
                    </div>
                    <div className="flex items-center gap-2">
                        <Switch id="split-mode" checked={showSplit} onCheckedChange={setShowSplit} />
                        <Label htmlFor="split-mode" className="text-xs">Split View</Label>
                    </div>
                </div>
            </CardHeader>
            <CardContent>
                {data.length === 0 ? (
                    <div className="flex h-[350px] flex-col items-center justify-center gap-2 text-muted-foreground">
                        <BarChart3 className="h-8 w-8 opacity-40" />
                        <p className="text-sm">No data available</p>
                    </div>
                ) : (
                    <div className="h-[350px] w-full">
                        <ResponsiveLine
                            data={nivoData}
                            theme={getNivoTheme()}
                            colors={colors}
                            margin={{ top: 10, right: 10, bottom: 40, left: 45 }}
                            xScale={{ type: "point" }}
                            yScale={{ type: "linear", stacked: showSplit, min: 0, max: "auto" }}
                            enableArea={true}
                            areaOpacity={0.2}
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
                            tooltip={({ point }) => (
                                <div className="bg-background border border-border p-2 rounded-lg text-xs shadow">
                                    <span className="font-semibold">{point.seriesId}</span>
                                    {" · "}
                                    <span>{String(point.data.x)}: {String(point.data.y)}</span>
                                </div>
                            )}
                        />
                    </div>
                )}
            </CardContent>
        </Card>
    )
}
