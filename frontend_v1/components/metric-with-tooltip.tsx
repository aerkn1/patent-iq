"use client"

import type React from "react"
import { Info } from "lucide-react"
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip"
import { Progress } from "@/components/ui/progress"
import { TierBadge } from "@/components/tier-badge"

interface MetricWithTooltipProps {
    label: string
    value: string | number
    tooltip: string
    percentile?: number
    tier?: string
    icon?: React.ElementType
    rawValue?: string | number
}

export function MetricWithTooltip({
    label,
    value,
    tooltip,
    percentile,
    tier,
    icon: Icon,
    rawValue,
}: MetricWithTooltipProps) {
    return (
        <div className="space-y-2">
            <div className="flex items-center gap-2">
                {Icon && <Icon className="h-4 w-4 text-muted-foreground" />}
                <span className="text-sm font-medium">{label}</span>
                <Tooltip>
                    <TooltipTrigger asChild>
                        <Info className="h-3.5 w-3.5 text-muted-foreground cursor-help" />
                    </TooltipTrigger>
                    <TooltipContent className="max-w-xs">
                        <p>{tooltip}</p>
                    </TooltipContent>
                </Tooltip>
            </div>
            <div className="text-2xl font-bold">{value}</div>
            {percentile !== undefined && (
                <div className="space-y-1">
                    <div className="flex items-center justify-between text-xs">
                        <span className="text-muted-foreground">Global Percentile</span>
                        <span className="font-semibold">{percentile.toFixed(1)}/100</span>
                    </div>
                    <Progress value={percentile} className="h-1.5" />
                </div>
            )}
            {tier && <TierBadge tier={tier} />}
            {rawValue !== undefined && <p className="text-xs text-muted-foreground">Raw: {rawValue}</p>}
        </div>
    )
}
