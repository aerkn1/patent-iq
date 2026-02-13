import { Card } from "@/components/ui/card"
import { Text, Metric, Flex, ProgressBar, BadgeDelta, type BadgeDeltaProps, type Color, Badge } from "@tremor/react"
import { LucideIcon } from "lucide-react"
import { cn } from "@/lib/utils"

interface TremorMetricCardProps {
    title: string
    metric: string | number
    subtext?: string
    icon?: LucideIcon
    progress?: {
        value: number
        label?: string
        color?: Color
    }
    trend?: {
        value: string
        direction: "up" | "down" | "neutral"
        label?: string
    }
    status?: {
        label: string
        color: Color
    }
    decorationColor?: Color
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
    return (
        <Card
            className={cn(
                "p-4 flex flex-col justify-between overflow-hidden h-full",
                decorationColor ? `border-t-4 border-${decorationColor}-500` : "",
                className
            )}
        >
            <div>
                <Flex alignItems="start" justifyContent="between">
                    <div className="truncate">
                        <Text>{title}</Text>
                        <Metric className="mt-2 truncate">{metric}</Metric>
                    </div>
                    {(Icon || status) && (
                        <div className="flex flex-col items-end gap-2">
                            {Icon && <Icon className="h-6 w-6 text-muted-foreground" />}
                            {status && (
                                <Badge color={status.color || "gray"}>
                                    {status.label}
                                </Badge>
                            )}
                        </div>
                    )}
                </Flex>
                {subtext && <Text className="mt-2">{subtext}</Text>}
            </div>

            {/* Trend Badge */}
            {trend && (
                <div className="mt-4">
                    <Flex justifyContent="start" className="space-x-2">
                        {trend.direction === "up" && (
                            <Badge size="xs" color="emerald">↗ {trend.value}</Badge>
                        )}
                        {trend.direction === "down" && (
                            <Badge size="xs" color="rose">↘ {trend.value}</Badge>
                        )}
                        {trend.direction === "neutral" && (
                            <Badge size="xs" color="gray">- {trend.value}</Badge>
                        )}
                        {trend.label && <Text className="truncate">{trend.label}</Text>}
                    </Flex>
                </div>
            )}

            {/* Progress Bar */}
            {progress && (
                <div className="mt-4 space-y-2">
                    <Flex>
                        <Text>{progress.label || `${Number(progress.value).toFixed(1)}%`}</Text>
                    </Flex>
                    <ProgressBar value={progress.value} color={progress.color || "blue"} className="mt-2" />
                </div>
            )}
        </Card>
    )
}
