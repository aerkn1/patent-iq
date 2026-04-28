"use client";

import clsx from "clsx";
import { useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  type TooltipProps,
  XAxis,
  YAxis,
} from "recharts";

import { PortfolioPaginationControls } from "@/components/portfolio/portfolio-pagination";
import { formatDecimal, formatNumber } from "@/components/portfolio/portfolio-format";
import { PortfolioTooltipLabel } from "@/components/portfolio/portfolio-tooltip-label";
import { InfoPill } from "@/components/ui/data-pill";
import { Surface } from "@/components/ui/surface";
import { getFocusAwareBarColor } from "@/lib/design/chart-tokens";
import { workspaceTooltipCopy } from "@/lib/content/workspace-tooltips";
import type { PortfolioCitationFieldsResponse } from "@/lib/types/portfolio-v2";
import styles from "@/components/portfolio/citation-panels.module.css";

type PortfolioCitationFieldsPanelProps = {
  fields: PortfolioCitationFieldsResponse;
  isLoading?: boolean;
  selectedJurisdiction?: string;
  selectedField?: string;
  selectedYear?: string;
  errorMessage?: string;
  onFieldSelect?: (value: string) => void;
  onPageChange?: (offset: number) => void;
};

type ViewMode = "chart" | "table";

type FieldChartRow = {
  wipoField: string;
  latestCitationYear: number;
  citationEventCount: number;
  citingAssigneeCount: number;
  cleanCitationCount: number;
  citationLethalitySum: number;
};

type WrappedAxisTickProps = {
  x?: number;
  y?: number;
  payload?: {
    value?: string;
  };
};

function splitTickLabel(value: string, maxCharsPerLine: number): string[] {
  const normalized = value.trim();
  if (normalized.length === 0) {
    return ["—"];
  }

  const tokens = normalized
    .replace(/([/&-])/g, "$1 ")
    .split(/\s+/)
    .filter(Boolean);

  const lines: string[] = [];
  let current = "";

  for (const token of tokens) {
    if (current.length === 0) {
      current = token;
      continue;
    }

    if (`${current} ${token}`.length <= maxCharsPerLine) {
      current = `${current} ${token}`;
      continue;
    }

    lines.push(current);
    current = token;
  }

  if (current.length > 0) {
    lines.push(current);
  }

  return lines.slice(0, 3);
}

function estimateCategoryRowHeight(label: string, maxCharsPerLine: number): number {
  return splitTickLabel(label, maxCharsPerLine).length * 16 + 14;
}

function WrappedAxisTick({ x = 0, y = 0, payload }: WrappedAxisTickProps) {
  const lines = splitTickLabel(String(payload?.value ?? ""), 18);
  const firstLineOffset = -((lines.length - 1) * 7);

  return (
    <g transform={`translate(${x},${y})`}>
      <text x={-8} y={0} textAnchor="end" fill="#516071" fontSize={11} fontWeight={600}>
        {lines.map((line, index) => (
          <tspan key={`${line}-${index}`} x={-8} dy={index === 0 ? firstLineOffset : 14}>
            {line}
          </tspan>
        ))}
      </text>
    </g>
  );
}

function renderFieldsTooltip({ active, payload }: TooltipProps<number, string>) {
  if (!active || !payload || payload.length === 0) {
    return null;
  }

  const row = payload[0]?.payload as FieldChartRow | undefined;
  if (!row) {
    return null;
  }

  return (
    <div className={styles.chartTooltip}>
      <strong className={styles.chartTooltipTitle}>{row.wipoField || "—"}</strong>
      <div className={styles.chartTooltipRows}>
        <div className={styles.chartTooltipRow}>
          <span className={styles.chartTooltipSeries}>Pressure</span>
          <strong>{formatDecimal(row.citationLethalitySum, 2)}</strong>
        </div>
        <div className={styles.chartTooltipRow}>
          <span className={styles.chartTooltipSeries}>Clean citations</span>
          <strong>{formatNumber(row.cleanCitationCount)}</strong>
        </div>
        <div className={styles.chartTooltipRow}>
          <span className={styles.chartTooltipSeries}>Citing owners</span>
          <strong>{formatNumber(row.citingAssigneeCount)}</strong>
        </div>
        <div className={styles.chartTooltipRow}>
          <span className={styles.chartTooltipSeries}>Last seen</span>
          <strong>{row.latestCitationYear || "—"}</strong>
        </div>
      </div>
    </div>
  );
}

export function PortfolioCitationFieldsPanel({
  fields,
  isLoading = false,
  selectedJurisdiction,
  selectedField,
  selectedYear,
  errorMessage,
  onFieldSelect,
  onPageChange,
}: PortfolioCitationFieldsPanelProps) {
  const [viewMode, setViewMode] = useState<ViewMode>("chart");
  const maxPressure = Math.max(...fields.rows.map((row) => row.citationLethalitySum), 1);
  const chartRows: FieldChartRow[] = fields.rows.slice(0, 8).map((row) => ({
    wipoField: row.wipoField,
    latestCitationYear: row.latestCitationYear,
    citationEventCount: row.citationEventCount,
    citingAssigneeCount: row.citingAssigneeCount,
    cleanCitationCount: row.cleanCitationCount,
    citationLethalitySum: row.citationLethalitySum,
  }));
  const chartHeight = Math.max(340, chartRows.reduce((sum, row) => sum + estimateCategoryRowHeight(row.wipoField, 18), 0) + 20);

  return (
    <Surface
      className="portfolio-panel--citation"
      title={<PortfolioTooltipLabel label="Top Citation Fields" tooltip={workspaceTooltipCopy.citation.topCitationFields} />}
      description="Where citation pressure clusters by field in the current slice."
      badge={
        <InfoPill tone={selectedJurisdiction ? "accent" : "neutral"}>
          {selectedJurisdiction ? `Jurisdiction: ${selectedJurisdiction}` : "All jurisdictions"}
          {selectedYear ? ` · ${selectedYear}` : ""}
        </InfoPill>
      }
      actions={
        fields.rows.length > 0 ? (
          <div className={styles.viewToggle} role="tablist" aria-label="Field pressure map view">
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
        ) : null
      }
    >
      {errorMessage ? <p className="portfolio-error">{errorMessage}</p> : null}
      {isLoading && fields.rows.length > 0 ? <p className="portfolio-small-note">Refreshing citation fields…</p> : null}
      {fields.rows.length === 0 ? (
        isLoading ? (
          <p className="portfolio-empty">Loading citation fields…</p>
        ) : (
          <p className="portfolio-empty">No citation field rows available.</p>
        )
      ) : (
        <>
          <p className="portfolio-small-note">
            {viewMode === "chart"
              ? `Click a bar to constrain the owner and jurisdiction views${selectedYear ? ` for ${selectedYear}` : ""}.`
              : `Select a field to constrain the owner and jurisdiction views${selectedYear ? ` for ${selectedYear}` : ""}.`}
          </p>

          {viewMode === "chart" ? (
            <div className={styles.chartFrame}>
              <ResponsiveContainer width="100%" height={chartHeight}>
                <BarChart data={chartRows} layout="vertical" margin={{ top: 8, right: 16, bottom: 8, left: 8 }}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                  <XAxis type="number" axisLine={false} tickLine={false} />
                  <YAxis
                    type="category"
                    dataKey="wipoField"
                    width={190}
                    interval={0}
                    axisLine={false}
                    tickLine={false}
                    tick={<WrappedAxisTick />}
                  />
                  <Tooltip content={renderFieldsTooltip} cursor={{ fill: "rgba(79, 124, 185, 0.08)" }} />
                  <Bar
                    dataKey="citationLethalitySum"
                    radius={[0, 10, 10, 0]}
                    onClick={(_, index) => {
                      const row = chartRows[index];
                      if (!row) {
                        return;
                      }
                      const nextValue = selectedField === row.wipoField ? "" : row.wipoField;
                      onFieldSelect?.(nextValue);
                    }}
                  >
                    {chartRows.map((row, index) => (
                      <Cell
                        key={row.wipoField || `field-${index}`}
                        fill={getFocusAwareBarColor(index, selectedField === row.wipoField)}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="portfolio-scroll-table">
              <table className={styles.rankTable}>
                <colgroup>
                  <col style={{ width: "10%" }} />
                  <col style={{ width: "34%" }} />
                  <col style={{ width: "24%" }} />
                  <col style={{ width: "12%" }} />
                  <col style={{ width: "10%" }} />
                  <col style={{ width: "10%" }} />
                </colgroup>
                <thead>
                  <tr>
                    <th><PortfolioTooltipLabel label="Rank" tooltip={workspaceTooltipCopy.citation.rank} /></th>
                    <th><PortfolioTooltipLabel label="Field" tooltip={workspaceTooltipCopy.citation.field} /></th>
                    <th><PortfolioTooltipLabel label="Pressure" tooltip={workspaceTooltipCopy.citation.pressure} /></th>
                    <th><PortfolioTooltipLabel label="Citations" tooltip={workspaceTooltipCopy.citation.citations} /></th>
                    <th><PortfolioTooltipLabel label="Owners" tooltip={workspaceTooltipCopy.citation.owners} /></th>
                    <th><PortfolioTooltipLabel label="Last seen" tooltip={workspaceTooltipCopy.citation.lastSeen} /></th>
                  </tr>
                </thead>
                <tbody>
                  {fields.rows.map((row, index) => (
                    <tr
                      key={row.wipoField || "unknown-field"}
                      className={selectedField === row.wipoField ? styles.tableRowSelected : undefined}
                    >
                      <td>{(fields.pagination?.offset ?? 0) + index + 1}</td>
                      <td>
                        <button
                          type="button"
                          className={selectedField === row.wipoField ? "portfolio-link-button selected" : "portfolio-link-button"}
                          onClick={() => onFieldSelect?.(selectedField === row.wipoField ? "" : row.wipoField)}
                        >
                          <strong className={styles.tableCellStrong}>{row.wipoField || "—"}</strong>
                        </button>
                      </td>
                      <td>
                        <div className={styles.metricBarCell}>
                          <span className={styles.tableMetricPrimary}>{formatDecimal(row.citationLethalitySum, 2)}</span>
                          <div className={styles.metricBarTrack} aria-hidden="true">
                            <span
                              className={selectedField === row.wipoField ? styles.metricBarFillAccent : styles.metricBarFill}
                              style={{ width: `${Math.min(Math.max((row.citationLethalitySum / maxPressure) * 100, 5), 100)}%` }}
                            />
                          </div>
                        </div>
                      </td>
                      <td><span className={styles.tableMetricPrimary}>{formatNumber(row.cleanCitationCount)}</span></td>
                      <td><span className={styles.tableMetricPrimary}>{formatNumber(row.citingAssigneeCount)}</span></td>
                      <td><span className={styles.tableMetricPrimary}>{row.latestCitationYear || "—"}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
      <p className={`portfolio-small-note ${styles.footnote}`}>
        Field rows aggregate clean citation counts and can be used to constrain the owner and jurisdiction views.
      </p>
      <PortfolioPaginationControls pagination={fields.pagination} onPageChange={onPageChange} />
    </Surface>
  );
}
