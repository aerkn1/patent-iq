"use client";

import { Search, X } from "lucide-react";
import Link from "next/link";

import { formatDecimal, formatNumber } from "@/components/portfolio/portfolio-format";
import { PortfolioPaginationControls } from "@/components/portfolio/portfolio-pagination";
import { PortfolioTooltipLabel } from "@/components/portfolio/portfolio-tooltip-label";
import { FieldPill, InfoPill, StatusPill } from "@/components/ui/data-pill";
import { Surface } from "@/components/ui/surface";
import { workspaceTooltipCopy } from "@/lib/content/workspace-tooltips";
import type { PortfolioFamiliesResponse } from "@/lib/types/portfolio-v2";

import styles from "./portfolio-top-families-table.module.css";

function prettyLabel(value: string): string {
  return value
    .split(/[_\s]+/)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1).toLowerCase())
    .join(" ");
}

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

function blockingBand(value: number): string {
  if (value >= 85) {
    return "very high";
  }

  if (value >= 70) {
    return "high";
  }

  if (value >= 50) {
    return "medium";
  }

  return "developing";
}

type PortfolioTopFamiliesTableProps = {
  families: PortfolioFamiliesResponse;
  isLoading?: boolean;
  searchValue: string;
  statusValue: string;
  primaryFieldValue: string;
  sortValue: "blocking" | "priority_year";
  fieldOptions: string[];
  onSearchChange?: (value: string) => void;
  onStatusChange?: (value: string) => void;
  onPrimaryFieldChange?: (value: string) => void;
  onSortChange?: (value: "blocking" | "priority_year") => void;
  onPageChange?: (offset: number) => void;
};

export function PortfolioTopFamiliesTable({
  families,
  isLoading = false,
  searchValue,
  statusValue,
  primaryFieldValue,
  sortValue,
  fieldOptions,
  onSearchChange,
  onStatusChange,
  onPrimaryFieldChange,
  onSortChange,
  onPageChange,
}: PortfolioTopFamiliesTableProps) {
  const canClearFilters = Boolean(searchValue || statusValue || primaryFieldValue || sortValue !== "blocking");
  const currentRowCount = families.rows.length;
  const totalRowCount = families.pagination?.totalCount ?? currentRowCount;

  function clearFilters() {
    onSearchChange?.("");
    onStatusChange?.("");
    onPrimaryFieldChange?.("");
    onSortChange?.("blocking");
  }

  return (
    <Surface
      className={`portfolio-top-families portfolio-panel--family ${styles.root}`}
      title={
        <PortfolioTooltipLabel
          label="Portfolio families"
          tooltip={workspaceTooltipCopy.families.portfolioFamilies}
        />
      }
      badge={<InfoPill tone="neutral">{formatNumber(totalRowCount)} total</InfoPill>}
    >
      <div className={styles.toolbar}>
        <div className={styles.selectGroup}>
          <label className={styles.selectLabel} htmlFor="portfolio-family-search">
            <PortfolioTooltipLabel label="Search" tooltip={workspaceTooltipCopy.families.search} />
          </label>
          <div className={styles.searchField}>
            <Search size={16} className={styles.searchIcon} />
            <input
              id="portfolio-family-search"
              value={searchValue}
              onChange={(event) => onSearchChange?.(event.target.value)}
              placeholder="Search family id, field, or lifecycle"
              className={styles.searchInput}
            />
          </div>
        </div>

        <div className={styles.selectGroup}>
          <label className={styles.selectLabel} htmlFor="portfolio-family-status">
            <PortfolioTooltipLabel label="Lifecycle" tooltip={workspaceTooltipCopy.families.lifecycle} />
          </label>
          <select
            id="portfolio-family-status"
            className={styles.select}
            value={statusValue}
            onChange={(event) => onStatusChange?.(event.target.value)}
          >
            <option value="">All lifecycles</option>
            <option value="fully_active">Fully active</option>
            <option value="pending_emerging">Pending / filing</option>
            <option value="under_fire">Under fire</option>
            <option value="partially_lapsed">Partially lapsed</option>
            <option value="dead">Dead</option>
            <option value="unknown">Unknown</option>
          </select>
        </div>

        <div className={styles.selectGroup}>
          <label className={styles.selectLabel} htmlFor="portfolio-family-field">
            <PortfolioTooltipLabel label="Primary field" tooltip={workspaceTooltipCopy.families.primaryField} />
          </label>
          <select
            id="portfolio-family-field"
            className={styles.select}
            value={primaryFieldValue}
            onChange={(event) => onPrimaryFieldChange?.(event.target.value)}
          >
            <option value="">All fields</option>
            {fieldOptions.map((field) => (
              <option key={field} value={field}>
                {field}
              </option>
            ))}
          </select>
        </div>

        <div className={styles.selectGroup}>
          <label className={styles.selectLabel} htmlFor="portfolio-family-sort">
            <PortfolioTooltipLabel label="Sort by" tooltip={workspaceTooltipCopy.families.sortBy} />
          </label>
          <select
            id="portfolio-family-sort"
            className={styles.select}
            value={sortValue}
            onChange={(event) => onSortChange?.(event.target.value as "blocking" | "priority_year")}
          >
            <option value="blocking">Blocking</option>
            <option value="priority_year">Priority year</option>
          </select>
        </div>

        <div className={styles.toolbarActions}>
          <button type="button" className={styles.clearButton} onClick={clearFilters} disabled={!canClearFilters}>
            <X size={14} />
            Clear
          </button>
        </div>
      </div>
      {isLoading && families.rows.length > 0 ? <p className="portfolio-small-note">Refreshing family slice…</p> : null}

      <div className={styles.tableSurface}>
        <div className={styles.tableWrap}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th><PortfolioTooltipLabel label="Family" tooltip={workspaceTooltipCopy.families.family} /></th>
                <th><PortfolioTooltipLabel label="Title" tooltip={workspaceTooltipCopy.families.title} /></th>
                <th><PortfolioTooltipLabel label="Lifecycle" tooltip={workspaceTooltipCopy.families.lifecycle} /></th>
                <th><PortfolioTooltipLabel label="Primary field" tooltip={workspaceTooltipCopy.families.primaryField} /></th>
                <th><PortfolioTooltipLabel label="Priority year" tooltip={workspaceTooltipCopy.families.priorityYear} /></th>
                <th className={styles.numericHeader}>
                  <PortfolioTooltipLabel label="Blocking" tooltip={workspaceTooltipCopy.families.blocking} />
                </th>
              </tr>
            </thead>
            <tbody>
              {families.rows.length === 0 ? (
                <tr>
                  <td colSpan={6} className={styles.emptyRow}>
                    {isLoading ? "Loading families…" : "No families found for the current slice."}
                  </td>
                </tr>
              ) : null}
              {families.rows.map((row) => (
                <tr key={row.familyId}>
                  <td>
                    <div className={styles.identityCell}>
                      <Link
                        href={`/family/${encodeURIComponent(row.familyId)}`}
                        className="portfolio-family-link"
                        aria-label={`Open family ${row.familyId}`}
                      >
                        <strong>{row.familyId}</strong>
                      </Link>
                    </div>
                  </td>
                  <td>
                    <span className={styles.titleText}>{row.title || "—"}</span>
                  </td>
                  <td>
                    <StatusPill tone={familyStatusTone(row.status)}>{prettyLabel(row.status)}</StatusPill>
                  </td>
                  <td>
                    <FieldPill soft>{row.primaryField}</FieldPill>
                  </td>
                  <td>
                    <span className={styles.inlineTag}>{row.priorityYear === "unknown" ? "—" : row.priorityYear}</span>
                  </td>
                  <td className={styles.numericCell}>
                    <div className={styles.metricStack}>
                      <div className={styles.metricValueRow}>
                        <strong>{formatDecimal(row.blockingScore, 1)}</strong>
                        <span>{blockingBand(row.blockingScore)}</span>
                      </div>
                      <div className={styles.progressTrack} aria-hidden="true">
                        <span className={styles.progressFillAccent} style={{ width: `${Math.min(Math.max(row.blockingScore, 4), 100)}%` }} />
                      </div>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <PortfolioPaginationControls pagination={families.pagination} onPageChange={onPageChange} />
    </Surface>
  );
}
