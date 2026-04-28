"use client";

import { Layers3, Radar, ShieldAlert } from "lucide-react";
import Link from "next/link";

import { formatDecimal, formatNumber, formatPercent } from "@/components/portfolio/portfolio-format";
import { PortfolioTooltipLabel } from "@/components/portfolio/portfolio-tooltip-label";
import { Surface } from "@/components/ui/surface";
import { workspaceTooltipCopy } from "@/lib/content/workspace-tooltips";
import type {
  PortfolioFamiliesResponse,
  PortfolioFieldRowsResponse,
  PortfolioThreatsResponse,
} from "@/lib/types/portfolio-v2";

type PortfolioOverviewBriefProps = {
  families: PortfolioFamiliesResponse;
  fields: PortfolioFieldRowsResponse;
  threats: PortfolioThreatsResponse;
};

function prettyStatus(value: string): string {
  return value.replace(/_/g, " ");
}

function hotspotLabel(value: string): string {
  return value.replace(/_/g, " ");
}

function BriefEmptyState({ label }: { label: string }) {
  return <p className="portfolio-overview-brief__empty">No {label} available for this portfolio.</p>;
}

export function PortfolioOverviewBrief({
  families,
  fields,
  threats,
}: PortfolioOverviewBriefProps) {
  const familyPreview = families.rows.slice(0, 4);
  const fieldPreview = fields.rows.slice(0, 4);
  const threatPreview = threats.rows.slice(0, 4);
  const maxBlockingScore = Math.max(...familyPreview.map((row) => row.blockingScore), 1);
  const maxPressureScore = Math.max(...threatPreview.map((row) => row.citationLethality), 1);

  return (
    <div className="portfolio-overview-brief__grid">
        <Surface
          className="portfolio-overview-brief__panel portfolio-overview-brief__panel--families"
          title={
            <PortfolioTooltipLabel
              label="Blocking leader families"
              tooltip={workspaceTooltipCopy.overview.blockingLeaderFamilies}
            />
          }
          eyebrow={
            <span className="portfolio-overview-brief__kicker">
              <Layers3 size={14} />
              Value concentration
            </span>
          }
        >
          {familyPreview.length > 0 ? (
            <ul className="portfolio-overview-brief__list portfolio-overview-brief__list--families">
              {familyPreview.map((row) => (
                <li key={row.familyId}>
                  <div className="portfolio-overview-brief__family-head">
                    <Link
                      href={`/family/${encodeURIComponent(row.familyId)}`}
                      className="portfolio-family-link"
                      aria-label={`Open family ${row.familyId}`}
                    >
                      <strong>{row.familyId}</strong>
                    </Link>
                    <span className="portfolio-overview-brief__family-score">{formatDecimal(row.blockingScore, 1)} blocking</span>
                  </div>
                  <div className="portfolio-overview-brief__metric-bar portfolio-overview-brief__metric-bar--families">
                    <span style={{ width: `${Math.max(4, Math.min((row.blockingScore / maxBlockingScore) * 100, 100))}%` }} />
                  </div>
                  <div className="portfolio-overview-brief__family-foot">
                    <span>{row.primaryField}</span>
                    <span>{prettyStatus(row.status)}</span>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <BriefEmptyState label="blocking leader families" />
          )}
        </Surface>

        <Surface
          className="portfolio-overview-brief__panel portfolio-overview-brief__panel--fields"
          title={
            <PortfolioTooltipLabel
              label="Top field concentration"
              tooltip={workspaceTooltipCopy.overview.topFieldConcentration}
            />
          }
          eyebrow={
            <span className="portfolio-overview-brief__kicker">
              <Radar size={14} />
              Field footprint
            </span>
          }
        >
          {fieldPreview.length > 0 ? (
            <div className="portfolio-overview-brief__field-list">
              {fieldPreview.map((row) => (
                <div key={row.field} className="portfolio-overview-brief__field-row">
                  <div className="portfolio-overview-brief__field-head">
                    <div className="portfolio-overview-brief__field-copy">
                      <strong>{row.field}</strong>
                    </div>
                    <span className="portfolio-overview-brief__field-share">{formatPercent(row.activeShare)}</span>
                  </div>
                  <div className="portfolio-overview-brief__field-bar">
                    <span style={{ width: `${Math.max(4, Math.min(row.activeShare * 100, 100))}%` }} />
                  </div>
                  <div className="portfolio-overview-brief__field-foot">
                    <span className="portfolio-overview-brief__field-support">{formatNumber(row.activeFamilies)} active families</span>
                    <span>{hotspotLabel(row.hotspotDirection)}</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <BriefEmptyState label="field concentration rows" />
          )}
        </Surface>

        <Surface
          className="portfolio-overview-brief__panel portfolio-overview-brief__panel--pressure"
          title={
            <PortfolioTooltipLabel
              label="Top citing owners"
              tooltip={workspaceTooltipCopy.overview.topCitingOwners}
            />
          }
          eyebrow={
            <span className="portfolio-overview-brief__kicker">
              <ShieldAlert size={14} />
              External pressure
            </span>
          }
        >
          {threatPreview.length > 0 ? (
            <ul className="portfolio-overview-brief__list portfolio-overview-brief__list--pressure">
              {threatPreview.map((row) => (
                <li key={`${row.citingAssignee}-${row.wipoField}`}>
                  <div className="portfolio-overview-brief__pressure-head">
                    <strong>{row.citingAssignee}</strong>
                    <span className="portfolio-overview-brief__pressure-score">{formatDecimal(row.citationLethality, 1)} pressure</span>
                  </div>
                  <div className="portfolio-overview-brief__metric-bar portfolio-overview-brief__metric-bar--pressure">
                    <span style={{ width: `${Math.max(4, Math.min((row.citationLethality / maxPressureScore) * 100, 100))}%` }} />
                  </div>
                  <div className="portfolio-overview-brief__pressure-foot">
                    <span>{row.wipoField}</span>
                    <span>{formatNumber(row.collidedFamilyCount)} families</span>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <BriefEmptyState label="citation pressure rows" />
          )}
        </Surface>
      </div>
  );
}
