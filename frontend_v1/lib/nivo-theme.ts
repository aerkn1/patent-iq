"use client"

export function getNivoTheme() {
  const style = typeof window !== "undefined" ? getComputedStyle(document.documentElement) : null
  const get = (v: string, fb: string) => style?.getPropertyValue(v).trim() || fb
  const mutedFg = get("--muted-foreground", "oklch(0.556 0.009 0)")
  const border  = get("--border",           "oklch(0.919 0.005 0)")
  const cardBg  = get("--card",             "oklch(1 0 0)")
  const fg      = get("--foreground",       "oklch(0.254 0.005 0)")
  return {
    background: "transparent", textColor: fg, fontSize: 12,
    axis: {
      domain: { line: { stroke: "transparent" } },
      ticks: { line: { stroke: "transparent" }, text: { fontSize: 12, fill: mutedFg } },
      legend: { text: { fontSize: 12, fill: mutedFg } },
    },
    grid: { line: { stroke: border, strokeDasharray: "3 3" } },
    legends: { text: { fontSize: 11, fill: mutedFg } },
    tooltip: {
      container: {
        background: cardBg, border: `1px solid ${border}`,
        borderRadius: "8px", fontSize: "13px",
        boxShadow: "0 4px 6px -1px rgba(0,0,0,.1)", color: fg,
      },
    },
    crosshair: { line: { stroke: mutedFg, strokeWidth: 1, strokeOpacity: 0.5 } },
  }
}
