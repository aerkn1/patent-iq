"use client";

import clsx from "clsx";
import { useState } from "react";
import {
  CartesianGrid,
  ComposedChart,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { formatNumber } from "@/components/portfolio/portfolio-format";
import { PortfolioTooltipLabel } from "@/components/portfolio/portfolio-tooltip-label";
import { Surface } from "@/components/ui/surface";
import { chartTokens } from "@/lib/design/chart-tokens";
import { workspaceTooltipCopy } from "@/lib/content/workspace-tooltips";
import type { PortfolioJurisdictionUnlockHistoryResponse } from "@/lib/types/portfolio-v2";
import styles from "@/components/portfolio/citation-panels.module.css";

type PortfolioJurisdictionUnlockPanelProps = {
  history: PortfolioJurisdictionUnlockHistoryResponse;
  isLoading?: boolean;
  errorMessage?: string;
};

type UnlockChartRow = PortfolioJurisdictionUnlockHistoryResponse["years"][number] & {
  trackedUnlockCount: number;
};

type UnlockTooltipProps = {
  active?: boolean;
  label?: string | number;
  payload?: Array<{ payload?: UnlockChartRow }>;
};

export function PortfolioJurisdictionUnlockPanel({
  history,
  isLoading = false,
  errorMessage,
}: PortfolioJurisdictionUnlockPanelProps) {
  const [viewMode, setViewMode] = useState<"chart" | "table">("chart");
  const summary = history.summary;
  const unlockYears: UnlockChartRow[] = history.years.map((row) => ({
    ...row,
    trackedUnlockCount: Math.max(
      0,
      row.unlockedJurisdictionCount - row.activeUnlockCount - row.pendingUnlockCount - row.lapsedOnlyUnlockCount,
    ),
  }));

  const renderReachTooltip = ({ active, label, payload }: UnlockTooltipProps) => {
    if (!active || !payload?.length) {
      return null;
    }

    const row = payload[0]?.payload;
    if (!row) {
      return null;
    }

    return (
      <div className={styles.chartTooltip}>
        <strong className={styles.chartTooltipTitle}>Year {label}</strong>
        <div className={styles.chartTooltipRows}>
          <div className={styles.chartTooltipRow}>
            <span className={styles.chartTooltipSeries}>
              <span className={styles.chartTooltipSwatch} style={{ background: chartTokens.series.success }} />
              Active/granted jurisdictions
            </span>
            <strong>{formatNumber(row.activeJurisdictionCount)}</strong>
          </div>
          <div className={styles.chartTooltipRow}>
            <span className={styles.chartTooltipSeries}>
              <span className={styles.chartTooltipSwatch} style={{ background: chartTokens.series.warning }} />
              Pending jurisdictions
            </span>
            <strong>{formatNumber(row.pendingJurisdictionCount)}</strong>
          </div>
          <div className={styles.chartTooltipRow}>
            <span className={styles.chartTooltipSeries}>
              <span className={styles.chartTooltipSwatch} style={{ background: chartTokens.series.critical }} />
              Lapsed jurisdictions
            </span>
            <strong>{formatNumber(row.lapsedJurisdictionCount)}</strong>
          </div>
          <div className={styles.chartTooltipRow}>
            <span>New unlocked jurisdictions</span>
            <strong>{formatNumber(row.unlockedJurisdictionCount)}</strong>
          </div>
          {row.unlockedJurisdictions.length > 0 ? (
            <div className={styles.chartTooltipBlock}>
              <span className={styles.chartTooltipBlockLabel}>Jurisdictions unlocked</span>
              <strong className={styles.chartTooltipBlockValue}>{row.unlockedJurisdictions.join(", ")}</strong>
            </div>
          ) : null}
        </div>
      </div>
    );
  };

  return (
    <Surface
      className="portfolio-panel--timeline"
      title={
        <PortfolioTooltipLabel
          label="Jurisdiction unlock chronology"
          tooltip={workspaceTooltipCopy.overview.jurisdictionUnlockChronology}
        />
      }
      description="First observed jurisdiction years plus yearly active/granted, pending, and lapsed reach from the dense legal branch ledger."
      actions={
        <div className={styles.viewToggle} role="tablist" aria-label="Jurisdiction unlock chronology view">
          <button
            type="button"
            role="tab"
            aria-selected={viewMode === "chart"}
            className={clsx(styles.viewToggleButton, viewMode === "chart" && styles.viewToggleButtonActive)}
            onClick={() => setViewMode("chart")}
          >
            Chart
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={viewMode === "table"}
            className={clsx(styles.viewToggleButton, viewMode === "table" && styles.viewToggleButtonActive)}
            onClick={() => setViewMode("table")}
          >
            Table
          </button>
        </div>
      }
    >
      {errorMessage ? <p className="portfolio-error">{errorMessage}</p> : null}
      {isLoading && history.years.length > 0 ? <p className="portfolio-small-note">Refreshing jurisdiction chronology…</p> : null}
      {history.years.length === 0 ? (
        isLoading ? (
          <p className="portfolio-empty">Loading jurisdiction chronology…</p>
        ) : (
          <p className="portfolio-empty">No jurisdiction unlock chronology loaded.</p>
        )
      ) : (
        <>
          <div className={styles.kpiStrip}>
            <article className={styles.signalCard}>
              <PortfolioTooltipLabel
                label="Unlocked jurisdictions"
                tooltip={workspaceTooltipCopy.overview.unlockedJurisdictions}
                textClassName={styles.signalLabel}
              />
              <strong className={styles.signalValue}>{formatNumber(summary?.unlockedJurisdictionCount ?? 0)}</strong>
              <span className={styles.signalCopy}>
                {summary?.firstUnlockYear ? `First observed in ${summary.firstUnlockYear}` : "No unlock year"}
              </span>
            </article>
            <article className={styles.signalCard}>
              <PortfolioTooltipLabel
                label="Latest active/granted reach"
                tooltip={workspaceTooltipCopy.overview.latestActiveGrantedReach}
                textClassName={styles.signalLabel}
              />
              <strong className={styles.signalValue}>{formatNumber(summary?.latestActiveJurisdictionCount ?? 0)}</strong>
              <span className={styles.signalCopy}>
                {summary?.latestPresenceYear ? `As of ${summary.latestPresenceYear}` : "Latest year unavailable"}
              </span>
            </article>
            <article className={styles.signalCard}>
              <PortfolioTooltipLabel
                label="Latest lapsed reach"
                tooltip={workspaceTooltipCopy.overview.latestLapsedReach}
                textClassName={styles.signalLabel}
              />
              <strong className={styles.signalValue}>{formatNumber(summary?.latestLapsedJurisdictionCount ?? 0)}</strong>
              <span className={styles.signalCopy}>
                {summary?.latestPresenceYear ? `As of ${summary.latestPresenceYear}` : "Latest year unavailable"}
              </span>
            </article>
          </div>

          <div className={styles.chartSurface}>
            <div className={styles.chartHeader}>
              <div className={styles.chartEyebrow}>Jurisdiction state mix</div>
              <h4 className={styles.chartTitle}>
                <PortfolioTooltipLabel
                  label="Active, pending, and lapsed offices over time"
                  tooltip={workspaceTooltipCopy.overview.jurisdictionStateMix}
                />
              </h4>
            </div>
            {viewMode === "chart" ? (
              <>
                <ResponsiveContainer width="100%" height={240}>
                  <ComposedChart data={unlockYears} margin={{ top: 16, right: 18, left: 4, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} />
                    <XAxis dataKey="year" />
                    <YAxis />
                    <Tooltip content={renderReachTooltip} />
                    <Line
                      type="monotone"
                      dataKey="activeJurisdictionCount"
                      name="Active/granted jurisdictions"
                      stroke={chartTokens.series.success}
                      strokeWidth={2.4}
                      dot={false}
                      isAnimationActive={false}
                    />
                    <Line
                      type="monotone"
                      dataKey="pendingJurisdictionCount"
                      name="Pending jurisdictions"
                      stroke={chartTokens.series.warning}
                      strokeWidth={2.2}
                      dot={false}
                      isAnimationActive={false}
                    />
                    <Line
                      type="monotone"
                      dataKey="lapsedJurisdictionCount"
                      name="Lapsed jurisdictions"
                      stroke={chartTokens.series.critical}
                      strokeWidth={2.2}
                      dot={false}
                      isAnimationActive={false}
                    />
                  </ComposedChart>
                </ResponsiveContainer>
                <div className={styles.legend}>
                  <span className={styles.legendItem}>
                    <span className={styles.legendSwatch} style={{ background: chartTokens.series.success }} />
                    <PortfolioTooltipLabel
                      label="Active/granted jurisdictions"
                      tooltip={workspaceTooltipCopy.overview.activeGranted}
                    />
                  </span>
                  <span className={styles.legendItem}>
                    <span className={styles.legendSwatch} style={{ background: chartTokens.series.warning }} />
                    <PortfolioTooltipLabel label="Pending jurisdictions" tooltip={workspaceTooltipCopy.overview.pending} />
                  </span>
                  <span className={styles.legendItem}>
                    <span className={styles.legendSwatch} style={{ background: chartTokens.series.critical }} />
                    <PortfolioTooltipLabel label="Lapsed jurisdictions" tooltip={workspaceTooltipCopy.overview.lapsed} />
                  </span>
                </div>
              </>
            ) : (
              <div className={styles.unlockTableWrap}>
                <table className={styles.unlockTable}>
                  <thead>
                    <tr>
                      <th>
                        <PortfolioTooltipLabel label="Year" tooltip={workspaceTooltipCopy.overview.latestYear} />
                      </th>
                      <th>
                        <PortfolioTooltipLabel label="Active/granted" tooltip={workspaceTooltipCopy.overview.activeGranted} />
                      </th>
                      <th>
                        <PortfolioTooltipLabel label="Pending" tooltip={workspaceTooltipCopy.overview.pending} />
                      </th>
                      <th>
                        <PortfolioTooltipLabel label="Lapsed" tooltip={workspaceTooltipCopy.overview.lapsed} />
                      </th>
                      <th>
                        <PortfolioTooltipLabel label="New unlocks" tooltip={workspaceTooltipCopy.overview.newUnlocks} />
                      </th>
                      <th>
                        <PortfolioTooltipLabel label="Unlock log" tooltip={workspaceTooltipCopy.overview.unlockLog} />
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {unlockYears.map((row) => (
                      <tr key={row.year}>
                        <td>
                          <strong>{row.year}</strong>
                        </td>
                        <td>{formatNumber(row.activeJurisdictionCount)}</td>
                        <td>{formatNumber(row.pendingJurisdictionCount)}</td>
                        <td>{formatNumber(row.lapsedJurisdictionCount)}</td>
                        <td>
                          {formatNumber(row.unlockedJurisdictionCount)}
                          {row.unlockedJurisdictionCount > 0
                            ? ` (${formatNumber(row.activeUnlockCount)} active, ${formatNumber(row.pendingUnlockCount)} pending, ${formatNumber(row.lapsedOnlyUnlockCount)} lapsed${row.trackedUnlockCount > 0 ? `, ${formatNumber(row.trackedUnlockCount)} tracked` : ""})`
                            : ""}
                        </td>
                        <td>{row.unlockedJurisdictions.length > 0 ? row.unlockedJurisdictions.join(", ") : "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </>
      )}
    </Surface>
  );
}
