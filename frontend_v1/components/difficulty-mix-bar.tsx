"use client"

import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from "@/components/ui/tooltip"
import type { DifficultyMix } from "@/lib/types/forecast"

const BUCKET_CONFIG = {
    LOW: { color: "bg-emerald-500", label: "Low Difficulty" },
    MID: { color: "bg-amber-500", label: "Mid Difficulty" },
    HIGH: { color: "bg-rose-500", label: "High Difficulty" },
} as const

interface DifficultyMixBarProps {
    mix: DifficultyMix
}

export function DifficultyMixBar({ mix }: DifficultyMixBarProps) {
    const segments = [
        { key: "LOW" as const, value: mix.LOW },
        { key: "MID" as const, value: mix.MID },
        { key: "HIGH" as const, value: mix.HIGH },
    ].filter((s) => s.value > 0)

    return (
        <div className="space-y-2">
            <span className="text-xs font-medium text-muted-foreground">Difficulty Mix</span>

            {/* Stacked bar */}
            <div className="h-3 w-full rounded-full overflow-hidden flex bg-muted">
                {segments.map((seg, i) => (
                    <TooltipProvider key={seg.key}>
                        <Tooltip>
                            <TooltipTrigger asChild>
                                <div
                                    className={`h-full ${BUCKET_CONFIG[seg.key].color} transition-all ${i === 0 ? "rounded-l-full" : ""
                                        } ${i === segments.length - 1 ? "rounded-r-full" : ""}`}
                                    style={{ width: `${seg.value * 100}%` }}
                                />
                            </TooltipTrigger>
                            <TooltipContent>
                                <p className="text-xs">
                                    {BUCKET_CONFIG[seg.key].label}: {(seg.value * 100).toFixed(1)}%
                                </p>
                            </TooltipContent>
                        </Tooltip>
                    </TooltipProvider>
                ))}
            </div>

            {/* Legend */}
            <div className="flex items-center gap-4 text-xs text-muted-foreground">
                {(["LOW", "MID", "HIGH"] as const).map((bucket) => (
                    <div key={bucket} className="flex items-center gap-1.5">
                        <div className={`h-2 w-2 rounded-full ${BUCKET_CONFIG[bucket].color}`} />
                        <span>{bucket} {(mix[bucket] * 100).toFixed(0)}%</span>
                    </div>
                ))}
            </div>
        </div>
    )
}
