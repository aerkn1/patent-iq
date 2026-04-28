"use client";

import {
  Area,
  Bar,
  Brush,
  CartesianGrid,
  ComposedChart,
  ReferenceLine,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { formatDecimal, formatNumber } from "@/components/portfolio/portfolio-format";
import { PortfolioTooltipLabel } from "@/components/portfolio/portfolio-tooltip-label";
import { Surface } from "@/components/ui/surface";
import { chartTokens } from "@/lib/design/chart-tokens";
import { workspaceTooltipCopy } from "@/lib/content/workspace-tooltips";
import type { PortfolioFilingTimeseriesResponse } from "@/lib/types/portfolio-v2";
import styles from "@/components/portfolio/citation-panels.module.css";

type PortfolioFilingStrengthPanelProps = {
  timeseries: PortfolioFilingTimeseriesResponse;
  isLoading?: boolean;
  errorMessage?: string;
};

export function PortfolioFilingStrengthPanel({
  timeseries,
  isLoading = false,
  errorMessage,
}: PortfolioFilingStrengthPanelProps) {
  const latestRow = timeseries.rows[timeseries.rows.length - 1];
  const peakRow =
    [...timeseries.rows].sort((left, right) => right.familyFilingCount - left.familyFilingCount || left.year - right.year)[0];
  const rollingDeltaPct = latestRow ? latestRow.rolling3yChangePct * 100 : 0;
  const momentumToneClass =
    latestRow?.momentumDirection === "accelerating"
      ? styles.tonalPositive
      : latestRow?.momentumDirection === "cooling"
        ? styles.tonalCritical
        : styles.tonalNeutral;
  const rollingDeltaLabel =
    latestRow == null
      ? "—"
      : `${rollingDeltaPct >= 0 ? "+" : ""}${formatDecimal(rollingDeltaPct, 1)}% vs prior 3y`;

  return (
    <Surface
      className="portfolio-panel--timeline"
      title={<PortfolioTooltipLabel label="Filing chronology" tooltip={workspaceTooltipCopy.overview.filingChronology} />}
    >
      {errorMessage ? <p className="portfolio-error">{errorMessage}</p> : null}
      {isLoading && timeseries.rows.length > 0 ? <p className="portfolio-small-note">Refreshing filing chronology…</p> : null}
      {timeseries.rows.length === 0 ? (
        isLoading ? (
          <p className="portfolio-empty">Loading filing chronology…</p>
        ) : (
          <p className="portfolio-empty">No filing chronology loaded.</p>
        )
      ) : (
        <>
          <div className={styles.kpiStrip}>
            <article className={styles.signalCard}>
              <PortfolioTooltipLabel
                label="Latest filing year"
                tooltip={workspaceTooltipCopy.overview.latestFilingYear}
                textClassName={styles.signalLabel}
              />
              <strong className={styles.signalValue}>{latestRow.year}</strong>
              <span className={styles.signalCopy}>{formatNumber(latestRow.familyFilingCount)} family filings</span>
            </article>
            <article className={styles.signalCard}>
              <PortfolioTooltipLabel
                label="Peak filing year"
                tooltip={workspaceTooltipCopy.overview.peakFilingYear}
                textClassName={styles.signalLabel}
              />
              <strong className={styles.signalValue}>{peakRow.year}</strong>
              <span className={styles.signalCopy}>{formatNumber(peakRow.familyFilingCount)} family filings</span>
            </article>
            <article className={styles.signalCard}>
              <PortfolioTooltipLabel
                label="Latest 3y window"
                tooltip={workspaceTooltipCopy.overview.latestThreeYearWindow}
                textClassName={styles.signalLabel}
              />
              <strong className={styles.signalValue}>{formatNumber(latestRow.rolling3yFamilyFilingCount)}</strong>
              <span className={styles.signalCopy}>
                <span className={momentumToneClass}>{latestRow.momentumDirection}</span>
                {" · "}
                {rollingDeltaLabel}
              </span>
            </article>
          </div>

          <div className={styles.chartSurface}>
            <div className={styles.chartHeader}>
              <div className={styles.chartEyebrow}>Historical buildup</div>
              <h4 className={styles.chartTitle}>
                <PortfolioTooltipLabel
                  label="Annual, rolling 3y, and cumulative portfolio buildup"
                  tooltip={workspaceTooltipCopy.overview.filingBuildup}
                />
              </h4>
            </div>
            <ResponsiveContainer width="100%" height={260}>
              <ComposedChart data={timeseries.rows} margin={{ top: 16, right: 18, left: 4, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="year" />
                <YAxis yAxisId="left" />
                <YAxis yAxisId="right" orientation="right" />
                <Tooltip
                  formatter={(value: number, name: string) => [formatDecimal(value, 1), name]}
                  labelFormatter={(label) => `Year: ${label}`}
                />
                <ReferenceLine
                  x={peakRow.year}
                  yAxisId="left"
                  stroke={chartTokens.reference.highlight}
                  strokeDasharray="4 4"
                />
                <Bar
                  yAxisId="left"
                  dataKey="familyFilingCount"
                  name="Annual family filings"
                  fill={chartTokens.series.accent}
                  radius={[8, 8, 0, 0]}
                  isAnimationActive={false}
                />
                <Area
                  yAxisId="left"
                  type="monotone"
                  dataKey="rolling3yFamilyFilingCount"
                  name="Rolling 3y filings"
                  stroke={chartTokens.series.warning}
                  fill={chartTokens.reference.areaAccent}
                  fillOpacity={1}
                  isAnimationActive={false}
                />
                <Line
                  yAxisId="right"
                  type="monotone"
                  dataKey="cumulativeFamilyCount"
                  name="Cumulative families"
                  stroke={chartTokens.series.info}
                  strokeWidth={2}
                  dot={false}
                  isAnimationActive={false}
                />
                {timeseries.rows.length > 10 ? (
                  <Brush
                    dataKey="year"
                    height={20}
                    stroke={chartTokens.series.info}
                    travellerWidth={10}
                  />
                ) : null}
              </ComposedChart>
            </ResponsiveContainer>
            <div className={styles.legend}>
              <span className={styles.legendItem}>
                <span className={styles.legendSwatch} style={{ background: chartTokens.series.accent }} />
                <PortfolioTooltipLabel
                  label="Annual family filings"
                  tooltip={workspaceTooltipCopy.overview.annualFamilyFilings}
                />
              </span>
              <span className={styles.legendItem}>
                <span className={styles.legendSwatch} style={{ background: chartTokens.series.warning }} />
                <PortfolioTooltipLabel
                  label="Rolling 3y filings"
                  tooltip={workspaceTooltipCopy.overview.rollingThreeYearFilings}
                />
              </span>
              <span className={styles.legendItem}>
                <span className={styles.legendSwatch} style={{ background: chartTokens.series.info }} />
                <PortfolioTooltipLabel
                  label="Cumulative families"
                  tooltip={workspaceTooltipCopy.overview.cumulativeFamilies}
                />
              </span>
            </div>
          </div>

          <p className={`portfolio-small-note ${styles.footnote}`}>
            Anchored on family priority year and shown through the last complete filing year. Current status mix may include newer pending families.
          </p>
        </>
      )}
    </Surface>
  );
}
