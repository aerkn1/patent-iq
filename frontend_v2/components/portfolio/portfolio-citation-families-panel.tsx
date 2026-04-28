"use client";

import clsx from "clsx";
import Link from "next/link";
import { useState } from "react";
import {
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  type TooltipProps,
  XAxis,
  YAxis,
  ZAxis,
} from "recharts";

import { PortfolioPaginationControls } from "@/components/portfolio/portfolio-pagination";
import { formatDecimal, formatNumber } from "@/components/portfolio/portfolio-format";
import { PortfolioTooltipLabel } from "@/components/portfolio/portfolio-tooltip-label";
import { chartTokens } from "@/lib/design/chart-tokens";
import { FieldPill, InfoPill, StatusPill } from "@/components/ui/data-pill";
import { Surface } from "@/components/ui/surface";
import { workspaceTooltipCopy } from "@/lib/content/workspace-tooltips";
import type { PortfolioCitationFamiliesResponse } from "@/lib/types/portfolio-v2";
import styles from "@/components/portfolio/citation-panels.module.css";

type PortfolioCitationFamiliesPanelProps = {
  families: PortfolioCitationFamiliesResponse;
  isLoading?: boolean;
  fieldOptions: string[];
  selectedField: string;
  selectedStatus: string;
  selectedSort: "forward_clean" | "forward_weighted" | "early_5y" | "early_7y" | "blocking";
  errorMessage?: string;
  onFieldChange: (value: string) => void;
  onStatusChange: (value: string) => void;
  onSortChange: (value: "forward_clean" | "forward_weighted" | "early_5y" | "early_7y" | "blocking") => void;
  onPageChange: (offset: number) => void;
};

type ViewMode = "chart" | "table";

type FamilyChartRow = {
  familyId: string;
  primaryField: string;
  status: string;
  familyPriorityYear: number;
  forwardCitationsClean: number;
  forwardCitationsWeighted: number;
  blockingScore: number;
  uniqueCitingFamilyCount: number;
  earlyCitations7y: number;
};

const statusOptions = [
  { value: "", label: "All statuses" },
  { value: "fully_active", label: "Fully active" },
  { value: "pending_emerging", label: "Pending / emerging" },
  { value: "partially_lapsed", label: "Partially lapsed" },
  { value: "dead", label: "Dead" },
];

function familyStatusTone(status: string): "positive" | "warning" | "critical" | "neutral" {
  if (status.includes("grant") || status.includes("active")) {
    return "positive";
  }
  if (status.includes("pending") || status.includes("emerging")) {
    return "warning";
  }
  if (status.includes("abandon") || status.includes("lapse") || status.includes("dead")) {
    return "critical";
  }
  return "neutral";
}

function familyStatusColor(status: string): string {
  const tone = familyStatusTone(status);
  if (tone === "positive") {
    return chartTokens.series.success;
  }
  if (tone === "warning") {
    return chartTokens.series.warning;
  }
  if (tone === "critical") {
    return chartTokens.series.critical;
  }
  return chartTokens.series.info;
}

function prettyLabel(value: string): string {
  return value
    .split(/[_\s]+/)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1).toLowerCase())
    .join(" ");
}

function renderFamiliesTooltip({ active, payload }: TooltipProps<number, string>) {
  if (!active || !payload || payload.length === 0) {
    return null;
  }

  const row = payload[0]?.payload as FamilyChartRow | undefined;
  if (!row) {
    return null;
  }

  return (
    <div className={styles.chartTooltip}>
      <strong className={styles.chartTooltipTitle}>{row.familyId}</strong>
      <div className={styles.chartTooltipRows}>
        <div className={styles.chartTooltipRow}>
          <span className={styles.chartTooltipSeries}>Field</span>
          <strong>{row.primaryField || "—"}</strong>
        </div>
        <div className={styles.chartTooltipRow}>
          <span className={styles.chartTooltipSeries}>Lifecycle</span>
          <strong>{prettyLabel(row.status)}</strong>
        </div>
        <div className={styles.chartTooltipRow}>
          <span className={styles.chartTooltipSeries}>Forward citations</span>
          <strong>{formatNumber(row.forwardCitationsClean)}</strong>
        </div>
        <div className={styles.chartTooltipRow}>
          <span className={styles.chartTooltipSeries}>Blocking score</span>
          <strong>{formatDecimal(row.blockingScore, 1)}</strong>
        </div>
        <div className={styles.chartTooltipRow}>
          <span className={styles.chartTooltipSeries}>Distinct citing families</span>
          <strong>{formatNumber(row.uniqueCitingFamilyCount)}</strong>
        </div>
        <div className={styles.chartTooltipRow}>
          <span className={styles.chartTooltipSeries}>Priority year</span>
          <strong>{row.familyPriorityYear || "—"}</strong>
        </div>
      </div>
    </div>
  );
}

export function PortfolioCitationFamiliesPanel({
  families,
  isLoading = false,
  fieldOptions,
  selectedField,
  selectedStatus,
  selectedSort,
  errorMessage,
  onFieldChange,
  onStatusChange,
  onSortChange,
  onPageChange,
}: PortfolioCitationFamiliesPanelProps) {
  const [viewMode, setViewMode] = useState<ViewMode>("chart");
  const chartRows: FamilyChartRow[] = families.rows.slice(0, 20).map((row) => ({
    familyId: row.familyId,
    primaryField: row.primaryField,
    status: row.status,
    familyPriorityYear: row.familyPriorityYear,
    forwardCitationsClean: row.forwardCitationsClean,
    forwardCitationsWeighted: row.forwardCitationsWeighted,
    blockingScore: row.blockingScore,
    uniqueCitingFamilyCount: row.uniqueCitingFamilyCount,
    earlyCitations7y: row.earlyCitations7y,
  }));

  return (
    <Surface
      className="portfolio-panel--citation"
      title={<PortfolioTooltipLabel label="Impact drivers" tooltip={workspaceTooltipCopy.citation.impactDrivers} />}
      description="Which cited families combine citation pull, distinct external reach, and blocking strength."
      badge={
        <InfoPill tone="neutral">
          {families.pagination?.totalCount != null ? `${families.pagination.totalCount} total` : `${families.rows.length} rows`}
        </InfoPill>
      }
      actions={
        families.rows.length > 0 ? (
          <div className={styles.viewToggle} role="tablist" aria-label="Impact drivers view">
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
      <div className={styles.filterBar}>
        <div className={styles.filterControls}>
          <div className={styles.filterGroup}>
            <label className={styles.filterLabel} htmlFor="portfolio-citation-family-field">
              <PortfolioTooltipLabel label="Field" tooltip={workspaceTooltipCopy.citation.field} />
            </label>
            <select
              id="portfolio-citation-family-field"
              className={styles.filterSelect}
              value={selectedField}
              onChange={(event) => onFieldChange(event.target.value)}
            >
              <option value="">All fields</option>
              {fieldOptions.map((field) => (
                <option key={field} value={field}>
                  {field}
                </option>
              ))}
            </select>
          </div>

          <div className={styles.filterGroup}>
            <label className={styles.filterLabel} htmlFor="portfolio-citation-family-status">
              <PortfolioTooltipLabel label="Lifecycle" tooltip={workspaceTooltipCopy.citation.lifecycle} />
            </label>
            <select
              id="portfolio-citation-family-status"
              className={styles.filterSelect}
              value={selectedStatus}
              onChange={(event) => onStatusChange(event.target.value)}
            >
              {statusOptions.map((option) => (
                <option key={option.value || "all"} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          <div className={styles.filterGroup}>
            <label className={styles.filterLabel} htmlFor="portfolio-citation-family-sort">
              <PortfolioTooltipLabel label="Sort" tooltip={workspaceTooltipCopy.citation.sort} />
            </label>
            <select
              id="portfolio-citation-family-sort"
              className={styles.filterSelect}
              value={selectedSort}
              onChange={(event) =>
                onSortChange(event.target.value as "forward_clean" | "forward_weighted" | "early_5y" | "early_7y" | "blocking")
              }
            >
              <option value="forward_clean">Forward citations</option>
              <option value="forward_weighted">Forward weighted</option>
              <option value="early_5y">Early citations 5y</option>
              <option value="early_7y">Early citations 7y</option>
              <option value="blocking">Blocking context</option>
            </select>
          </div>
        </div>
      </div>

      {isLoading && families.rows.length > 0 ? <p className="portfolio-small-note">Refreshing cited-family ranking…</p> : null}
      {families.rows.length === 0 && isLoading ? (
        <p className="portfolio-empty">Loading cited-family ranking…</p>
      ) : families.rows.length === 0 ? (
        <p className="portfolio-empty">No cited-family rows available for the current filter.</p>
      ) : (
        <>
          <p className="portfolio-small-note">
            {viewMode === "chart"
              ? "Each bubble is a family on the current ranked slice. Position shows citation pull versus blocking strength; bubble size reflects distinct citing-family breadth."
              : "Portfolio families ranked by citation concentration in the current portfolio."}
          </p>

          {viewMode === "chart" ? (
            <div className={styles.chartFrame}>
              <ResponsiveContainer width="100%" height={340}>
                <ScatterChart margin={{ top: 12, right: 16, bottom: 12, left: 8 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    type="number"
                    dataKey="forwardCitationsClean"
                    name="Forward citations"
                    tickFormatter={(value: number) => formatNumber(value)}
                    axisLine={false}
                    tickLine={false}
                  />
                  <YAxis
                    type="number"
                    dataKey="blockingScore"
                    name="Blocking score"
                    tickFormatter={(value: number) => formatDecimal(value, 1)}
                    axisLine={false}
                    tickLine={false}
                    width={84}
                  />
                  <ZAxis type="number" dataKey="uniqueCitingFamilyCount" range={[120, 620]} />
                  <Tooltip content={renderFamiliesTooltip} cursor={{ stroke: chartTokens.reference.highlight }} />
                  <Scatter data={chartRows}>
                    {chartRows.map((row) => (
                      <Cell key={row.familyId} fill={familyStatusColor(row.status)} fillOpacity={0.9} />
                    ))}
                  </Scatter>
                </ScatterChart>
              </ResponsiveContainer>
              <div className={styles.legend}>
                <span className={styles.legendItem}>
                  <span className={styles.legendSwatch} style={{ background: chartTokens.series.success }} />
                  <PortfolioTooltipLabel label="Fully active" tooltip={workspaceTooltipCopy.overview.fullyActive} />
                </span>
                <span className={styles.legendItem}>
                  <span className={styles.legendSwatch} style={{ background: chartTokens.series.warning }} />
                  <PortfolioTooltipLabel label="Pending / emerging" tooltip={workspaceTooltipCopy.overview.pending} />
                </span>
                <span className={styles.legendItem}>
                  <span className={styles.legendSwatch} style={{ background: chartTokens.series.critical }} />
                  <PortfolioTooltipLabel label="Lapsed / dead" tooltip={workspaceTooltipCopy.overview.lapsedAndDead} />
                </span>
              </div>
            </div>
          ) : (
            <div className="portfolio-scroll-table">
              <table>
                <thead>
                  <tr>
                    <th><PortfolioTooltipLabel label="Rank" tooltip={workspaceTooltipCopy.citation.rank} /></th>
                    <th><PortfolioTooltipLabel label="Family" tooltip={workspaceTooltipCopy.citation.family} /></th>
                    <th><PortfolioTooltipLabel label="Field" tooltip={workspaceTooltipCopy.citation.primaryField} /></th>
                    <th><PortfolioTooltipLabel label="Lifecycle" tooltip={workspaceTooltipCopy.citation.lifecycle} /></th>
                    <th><PortfolioTooltipLabel label="Forward citations" tooltip={workspaceTooltipCopy.citation.forwardCitations} /></th>
                    <th><PortfolioTooltipLabel label="Early 7y" tooltip={workspaceTooltipCopy.citation.earlyCitations7y} /></th>
                    <th><PortfolioTooltipLabel label="Blocking" tooltip={workspaceTooltipCopy.citation.blocking} /></th>
                  </tr>
                </thead>
                <tbody>
                  {families.rows.map((row, index) => (
                    <tr key={row.familyId}>
                      <td>{(families.pagination?.offset ?? 0) + index + 1}</td>
                      <td>
                        <Link
                          href={`/family/${encodeURIComponent(row.familyId)}`}
                          className="portfolio-family-link"
                          aria-label={`Open family ${row.familyId}`}
                        >
                          <strong className={styles.tableCellStrong}>{row.familyId}</strong>
                        </Link>
                      </td>
                      <td>
                        <FieldPill soft>{row.primaryField}</FieldPill>
                      </td>
                      <td>
                        <StatusPill tone={familyStatusTone(row.status)}>{prettyLabel(row.status)}</StatusPill>
                      </td>
                      <td><span className={styles.tableMetricPrimary}>{formatNumber(row.forwardCitationsClean)}</span></td>
                      <td><span className={styles.tableMetricPrimary}>{formatNumber(row.earlyCitations7y)}</span></td>
                      <td><span className={styles.tableMetricPrimary}>{formatDecimal(row.blockingScore, 1)}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          <PortfolioPaginationControls pagination={families.pagination} onPageChange={onPageChange} />
        </>
      )}
    </Surface>
  );
}
