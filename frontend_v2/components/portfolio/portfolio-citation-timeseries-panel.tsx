"use client";

import {
  Area,
  CartesianGrid,
  ComposedChart,
  Line,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  type TooltipProps,
  XAxis,
  YAxis,
} from "recharts";

import { PortfolioPaginationControls } from "@/components/portfolio/portfolio-pagination";
import { formatNumber, formatPercent } from "@/components/portfolio/portfolio-format";
import { PortfolioTooltipLabel } from "@/components/portfolio/portfolio-tooltip-label";
import { InfoPill } from "@/components/ui/data-pill";
import { Surface } from "@/components/ui/surface";
import { chartTokens } from "@/lib/design/chart-tokens";
import { workspaceTooltipCopy } from "@/lib/content/workspace-tooltips";
import type {
  ForecastHorizon,
  PortfolioCitationTimeseriesResponse,
  PortfolioForecastContributorsResponse,
  PortfolioForecastPayload,
} from "@/lib/types/portfolio-v2";
import styles from "@/components/portfolio/citation-panels.module.css";

type PortfolioCitationTimeseriesPanelProps = {
  timeseries: PortfolioCitationTimeseriesResponse;
  forecast: PortfolioForecastPayload;
  forecastContributors: PortfolioForecastContributorsResponse;
  isLoading?: boolean;
  forecastContributorsLoading?: boolean;
  forecastHorizon: ForecastHorizon;
  errorMessage?: string;
  forecastContributorsError?: string;
  onForecastHorizonChange: (horizon: ForecastHorizon) => void;
  onForecastContributorPageChange?: (offset: number) => void;
};

type ChartRow = {
  year: number;
  forwardCitationsCleanTotal: number | null;
  forecast3Midpoint: number | null;
  forecast3Lower: number | null;
  forecast3Range: number | null;
  forecast5Midpoint: number | null;
  forecast5Lower: number | null;
  forecast5Range: number | null;
};

type ProjectionDotProps = {
  cx?: number;
  cy?: number;
  payload?: ChartRow;
};

type TooltipSeriesRow = {
  label: string;
  value: string;
  color: string;
};

function roundCitation(value: number | null | undefined): number | null {
  if (value == null || Number.isNaN(value)) {
    return null;
  }

  return Math.max(0, Math.round(value));
}

function formatRoundedCitation(value: number | null | undefined): string {
  const rounded = roundCitation(value);
  return rounded == null ? "—" : formatNumber(rounded);
}

export function PortfolioCitationTimeseriesPanel({
  timeseries,
  forecast,
  forecastContributors,
  isLoading = false,
  forecastContributorsLoading = false,
  forecastHorizon,
  errorMessage,
  forecastContributorsError,
  onForecastHorizonChange,
  onForecastContributorPageChange,
}: PortfolioCitationTimeseriesPanelProps) {
  const latestRow = timeseries.rows[timeseries.rows.length - 1];
  const peakRow =
    [...timeseries.rows].sort((left, right) => right.forwardCitationsCleanTotal - left.forwardCitationsCleanTotal)[0];
  const interval3y = forecast.interval3y;
  const interval5y = forecast.interval5y;
  const latestCitationCount = latestRow?.forwardCitationsCleanTotal ?? null;
  const forecast3Midpoint = latestCitationCount == null ? null : roundCitation(latestCitationCount + interval3y.total);
  const forecast3Low = latestCitationCount == null ? null : roundCitation(latestCitationCount + interval3y.low);
  const forecast3High = latestCitationCount == null ? null : roundCitation(latestCitationCount + interval3y.high);
  const forecast5Midpoint = latestCitationCount == null ? null : roundCitation(latestCitationCount + interval5y.total);
  const forecast5Low = latestCitationCount == null ? null : roundCitation(latestCitationCount + interval5y.low);
  const forecast5High = latestCitationCount == null ? null : roundCitation(latestCitationCount + interval5y.high);
  const projectionBaseYear = latestRow == null ? 2026 : Math.max(latestRow.year, 2026);

  const chartData: ChartRow[] = timeseries.rows.map((row) => ({
    year: row.year,
    forwardCitationsCleanTotal: row.forwardCitationsCleanTotal,
    forecast3Midpoint: null,
    forecast3Lower: null,
    forecast3Range: null,
    forecast5Midpoint: null,
    forecast5Lower: null,
    forecast5Range: null,
  }));

  if (latestRow) {
    const anchorIndex = chartData.findIndex((row) => row.year === projectionBaseYear);
    if (anchorIndex >= 0) {
      chartData[anchorIndex] = {
        ...chartData[anchorIndex],
        forecast3Midpoint: latestRow.forwardCitationsCleanTotal,
        forecast3Lower: latestRow.forwardCitationsCleanTotal,
        forecast3Range: 0,
        forecast5Midpoint: latestRow.forwardCitationsCleanTotal,
        forecast5Lower: latestRow.forwardCitationsCleanTotal,
        forecast5Range: 0,
      };
    } else {
      chartData.push({
        year: projectionBaseYear,
        forwardCitationsCleanTotal: latestRow.forwardCitationsCleanTotal,
        forecast3Midpoint: latestRow.forwardCitationsCleanTotal,
        forecast3Lower: latestRow.forwardCitationsCleanTotal,
        forecast3Range: 0,
        forecast5Midpoint: latestRow.forwardCitationsCleanTotal,
        forecast5Lower: latestRow.forwardCitationsCleanTotal,
        forecast5Range: 0,
      });
    }
    chartData.push({
      year: projectionBaseYear + 3,
      forwardCitationsCleanTotal: null,
      forecast3Midpoint,
      forecast3Lower: forecast3Low,
      forecast3Range:
        forecast3Low == null || forecast3High == null ? null : Math.max(forecast3High - forecast3Low, 0),
      forecast5Midpoint: null,
      forecast5Lower: null,
      forecast5Range: null,
    });
    chartData.push({
      year: projectionBaseYear + 5,
      forwardCitationsCleanTotal: null,
      forecast3Midpoint: null,
      forecast3Lower: null,
      forecast3Range: null,
      forecast5Midpoint,
      forecast5Lower: forecast5Low,
      forecast5Range:
        forecast5Low == null || forecast5High == null ? null : Math.max(forecast5High - forecast5Low, 0),
    });
  }

  chartData.sort((left, right) => left.year - right.year);

  const renderProjectionDot = (
    props: ProjectionDotProps,
    targetYear: number | null,
    color: string,
    label: string,
  ) => {
    if (props.cx == null || props.cy == null || props.payload == null || targetYear == null || props.payload.year !== targetYear) {
      return <g />;
    }

    return (
      <g>
        <circle cx={props.cx} cy={props.cy} r={5.5} fill="#fff" stroke={color} strokeWidth={2.5} />
        <circle cx={props.cx} cy={props.cy} r={2.5} fill={color} />
        <text x={props.cx} y={props.cy - 16} textAnchor="middle" fill={color} fontSize={11} fontWeight={700}>
          <tspan x={props.cx}>{label}</tspan>
        </text>
      </g>
    );
  };

  const renderChronologyTooltip = ({ active, label, payload }: TooltipProps<number, string>) => {
    if (!active || !payload || payload.length === 0) {
      return null;
    }

    const row = payload[0]?.payload as ChartRow | undefined;
    if (!row) {
      return null;
    }

    const tooltipRows = [
      row.forwardCitationsCleanTotal != null
        ? {
            label: "Observed citations",
            value: formatNumber(row.forwardCitationsCleanTotal),
            color: chartTokens.series.accent,
          }
        : null,
      row.forecast3Midpoint != null
        ? {
            label: "3y projection",
            value: formatRoundedCitation(row.forecast3Midpoint),
            color: chartTokens.series.success,
          }
        : null,
      row.forecast5Midpoint != null
        ? {
            label: "5y projection",
            value: formatRoundedCitation(row.forecast5Midpoint),
            color: chartTokens.series.warning,
          }
        : null,
    ].filter(Boolean) as TooltipSeriesRow[];

    return (
      <div className={styles.chartTooltip}>
        <strong className={styles.chartTooltipTitle}>Year {label}</strong>
        <div className={styles.chartTooltipRows}>
          {tooltipRows.map((entry) => (
            <div className={styles.chartTooltipRow} key={entry.label}>
              <span className={styles.chartTooltipSeries}>
                <span className={styles.chartTooltipSwatch} style={{ background: entry.color }} />
                {entry.label}
              </span>
              <strong>{entry.value}</strong>
            </div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <Surface
      className="portfolio-panel--timeline"
      title={
        <PortfolioTooltipLabel
          label="Citation chronology"
          tooltip={workspaceTooltipCopy.citation.citationChronology}
        />
      }
      badge={<InfoPill tone="neutral">{timeseries.rows.length} years</InfoPill>}
    >
      {errorMessage ? <p className="portfolio-error">{errorMessage}</p> : null}
      {isLoading && timeseries.rows.length > 0 ? <p className="portfolio-small-note">Refreshing citation chronology…</p> : null}
      {timeseries.rows.length === 0 ? (
        isLoading ? (
          <p className="portfolio-empty">Loading citation chronology…</p>
        ) : (
          <p className="portfolio-empty">No citation chronology loaded.</p>
        )
      ) : (
        <>
          <div className={styles.kpiStrip}>
            <article className={styles.signalCard}>
              <PortfolioTooltipLabel
                label="Latest year"
                tooltip={workspaceTooltipCopy.citation.latestYear}
                textClassName={styles.signalLabel}
              />
              <strong className={styles.signalValue}>{latestRow.year}</strong>
              <span className={styles.signalCopy}>{formatNumber(latestRow.forwardCitationsCleanTotal)} forward citations</span>
            </article>
            <article className={styles.signalCard}>
              <PortfolioTooltipLabel
                label="3y projection"
                tooltip={workspaceTooltipCopy.citation.projection3y}
                textClassName={styles.signalLabel}
              />
              <strong className={styles.signalValue}>{formatRoundedCitation(forecast3Midpoint)}</strong>
              <span className={styles.signalCopy}>
                Range {formatRoundedCitation(forecast3Low)} to {formatRoundedCitation(forecast3High)}
              </span>
            </article>
            <article className={styles.signalCard}>
              <PortfolioTooltipLabel
                label="5y projection"
                tooltip={workspaceTooltipCopy.citation.projection5y}
                textClassName={styles.signalLabel}
              />
              <strong className={styles.signalValue}>{formatRoundedCitation(forecast5Midpoint)}</strong>
              <span className={styles.signalCopy}>
                Range {formatRoundedCitation(forecast5Low)} to {formatRoundedCitation(forecast5High)}
              </span>
            </article>
          </div>

          <div className={styles.chartSurface}>
            <div className={styles.chartHeader}>
              <div className={styles.chartEyebrow}>Observed history + outlook</div>
            </div>
            <ResponsiveContainer width="100%" height={320}>
              <ComposedChart data={chartData} margin={{ top: 16, right: 18, left: 4, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="year" />
                <YAxis allowDecimals={false} />
                <Tooltip content={renderChronologyTooltip} />
                <ReferenceLine x={peakRow.year} stroke={chartTokens.reference.highlight} strokeDasharray="4 4" />
                <ReferenceLine x={projectionBaseYear + 3} stroke={chartTokens.series.success} strokeDasharray="3 6" strokeOpacity={0.3} />
                <ReferenceLine x={projectionBaseYear + 5} stroke={chartTokens.series.warning} strokeDasharray="3 6" strokeOpacity={0.28} />
                <Area
                  type="monotone"
                  dataKey="forecast3Lower"
                  stackId="forecast3Band"
                  stroke="none"
                  fill="transparent"
                  isAnimationActive={false}
                  legendType="none"
                  connectNulls
                />
                <Area
                  type="monotone"
                  dataKey="forecast3Range"
                  name="3y outlook interval"
                  stackId="forecast3Band"
                  stroke="none"
                  fill={chartTokens.series.success}
                  fillOpacity={0.12}
                  isAnimationActive={false}
                  legendType="none"
                  connectNulls
                />
                <Area
                  type="monotone"
                  dataKey="forecast5Lower"
                  stackId="forecast5Band"
                  stroke="none"
                  fill="transparent"
                  isAnimationActive={false}
                  legendType="none"
                  connectNulls
                />
                <Area
                  type="monotone"
                  dataKey="forecast5Range"
                  name="5y outlook interval"
                  stackId="forecast5Band"
                  stroke="none"
                  fill={chartTokens.series.warning}
                  fillOpacity={0.1}
                  isAnimationActive={false}
                  legendType="none"
                  connectNulls
                />
                <Line
                  type="monotone"
                  dataKey="forwardCitationsCleanTotal"
                  name="Forward citations"
                  stroke={chartTokens.series.accent}
                  strokeWidth={2.6}
                  dot={false}
                  isAnimationActive={false}
                />
                <Line
                  type="monotone"
                  dataKey="forecast3Midpoint"
                  name="3y outlook"
                  stroke={chartTokens.series.success}
                  strokeWidth={2.3}
                  strokeDasharray="6 4"
                  dot={(props) => renderProjectionDot(props, projectionBaseYear + 3, chartTokens.series.success, "3y")}
                  isAnimationActive={false}
                  connectNulls
                />
                <Line
                  type="monotone"
                  dataKey="forecast5Midpoint"
                  name="5y outlook"
                  stroke={chartTokens.series.warning}
                  strokeWidth={2.3}
                  strokeDasharray="3 4"
                  dot={(props) => renderProjectionDot(props, projectionBaseYear + 5, chartTokens.series.warning, "5y")}
                  isAnimationActive={false}
                  connectNulls
                />
              </ComposedChart>
            </ResponsiveContainer>
            <div className={styles.legend}>
              <span className={styles.legendItem}>
                <span className={styles.legendSwatch} style={{ background: chartTokens.series.accent }} />
                <PortfolioTooltipLabel
                  label="Forward citations"
                  tooltip={workspaceTooltipCopy.citation.observedCitations}
                />
              </span>
              <span className={styles.legendItem}>
                <span className={styles.legendSwatch} style={{ background: chartTokens.series.success }} />
                <PortfolioTooltipLabel
                  label="3y projection"
                  tooltip={workspaceTooltipCopy.citation.projection3y}
                />
              </span>
              <span className={styles.legendItem}>
                <span className={styles.legendSwatch} style={{ background: chartTokens.series.warning }} />
                <PortfolioTooltipLabel
                  label="5y projection"
                  tooltip={workspaceTooltipCopy.citation.projection5y}
                />
              </span>
            </div>
          </div>

          <div className={styles.chartSurface}>
            <div className={styles.chartHeaderRow}>
              <div className={styles.chartHeader}>
                <div className={styles.chartEyebrow}>
                  <PortfolioTooltipLabel
                    label="Top forecast driver table"
                    tooltip={workspaceTooltipCopy.citation.forecastContributorTable}
                  />
                </div>
                <p className={styles.chartCopy}>
                  Citation forecast contributors for the selected {forecastHorizon} horizon.
                </p>
              </div>
              <div className="portfolio-horizon-switcher" role="tablist" aria-label="Forecast contributor horizon">
                <button
                  type="button"
                  role="tab"
                  aria-selected={forecastHorizon === "3y"}
                  className={forecastHorizon === "3y" ? "selected" : ""}
                  onClick={() => onForecastHorizonChange("3y")}
                >
                  3y
                </button>
                <button
                  type="button"
                  role="tab"
                  aria-selected={forecastHorizon === "5y"}
                  className={forecastHorizon === "5y" ? "selected" : ""}
                  onClick={() => onForecastHorizonChange("5y")}
                >
                  5y
                </button>
              </div>
            </div>
            {forecastContributorsError ? <p className="portfolio-error">{forecastContributorsError}</p> : null}
            {forecastContributorsLoading && forecastContributors.rows.length > 0 ? (
              <p className="portfolio-small-note">Refreshing forecast contributors…</p>
            ) : null}
            {forecastContributors.rows.length === 0 ? (
              forecastContributorsLoading ? (
                <p className="portfolio-empty">Loading forecast contributors…</p>
              ) : (
                <p className="portfolio-empty">No forecast contributor rows available.</p>
              )
            ) : (
              <>
                <div className="portfolio-scroll-table">
                  <table>
                    <thead>
                      <tr>
                        <th><PortfolioTooltipLabel label="Rank" tooltip={workspaceTooltipCopy.citation.rank} /></th>
                        <th>
                          <PortfolioTooltipLabel
                            label="Contributor"
                            tooltip={workspaceTooltipCopy.citation.contributor}
                          />
                        </th>
                        <th>
                          <PortfolioTooltipLabel
                            label="Contribution"
                            tooltip={workspaceTooltipCopy.citation.contribution}
                          />
                        </th>
                        <th><PortfolioTooltipLabel label="Share" tooltip={workspaceTooltipCopy.citation.share} /></th>
                      </tr>
                    </thead>
                    <tbody>
                      {forecastContributors.rows.map((row) => (
                        <tr key={`${row.horizon}-${row.contributorEntityId}-${row.contributorRank}`}>
                          <td><span className={styles.tableMetricPrimary}>#{row.contributorRank}</span></td>
                          <td><strong className={styles.tableCellStrong}>{row.contributorEntityId}</strong></td>
                          <td><span className={styles.tableMetricPrimary}>{formatRoundedCitation(row.contributionValue)}</span></td>
                          <td><span className={styles.tableMetricPrimary}>{formatPercent(row.contributionShare, 2)}</span></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <PortfolioPaginationControls
                  pagination={forecastContributors.pagination}
                  onPageChange={onForecastContributorPageChange}
                />
              </>
            )}
          </div>
        </>
      )}
    </Surface>
  );
}
