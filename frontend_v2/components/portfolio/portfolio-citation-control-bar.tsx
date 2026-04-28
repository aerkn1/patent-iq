"use client";

import { X } from "lucide-react";

import { PortfolioTooltipLabel } from "@/components/portfolio/portfolio-tooltip-label";
import { workspaceTooltipCopy } from "@/lib/content/workspace-tooltips";
import styles from "@/components/portfolio/citation-panels.module.css";

type PortfolioCitationControlBarProps = {
  fieldOptions: string[];
  jurisdictionOptions: string[];
  yearOptions: number[];
  selectedField: string;
  selectedJurisdiction: string;
  selectedYear: string;
  onFieldChange: (value: string) => void;
  onJurisdictionChange: (value: string) => void;
  onYearChange: (value: string) => void;
  onClear: () => void;
};

export function PortfolioCitationControlBar({
  fieldOptions,
  jurisdictionOptions,
  yearOptions,
  selectedField,
  selectedJurisdiction,
  selectedYear,
  onFieldChange,
  onJurisdictionChange,
  onYearChange,
  onClear,
}: PortfolioCitationControlBarProps) {
  const hasFilters = Boolean(selectedField || selectedJurisdiction || selectedYear);

  return (
    <section className={styles.filterBar}>
      <div className={styles.filterControls}>
        <div className={styles.filterGroup}>
          <label className={styles.filterLabel} htmlFor="portfolio-citation-attacker-field">
            <PortfolioTooltipLabel label="Field" tooltip={workspaceTooltipCopy.citation.field} />
          </label>
          <select
            id="portfolio-citation-attacker-field"
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
          <label className={styles.filterLabel} htmlFor="portfolio-citation-attacker-jurisdiction">
            <PortfolioTooltipLabel label="Jurisdiction" tooltip={workspaceTooltipCopy.citation.jurisdictions} />
          </label>
          <select
            id="portfolio-citation-attacker-jurisdiction"
            className={styles.filterSelect}
            value={selectedJurisdiction}
            onChange={(event) => onJurisdictionChange(event.target.value)}
          >
            <option value="">All jurisdictions</option>
            {jurisdictionOptions.map((jurisdiction) => (
              <option key={jurisdiction} value={jurisdiction}>
                {jurisdiction}
              </option>
            ))}
          </select>
        </div>

        <div className={styles.filterGroup}>
          <label className={styles.filterLabel} htmlFor="portfolio-citation-attacker-year">
            <PortfolioTooltipLabel label="Year" tooltip={workspaceTooltipCopy.citation.year} />
          </label>
          <select
            id="portfolio-citation-attacker-year"
            className={styles.filterSelect}
            value={selectedYear}
            onChange={(event) => onYearChange(event.target.value)}
          >
            <option value="">All years</option>
            {yearOptions.map((year) => (
              <option key={year} value={String(year)}>
                {year}
              </option>
            ))}
          </select>
        </div>

        <button type="button" className={styles.filterButton} onClick={onClear} disabled={!hasFilters}>
          <X size={14} />
          Clear
        </button>
      </div>
    </section>
  );
}
