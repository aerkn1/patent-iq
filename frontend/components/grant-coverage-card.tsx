"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Info } from "lucide-react"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import type { PortfolioGrantCoverage, PortfolioGrantMixItem } from "@/lib/types/patent"
import { ResponsivePie } from "@nivo/pie"

interface GrantCoverageCardProps {
    grantCoverage: PortfolioGrantCoverage
    grantMix: PortfolioGrantMixItem[]
}

const COLORS = ["#0088FE", "#00C49F", "#FFBB28", "#FF8042", "#8884d8"]

export function GrantCoverageCard({ grantCoverage, grantMix }: GrantCoverageCardProps) {
    const [hovered, setHovered] = useState<{ id: string; label: string; value: number } | null>(null)

    const coverageData = [
        { office: "EP", value: grantCoverage?.EP || 0 },
        { office: "US", value: grantCoverage?.US || 0 },
        { office: "CN", value: grantCoverage?.CN || 0 },
        { office: "JP", value: grantCoverage?.JP || 0 },
        { office: "KR", value: grantCoverage?.KR || 0 },
    ]

    const pieData = grantMix
        ? grantMix
            .map((d, i) => ({
                id: d.publn_auth,
                label: d.publn_auth,
                value: d.granted_share,
                color: COLORS[i % COLORS.length],
            }))
            .filter((d) => d.value > 0)
        : []

    return (
        <Card className="h-full">
            <CardHeader>
                <CardTitle className="flex items-center gap-2">
                    Grant Coverage
                    <TooltipProvider>
                        <Tooltip>
                            <TooltipTrigger>
                                <Info className="h-4 w-4 text-muted-foreground" />
                            </TooltipTrigger>
                            <TooltipContent>
                                <p>Grant coverage indicates the % of portfolio families with at least one grant in the jurisdiction.</p>
                            </TooltipContent>
                        </Tooltip>
                    </TooltipProvider>
                </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
                <div className="grid md:grid-cols-2 gap-6 pt-4">
                    {/* Grant Coverage Bars */}
                    <div className="space-y-4">
                        <h4 className="text-sm font-semibold text-muted-foreground mb-2">Coverage by Office</h4>
                        {coverageData.map((item) => (
                            <div key={item.office} className="space-y-1">
                                <div className="flex justify-between text-xs">
                                    <span className="font-medium">{item.office}</span>
                                    <span className="text-muted-foreground">{item.value.toFixed(1)}% families</span>
                                </div>
                                <Progress value={item.value} className="h-2" />
                            </div>
                        ))}
                    </div>

                    {/* Grant Mix Donut */}
                    <div className="h-[250px] w-full flex flex-col items-center justify-center">
                        <h4 className="text-sm font-semibold text-muted-foreground mb-4 text-center">Grant Mix</h4>
                        <div className="h-[200px] w-full relative">
                            <ResponsivePie
                                data={pieData}
                                innerRadius={0.65}
                                padAngle={4}
                                cornerRadius={5}
                                activeOuterRadiusOffset={8}
                                colors={pieData.map((d) => d.color)}
                                enableArcLabels={false}
                                enableArcLinkLabels={false}
                                onMouseEnter={(datum) =>
                                    setHovered({ id: datum.id as string, label: datum.label as string, value: datum.value })
                                }
                                onMouseLeave={() => setHovered(null)}
                                tooltip={() => null}
                            />
                            {hovered && (
                                <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                                    <span className="text-base font-bold">{hovered.label}</span>
                                    <span className="text-sm text-muted-foreground">{(hovered.value).toFixed(1)}%</span>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </CardContent>
        </Card>
    )
}
