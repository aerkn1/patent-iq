"use client"

import { ResponsivePie } from "@nivo/pie"

interface GaugeChartProps {
    value: number // 0 to 100
    color?: string
    showValue?: boolean
    height?: number
}

export function GaugeChart({ value, color = "#3b82f6", showValue = true, height = 120 }: GaugeChartProps) {
    const normalizedValue = Math.min(Math.max(value, 0), 100)

    const data = [
        { id: "value", value: normalizedValue },
        { id: "remainder", value: 100 - normalizedValue },
    ]

    return (
        <div style={{ height: height, width: "100%", position: "relative" }}>
            <div style={{ height: height * 2, overflow: "hidden" }}>
                <ResponsivePie
                    data={data}
                    startAngle={-90}
                    endAngle={90}
                    innerRadius={0.8}
                    fit={false}
                    colors={[color, "#e5e7eb"]}
                    enableArcLabels={false}
                    enableArcLinkLabels={false}
                    isInteractive={false}
                    animate={false}
                />
            </div>

            {showValue && (
                <div className="absolute bottom-0 left-0 right-0 flex flex-col items-center justify-end pb-2">
                    <span className="text-2xl font-bold" style={{ color }}>
                        {normalizedValue.toFixed(0)}
                    </span>
                </div>
            )}
        </div>
    )
}
