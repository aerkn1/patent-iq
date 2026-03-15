"use client"

import { ResponsiveLine } from "@nivo/line"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { TrendingUp, BarChart3 } from "lucide-react"
import { CHART_COLORS } from "@/lib/chart-config"
import { getNivoTheme } from "@/lib/nivo-theme"

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
    const nivoData = [
        {
            id: "Avg. Cites/Patent",
            color: CHART_COLORS.indigo,
            data: data.map((d) => ({ x: d.year, y: d.avg_cites_per_patent })),
        },
    ]

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
                            colors={[CHART_COLORS.indigo]}
                            margin={{ top: 10, right: 10, bottom: 40, left: 45 }}
                            xScale={{ type: "point" }}
                            yScale={{ type: "linear", min: 0, max: "auto" }}
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
                                    <span className="font-semibold">{String(point.data.x)}</span>
                                    {": "}
                                    <span>{Number(point.data.y).toFixed(2)} cites/patent</span>
                                </div>
                            )}
                        />
                    </div>
                )}
            </CardContent>
        </Card>
    )
}
