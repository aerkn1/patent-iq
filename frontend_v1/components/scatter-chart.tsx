"use client"

interface Patent {
  id: string
  opportunityScore: number
  riskScore: number
  recommendation: string
}

interface ScatterChartProps {
  data: Patent[]
}

export function ScatterChart({ data }: ScatterChartProps) {
  const width = 800
  const height = 500
  const padding = 60

  const colorMap = {
    ACQUIRE: "#059669", // emerald-600
    MONITOR: "#d97706", // amber-600
    AVOID: "#dc2626", // red-600 primary
  }

  return (
    <div className="w-full overflow-x-auto">
      <svg width={width} height={height} className="text-foreground">
        {/* Grid lines */}
        {[0, 25, 50, 75, 100].map((value) => {
          const x = padding + (value / 100) * (width - 2 * padding)
          const y = height - padding - (value / 100) * (height - 2 * padding)
          return (
            <g key={value}>
              {/* Vertical grid */}
              <line
                x1={x}
                y1={padding}
                x2={x}
                y2={height - padding}
                stroke="currentColor"
                strokeWidth="1"
                opacity="0.1"
              />
              {/* Horizontal grid */}
              <line
                x1={padding}
                y1={y}
                x2={width - padding}
                y2={y}
                stroke="currentColor"
                strokeWidth="1"
                opacity="0.1"
              />
            </g>
          )
        })}

        {/* Quadrant lines */}
        <line
          x1={padding + (width - 2 * padding) / 2}
          y1={padding}
          x2={padding + (width - 2 * padding) / 2}
          y2={height - padding}
          stroke="currentColor"
          strokeWidth="1"
          strokeDasharray="5,5"
          opacity="0.3"
        />
        <line
          x1={padding}
          y1={padding + (height - 2 * padding) / 2}
          x2={width - padding}
          y2={padding + (height - 2 * padding) / 2}
          stroke="currentColor"
          strokeWidth="1"
          strokeDasharray="5,5"
          opacity="0.3"
        />

        {/* Axes */}
        <line
          x1={padding}
          y1={height - padding}
          x2={width - padding}
          y2={height - padding}
          stroke="currentColor"
          strokeWidth="2"
        />
        <line x1={padding} y1={height - padding} x2={padding} y2={padding} stroke="currentColor" strokeWidth="2" />

        {/* Axis labels */}
        <text x={width / 2} y={height - 20} textAnchor="middle" className="text-sm fill-current" opacity="0.7">
          Risk Score →
        </text>
        <text
          x={20}
          y={height / 2}
          textAnchor="middle"
          className="text-sm fill-current"
          opacity="0.7"
          transform={`rotate(-90, 20, ${height / 2})`}
        >
          Opportunity Score →
        </text>

        {/* Data points */}
        {data.map((patent, index) => {
          const x = padding + (patent.riskScore / 100) * (width - 2 * padding)
          const y = height - padding - (patent.opportunityScore / 100) * (height - 2 * padding)
          const color = colorMap[patent.recommendation as keyof typeof colorMap] || "currentColor"

          return (
            <circle
              key={index}
              cx={x}
              cy={y}
              r="4"
              fill={color}
              opacity="0.7"
              className="hover:opacity-100 transition-opacity cursor-pointer"
            >
              <title>{patent.id}</title>
            </circle>
          )
        })}

        {/* Quadrant labels */}
        <text
          x={padding + (width - 2 * padding) * 0.25}
          y={padding + (height - 2 * padding) * 0.25}
          textAnchor="middle"
          className="text-xs fill-current"
          opacity="0.4"
        >
          High Opp, Low Risk
        </text>
        <text
          x={padding + (width - 2 * padding) * 0.75}
          y={padding + (height - 2 * padding) * 0.25}
          textAnchor="middle"
          className="text-xs fill-current"
          opacity="0.4"
        >
          High Opp, High Risk
        </text>
        <text
          x={padding + (width - 2 * padding) * 0.25}
          y={padding + (height - 2 * padding) * 0.75}
          textAnchor="middle"
          className="text-xs fill-current"
          opacity="0.4"
        >
          Low Opp, Low Risk
        </text>
        <text
          x={padding + (width - 2 * padding) * 0.75}
          y={padding + (height - 2 * padding) * 0.75}
          textAnchor="middle"
          className="text-xs fill-current"
          opacity="0.4"
        >
          Low Opp, High Risk
        </text>

        {/* Legend */}
        <g transform={`translate(${width - 150}, ${padding})`}>
          {Object.entries(colorMap).map(([recommendation, color], index) => (
            <g key={recommendation} transform={`translate(0, ${index * 25})`}>
              <circle cx="10" cy="10" r="5" fill={color} />
              <text x="20" y="15" className="text-xs fill-current">
                {recommendation}
              </text>
            </g>
          ))}
        </g>
      </svg>
    </div>
  )
}
