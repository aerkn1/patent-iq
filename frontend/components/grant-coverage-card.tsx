"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Info } from "lucide-react"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import type { PortfolioGrantCoverage, PortfolioGrantMixItem } from "@/lib/types/patent"
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip as RechartsTooltip, Legend, Sector } from "recharts"

interface GrantCoverageCardProps {
    grantCoverage: PortfolioGrantCoverage
    grantMix: PortfolioGrantMixItem[]
}

const COLORS = ["#0088FE", "#00C49F", "#FFBB28", "#FF8042", "#8884d8"]

export function GrantCoverageCard({ grantCoverage, grantMix }: GrantCoverageCardProps) {
    const [activeIndex, setActiveIndex] = useState(0)

    const onPieEnter = (_: any, index: number) => {
        setActiveIndex(index)
    }

    const coverageData = [
        { office: "EP", value: grantCoverage?.EP || 0 },
        { office: "US", value: grantCoverage?.US || 0 },
        { office: "CN", value: grantCoverage?.CN || 0 },
        { office: "JP", value: grantCoverage?.JP || 0 },
        { office: "KR", value: grantCoverage?.KR || 0 },
    ]

    // Donut chart data - share of granted families by office
    const pieData = grantMix ? grantMix.map(d => ({
        name: d.publn_auth,
        value: d.granted_share
    })).filter(d => d.value > 0) : []

    const renderActiveShape = (props: any) => {
        const { cx, cy, innerRadius, outerRadius, startAngle, endAngle, fill, payload, value } = props

        return (
            <g>
                <text x={cx} y={cy} dy={-4} textAnchor="middle" fill={fill} className="text-xl font-bold">
                    {payload.name}
                </text>
                <text x={cx} y={cy} dy={16} textAnchor="middle" fill="#999" className="text-sm">
                    {`${(value).toFixed(1)}%`}
                </text>
                <Sector
                    cx={cx}
                    cy={cy}
                    innerRadius={innerRadius}
                    outerRadius={outerRadius + 6}
                    startAngle={startAngle}
                    endAngle={endAngle}
                    fill={fill}
                    cornerRadius={6}
                />
                <Sector
                    cx={cx}
                    cy={cy}
                    startAngle={startAngle}
                    endAngle={endAngle}
                    innerRadius={innerRadius - 8}
                    outerRadius={innerRadius - 4}
                    fill={fill}
                />
            </g>
        )
    }

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
                        <div className="h-[200px] w-full">
                            <ResponsiveContainer width="100%" height="100%">
                                <PieChart>
                                    <Pie
                                        activeIndex={activeIndex}
                                        activeShape={renderActiveShape}
                                        data={pieData}
                                        cx="50%"
                                        cy="50%"
                                        innerRadius={60}
                                        outerRadius={80}
                                        paddingAngle={4}
                                        dataKey="value"
                                        onMouseEnter={onPieEnter}
                                        stroke="none"
                                        cornerRadius={5}
                                    >
                                        {pieData.map((entry, index) => (
                                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                        ))}
                                    </Pie>
                                </PieChart>
                            </ResponsiveContainer>
                        </div>
                    </div>
                </div>

            </CardContent>
        </Card>
    )
}
