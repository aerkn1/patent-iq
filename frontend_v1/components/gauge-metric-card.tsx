import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { LucideIcon } from "lucide-react"
import { cn } from "@/lib/utils"
import { GaugeChart } from "./gauge-chart"

// Maps decoration color names to full static Tailwind border classes.
// Full class strings must be present so Tailwind v4 static analysis retains them.
const DECORATION_BORDER_CLASS: Record<string, string> = {
    emerald: "border-t-4 border-t-emerald-500",
    amber: "border-t-4 border-t-amber-500",
    blue: "border-t-4 border-t-blue-500",
    red: "border-t-4 border-t-red-500",
    green: "border-t-4 border-t-green-500",
    gray: "border-t-4 border-t-gray-500",
    rose: "border-t-4 border-t-rose-500",
    orange: "border-t-4 border-t-orange-500",
    yellow: "border-t-4 border-t-yellow-500",
    indigo: "border-t-4 border-t-indigo-500",
    violet: "border-t-4 border-t-violet-500",
    purple: "border-t-4 border-t-purple-500",
    teal: "border-t-4 border-t-teal-500",
    cyan: "border-t-4 border-t-cyan-500",
    sky: "border-t-4 border-t-sky-500",
    lime: "border-t-4 border-t-lime-500",
    pink: "border-t-4 border-t-pink-500",
    fuchsia: "border-t-4 border-t-fuchsia-500",
}

interface GaugeMetricCardProps {
    title: string
    metric: string | number
    category?: string
    subtext?: string
    icon?: LucideIcon
    gauge?: {
        value: number
        color?: string
    }
    status?: {
        label: string
        color: string
    }
    decorationColor?: string
    className?: string
}

export function GaugeMetricCard({
    title,
    metric,
    category,
    subtext,
    icon: Icon,
    gauge,
    status,
    decorationColor,
    className
}: GaugeMetricCardProps) {
    const borderClass = decorationColor ? (DECORATION_BORDER_CLASS[decorationColor] ?? "") : ""

    return (
        <Card
            className={cn(
                "p-4 flex flex-col justify-between overflow-hidden h-full",
                borderClass,
                className
            )}
        >
            <div>
                {/* Category label */}
                {category && (
                    <p className="metric-label mb-2">{category}</p>
                )}
                <div className="flex items-start justify-between">
                    <div className="truncate">
                        <p className="text-sm text-muted-foreground">{title}</p>
                        <p className="metric-value mt-1 truncate text-lg sm:text-xl">{metric}</p>
                    </div>
                    {Icon && <Icon className="h-5 w-5 text-muted-foreground shrink-0" />}
                </div>

                {status && (
                    <div className="mt-2 text-center">
                        <Badge variant="secondary">{status.label}</Badge>
                    </div>
                )}
            </div>

            {/* Gauge Chart */}
            {gauge && (
                <div className="mt-2 flex flex-col items-center justify-center flex-grow">
                    <div className="w-full h-[80px] relative mt-2">
                        <GaugeChart value={gauge.value} color={gauge.color} showValue={false} height={80} />
                        {/* Centered Value inside Gauge */}
                        <div className="absolute bottom-0 left-0 right-0 text-center -mb-1">
                            <span className="metric-value text-xl" style={{ color: gauge.color }}>
                                {gauge.value.toFixed(0)}
                            </span>
                        </div>
                    </div>
                    {subtext && (
                        <p className="mt-1 text-xs text-center text-muted-foreground">{subtext}</p>
                    )}
                </div>
            )}
        </Card>
    )
}
