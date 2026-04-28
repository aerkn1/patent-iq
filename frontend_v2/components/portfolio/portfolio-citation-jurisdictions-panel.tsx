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
import type { PortfolioCitationJurisdictionsResponse } from "@/lib/types/portfolio-v2";
import styles from "@/components/portfolio/citation-panels.module.css";

type PortfolioCitationJurisdictionsPanelProps = {
  jurisdictions: PortfolioCitationJurisdictionsResponse;
  isLoading?: boolean;
  selectedField?: string;
  selectedJurisdiction?: string;
  selectedYear?: string;
  errorMessage?: string;
  onJurisdictionSelect?: (value: string) => void;
  onPageChange?: (offset: number) => void;
};

type ViewMode = "chart" | "table";

type JurisdictionChartRow = {
  jurisdictionCode: string;
  latestCitationYear: number;
  citationEventCount: number;
  citingAssigneeCount: number;
  wipoFieldCount: number;
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
  const lines = splitTickLabel(String(payload?.value ?? ""), 12);
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

function renderJurisdictionsTooltip({ active, payload }: TooltipProps<number, string>) {
  if (!active || !payload || payload.length === 0) {
    return null;
  }

  const row = payload[0]?.payload as JurisdictionChartRow | undefined;
  if (!row) {
    return null;
  }

  return (
    <div className={styles.chartTooltip}>
      <strong className={styles.chartTooltipTitle}>{row.jurisdictionCode || "—"}</strong>
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
          <span className={styles.chartTooltipSeries}>Fields</span>
          <strong>{formatNumber(row.wipoFieldCount)}</strong>
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

export function PortfolioCitationJurisdictionsPanel({
  jurisdictions,
  isLoading = false,
  selectedField,
  selectedJurisdiction,
  selectedYear,
  errorMessage,
  onJurisdictionSelect,
  onPageChange,
}: PortfolioCitationJurisdictionsPanelProps) {
  const [viewMode, setViewMode] = useState<ViewMode>("chart");
  const maxPressure = Math.max(...jurisdictions.rows.map((row) => row.citationLethalitySum), 1);
  const chartRows: JurisdictionChartRow[] = jurisdictions.rows.slice(0, 10).map((row) => ({
    jurisdictionCode: row.jurisdictionCode,
    latestCitationYear: row.latestCitationYear,
    citationEventCount: row.citationEventCount,
    citingAssigneeCount: row.citingAssigneeCount,
    wipoFieldCount: row.wipoFieldCount,
    cleanCitationCount: row.cleanCitationCount,
    citationLethalitySum: row.citationLethalitySum,
  }));
  const chartHeight = Math.max(
    340,
    chartRows.reduce((sum, row) => sum + estimateCategoryRowHeight(row.jurisdictionCode, 12), 0) + 20,
  );

  return (
    <Surface
      className="portfolio-panel--citation"
      title={
        <PortfolioTooltipLabel
          label="Top Citation Jurisdictions"
          tooltip={workspaceTooltipCopy.citation.topCitationJurisdictions}
        />
      }
      description="Where citation pressure lands geographically in the current slice."
      badge={
        <InfoPill tone={selectedField ? "accent" : "neutral"}>
          {selectedField ? `Field: ${selectedField}` : "All fields"}
          {selectedYear ? ` · ${selectedYear}` : ""}
        </InfoPill>
      }
      actions={
        jurisdictions.rows.length > 0 ? (
          <div className={styles.viewToggle} role="tablist" aria-label="Jurisdiction pressure map view">
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
      {isLoading && jurisdictions.rows.length > 0 ? <p className="portfolio-small-note">Refreshing citation jurisdictions…</p> : null}
      {jurisdictions.rows.length === 0 ? (
        isLoading ? (
          <p className="portfolio-empty">Loading citation jurisdictions…</p>
        ) : (
          <p className="portfolio-empty">No citation jurisdiction rows available.</p>
        )
      ) : (
        <>
          <p className="portfolio-small-note">
            {viewMode === "chart"
              ? `Click a bar to constrain the field and owner views${selectedYear ? ` for ${selectedYear}` : ""}.`
              : `Select a jurisdiction to constrain the field and owner views${selectedYear ? ` for ${selectedYear}` : ""}.`}
          </p>
          {viewMode === "chart" ? (
            <div className={styles.chartFrame}>
              <ResponsiveContainer width="100%" height={chartHeight}>
                <BarChart data={chartRows} layout="vertical" margin={{ top: 8, right: 16, bottom: 8, left: 8 }}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                  <XAxis type="number" axisLine={false} tickLine={false} />
                  <YAxis
                    type="category"
                    dataKey="jurisdictionCode"
                    width={128}
                    interval={0}
                    axisLine={false}
                    tickLine={false}
                    tick={<WrappedAxisTick />}
                  />
                  <Tooltip content={renderJurisdictionsTooltip} cursor={{ fill: "rgba(79, 124, 185, 0.08)" }} />
                  <Bar
                    dataKey="citationLethalitySum"
                    radius={[0, 10, 10, 0]}
                    onClick={(_, index) => {
                      const row = chartRows[index];
                      if (!row) {
                        return;
                      }
                      const nextValue = selectedJurisdiction === row.jurisdictionCode ? "" : row.jurisdictionCode;
                      onJurisdictionSelect?.(nextValue);
                    }}
                  >
                    {chartRows.map((row, index) => (
                      <Cell
                        key={row.jurisdictionCode || `jurisdiction-${index}`}
                        fill={getFocusAwareBarColor(index, selectedJurisdiction === row.jurisdictionCode)}
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
                  <col style={{ width: "30%" }} />
                  <col style={{ width: "24%" }} />
                  <col style={{ width: "12%" }} />
                  <col style={{ width: "12%" }} />
                  <col style={{ width: "12%" }} />
                </colgroup>
                <thead>
                  <tr>
                    <th><PortfolioTooltipLabel label="Rank" tooltip={workspaceTooltipCopy.citation.rank} /></th>
                    <th><PortfolioTooltipLabel label="Jurisdiction" tooltip={workspaceTooltipCopy.citation.jurisdictions} /></th>
                    <th><PortfolioTooltipLabel label="Pressure" tooltip={workspaceTooltipCopy.citation.pressure} /></th>
                    <th><PortfolioTooltipLabel label="Citations" tooltip={workspaceTooltipCopy.citation.citations} /></th>
                    <th><PortfolioTooltipLabel label="Fields" tooltip={workspaceTooltipCopy.citation.fields} /></th>
                    <th><PortfolioTooltipLabel label="Last seen" tooltip={workspaceTooltipCopy.citation.lastSeen} /></th>
                  </tr>
                </thead>
                <tbody>
                  {jurisdictions.rows.map((row, index) => (
                    <tr
                      key={row.jurisdictionCode || "unknown-jurisdiction"}
                      className={selectedJurisdiction === row.jurisdictionCode ? styles.tableRowSelected : undefined}
                    >
                      <td>{(jurisdictions.pagination?.offset ?? 0) + index + 1}</td>
                      <td>
                        <button
                          type="button"
                          className={selectedJurisdiction === row.jurisdictionCode ? "portfolio-link-button selected" : "portfolio-link-button"}
                          onClick={() => onJurisdictionSelect?.(selectedJurisdiction === row.jurisdictionCode ? "" : row.jurisdictionCode)}
                        >
                          <strong className={styles.tableCellStrong}>{row.jurisdictionCode || "—"}</strong>
                        </button>
                      </td>
                      <td>
                        <div className={styles.metricBarCell}>
                          <span className={styles.tableMetricPrimary}>{formatDecimal(row.citationLethalitySum, 2)}</span>
                          <div className={styles.metricBarTrack} aria-hidden="true">
                            <span
                              className={selectedJurisdiction === row.jurisdictionCode ? styles.metricBarFillAccent : styles.metricBarFill}
                              style={{ width: `${Math.min(Math.max((row.citationLethalitySum / maxPressure) * 100, 5), 100)}%` }}
                            />
                          </div>
                        </div>
                      </td>
                      <td><span className={styles.tableMetricPrimary}>{formatNumber(row.cleanCitationCount)}</span></td>
                      <td><span className={styles.tableMetricPrimary}>{formatNumber(row.wipoFieldCount)}</span></td>
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
        Jurisdiction rows aggregate clean citation counts and can be used to constrain the field and owner views.
      </p>
      <PortfolioPaginationControls pagination={jurisdictions.pagination} onPageChange={onPageChange} />
    </Surface>
  );
}
