"use client";

import { Skull } from "lucide-react";

import { PortfolioPaginationControls } from "@/components/portfolio/portfolio-pagination";
import { formatDecimal, formatNumber } from "@/components/portfolio/portfolio-format";
import { FieldPill, InfoPill, StatusPill } from "@/components/ui/data-pill";
import { Surface } from "@/components/ui/surface";
import type { PortfolioThreatsResponse } from "@/lib/types/portfolio-v2";

type PortfolioThreatPanelProps = {
  threats: PortfolioThreatsResponse;
  selectedField?: string;
  availableFields?: string[];
  onFieldChange?: (value: string) => void;
  onPageChange?: (offset: number) => void;
};

function threatBand(lethality: number, collidedFamilies: number): string {
  if (lethality >= 12 || collidedFamilies >= 12) {
    return "concentrated pressure";
  }

  if (lethality >= 5 || collidedFamilies >= 5) {
    return "watch pressure";
  }

  return "edge pressure";
}

export function PortfolioThreatPanel({
  threats,
  selectedField = "",
  availableFields = [],
  onFieldChange,
  onPageChange,
}: PortfolioThreatPanelProps) {
  const topThreat = threats.rows[0];
  const affectedFieldCount = new Set(threats.rows.map((row) => row.wipoField)).size;
  const highestLethality = threats.rows.reduce((best, row) => Math.max(best, row.citationLethality), 0);

  return (
    <Surface
      className="portfolio-threat-panel portfolio-panel--threat"
      title="Threat and exposure"
      icon={<Skull size={14} />}
      badge={
        <InfoPill tone="neutral">
          {threats.pagination?.totalCount != null ? `${threats.pagination.totalCount} total` : `${threats.rows.length} rows`}
        </InfoPill>
      }
    >
      <div className="portfolio-section-summary">
        <article className="portfolio-section-summary__card">
          <span className="portfolio-section-summary__label">Lead attacker</span>
          <strong>{topThreat?.citingAssignee ?? "—"}</strong>
          <span>{topThreat?.wipoField ?? "No active threat rows in this slice"}</span>
        </article>
        <article className="portfolio-section-summary__card">
          <span className="portfolio-section-summary__label">Highest lethality in page</span>
          <strong>{threats.rows.length > 0 ? formatDecimal(highestLethality, 1) : "—"}</strong>
          <span>current ranked slice</span>
        </article>
        <article className="portfolio-section-summary__card">
          <span className="portfolio-section-summary__label">Fields under pressure</span>
          <strong>{affectedFieldCount}</strong>
          <span>distinct WIPO fields in current page</span>
        </article>
      </div>
      {onFieldChange ? (
        <div className="portfolio-inline-filters">
          <label className="portfolio-inline-filters__label" htmlFor="portfolio-threat-field">
            WIPO field
          </label>
          <select id="portfolio-threat-field" value={selectedField} onChange={(event) => onFieldChange(event.target.value)}>
            <option value="">All fields</option>
            {availableFields.map((field) => (
              <option key={field} value={field}>
                {field}
              </option>
            ))}
          </select>
        </div>
      ) : null}
      <div className="portfolio-threat-list">
        {threats.rows.length === 0 ? (
          <p className="portfolio-empty">Threat matrix not yet loaded.</p>
        ) : (
          threats.rows.map((row) => (
            <article key={`${row.citingAssignee}-${row.wipoField}`} className="portfolio-threat-card">
              <div className="portfolio-threat-card__identity">
                <strong>{row.citingAssignee}</strong>
                <FieldPill soft>{row.wipoField}</FieldPill>
              </div>
              <div className="portfolio-threat-card__metric">
                <strong>{formatDecimal(row.citationLethality, 1)}</strong>
                <span>citation lethality</span>
              </div>
              <div className="portfolio-threat-card__metric">
                <strong>{formatNumber(row.collidedFamilyCount)}</strong>
                <span>collided families</span>
              </div>
              <StatusPill tone="critical">
                {threatBand(row.citationLethality, row.collidedFamilyCount)}
              </StatusPill>
            </article>
          ))
        )}
      </div>
      <PortfolioPaginationControls pagination={threats.pagination} onPageChange={onPageChange} />
    </Surface>
  );
}
