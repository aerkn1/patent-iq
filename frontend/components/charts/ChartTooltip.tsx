"use client"

/**
 * Shared Recharts tooltip component used across citation evolution charts.
 */

interface TooltipEntry {
    name: string
    value: number | null
    color: string
    dataKey: string
}

interface ChartTooltipProps {
    active?: boolean
    payload?: TooltipEntry[]
    label?: string | number
    /** If true, format yoy_growth values as percentages */
    formatYoY?: boolean
}

export function ChartTooltip({ active, payload, label, formatYoY = false }: ChartTooltipProps) {
    if (!active || !payload || payload.length === 0) return null

    return (
        <div className="bg-background border border-border p-3 rounded-lg shadow-lg text-sm">
            <p className="font-bold mb-2">{label}</p>
            {payload.map((entry, index) => (
                <div key={index} className="flex items-center gap-2 mb-1">
                    <div
                        className="w-2 h-2 rounded-full"
                        style={{ backgroundColor: entry.color }}
                    />
                    <span className="text-muted-foreground capitalize">
                        {entry.name.replace(/_/g, " ")}:
                    </span>
                    <span className="font-mono font-medium">
                        {entry.value !== null && entry.value !== undefined
                            ? formatYoY && entry.dataKey === "yoy_growth"
                                ? `${entry.value.toFixed(1)}%`
                                : typeof entry.value === "number"
                                    ? entry.value.toFixed(2)
                                    : entry.value
                            : "N/A"}
                    </span>
                </div>
            ))}
        </div>
    )
}
