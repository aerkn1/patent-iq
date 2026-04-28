/**
 * Centralized chart color palette and configuration.
 * All charts should import colors from here instead of hardcoding hex values.
 */

export const CHART_COLORS = {
    primary: "oklch(0.637 0.237 15.34)",
    primaryLight: "oklch(0.75 0.18 15.34)",
    primaryDark: "oklch(0.50 0.20 15.34)",

    green: "#10b981",
    greenLight: "#34d399",
    greenDark: "#059669",

    blue: "#3b82f6",
    blueLight: "#60a5fa",
    blueDark: "#2563eb",

    amber: "#f59e0b",
    amberLight: "#fbbf24",
    amberDark: "#d97706",

    gray: "#6b7280",
    grayLight: "#9ca3af",
    grayDark: "#4b5563",

    red: "#ef4444",
    redLight: "#f87171",
    redDark: "#dc2626",

    purple: "#8b5cf6",
    purpleLight: "#a78bfa",
    purpleDark: "#7c3aed",

    teal: "#14b8a6",
    cyan: "#06b6d4",
    indigo: "#6366f1",
    pink: "#ec4899",
} as const

/** Categorical palette — use for pie charts, bar charts with multiple categories */
export const CATEGORICAL_PALETTE = [
    CHART_COLORS.blue,
    CHART_COLORS.green,
    CHART_COLORS.amber,
    CHART_COLORS.purple,
    CHART_COLORS.teal,
    CHART_COLORS.pink,
    CHART_COLORS.cyan,
    CHART_COLORS.indigo,
    CHART_COLORS.redLight,
    CHART_COLORS.grayLight,
]

/** Sequential palette — use for heatmaps, choropleth, density */
export const SEQUENTIAL_PALETTE = [
    CHART_COLORS.primaryLight,
    CHART_COLORS.primary,
    CHART_COLORS.primaryDark,
]

/** Red palette — use for patent-specific category charts (current brand) */
export const RED_PALETTE = [
    "#fca5a5",
    "#f87171",
    "#ef4444",
    "#dc2626",
    "#b91c1c",
]

/** Diverging palette — positive/neutral/negative */
export const DIVERGING_PALETTE = {
    positive: CHART_COLORS.green,
    neutral: CHART_COLORS.gray,
    negative: CHART_COLORS.red,
}

/** Radar chart theme */
export const RADAR_THEME = {
    dots: {
        size: 8,
        color: CHART_COLORS.primary,
        borderWidth: 2,
        borderColor: "#ffffff",
    },
    grid: {
        color: "#e5e7eb",
    },
    fill: {
        color: CHART_COLORS.primary,
        opacity: 0.2,
    },
    stroke: {
        color: CHART_COLORS.primary,
        width: 2,
    },
}

/** Common Recharts tooltip styles */
export const TOOLTIP_STYLE = {
    contentStyle: {
        backgroundColor: "hsl(var(--card))",
        border: "1px solid hsl(var(--border))",
        borderRadius: "8px",
        fontSize: "13px",
        boxShadow: "0 4px 6px -1px rgba(0,0,0,.1)",
    },
    labelStyle: {
        fontWeight: 600,
        marginBottom: "4px",
    },
}

/** Common bar chart radius */
export const BAR_RADIUS: [number, number, number, number] = [4, 4, 0, 0]
