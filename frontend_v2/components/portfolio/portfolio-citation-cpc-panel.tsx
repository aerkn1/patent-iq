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

import { Sparkles } from "lucide-react";

import { formatDecimal, formatNumber } from "@/components/portfolio/portfolio-format";
import { PortfolioTooltipLabel } from "@/components/portfolio/portfolio-tooltip-label";
import { PortfolioPaginationControls } from "@/components/portfolio/portfolio-pagination";
import styles from "@/components/portfolio/citation-panels.module.css";
import { InfoPill } from "@/components/ui/data-pill";
import { Surface } from "@/components/ui/surface";
import { getRankedBarColor } from "@/lib/design/chart-tokens";
import { workspaceTooltipCopy } from "@/lib/content/workspace-tooltips";
import type { PortfolioCitationCpcGroupsResponse } from "@/lib/types/portfolio-v2";

type PortfolioCitationCpcPanelProps = {
  cpcGroups: PortfolioCitationCpcGroupsResponse;
  selectedField: string;
  selectedJurisdiction: string;
  selectedYear: string;
  isLoading?: boolean;
  errorMessage?: string;
  onPageChange?: (offset: number) => void;
};

type ViewMode = "chart" | "table";

type CpcChartRow = {
  cpcMainGroup: string;
  latestCitationYear: number;
  citationEventCount: number;
  cleanCitationCount: number;
  citationLethalitySum: number;
  citedFamilyCount: number;
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

function buildScopeText(field: string, jurisdiction: string, year: string): string {
  const parts: string[] = [];
  if (field) {
    parts.push(field);
  }
  if (jurisdiction) {
    parts.push(jurisdiction);
  }
  if (year) {
    parts.push(year);
  }
  return parts.length > 0 ? parts.join(" · ") : "all citation slices";
}

function renderCpcTooltip({ active, payload }: TooltipProps<number, string>) {
  if (!active || !payload || payload.length === 0) {
    return null;
  }

  const row = payload[0]?.payload as CpcChartRow | undefined;
  if (!row) {
    return null;
  }

  return (
    <div className={styles.chartTooltip}>
      <strong className={styles.chartTooltipTitle}>{row.cpcMainGroup}</strong>
      <div className={styles.chartTooltipRows}>
        <div className={styles.chartTooltipRow}>
          <span className={styles.chartTooltipSeries}>Citation events</span>
          <strong>{formatNumber(row.citationEventCount)}</strong>
        </div>
        <div className={styles.chartTooltipRow}>
          <span className={styles.chartTooltipSeries}>Clean citations</span>
          <strong>{formatNumber(row.cleanCitationCount)}</strong>
        </div>
        <div className={styles.chartTooltipRow}>
          <span className={styles.chartTooltipSeries}>Pressure</span>
          <strong>{formatDecimal(row.citationLethalitySum, 1)}</strong>
        </div>
        <div className={styles.chartTooltipRow}>
          <span className={styles.chartTooltipSeries}>Cited families</span>
          <strong>{formatNumber(row.citedFamilyCount)}</strong>
        </div>
        <div className={styles.chartTooltipRow}>
          <span className={styles.chartTooltipSeries}>Last seen</span>
          <strong>{row.latestCitationYear || "—"}</strong>
        </div>
      </div>
    </div>
  );
}

export function PortfolioCitationCpcPanel({
  cpcGroups,
  selectedField,
  selectedJurisdiction,
  selectedYear,
  isLoading = false,
  errorMessage,
  onPageChange,
}: PortfolioCitationCpcPanelProps) {
  const [viewMode, setViewMode] = useState<ViewMode>("chart");
  const scopeText = buildScopeText(selectedField, selectedJurisdiction, selectedYear);
  const chartRows: CpcChartRow[] = cpcGroups.rows.slice(0, 10).map((row) => ({
    cpcMainGroup: row.cpcMainGroup,
    latestCitationYear: row.latestCitationYear,
    citationEventCount: row.citationEventCount,
    cleanCitationCount: row.cleanCitationCount,
    citationLethalitySum: row.citationLethalitySum,
    citedFamilyCount: row.citedFamilyCount,
  }));
  const chartHeight = Math.max(340, chartRows.reduce((sum, row) => sum + estimateCategoryRowHeight(row.cpcMainGroup, 18), 0) + 20);

  return (
    <Surface
      className="portfolio-panel--citation"
      title={
        <PortfolioTooltipLabel
          label="Top Cited CPC Groups"
          tooltip={workspaceTooltipCopy.citation.topCitedCpcGroups}
        />
      }
      description="Which CPC main groups absorb the most citation activity across the cited family set."
      icon={<Sparkles size={14} />}
      badge={
        <InfoPill tone="neutral">
          {cpcGroups.pagination?.totalCount != null ? `${cpcGroups.pagination.totalCount} total` : `${cpcGroups.rows.length} rows`}
        </InfoPill>
      }
      actions={
        cpcGroups.rows.length > 0 ? (
          <div className={styles.viewToggle} role="tablist" aria-label="CPC concentration view">
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
      <p className="portfolio-small-note">
        CPC main groups attached to cited portfolio families within {scopeText}. Families can contribute to multiple CPC groups.
      </p>
      {isLoading && cpcGroups.rows.length > 0 ? <p className="portfolio-small-note">Refreshing cited CPC groups…</p> : null}
      {cpcGroups.rows.length === 0 && isLoading ? (
        <p className="portfolio-empty">Loading cited CPC groups…</p>
      ) : cpcGroups.rows.length === 0 ? (
        <p className="portfolio-empty">No cited CPC groups available for the current citation slice.</p>
      ) : (
        <>
          {viewMode === "chart" ? (
            <div className={styles.chartFrame}>
              <ResponsiveContainer width="100%" height={chartHeight}>
                <BarChart data={chartRows} layout="vertical" margin={{ top: 8, right: 16, bottom: 8, left: 8 }}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                  <XAxis type="number" axisLine={false} tickLine={false} />
                  <YAxis
                    type="category"
                    dataKey="cpcMainGroup"
                    width={168}
                    interval={0}
                    axisLine={false}
                    tickLine={false}
                    tick={<WrappedAxisTick />}
                  />
                  <Tooltip content={renderCpcTooltip} cursor={{ fill: "rgba(79, 124, 185, 0.08)" }} />
                  <Bar dataKey="citationEventCount" radius={[0, 10, 10, 0]}>
                    {chartRows.map((row, index) => (
                      <Cell key={`${row.cpcMainGroup}-${row.latestCitationYear}`} fill={getRankedBarColor(index)} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="portfolio-scroll-table">
              <table>
                <thead>
                  <tr>
                    <th><PortfolioTooltipLabel label="CPC main group" tooltip={workspaceTooltipCopy.citation.cpcMainGroup} /></th>
                    <th><PortfolioTooltipLabel label="Events" tooltip={workspaceTooltipCopy.citation.events} /></th>
                    <th><PortfolioTooltipLabel label="Citations" tooltip={workspaceTooltipCopy.citation.citations} /></th>
                    <th><PortfolioTooltipLabel label="Pressure" tooltip={workspaceTooltipCopy.citation.pressure} /></th>
                    <th><PortfolioTooltipLabel label="Cited families" tooltip={workspaceTooltipCopy.citation.citedFamilies} /></th>
                    <th><PortfolioTooltipLabel label="Last seen" tooltip={workspaceTooltipCopy.citation.lastSeen} /></th>
                  </tr>
                </thead>
                <tbody>
                  {cpcGroups.rows.map((row) => (
                    <tr key={`${row.cpcMainGroup}-${row.latestCitationYear}`}>
                      <td>
                        <span className={styles.tableCellStrong}>{row.cpcMainGroup}</span>
                      </td>
                      <td>
                        <span className={styles.tableMetricPrimary}>{formatNumber(row.citationEventCount)}</span>
                      </td>
                      <td>
                        <span className={styles.tableMetricPrimary}>{formatNumber(row.cleanCitationCount)}</span>
                      </td>
                      <td>
                        <span className={styles.tableMetricPrimary}>{formatDecimal(row.citationLethalitySum, 1)}</span>
                      </td>
                      <td>
                        <span className={styles.tableMetricPrimary}>{formatNumber(row.citedFamilyCount)}</span>
                      </td>
                      <td>
                        <span className={styles.tableMetricPrimary}>{row.latestCitationYear || "—"}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
      <PortfolioPaginationControls pagination={cpcGroups.pagination} onPageChange={onPageChange} />
    </Surface>
  );
}
