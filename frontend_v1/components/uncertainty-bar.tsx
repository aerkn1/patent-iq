"use client"

import type { DifficultyBucket } from "@/lib/types/forecast"

const BUCKET_COLORS: Record<DifficultyBucket, string> = {
    LOW: "bg-emerald-500",
    MID: "bg-amber-500",
    HIGH: "bg-rose-500",
}

const MARKER_COLORS: Record<DifficultyBucket, string> = {
    LOW: "border-emerald-600",
    MID: "border-amber-600",
    HIGH: "border-rose-600",
}

interface UncertaintyBarProps {
    low: number
    expected: number
    high: number
    bucket: DifficultyBucket
}

export function UncertaintyBar({ low, expected, high, bucket }: UncertaintyBarProps) {
    // Compute marker position as percentage within [low, high]
    const range = high - low
    const position = range > 0 ? ((expected - low) / range) * 100 : 50

    return (
        <div className="space-y-1.5">
            <div className="flex items-center justify-between text-xs text-muted-foreground">
                <span>80% interval</span>
            </div>
            <div className="relative h-3 w-full rounded-full bg-muted overflow-hidden">
                {/* Interval bar */}
                <div
                    className={`absolute h-full rounded-full ${BUCKET_COLORS[bucket]} opacity-25`}
                    style={{ left: "0%", width: "100%" }}
                />
                {/* Expected value marker */}
                <div
                    className={`absolute top-0 h-full w-1 rounded-full ${BUCKET_COLORS[bucket]}`}
                    style={{ left: `${Math.min(Math.max(position, 2), 98)}%` }}
                />
            </div>
            <div className="flex items-center justify-between text-xs font-medium">
                <span className="text-muted-foreground">{low.toFixed(1)}</span>
                <span className={`font-semibold ${MARKER_COLORS[bucket].replace("border-", "text-")}`}>
                    {expected.toFixed(1)}
                </span>
                <span className="text-muted-foreground">{high.toFixed(1)}</span>
            </div>
        </div>
    )
}
