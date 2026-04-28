import { enterpriseTokens } from "./tokens";

export const chartTokens = {
  rank: {
    primary: enterpriseTokens.colors.accent,
    secondary: enterpriseTokens.colors.warning,
    tertiary: enterpriseTokens.colors.info,
  },
  reference: {
    areaAccent: "rgba(161, 79, 49, 0.16)",
    axis: "rgba(15, 23, 42, 0.16)",
    highlight: "rgba(161, 79, 49, 0.28)",
  },
  series: {
    accent: enterpriseTokens.colors.accent,
    critical: enterpriseTokens.colors.critical,
    info: enterpriseTokens.colors.info,
    neutral: enterpriseTokens.colors.neutral,
    success: enterpriseTokens.colors.success,
    warning: enterpriseTokens.colors.warning,
  },
} as const;

export function getBinaryRankColor(index: number): string {
  return index < 2 ? chartTokens.series.accent : chartTokens.series.info;
}

export function getCompareDeltaColor(value: number): string {
  if (value > 0) {
    return chartTokens.series.success;
  }

  if (value < 0) {
    return chartTokens.series.critical;
  }

  return chartTokens.series.warning;
}

export function getDirectionColor(value: string): string {
  const normalized = value.toLowerCase();
  if (normalized.includes("heat") || normalized.includes("gain") || normalized.includes("up")) {
    return chartTokens.series.success;
  }

  if (normalized.includes("cool") || normalized.includes("loss") || normalized.includes("down")) {
    return chartTokens.series.critical;
  }

  return chartTokens.series.neutral;
}

export function getFocusAwareBarColor(index: number, selected: boolean): string {
  if (selected) {
    return chartTokens.series.accent;
  }

  return index < 4 ? chartTokens.series.info : chartTokens.rank.tertiary;
}

export function getRankedBarColor(index: number): string {
  if (index < 3) {
    return chartTokens.rank.primary;
  }

  if (index < 6) {
    return chartTokens.rank.secondary;
  }

  return chartTokens.rank.tertiary;
}

export function getRiskBandColor(label: string): string {
  const normalized = label.toLowerCase();
  if (normalized === "low") {
    return chartTokens.series.success;
  }

  if (normalized === "medium") {
    return chartTokens.series.warning;
  }

  if (normalized === "high") {
    return chartTokens.series.critical;
  }

  return chartTokens.series.accent;
}

export function getTrajectoryColor(direction: "gain" | "loss" | "flat"): string {
  if (direction === "gain") {
    return chartTokens.series.success;
  }

  if (direction === "loss") {
    return chartTokens.series.critical;
  }

  return chartTokens.series.neutral;
}

export function getWarningRankColor(index: number): string {
  return index < 2 ? chartTokens.series.accent : chartTokens.series.warning;
}
