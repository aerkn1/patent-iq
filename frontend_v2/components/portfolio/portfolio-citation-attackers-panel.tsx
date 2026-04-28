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

import { PortfolioCitationControlBar } from "@/components/portfolio/portfolio-citation-control-bar";
import { PortfolioPaginationControls } from "@/components/portfolio/portfolio-pagination";
import { formatDecimal, formatNumber } from "@/components/portfolio/portfolio-format";
import { PortfolioTooltipLabel } from "@/components/portfolio/portfolio-tooltip-label";
import { FieldPill, InfoPill } from "@/components/ui/data-pill";
import { Surface } from "@/components/ui/surface";
import { getRankedBarColor } from "@/lib/design/chart-tokens";
import { workspaceTooltipCopy } from "@/lib/content/workspace-tooltips";
import type { PortfolioCitationAttackersResponse } from "@/lib/types/portfolio-v2";
import styles from "@/components/portfolio/citation-panels.module.css";

type PortfolioCitationAttackersPanelProps = {
  attackers: PortfolioCitationAttackersResponse;
  isLoading?: boolean;
  fieldOptions: string[];
  jurisdictionOptions: string[];
  yearOptions: number[];
  selectedField: string;
  selectedJurisdiction: string;
  selectedYear: string;
  errorMessage?: string;
  onFieldChange: (value: string) => void;
  onJurisdictionChange: (value: string) => void;
  onYearChange: (value: string) => void;
  onClearFilters: () => void;
  onPageChange?: (offset: number) => void;
};

type ViewMode = "chart" | "table";

type AttackerChartRow = {
  citingAssignee: string;
  wipoField: string;
  jurisdictionCode: string;
  latestCitationYear: number;
  citationEventCount: number;
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
  const lines = splitTickLabel(String(payload?.value ?? ""), 22);
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

function renderAttackersTooltip({ active, payload }: TooltipProps<number, string>) {
  if (!active || !payload || payload.length === 0) {
    return null;
  }

  const row = payload[0]?.payload as AttackerChartRow | undefined;
  if (!row) {
    return null;
  }

  return (
    <div className={styles.chartTooltip}>
      <strong className={styles.chartTooltipTitle}>{row.citingAssignee}</strong>
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
          <span className={styles.chartTooltipSeries}>Citation events</span>
          <strong>{formatNumber(row.citationEventCount)}</strong>
        </div>
        <div className={styles.chartTooltipRow}>
          <span className={styles.chartTooltipSeries}>Field</span>
          <strong>{row.wipoField || "—"}</strong>
        </div>
        <div className={styles.chartTooltipRow}>
          <span className={styles.chartTooltipSeries}>Jurisdiction</span>
          <strong>{row.jurisdictionCode || "—"}</strong>
        </div>
        <div className={styles.chartTooltipRow}>
          <span className={styles.chartTooltipSeries}>Last seen</span>
          <strong>{row.latestCitationYear || "—"}</strong>
        </div>
      </div>
    </div>
  );
}

export function PortfolioCitationAttackersPanel({
  attackers,
  isLoading = false,
  fieldOptions,
  jurisdictionOptions,
  yearOptions,
  selectedField,
  selectedJurisdiction,
  selectedYear,
  errorMessage,
  onFieldChange,
  onJurisdictionChange,
  onYearChange,
  onClearFilters,
  onPageChange,
}: PortfolioCitationAttackersPanelProps) {
  const [viewMode, setViewMode] = useState<ViewMode>("chart");
  const sliceLabel = [selectedYear || "All years", selectedField || "All fields", selectedJurisdiction || "All jurisdictions"].join(" · ");
  const chartRows: AttackerChartRow[] = attackers.rows.slice(0, 10).map((row) => ({
    citingAssignee: row.citingAssignee,
    wipoField: row.wipoField,
    jurisdictionCode: row.jurisdictionCode,
    latestCitationYear: row.latestCitationYear,
    citationEventCount: row.citationEventCount,
    cleanCitationCount: row.cleanCitationCount,
    citationLethalitySum: row.citationLethalitySum,
  }));
  const chartHeight = Math.max(340, chartRows.reduce((sum, row) => sum + estimateCategoryRowHeight(row.citingAssignee, 22), 0) + 20);

  return (
    <Surface
      className="portfolio-panel--citation"
      title={<PortfolioTooltipLabel label="Top Citing Owners" tooltip={workspaceTooltipCopy.citation.topCitingOwners} />}
      description="Owner pressure ranked by citation lethality and volume within the current citation slice."
      badge={
        <InfoPill tone="neutral">
          {attackers.pagination?.totalCount != null ? `${attackers.pagination.totalCount} total` : `${attackers.rows.length} rows`}
        </InfoPill>
      }
      actions={
        attackers.rows.length > 0 ? (
          <div className={styles.viewToggle} role="tablist" aria-label="Top citing owners view">
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
      <PortfolioCitationControlBar
        fieldOptions={fieldOptions}
        jurisdictionOptions={jurisdictionOptions}
        yearOptions={yearOptions}
        selectedField={selectedField}
        selectedJurisdiction={selectedJurisdiction}
        selectedYear={selectedYear}
        onFieldChange={onFieldChange}
        onJurisdictionChange={onJurisdictionChange}
        onYearChange={onYearChange}
        onClear={onClearFilters}
      />
      {isLoading && attackers.rows.length > 0 ? <p className="portfolio-small-note">Refreshing citing-owner ranking…</p> : null}
      {attackers.rows.length === 0 ? (
        isLoading ? (
          <p className="portfolio-empty">Loading citing-owner ranking…</p>
        ) : (
          <p className="portfolio-empty">No attacker rows available.</p>
        )
      ) : (
        <>
          <p className="portfolio-small-note">
            {viewMode === "chart"
              ? `Bars show citing-owner pressure for the current ranked slice. Current scope: ${sliceLabel}.`
              : `Citing owners ranked in the current citation slice. Current scope: ${sliceLabel}.`}
          </p>
          {viewMode === "chart" ? (
            <div className={styles.chartFrame}>
              <ResponsiveContainer width="100%" height={chartHeight}>
                <BarChart data={chartRows} layout="vertical" margin={{ top: 8, right: 16, bottom: 8, left: 16 }}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                  <XAxis type="number" axisLine={false} tickLine={false} />
                  <YAxis
                    type="category"
                    dataKey="citingAssignee"
                    width={240}
                    interval={0}
                    axisLine={false}
                    tickLine={false}
                    tick={<WrappedAxisTick />}
                  />
                  <Tooltip content={renderAttackersTooltip} cursor={{ fill: "rgba(79, 124, 185, 0.08)" }} />
                  <Bar dataKey="citationLethalitySum" radius={[0, 10, 10, 0]}>
                    {chartRows.map((row, index) => (
                      <Cell key={`${row.citingAssignee}-${row.wipoField}-${row.jurisdictionCode}`} fill={getRankedBarColor(index)} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="portfolio-scroll-table">
              <table className={styles.attackersTable}>
                <colgroup>
                  <col style={{ width: "7%" }} />
                  <col style={{ width: "29%" }} />
                  <col style={{ width: "22%" }} />
                  <col style={{ width: "14%" }} />
                  <col style={{ width: "18%" }} />
                  <col style={{ width: "10%" }} />
                </colgroup>
                <thead>
                  <tr>
                    <th><PortfolioTooltipLabel label="Rank" tooltip={workspaceTooltipCopy.citation.rank} /></th>
                    <th><PortfolioTooltipLabel label="Owner" tooltip={workspaceTooltipCopy.citation.topCitingOwners} /></th>
                    <th><PortfolioTooltipLabel label="Field" tooltip={workspaceTooltipCopy.citation.field} /></th>
                    <th><PortfolioTooltipLabel label="Pressure" tooltip={workspaceTooltipCopy.citation.pressure} /></th>
                    <th><PortfolioTooltipLabel label="Citations" tooltip={workspaceTooltipCopy.citation.citations} /></th>
                    <th><PortfolioTooltipLabel label="Last seen" tooltip={workspaceTooltipCopy.citation.lastSeen} /></th>
                  </tr>
                </thead>
                <tbody>
                  {attackers.rows.map((row, index) => (
                    <tr key={`${row.citingAssignee}-${row.wipoField}-${row.jurisdictionCode}`}>
                      <td>{(attackers.pagination?.offset ?? 0) + index + 1}</td>
                      <td>
                        <div className={styles.tableCellPrimary}>
                          <strong className={styles.tableCellStrong}>{row.citingAssignee}</strong>
                        </div>
                      </td>
                      <td>
                        <div className={styles.tableCellPrimary}>
                          <FieldPill soft>{row.wipoField || "—"}</FieldPill>
                        </div>
                      </td>
                      <td>
                        <div className={styles.tableCellPrimary}>
                          <span className={styles.tableMetricPrimary}>{formatDecimal(row.citationLethalitySum, 2)}</span>
                        </div>
                      </td>
                      <td>
                        <div className={styles.tableCellPrimary}>
                          <span className={styles.tableMetricPrimary}>{formatNumber(row.cleanCitationCount)}</span>
                        </div>
                      </td>
                      <td>
                        <div className={styles.tableCellPrimary}>
                          <span className={styles.tableMetricPrimary}>{row.latestCitationYear || "—"}</span>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
      <p className={`portfolio-small-note ${styles.footnote}`}>
        Citing-owner rows are ranked by citation pressure, then citation count.
      </p>
      <PortfolioPaginationControls pagination={attackers.pagination} onPageChange={onPageChange} />
    </Surface>
  );
}
