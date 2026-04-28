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
  XAxis,
  YAxis,
} from "recharts";

import { BookOpen } from "lucide-react";

import { PortfolioPaginationControls } from "@/components/portfolio/portfolio-pagination";
import { formatPercent } from "@/components/portfolio/portfolio-format";
import { PortfolioTooltipLabel } from "@/components/portfolio/portfolio-tooltip-label";
import { InfoPill } from "@/components/ui/data-pill";
import { Surface } from "@/components/ui/surface";
import { chartTokens, getTrajectoryColor } from "@/lib/design/chart-tokens";
import { workspaceTooltipCopy } from "@/lib/content/workspace-tooltips";
import type { PortfolioClassificationResponse } from "@/lib/types/portfolio-v2";
import styles from "@/components/portfolio/technology-panels.module.css";

type PortfolioClassificationPanelProps = {
  classification: PortfolioClassificationResponse;
  errorMessage?: string;
  isLoading?: boolean;
  selectedField?: string;
  onPageChange?: (offset: number) => void;
};

function ChangePill({ direction }: { direction: "gain" | "loss" | "flat" }) {
  if (direction === "gain") {
    return <span className="classification-pill classification-pill--gain">gain</span>;
  }

  if (direction === "loss") {
    return <span className="classification-pill classification-pill--loss">loss</span>;
  }

  return <span className="classification-pill classification-pill--flat">flat</span>;
}

export function PortfolioClassificationPanel({
  classification,
  errorMessage,
  isLoading = false,
  selectedField = "",
  onPageChange,
}: PortfolioClassificationPanelProps) {
  const [viewMode, setViewMode] = useState<"chart" | "table">("chart");
  const isFieldScopedCpc = selectedField.length > 0;
  const chartTitle = isFieldScopedCpc ? `CPC share within ${selectedField}` : "Portfolio-wide CPC share concentration";
  const chartRows = [...classification.rows]
    .sort((left, right) => right.familyShare - left.familyShare)
    .slice(0, 8)
    .map((row) => ({
      ...row,
      sharePercent: row.familyShare * 100,
      trajectoryPercent: row.trajectory * 100,
    }));

  return (
    <Surface
      className="portfolio-panel--classification"
      title={<PortfolioTooltipLabel label="Classification mix" tooltip={workspaceTooltipCopy.fields.classificationMix} />}
      icon={<BookOpen size={14} />}
      badge={
        <InfoPill tone="neutral">
          {classification.pagination?.totalCount != null
            ? `${classification.pagination.totalCount} total`
            : `${classification.rows.length} rows`}
        </InfoPill>
      }
      actions={
        classification.rows.length > 0 ? (
          <div className={styles.viewToggle} role="tablist" aria-label="Classification mix view">
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
      {isLoading && classification.rows.length > 0 ? <p className="portfolio-small-note">Refreshing classification mix…</p> : null}
      {isLoading && classification.rows.length === 0 ? (
        <p className="portfolio-empty">Loading classification mix…</p>
      ) : errorMessage ? (
        <p className="portfolio-empty">{errorMessage}</p>
      ) : classification.rows.length === 0 ? (
        <p className="portfolio-empty">No classification rows available.</p>
      ) : (
        <>
          {viewMode === "chart" ? (
          <div className={styles.chartShell}>
              <h4 className={styles.chartShellTitle}>
                <PortfolioTooltipLabel label={chartTitle} tooltip={workspaceTooltipCopy.fields.classificationView} />
              </h4>
              <ResponsiveContainer width="100%" height={310}>
                <BarChart data={chartRows} layout="vertical" margin={{ top: 20, right: 16, left: 16, bottom: 4 }}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                  <XAxis type="number" tickFormatter={(value: number) => `${value}%`} />
                  <YAxis type="category" dataKey="segment" width={110} tickLine={false} axisLine={false} />
                  <Tooltip
                    formatter={(value: number, name: string) => {
                      if (name === "sharePercent") {
                        return [`${value.toFixed(1)}%`, "Family share"];
                      }
                      return [`${value.toFixed(1)}%`, "Trajectory"];
                    }}
                    labelFormatter={(label) => `Segment: ${label}`}
                  />
                  <Bar dataKey="sharePercent" radius={[0, 10, 10, 0]}>
                    {chartRows.map((row) => (
                      <Cell key={`${row.classificationType}-${row.segment}`} fill={getTrajectoryColor(row.topChange)} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
              <div className={styles.legend}>
                <span className={styles.legendItem}>
                  <span className={styles.legendSwatch} style={{ background: chartTokens.series.success }} />
                  <PortfolioTooltipLabel
                    label="Gain-led segments"
                    tooltip={workspaceTooltipCopy.fields.gainLedSegments}
                  />
                </span>
                <span className={styles.legendItem}>
                  <span className={styles.legendSwatch} style={{ background: chartTokens.series.critical }} />
                  <PortfolioTooltipLabel
                    label="Loss-led segments"
                    tooltip={workspaceTooltipCopy.fields.lossLedSegments}
                  />
                </span>
                <span className={styles.legendItem}>
                  <span className={styles.legendSwatch} style={{ background: chartTokens.series.neutral }} />
                  <PortfolioTooltipLabel
                    label="Flat segments"
                    tooltip={workspaceTooltipCopy.fields.flatSegments}
                  />
                </span>
              </div>
            </div>
          ) : (
            <div className="portfolio-classification-table portfolio-scroll-table">
              <table>
                <thead>
                    <tr>
                      <th><PortfolioTooltipLabel label="Segment" tooltip={workspaceTooltipCopy.fields.segment} /></th>
                    <th>
                      <PortfolioTooltipLabel
                        label={selectedField ? "WIPO field" : "Scope"}
                        tooltip={selectedField ? workspaceTooltipCopy.fields.field : workspaceTooltipCopy.fields.scope}
                      />
                    </th>
                    <th><PortfolioTooltipLabel label="Family share" tooltip={workspaceTooltipCopy.fields.familyShare} /></th>
                    <th><PortfolioTooltipLabel label="Trajectory" tooltip={workspaceTooltipCopy.fields.trajectory} /></th>
                    <th><PortfolioTooltipLabel label="Movement" tooltip={workspaceTooltipCopy.fields.movement} /></th>
                  </tr>
                </thead>
                <tbody>
                  {classification.rows.map((row) => (
                    <tr key={`${row.classificationType}-${row.segment}`}>
                      <td>
                        <strong>{row.segment}</strong>
                      </td>
                      <td>
                        {selectedField || row.wipoField || "All fields"}
                      </td>
                      <td>{formatPercent(row.familyShare)}</td>
                      <td>{formatPercent(row.trajectory)}</td>
                      <td>
                        <ChangePill direction={row.topChange} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          <p className="portfolio-small-note">
            {isFieldScopedCpc
              ? `CPC shares are measured against families whose primary WIPO field is ${selectedField}. Families can carry multiple CPC main groups, so row shares are not additive.`
              : "CPC shares are measured against the full in-scope portfolio. Families can carry multiple CPC main groups, so row shares are not additive."}
          </p>
          <PortfolioPaginationControls pagination={classification.pagination} onPageChange={onPageChange} />
        </>
      )}
    </Surface>
  );
}
