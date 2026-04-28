"use client";

import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { formatNumber, formatPercent } from "@/components/portfolio/portfolio-format";
import { PortfolioTooltipLabel } from "@/components/portfolio/portfolio-tooltip-label";
import { Surface } from "@/components/ui/surface";
import { workspaceTooltipCopy } from "@/lib/content/workspace-tooltips";
import type { PortfolioStatusTimeseriesResponse } from "@/lib/types/portfolio-v2";
import styles from "@/components/portfolio/citation-panels.module.css";

type PortfolioStatusChronologyPanelProps = {
  history: PortfolioStatusTimeseriesResponse;
  isLoading?: boolean;
  errorMessage?: string;
};

const SERIES = [
  { key: "fullyActiveFamilyCount", label: "Fully active", color: "#2f9e44" },
  { key: "partiallyLapsedFamilyCount", label: "Partially lapsed", color: "#e03131" },
  { key: "deadFamilyCount", label: "Dead", color: "#5c677d" },
] as const;

export function PortfolioStatusChronologyPanel({
  history,
  isLoading = false,
  errorMessage,
}: PortfolioStatusChronologyPanelProps) {
  const latestRow = history.rows[history.rows.length - 1];
  const audit = history.audit;

  return (
    <Surface
      className="portfolio-panel--timeline"
      title={
        <PortfolioTooltipLabel
          label="Family status chronology"
          tooltip={workspaceTooltipCopy.overview.familyStatusChronology}
        />
      }
      description="Historical distribution of fully active, partially lapsed, and dead families across the current portfolio replay."
    >
      {errorMessage ? <p className="portfolio-error">{errorMessage}</p> : null}
      {isLoading && history.rows.length > 0 ? <p className="portfolio-small-note">Refreshing status chronology…</p> : null}
      {history.rows.length === 0 ? (
        isLoading ? (
          <p className="portfolio-empty">Loading status chronology…</p>
        ) : (
          <p className="portfolio-empty">No status chronology loaded.</p>
        )
      ) : (
        <>
          <div className={styles.kpiStrip}>
            <article className={styles.signalCard}>
              <PortfolioTooltipLabel
                label="Latest year"
                tooltip={workspaceTooltipCopy.overview.latestYear}
                textClassName={styles.signalLabel}
              />
              <strong className={styles.signalValue}>{latestRow.year}</strong>
              <span className={styles.signalCopy}>{formatNumber(latestRow.familyCount)} families in replay scope</span>
            </article>
            <article className={styles.signalCard}>
              <PortfolioTooltipLabel
                label="Fully active"
                tooltip={workspaceTooltipCopy.overview.fullyActive}
                textClassName={styles.signalLabel}
              />
              <strong className={styles.signalValue}>{formatNumber(latestRow.fullyActiveFamilyCount)}</strong>
              <span className={styles.signalCopy}>{formatPercent(latestRow.fullyActiveShare)} of latest year</span>
            </article>
            <article className={styles.signalCard}>
              <PortfolioTooltipLabel
                label="Lapsed + dead"
                tooltip={workspaceTooltipCopy.overview.lapsedAndDead}
                textClassName={styles.signalLabel}
              />
              <strong className={styles.signalValue}>
                {formatNumber(latestRow.partiallyLapsedFamilyCount + latestRow.deadFamilyCount)}
              </strong>
              <span className={styles.signalCopy}>
                {formatPercent(latestRow.partiallyLapsedShare + latestRow.deadShare)} of latest year
              </span>
            </article>
          </div>

          <div className={styles.chartSurface}>
            <div className={styles.chartHeader}>
              <div className={styles.chartEyebrow}>Legal replay</div>
              <h4 className={styles.chartTitle}>
                <PortfolioTooltipLabel
                  label="Status mix over time"
                  tooltip={workspaceTooltipCopy.overview.statusMixOverTime}
                />
              </h4>
            </div>
            <ResponsiveContainer width="100%" height={260}>
              <AreaChart data={history.rows} margin={{ top: 16, right: 18, left: 4, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="year" />
                <YAxis />
                <Tooltip
                  formatter={(value: number, name: string) => [formatNumber(value), name]}
                  labelFormatter={(label) => `Year: ${label}`}
                />
                {SERIES.map((series) => (
                  <Area
                    key={series.key}
                    type="monotone"
                    dataKey={series.key}
                    name={series.label}
                    stackId="status"
                    stroke={series.color}
                    fill={series.color}
                    fillOpacity={0.9}
                    isAnimationActive={false}
                  />
                ))}
              </AreaChart>
            </ResponsiveContainer>
            <div className={styles.legend}>
              {SERIES.map((series) => (
                <span key={series.key} className={styles.legendItem}>
                  <span className={styles.legendSwatch} style={{ background: series.color }} />
                  <PortfolioTooltipLabel
                    label={series.label}
                    tooltip={
                      series.key === "fullyActiveFamilyCount"
                        ? workspaceTooltipCopy.overview.fullyActive
                        : series.key === "partiallyLapsedFamilyCount"
                          ? workspaceTooltipCopy.overview.partiallyLapsed
                          : workspaceTooltipCopy.overview.dead
                    }
                  />
                </span>
              ))}
            </div>
          </div>

          <p className={`portfolio-small-note ${styles.footnote}`}>
            Audit: {audit.supportLevel} support with {formatPercent(audit.coveragePct)} coverage
            {audit.coveredCount != null && audit.denominatorCount != null
              ? ` across ${formatNumber(audit.coveredCount)}/${formatNumber(audit.denominatorCount)} returned years`
              : ""}
            . {audit.coverageCaveatText ?? "Historical owner truth remains replay-based in this chronology."}
          </p>
        </>
      )}
    </Surface>
  );
}
