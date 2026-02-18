"use client"

import { PieChart, Pie, Cell, ResponsiveContainer } from "recharts"

interface GaugeChartProps {
    value: number // 0 to 100
    color?: string
    showValue?: boolean
    height?: number
}

export function GaugeChart({ value, color = "#3b82f6", showValue = true, height = 120 }: GaugeChartProps) {
    // Normalize value to 0-100
    const normalizedValue = Math.min(Math.max(value, 0), 100)

    const data = [
        { name: "value", value: normalizedValue },
        { name: "remainder", value: 100 - normalizedValue }
    ]

    const settings = {
        startAngle: 180,
        endAngle: 0,
        innerRadius: "80%",
        outerRadius: "100%",
    }

    return (
        <div style={{ height: height, width: "100%", position: "relative" }}>
            <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                    <Pie
                        data={data}
                        cx="50%"
                        cy="100%" // Moved to bottom to show half circle
                        {...settings}
                        dataKey="value"
                        stroke="none"
                    >
                        {data.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={index === 0 ? color : "#e5e7eb"} />
                        ))}
                    </Pie>
                </PieChart>
            </ResponsiveContainer>

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
