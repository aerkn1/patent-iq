"use client";

import { formatDecimal, formatPercent } from "@/components/portfolio/portfolio-format";
import { PortfolioTooltipLabel } from "@/components/portfolio/portfolio-tooltip-label";
import { InfoPill } from "@/components/ui/data-pill";
import { Surface } from "@/components/ui/surface";
import { workspaceTooltipCopy } from "@/lib/content/workspace-tooltips";
import type { PortfolioCitationSummaryResponse } from "@/lib/types/portfolio-v2";
import styles from "@/components/portfolio/citation-panels.module.css";

type PortfolioCitationQualityPanelProps = {
  summary: PortfolioCitationSummaryResponse;
  isLoading?: boolean;
  errorMessage?: string;
};

type QualityMetric = {
  label: string;
  value: string;
  copy: string;
  ratio: number;
  tone: "accent" | "info" | "success" | "warning" | "critical";
};

function clamp01(value: number): number {
  if (Number.isNaN(value)) {
    return 0;
  }

  return Math.min(Math.max(value, 0), 1);
}

function formatRatioPercent(value: number): string {
  return formatPercent(clamp01(value), 0);
}

function buildMetrics(summary: NonNullable<PortfolioCitationSummaryResponse["summary"]>): QualityMetric[] {
  return [
    {
      label: "Generality",
      value: formatRatioPercent(summary.avgGeneralityPercentile),
      copy: "How broadly later citations spread across adjacent domains.",
      ratio: summary.avgGeneralityPercentile,
      tone: "info",
    },
    {
      label: "Originality",
      value: formatRatioPercent(summary.avgOriginalityPercentile),
      copy: "How atypical the cited prior-art mix is versus common combinations.",
      ratio: summary.avgOriginalityPercentile,
      tone: "accent",
    },
    {
      label: "Science grounding",
      value: formatRatioPercent(summary.avgScienceGroundingScore),
      copy: "Portfolio-level signal of linkage to science-heavy prior art.",
      ratio: summary.avgScienceGroundingScore,
      tone: "success",
    },
    {
      label: "Citing-family depth",
      value: formatDecimal(summary.avgUniqueCitingFamilyCount, 1),
      copy: "Average number of distinct citing families touching each family.",
      ratio: clamp01(summary.avgUniqueCitingFamilyCount / 8),
      tone: "info",
    },
    {
      label: "Owner diversity",
      value: formatDecimal(summary.avgCitingAssigneeDiversity, 2),
      copy: "How varied the external citing-owner base is across the portfolio.",
      ratio: summary.avgCitingAssigneeDiversity,
      tone: "accent",
    },
    {
      label: "Attacker density",
      value: formatDecimal(summary.avgAttackerDensityScore, 2),
      copy: "How concentrated repeat pressure is among the same external owners.",
      ratio: summary.avgAttackerDensityScore,
      tone: "warning",
    },
  ];
}

function metricTooltip(label: string): string {
  switch (label) {
    case "Generality":
      return workspaceTooltipCopy.citation.generality;
    case "Originality":
      return workspaceTooltipCopy.citation.originality;
    case "Science grounding":
      return workspaceTooltipCopy.citation.scienceGrounding;
    case "Citing-family depth":
      return workspaceTooltipCopy.citation.citingFamilyDepth;
    case "Owner diversity":
      return workspaceTooltipCopy.citation.ownerDiversity;
    case "Attacker density":
      return workspaceTooltipCopy.citation.attackerDensity;
    default:
      return label;
  }
}

function qualityFillClass(tone: QualityMetric["tone"]): string {
  switch (tone) {
    case "accent":
      return styles.qualityFillAccent;
    case "success":
      return styles.qualityFillSuccess;
    case "warning":
      return styles.qualityFillWarning;
    case "critical":
      return styles.qualityFillCritical;
    case "info":
    default:
      return styles.qualityFillInfo;
  }
}

export function PortfolioCitationQualityPanel({
  summary,
  isLoading = false,
  errorMessage,
}: PortfolioCitationQualityPanelProps) {
  const current = summary.summary;

  return (
    <Surface
      className="portfolio-panel--citation"
      title={
        <PortfolioTooltipLabel
          label="Citation quality and shape"
          tooltip={workspaceTooltipCopy.citation.citationQualityAndShape}
        />
      }
      description="A compact read on breadth, novelty, concentration, and science linkage behind the portfolio's citation footprint."
      badge={current ? <InfoPill tone="neutral">As of {current.asOfYear}</InfoPill> : null}
    >
      {errorMessage ? <p className="portfolio-error">{errorMessage}</p> : null}
      {!current && isLoading ? (
        <p className="portfolio-empty">Loading citation quality signals…</p>
      ) : !current ? (
        <p className="portfolio-empty">No citation quality signals loaded.</p>
      ) : (
        <>
          {isLoading ? <p className="portfolio-small-note">Refreshing citation quality signals…</p> : null}
          <div className={styles.qualityGrid}>
            {buildMetrics(current).map((metric) => (
              <article className={styles.qualityCard} key={metric.label}>
                <div className={styles.qualityCardHeader}>
                  <PortfolioTooltipLabel
                    label={metric.label}
                    tooltip={metricTooltip(metric.label)}
                    textClassName={styles.qualityLabel}
                  />
                  <strong className={styles.qualityValue}>{metric.value}</strong>
                </div>
                <div className={styles.qualityTrack} aria-hidden="true">
                  <span
                    className={qualityFillClass(metric.tone)}
                    style={{ width: `${Math.max(metric.ratio * 100, 6)}%` }}
                  />
                </div>
                <p className={styles.qualityCopy}>{metric.copy}</p>
              </article>
            ))}
          </div>
        </>
      )}
    </Surface>
  );
}
