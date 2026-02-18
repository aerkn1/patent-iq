"use client"

import { ResponsiveRadar } from "@nivo/radar"
import { RED_PALETTE } from "@/lib/chart-config"

interface RadarData {
  category: string
  value: number
  max: number
  description?: string
}

interface RadarChartProps {
  data: RadarData[]
}

export function RadarChart({ data }: RadarChartProps) {
  // Normalize data to 0-100 scale for the chart, but keep original values for tooltip
  const chartData = data.map(d => ({
    category: d.category,
    value: Math.min(100, Math.max(0, (d.value / d.max) * 100)), // Clamp 0-100
    originalValue: d.value,
    max: d.max,
    description: d.description
  }))

  return (
    <div className="w-full" style={{ height: 300 }}>
      {/* Explicit height style to ensure visibility if Tailwind class fails */}
      <ResponsiveRadar
        data={chartData}
        keys={["value"]}
        indexBy="category"
        maxValue={100}
        margin={{ top: 40, right: 40, bottom: 40, left: 40 }}
        curve="linearClosed"
        borderWidth={2}
        borderColor={RED_PALETTE[3]}
        gridLevels={5}
        gridShape="circular"
        gridLabelOffset={16}
        enableDots={true}
        dotSize={8}
        dotColor="white"
        dotBorderWidth={2}
        dotBorderColor={RED_PALETTE[3]}
        enableDotLabel={false}
        colors={[RED_PALETTE[3]]}
        fillOpacity={0.25}
        blendMode="multiply"
        motionConfig="wobbly"
        theme={{
          axis: {
            ticks: {
              text: {
                fontSize: 12,
                fill: "#6b7280" // Gray-500 hardcoded
              }
            }
          },
          grid: {
            line: {
              stroke: "#e5e7eb", // Gray-200 hardcoded
              strokeDasharray: "4 4"
            }
          },
          tooltip: {
            container: {
              background: "#ffffff",
              color: "#000000",
              fontSize: 12,
              borderRadius: "6px",
              boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)",
              border: "1px solid #e5e7eb"
            }
          }
        }}
        sliceTooltip={(props: any) => {
          const index = props.index || props.slice?.index
          const data = props.data || props.slice?.data

          return (
            <div className="bg-background border border-border p-3 rounded-lg shadow-lg">
              <div className="font-semibold mb-1">{index}</div>
              {data && data[0]?.data?.description && (
                <p className="text-xs text-muted-foreground mb-2 max-w-xs leading-snug">
                  {data[0].data.description}
                </p>
              )}
              {data && data.map((point: any) => {
                const original = point.data?.originalValue
                const max = point.data?.max
                return (
                  <div key={point.id} className="text-sm text-muted-foreground">
                    <span className="text-foreground font-medium">{point.formattedValue || original?.toFixed(1) || point.value?.toFixed(0)}</span>
                    <span className="mx-1">/</span>
                    <span>{max}</span>
                  </div>
                )
              })}
            </div>
          )
        }}
      />
    </div>
  )
}
