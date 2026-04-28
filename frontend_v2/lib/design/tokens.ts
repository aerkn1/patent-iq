export const enterpriseTokens = {
  colors: {
    accent: "#a14f31",
    accentDark: "#7a3520",
    background: "#eef3f7",
    border: "#d6e0ea",
    critical: "#c46052",
    foreground: "#0f1a2b",
    info: "#3f6e96",
    muted: "#66778f",
    neutral: "#8693a3",
    success: "#2d8a64",
    surface: "#ffffff",
    warning: "#b48438",
  },
  radii: {
    card: 22,
    panel: 30,
    pill: 999,
  },
  shadows: {
    panel: "0 24px 64px rgba(15, 23, 42, 0.1)",
    soft: "0 18px 42px rgba(15, 23, 42, 0.08)",
  },
  typography: {
    bodyVar: "var(--font-body)",
    displayVar: "var(--font-display)",
    monoVar: "var(--font-mono-ui)",
    uiVar: "var(--font-ui)",
  },
} as const;

export type EnterpriseStatusTone = "accent" | "critical" | "info" | "neutral" | "positive" | "warning";
