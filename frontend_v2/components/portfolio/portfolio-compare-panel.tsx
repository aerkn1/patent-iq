"use client";

import clsx from "clsx";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { formatDecimal } from "@/components/portfolio/portfolio-format";
import { StatusPill } from "@/components/ui/data-pill";
import { Surface } from "@/components/ui/surface";
import { chartTokens, getCompareDeltaColor } from "@/lib/design/chart-tokens";
import type { PortfolioCompareTimesliceResponse } from "@/lib/types/portfolio-v2";
import styles from "@/components/portfolio/technology-panels.module.css";

type PortfolioComparePanelProps = {
  compare: PortfolioCompareTimesliceResponse;
  errorMessage?: string;
};

function deltaTone(value: number): "positive" | "warning" | "critical" {
  if (value >= 0) {
    return "positive";
  }

  if (value <= -10) {
    return "critical";
  }

  return "warning";
}

export function PortfolioComparePanel({ compare, errorMessage }: PortfolioComparePanelProps) {
  const chartRows = [...compare.rows].sort((left, right) => Math.abs(right.delta) - Math.abs(left.delta));
  const maxAbsDelta = Math.max(10, ...chartRows.map((row) => Math.abs(row.delta)));

  return (
    <Surface className="portfolio-panel--compare" title="Field compare">
      {errorMessage ? <p className="portfolio-error">{errorMessage}</p> : null}
      {compare.rows.length === 0 ? (
        <p className="portfolio-empty">No compare-safe year pair available.</p>
      ) : (
        <>
          <div className={clsx(styles.chartShell, styles.compareChartShell)}>
            <h4 className={styles.chartShellTitle}>Normalized score spread by metric</h4>
            <ResponsiveContainer width="100%" height={320}>
              <BarChart data={chartRows} layout="vertical" margin={{ top: 20, right: 16, left: 16, bottom: 4 }}>
                <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                <XAxis
                  type="number"
                  domain={[-maxAbsDelta, maxAbsDelta]}
                  tickFormatter={(value: number) => formatDecimal(value, 1)}
                />
                <YAxis type="category" dataKey="label" width={128} tickLine={false} axisLine={false} />
                <Tooltip
                  formatter={(value: number) => [`${formatDecimal(value, 2)} delta`, "Score spread"]}
                  labelFormatter={(label) => `Metric: ${label}`}
                />
                <ReferenceLine x={0} stroke={chartTokens.reference.axis} />
                <Bar dataKey="delta" radius={[0, 8, 8, 0]}>
                  {chartRows.map((row) => (
                    <Cell key={row.metric} fill={getCompareDeltaColor(row.delta)} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className={styles.compareMatrix}>
            {chartRows.map((row) => (
              <article key={row.metric} className={styles.compareRow}>
                <div className={styles.compareRowHead}>
                  <div className={styles.compareIdentity}>
                    <strong>{row.label}</strong>
                    <span>{row.metric}</span>
                  </div>
                  <div className={styles.compareRowMeta}>
                    <span
                      className={clsx(
                        styles.deltaPill,
                        row.delta > 0 && styles.deltaPositive,
                        row.delta < 0 && styles.deltaNegative,
                        row.delta === 0 && styles.deltaNeutral,
                      )}
                    >
                      {row.delta >= 0 ? "+" : ""}
                      {formatDecimal(row.delta, 2)} delta
                    </span>
                    <StatusPill tone={deltaTone(row.delta)}>
                      {row.delta > 0 ? "current leading" : row.delta < 0 ? "compare leading" : "balanced"}
                    </StatusPill>
                  </div>
                </div>
                <div className={styles.compareEvidence}>
                  <div className={styles.compareEvidenceCell}>
                    <span>Current raw</span>
                    <strong>{formatDecimal(row.currentValue, 2)}</strong>
                    <small>{row.currentYear}</small>
                  </div>
                  <div className={styles.compareEvidenceCell}>
                    <span>Compare raw</span>
                    <strong>{formatDecimal(row.compareValue, 2)}</strong>
                    <small>{row.compareYear}</small>
                  </div>
                  <div className={styles.compareEvidenceCell}>
                    <span>Current score</span>
                    <strong>{formatDecimal(row.currentScore, 1)}</strong>
                    <small>0 to 100 normalized</small>
                  </div>
                  <div className={styles.compareEvidenceCell}>
                    <span>Compare score</span>
                    <strong>{formatDecimal(row.compareScore, 1)}</strong>
                    <small>0 to 100 normalized</small>
                  </div>
                </div>
              </article>
            ))}
          </div>
        </>
      )}
      <p className="portfolio-small-note">
        Score columns are normalized to 0-100 for shape comparison. Raw columns remain the evidence values.
      </p>
    </Surface>
  );
}
