"use client";

import Link from "next/link";
import { Sparkles } from "lucide-react";

import { formatDecimal, formatNumber } from "@/components/portfolio/portfolio-format";
import { PortfolioPaginationControls } from "@/components/portfolio/portfolio-pagination";
import { PortfolioTooltipLabel } from "@/components/portfolio/portfolio-tooltip-label";
import styles from "@/components/portfolio/citation-panels.module.css";
import { FieldPill, InfoPill, StatusPill } from "@/components/ui/data-pill";
import { Surface } from "@/components/ui/surface";
import { workspaceTooltipCopy } from "@/lib/content/workspace-tooltips";
import type { PortfolioCitationFamiliesResponse } from "@/lib/types/portfolio-v2";

type PortfolioFieldCitationFamiliesPanelProps = {
  field: string;
  families: PortfolioCitationFamiliesResponse;
  isLoading?: boolean;
  errorMessage?: string;
  onPageChange?: (offset: number) => void;
};

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

function prettyLabel(value: string): string {
  return value
    .split(/[_\s]+/)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1).toLowerCase())
    .join(" ");
}

export function PortfolioFieldCitationFamiliesPanel({
  field,
  families,
  isLoading = false,
  errorMessage,
  onPageChange,
}: PortfolioFieldCitationFamiliesPanelProps) {
  return (
    <Surface
      className="portfolio-panel--citation"
      title={<PortfolioTooltipLabel label="Most cited families" tooltip={workspaceTooltipCopy.fields.mostCitedFamilies} />}
      icon={<Sparkles size={14} />}
      badge={
        <InfoPill tone="neutral">
          {families.pagination?.totalCount != null ? `${families.pagination.totalCount} total` : `${families.rows.length} rows`}
        </InfoPill>
      }
    >
      {errorMessage ? <p className="portfolio-error">{errorMessage}</p> : null}
      <p className="portfolio-small-note">Portfolio families ranked by citation concentration within {field}.</p>
      {isLoading && families.rows.length > 0 ? <p className="portfolio-small-note">Refreshing field-scoped cited families…</p> : null}
      {families.rows.length === 0 && isLoading ? (
        <p className="portfolio-empty">Loading field-scoped cited families…</p>
      ) : families.rows.length === 0 ? (
        <p className="portfolio-empty">No cited-family rows available for this field.</p>
      ) : (
        <div className="portfolio-scroll-table">
          <table>
            <thead>
              <tr>
                <th><PortfolioTooltipLabel label="Family" tooltip={workspaceTooltipCopy.citation.family} /></th>
                <th><PortfolioTooltipLabel label="Lifecycle" tooltip={workspaceTooltipCopy.fields.lifecycle} /></th>
                <th><PortfolioTooltipLabel label="Forward citations" tooltip={workspaceTooltipCopy.fields.forwardCitations} /></th>
                <th><PortfolioTooltipLabel label="Early 7y" tooltip={workspaceTooltipCopy.fields.earlyCitations7y} /></th>
                <th><PortfolioTooltipLabel label="Blocking" tooltip={workspaceTooltipCopy.fields.blocking} /></th>
              </tr>
            </thead>
            <tbody>
              {families.rows.map((row) => (
                <tr key={`${field}-${row.familyId}`}>
                  <td>
                    <Link href={`/family/${encodeURIComponent(row.familyId)}`} className="portfolio-family-link">
                      <strong className={styles.tableCellStrong}>{row.familyId}</strong>
                    </Link>
                  </td>
                  <td>
                    <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                      <FieldPill soft>{row.primaryField}</FieldPill>
                      <StatusPill tone={familyStatusTone(row.status)}>{prettyLabel(row.status)}</StatusPill>
                    </div>
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
    </Surface>
  );
}
