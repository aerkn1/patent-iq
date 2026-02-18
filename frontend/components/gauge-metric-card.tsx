import { Card } from "@/components/ui/card"
import { Text, Metric, Flex, Badge, type Color } from "@tremor/react"
import { LucideIcon } from "lucide-react"
import { cn } from "@/lib/utils"
import { GaugeChart } from "./gauge-chart"

interface GaugeMetricCardProps {
    title: string
    metric: string | number // e.g., "75/100"
    subtext?: string // e.g., "Avg: 60"
    icon?: LucideIcon
    gauge?: {
        value: number // 0-100
        color?: string
    }
    status?: {
        label: string
        color: Color
    }
    decorationColor?: Color
    className?: string
}

export function GaugeMetricCard({
    title,
    metric,
    subtext,
    icon: Icon,
    gauge,
    status,
    decorationColor,
    className
}: GaugeMetricCardProps) {
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
                        <Metric className="mt-1 truncate text-lg sm:text-xl">{metric}</Metric>
                    </div>
                    {Icon && <Icon className="h-5 w-5 text-muted-foreground" />}
                </Flex>

                {status && (
                    <div className="mt-2 text-center">
                        <Badge size="xs" color={status.color || "gray"}>
                            {status.label}
                        </Badge>
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
                            <span className="text-xl font-bold" style={{ color: gauge.color }}>
                                {gauge.value.toFixed(0)}
                            </span>
                        </div>
                    </div>
                    {subtext && <Text className="mt-1 text-xs text-center">{subtext}</Text>}
                </div>
            )}
        </Card>
    )
}
