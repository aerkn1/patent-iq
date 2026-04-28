"use client";

import { Gauge, Shield, ShieldAlert } from "lucide-react";

import { formatNumber, formatPercent } from "@/components/portfolio/portfolio-format";
import { PortfolioMetricTooltip } from "@/components/portfolio/portfolio-metric-tooltip";
import { StatusPill } from "@/components/ui/data-pill";
import { Surface } from "@/components/ui/surface";
import type { PortfolioCountScopes, PortfolioCoveragePayload } from "@/lib/types/portfolio-v2";

type PortfolioCoveragePanelProps = {
  coverage: PortfolioCoveragePayload;
  countScopes: PortfolioCountScopes;
};

function prettyLabel(value: string | null | undefined): string {
  if (!value) {
    return "Limited";
  }

  return value
    .split(/[_\s]+/)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1).toLowerCase())
    .join(" ");
}

function CoverageBar({
  label,
  value,
  tone,
  tooltip,
}: {
  label: string;
  value: number;
  tone: "green" | "yellow" | "red";
  tooltip: string;
}) {
  return (
    <div className="portfolio-coverage-bar">
      <div className="portfolio-coverage-bar__label">
        <span className="portfolio-metric-label">
          <span>{label}</span>
          <PortfolioMetricTooltip text={tooltip} />
        </span>
        <span>{formatPercent(value)}</span>
      </div>
      <div className="portfolio-coverage-bar__track">
        <div
          className={`portfolio-coverage-bar__fill portfolio-coverage-bar__fill--${tone}`}
          style={{ width: `${Math.max(0, Math.min(100, value * 100))}%` }}
        />
      </div>
    </div>
  );
}

function getCoverageBasisLabel(coverage: PortfolioCoveragePayload, countScopes: PortfolioCountScopes): string {
  if (coverage.denominatorCount != null && coverage.denominatorCount === countScopes.primaryOwnerFamilyCount) {
    return "Measured against primary-owner families.";
  }
  if (coverage.denominatorCount != null && coverage.denominatorCount === countScopes.inScopeFamilyCount) {
    return "Measured against the portfolio analytics scope.";
  }
  return "Measured against the modeled family denominator returned by the service.";
}

function coverageTone(status: PortfolioCoveragePayload["predictionCoverageStatus"]): "positive" | "warning" | "critical" {
  if (status === "high") {
    return "positive";
  }

  if (status === "medium") {
    return "warning";
  }

  return "critical";
}

export function PortfolioCoveragePanel({ coverage, countScopes }: PortfolioCoveragePanelProps) {
  const basisLabel = getCoverageBasisLabel(coverage, countScopes);
  const methodologyLabel = [coverage.contributionMethod, coverage.coverageCaveatText].filter(Boolean).join(" ");
  const coverageBars = [
    {
      key: "phase03",
      label: "Citation forecast family coverage",
      value: coverage.phase03FamilyCoveragePct,
      tone: coverage.phase03FamilyCoveragePct > 0.7 ? "green" : "yellow",
      tooltip: "Share of modeled families covered by the citation forecast layer.",
    },
    coverage.phase04FamilyCoveragePct == null
      ? null
      : {
          key: "phase04",
          label: "Lapse-risk family coverage",
          value: coverage.phase04FamilyCoveragePct,
          tone: coverage.phase04FamilyCoveragePct > 0.7 ? "green" : "red",
          tooltip: "Share of modeled families covered by the lapse-risk layer.",
        },
    coverage.phase06FamilyCoveragePct == null
      ? null
      : {
          key: "phase06",
          label: "Market-direction family coverage",
          value: coverage.phase06FamilyCoveragePct,
          tone: coverage.phase06FamilyCoveragePct > 0.7 ? "green" : "yellow",
          tooltip: "Share of modeled families covered by the market-direction layer.",
        },
  ].filter((item): item is { key: string; label: string; value: number; tone: "green" | "yellow" | "red"; tooltip: string } => item !== null);

  return (
    <Surface
      className="portfolio-panel--coverage"
      title="Coverage context"
      icon={<Shield className="portfolio-section-icon" />}
      badge={
        <StatusPill tone={coverageTone(coverage.predictionCoverageStatus)}>
          {coverage.predictionCoverageStatus}
        </StatusPill>
      }
    >
      <div className="portfolio-section-summary">
        <article className="portfolio-section-summary__card">
          <span className="portfolio-section-summary__label">Modeled denominator</span>
          <strong>
            {coverage.coveredCount != null ? formatNumber(coverage.coveredCount) : "—"} /{" "}
            {coverage.denominatorCount != null ? formatNumber(coverage.denominatorCount) : "—"}
          </strong>
          <span>{basisLabel}</span>
        </article>
        <article className="portfolio-section-summary__card">
          <span className="portfolio-section-summary__label">Support level</span>
          <strong>{prettyLabel(coverage.supportLevel)}</strong>
          <span>{countScopes.primaryOwnerFamilyCount} primary-owner families in current scope</span>
        </article>
      </div>
      <div className="portfolio-metric-list">
        {coverageBars.map((bar) => (
          <CoverageBar key={bar.key} label={bar.label} value={bar.value} tone={bar.tone} tooltip={bar.tooltip} />
        ))}
      </div>
      {methodologyLabel ? (
        <details className="portfolio-caveat">
          <summary className="portfolio-support-row">
            <Gauge className="portfolio-support-row__icon" />
            <span>Methodology and support</span>
          </summary>
          <div className="portfolio-caveat__detail">
            <ShieldAlert className="portfolio-caveat__icon" />
            <span>{methodologyLabel}</span>
          </div>
        </details>
      ) : null}
    </Surface>
  );
}
