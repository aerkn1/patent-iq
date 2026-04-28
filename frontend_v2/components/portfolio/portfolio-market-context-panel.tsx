"use client";

import clsx from "clsx";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { formatDecimal, formatPercent, formatNumber } from "@/components/portfolio/portfolio-format";
import { InfoPill } from "@/components/ui/data-pill";
import { Surface } from "@/components/ui/surface";
import { chartTokens, getDirectionColor } from "@/lib/design/chart-tokens";
import type { PortfolioMarketContextResponse } from "@/lib/types/portfolio-v2";
import styles from "@/components/portfolio/technology-panels.module.css";

type PortfolioMarketContextPanelProps = {
  context: PortfolioMarketContextResponse;
  errorMessage?: string;
};

function directionTone(value: string): "heating" | "cooling" | "stable" {
  const normalized = value.toLowerCase();
  if (normalized.includes("heat") || normalized.includes("gain") || normalized.includes("up")) {
    return "heating";
  }
  if (normalized.includes("cool") || normalized.includes("loss") || normalized.includes("down")) {
    return "cooling";
  }
  return "stable";
}

function supportTone(value: string): "strong" | "moderate" | "limited" {
  if (value === "strong") {
    return "strong";
  }
  if (value === "moderate") {
    return "moderate";
  }
  return "limited";
}

export function PortfolioMarketContextPanel({ context, errorMessage }: PortfolioMarketContextPanelProps) {
  const summary = context.summary;
  const sortedSegments = [...context.segments].sort((left, right) => right.activeFamilyCount - left.activeFamilyCount);
  const chartRows = sortedSegments.slice(0, 8).map((segment) => ({
    ...segment,
    growthPct: segment.predictedGrowthRateReference * 100,
  }));

  return (
    <Surface
      className="portfolio-panel--market"
      title="Market direction"
      badge={summary ? <InfoPill tone="neutral">{summary.horizon}</InfoPill> : null}
    >
      {errorMessage ? <p className="portfolio-error">{errorMessage}</p> : null}
      {summary ? (
        <div className={styles.chartShell}>
          <h4 className={styles.chartShellTitle}>Directional field coverage</h4>
          <ResponsiveContainer width="100%" height={290}>
            <BarChart data={chartRows} layout="vertical" margin={{ top: 20, right: 16, left: 16, bottom: 4 }}>
              <CartesianGrid strokeDasharray="3 3" horizontal={false} />
              <XAxis type="number" tickFormatter={(value: number) => formatNumber(value)} />
              <YAxis type="category" dataKey="wipoField" width={112} tickLine={false} axisLine={false} />
              <Tooltip
                formatter={(value: number, name: string) => {
                  if (name === "activeFamilyCount") {
                    return [formatNumber(value), "Active families"];
                  }
                  return [`${value.toFixed(1)}%`, "Growth reference"];
                }}
                labelFormatter={(label) => `Field: ${label}`}
              />
              <Bar dataKey="activeFamilyCount" radius={[0, 10, 10, 0]}>
                {chartRows.map((row) => (
                  <Cell key={row.wipoField} fill={getDirectionColor(row.predictedDirectionBand)} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          <div className={styles.legend}>
            <span className={styles.legendItem}>
              <span className={styles.legendSwatch} style={{ background: chartTokens.series.success }} />
              Heating or gaining
            </span>
            <span className={styles.legendItem}>
              <span className={styles.legendSwatch} style={{ background: chartTokens.series.critical }} />
              Cooling or losing
            </span>
            <span className={styles.legendItem}>
              <span className={styles.legendSwatch} style={{ background: chartTokens.series.neutral }} />
              Stable or mixed
            </span>
          </div>
        </div>
      ) : (
        <p className="portfolio-empty">No current market overlay loaded.</p>
      )}
      {context.segments.length > 0 ? (
        <div className={styles.marketList}>
          {sortedSegments.map((segment) => (
            <article key={`${segment.horizon}-${segment.wipoField}`} className={styles.marketRow}>
              <div className={styles.marketRowHead}>
                <div className={styles.marketIdentity}>
                  <strong>{segment.wipoField}</strong>
                  <span>Market-direction overlay for the current owner footprint</span>
                </div>
                <div className={styles.marketTags}>
                  <span
                    className={clsx(
                      styles.directionPill,
                      directionTone(segment.predictedDirectionBand) === "heating" && styles.directionHeating,
                      directionTone(segment.predictedDirectionBand) === "cooling" && styles.directionCooling,
                      directionTone(segment.predictedDirectionBand) === "stable" && styles.directionStable,
                    )}
                  >
                    {segment.predictedDirectionBand}
                  </span>
                  <span
                    className={clsx(
                      styles.supportPill,
                      supportTone(segment.supportLevel) === "strong" && styles.supportStrong,
                      supportTone(segment.supportLevel) === "moderate" && styles.supportModerate,
                      supportTone(segment.supportLevel) === "limited" && styles.supportLimited,
                    )}
                  >
                    {segment.supportLevel} support
                  </span>
                </div>
              </div>
              <div className={styles.marketMetrics}>
                <div className={styles.metricCell}>
                  <span>Active families</span>
                  <strong>{formatNumber(segment.activeFamilyCount)}</strong>
                </div>
                <div className={styles.metricCell}>
                  <span>Growth reference</span>
                  <strong>{formatDecimal(segment.predictedGrowthRateReference * 100, 1)}%</strong>
                </div>
                <div className={styles.metricCell}>
                  <span>Count reference</span>
                  <strong>{formatNumber(segment.predictedCountReference)}</strong>
                </div>
              </div>
            </article>
          ))}
        </div>
      ) : null}
      {context.segments.length > 0 ? (
        <p className="portfolio-small-note">
          Direction band is primary. Coverage is current-state only, not historical chronology.
        </p>
      ) : null}
    </Surface>
  );
}
