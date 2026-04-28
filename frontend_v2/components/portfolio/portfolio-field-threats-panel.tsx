"use client";

import { AlertTriangle } from "lucide-react";

import { formatDecimal, formatNumber } from "@/components/portfolio/portfolio-format";
import { PortfolioPaginationControls } from "@/components/portfolio/portfolio-pagination";
import { PortfolioTooltipLabel } from "@/components/portfolio/portfolio-tooltip-label";
import { InfoPill } from "@/components/ui/data-pill";
import { Surface } from "@/components/ui/surface";
import { workspaceTooltipCopy } from "@/lib/content/workspace-tooltips";
import type { PortfolioThreatsResponse } from "@/lib/types/portfolio-v2";

type PortfolioFieldThreatsPanelProps = {
  field: string;
  threats: PortfolioThreatsResponse;
  isLoading?: boolean;
  errorMessage?: string;
  onPageChange?: (offset: number) => void;
};

export function PortfolioFieldThreatsPanel({
  field,
  threats,
  isLoading = false,
  errorMessage,
  onPageChange,
}: PortfolioFieldThreatsPanelProps) {
  const maxPressureScore = Math.max(...threats.rows.map((row) => row.citationLethality), 1);

  return (
    <Surface
      className="portfolio-panel--citation"
      title={<PortfolioTooltipLabel label="Top citing owners" tooltip={workspaceTooltipCopy.fields.topCitingOwners} />}
      icon={<AlertTriangle size={14} />}
      badge={
        <InfoPill tone="neutral">
          {threats.pagination?.totalCount != null ? `${threats.pagination.totalCount} total` : `${threats.rows.length} rows`}
        </InfoPill>
      }
    >
      {errorMessage ? <p className="portfolio-error">{errorMessage}</p> : null}
      <p className="portfolio-small-note">Citing owners ranked by citation pressure within {field}.</p>
      {isLoading && threats.rows.length > 0 ? <p className="portfolio-small-note">Refreshing field-scoped citing owners…</p> : null}
      {threats.rows.length === 0 && isLoading ? (
        <p className="portfolio-empty">Loading field-scoped citing owners…</p>
      ) : threats.rows.length === 0 ? (
        <p className="portfolio-empty">No citing-owner rows available for this field.</p>
      ) : (
        <ul className="portfolio-overview-brief__list portfolio-overview-brief__list--pressure">
          {threats.rows.map((row) => (
            <li key={`${field}-${row.citingAssignee}`}>
              <div className="portfolio-overview-brief__pressure-head">
                <strong>{row.citingAssignee}</strong>
                <span className="portfolio-overview-brief__pressure-score">
                  {formatDecimal(row.citationLethality, 1)}{" "}
                  <PortfolioTooltipLabel label="pressure" tooltip={workspaceTooltipCopy.fields.pressure} />
                </span>
              </div>
              <div className="portfolio-overview-brief__metric-bar portfolio-overview-brief__metric-bar--pressure">
                <span
                  style={{
                    width: `${Math.max(4, Math.min((row.citationLethality / maxPressureScore) * 100, 100))}%`,
                  }}
                />
              </div>
              <div className="portfolio-overview-brief__pressure-foot">
                <span>{field}</span>
                <PortfolioTooltipLabel
                  label={`${formatNumber(row.collidedFamilyCount)} families`}
                  tooltip={workspaceTooltipCopy.fields.families}
                />
              </div>
            </li>
          ))}
        </ul>
      )}
      <PortfolioPaginationControls pagination={threats.pagination} onPageChange={onPageChange} />
    </Surface>
  );
}
