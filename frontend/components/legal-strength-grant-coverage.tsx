"use client"

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Info } from "lucide-react"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import type { PortfolioGrantCoverage, PortfolioGrantMixItem } from "@/lib/types/patent"
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip as RechartsTooltip, Legend } from "recharts"

interface LegalStrengthGrantCoverageProps {
    grantCoverage: PortfolioGrantCoverage
    grantMix: PortfolioGrantMixItem[]
    legalScore: number
    legalScorePercentile?: number
}

const COLORS = ["#0088FE", "#00C49F", "#FFBB28", "#FF8042", "#8884d8"]

export function LegalStrengthGrantCoverage({ grantCoverage, grantMix, legalScore, legalScorePercentile }: LegalStrengthGrantCoverageProps) {

    const coverageData = [
        { office: "EP", value: grantCoverage?.EP || 0, fullLabel: "European Patent Office" },
        { office: "US", value: grantCoverage?.US || 0, fullLabel: "USPTO" },
        { office: "CN", value: grantCoverage?.CN || 0, fullLabel: "CNIPA (China)" },
        { office: "JP", value: grantCoverage?.JP || 0, fullLabel: "JPO (Japan)" },
        { office: "KR", value: grantCoverage?.KR || 0, fullLabel: "KIPO (Korea)" },
    ]

    // Donut chart data - share of granted families by office
    // Use the provided grantMix which comes from the specific parquet file for this purpose

    const pieData = grantMix ? grantMix.map(d => ({
        name: d.publn_auth,
        value: d.granted_share
    })).filter(d => d.value > 0) : []

    return (
        <Card className="h-full">
            <CardHeader>
                <CardTitle className="flex items-center gap-2">
                    Legal Strength & Grant Coverage
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

                {/* Legal Strength Score */}
                <div className="space-y-2">
                    <div className="flex items-center justify-between">
                        <span className="text-sm font-medium">Legal Strength Score</span>
                        <span className="text-2xl font-bold">{legalScore.toFixed(0)}/100</span>
                    </div>
                    <Progress value={legalScore} className="h-2" />
                </div>

                <div className="grid md:grid-cols-2 gap-6 pt-4">

                    {/* Grant Coverage Bars */}
                    <div className="space-y-4">
                        <h4 className="text-sm font-semibold text-muted-foreground mb-2">Grant Coverage by Office</h4>
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
                    <div className="h-[200px] w-full">
                        <h4 className="text-sm font-semibold text-muted-foreground mb-2 text-center">Grant Mix</h4>
                        <ResponsiveContainer width="100%" height="100%">
                            <PieChart>
                                <Pie
                                    data={pieData}
                                    cx="50%"
                                    cy="50%"
                                    innerRadius={40}
                                    outerRadius={60}
                                    paddingAngle={5}
                                    dataKey="value"
                                >
                                    {pieData.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                    ))}
                                </Pie>
                                <RechartsTooltip formatter={(value: number) => value.toFixed(1)} />
                                <Legend verticalAlign="bottom" height={36} iconType="circle" />
                            </PieChart>
                        </ResponsiveContainer>
                    </div>
                </div>

            </CardContent>
        </Card>
    )
}
