"use client"

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Info } from "lucide-react"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import type { PortfolioOverviewResponse } from "@/lib/types/patent"
import { motion } from "motion/react"
import { cardContainerVariants, cardItemVariants } from "@/lib/motion-variants"

import { cn, formatLabel } from "@/lib/utils"

interface PortfolioOverviewCardProps {
    data: PortfolioOverviewResponse
}

export function PortfolioOverviewCard({ data }: PortfolioOverviewCardProps) {
    const { portfolio, family_metrics, strength, ranking } = data

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
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div className="space-y-1">
                        <div className="flex items-center gap-4 flex-wrap">
                            <CardTitle className="text-2xl">{portfolio.owner_name}</CardTitle>

                            {/* Portfolio Score */}
                            <div className="flex items-center gap-2 bg-muted/40 px-3 py-1 rounded-full border">
                                <span className="text-sm font-medium text-muted-foreground">Portfolio Score:</span>
                                <span className="text-base font-bold text-primary">
                                    {strength?.portfolio_general?.power_score?.toFixed(0) ?? "-"}
                                </span>
                            </div>

                            {/* Top Tier Badge */}
                            <Badge
                                variant="outline"
                                className="text-sm px-3 py-1 bg-primary/5 border-primary/20 text-primary font-medium"
                            >
                                {ranking?.tier ? formatLabel(ranking.tier) : "Unranked"}
                            </Badge>
                        </div>
                    </div>
                </div>
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
                <motion.div
                    className="grid grid-cols-2 md:grid-cols-3 gap-6"
                    variants={cardContainerVariants}
                    initial="hidden"
                    animate="visible"
                >
                    {metrics.map((metric, index) => (
                        <motion.div key={index} variants={cardItemVariants} className="space-y-1">
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
                            <div className="metric-value text-2xl">{metric.value}</div>
                        </motion.div>
                    ))}
                </motion.div>
            </CardContent>
        </Card>
    )
}
