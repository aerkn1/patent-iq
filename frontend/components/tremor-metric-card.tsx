import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { LucideIcon } from "lucide-react"
import { cn } from "@/lib/utils"

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

const TREND_BADGE_CLASS: Record<"up" | "down" | "neutral", string> = {
    up: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-200",
    down: "bg-rose-100 text-rose-800 dark:bg-rose-900 dark:text-rose-200",
    neutral: "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300",
}

const TREND_PREFIX: Record<"up" | "down" | "neutral", string> = {
    up: "↗ ",
    down: "↘ ",
    neutral: "- ",
}

interface TremorMetricCardProps {
    title: string
    metric: string | number
    subtext?: string
    icon?: LucideIcon
    progress?: {
        value: number
        label?: string
        color?: string
    }
    trend?: {
        value: string
        direction: "up" | "down" | "neutral"
        label?: string
    }
    status?: {
        label: string
        color: string
    }
    decorationColor?: string
    className?: string
}

export function TremorMetricCard({
    title,
    metric,
    subtext,
    icon: Icon,
    progress,
    trend,
    status,
    decorationColor,
    className
}: TremorMetricCardProps) {
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
                <div className="flex items-start justify-between">
                    <div>
                        <p className="text-sm text-muted-foreground">{title}</p>
                        <p className="mt-2 text-2xl font-bold tracking-tight">{metric}</p>
                    </div>
                    {(Icon || status) && (
                        <div className="flex flex-col items-end gap-2 pl-2">
                            {Icon && <Icon className="h-6 w-6 text-muted-foreground" />}
                            {status && (
                                <Badge variant="secondary">{status.label}</Badge>
                            )}
                        </div>
                    )}
                </div>
                {subtext && <p className="mt-2 text-sm text-muted-foreground">{subtext}</p>}
            </div>

            {/* Trend Badge */}
            {trend && (
                <div className="mt-4 flex items-center gap-2">
                    <span className={cn(
                        "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium",
                        TREND_BADGE_CLASS[trend.direction]
                    )}>
                        {TREND_PREFIX[trend.direction]}{trend.value}
                    </span>
                    {trend.label && (
                        <p className="truncate text-sm text-muted-foreground">{trend.label}</p>
                    )}
                </div>
            )}

            {/* Progress Bar */}
            {progress && (
                <div className="mt-4 space-y-2">
                    <p className="text-sm text-muted-foreground">
                        {progress.label || `${Number(progress.value).toFixed(1)}%`}
                    </p>
                    <Progress value={progress.value} className="mt-2" />
                </div>
            )}
        </Card>
    )
}
