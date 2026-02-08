"use client"

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Info } from "lucide-react"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import type { PortfolioOverviewResponse } from "@/lib/types/patent"

interface PortfolioOverviewCardProps {
    data: PortfolioOverviewResponse
}

export function PortfolioOverviewCard({ data }: PortfolioOverviewCardProps) {
    const { portfolio, family_metrics } = data

    const metrics = [
        {
            label: "Total EP Patents",
            value: portfolio.size.n_patents.toLocaleString(),
            description: "Total count of EP patents",
            tooltip: "Total number of EP patents in the portfolio."
        },
        {
            label: "Active Families",
            value: family_metrics?.active_patent_families?.toLocaleString() || "-",
            description: "Distinct patent families with at least one active member",
            tooltip: "Number of unique patent families that are currently active."
        },
        {
            label: "Effective Patents",
            value: family_metrics?.effective_patents?.toFixed(1) || "-",
            description: "Total count of active patent applications",
            tooltip: "Patents are weighted by ownership share. A patent with two owners contributes 0.5 to each portfolio."
        },
        {
            label: "Avg Family Size",
            value: family_metrics?.avg_family_size?.toFixed(1) || "-",
            description: "Average number of applications per family",
            tooltip: "Average count of patent applications per DocDB family."
        },
        {
            label: "Avg Jurisdiction Reach",
            value: family_metrics?.avg_jurisdiction_reach?.toFixed(1) || "-",
            description: "Average number of jurisdictions per family",
            tooltip: "Average count of unique jurisdictions protected per family."
        },
        {
            label: "Major Office Coverage",
            value: family_metrics?.major_office_coverage ? (family_metrics.major_office_coverage * 100).toFixed(0) + "%" : "-",
            description: "Index of coverage in IP5 offices",
            tooltip: "Composite index representing coverage in major offices (US, EP, CN, JP, KR)."
        }
    ]


    return (
        <Card>
            <CardHeader>
                <CardTitle className="text-2xl">{portfolio.owner_name}</CardTitle>
                <CardDescription>
                    <div className="flex flex-wrap items-center gap-4 text-sm mt-2">
                        <div className="flex items-center gap-2">
                            <span className="text-muted-foreground">Owner ID:</span>
                            <span className="font-semibold font-mono">{portfolio.owner_id}</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="text-muted-foreground">Type:</span>
                            <Badge variant="outline">{portfolio.owner_type}</Badge>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="text-muted-foreground">Country:</span>
                            <Badge variant="outline">{portfolio.country}</Badge>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="text-muted-foreground">Size Bucket:</span>
                            <Badge variant="outline">{portfolio.size.size_bucket}</Badge>
                        </div>
                    </div>
                </CardDescription>
            </CardHeader>
            <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-6">
                    {metrics.map((metric, index) => (
                        <div key={index} className="space-y-1">
                            <div className="flex items-center gap-1.5">
                                <span className="text-sm font-medium text-muted-foreground">{metric.label}</span>
                                <TooltipProvider>
                                    <Tooltip>
                                        <TooltipTrigger>
                                            <Info className="h-3.5 w-3.5 text-muted-foreground/70" />
                                        </TooltipTrigger>
                                        <TooltipContent>
                                            <p className="max-w-xs">{metric.tooltip}</p>
                                        </TooltipContent>
                                    </Tooltip>
                                </TooltipProvider>
                            </div>
                            <div className="text-2xl font-bold">{metric.value}</div>
                            {/* <div className="text-xs text-muted-foreground">{metric.description}</div> */}
                        </div>
                    ))}
                </div>
            </CardContent>
        </Card>
    )
}
