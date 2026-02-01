"use client"

interface RadarData {
  category: string
  value: number
  max: number
}

interface RadarChartProps {
  data: RadarData[]
}

export function RadarChart({ data }: RadarChartProps) {
  const size = 300
  const center = size / 2
  const radius = size / 2 - 40
  const levels = 5

  // Calculate points for the data polygon
  const calculatePoint = (value: number, max: number, angle: number) => {
    const ratio = value / max
    const x = center + radius * ratio * Math.cos(angle - Math.PI / 2)
    const y = center + radius * ratio * Math.sin(angle - Math.PI / 2)
    return { x, y }
  }

  const angleStep = (2 * Math.PI) / data.length
  const dataPoints = data.map((item, index) => {
    const angle = index * angleStep
    return calculatePoint(item.value, item.max, angle)
  })

  const dataPath = dataPoints.map((point, index) => `${index === 0 ? "M" : "L"} ${point.x},${point.y}`).join(" ") + " Z"

  return (
    <div className="flex items-center justify-center">
      <svg width={size} height={size}>
        {Array.from({ length: levels }).map((_, i) => {
          const r = radius * ((i + 1) / levels)
          return <circle key={i} cx={center} cy={center} r={r} fill="none" stroke="#d1d5db" strokeWidth="1.5" />
        })}

        {data.map((_, index) => {
          const angle = index * angleStep
          const x = center + radius * Math.cos(angle - Math.PI / 2)
          const y = center + radius * Math.sin(angle - Math.PI / 2)
          return <line key={index} x1={center} y1={center} x2={x} y2={y} stroke="#9ca3af" strokeWidth="2" />
        })}

        <path d={dataPath} fill="#dc2626" fillOpacity="0.25" stroke="#dc2626" strokeWidth="3" />

        {dataPoints.map((point, index) => (
          <circle key={index} cx={point.x} cy={point.y} r="6" fill="#dc2626" stroke="white" strokeWidth="3" />
        ))}
        {/* </CHANGE> */}

        {data.map((item, index) => {
          const angle = index * angleStep
          const labelDistance = radius + 25
          const x = center + labelDistance * Math.cos(angle - Math.PI / 2)
          const y = center + labelDistance * Math.sin(angle - Math.PI / 2)

          return (
            <text
              key={index}
              x={x}
              y={y}
              textAnchor="middle"
              dominantBaseline="middle"
              className="text-xs font-semibold"
              fill="#374151"
            >
              {item.category}
            </text>
          )
        })}
      </svg>
    </div>
  )
}
