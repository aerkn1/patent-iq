"use client";

import { formatDecimal, formatNumber } from "@/components/portfolio/portfolio-format";
import { PortfolioTooltipLabel } from "@/components/portfolio/portfolio-tooltip-label";
import { InfoPill } from "@/components/ui/data-pill";
import { Surface } from "@/components/ui/surface";
import { workspaceTooltipCopy } from "@/lib/content/workspace-tooltips";
import type { PortfolioCitationSummaryResponse } from "@/lib/types/portfolio-v2";
import styles from "@/components/portfolio/citation-panels.module.css";

type PortfolioCitationSummaryPanelProps = {
  summary: PortfolioCitationSummaryResponse;
  isLoading?: boolean;
  errorMessage?: string;
};

export function PortfolioCitationSummaryPanel({
  summary,
  isLoading = false,
  errorMessage,
}: PortfolioCitationSummaryPanelProps) {
  const current = summary.summary;

  return (
    <Surface
      className="portfolio-citation-summary portfolio-panel--citation"
      title={<PortfolioTooltipLabel label="Citation summary" tooltip={workspaceTooltipCopy.citation.citationSummary} />}
      badge={current ? <InfoPill tone="neutral">As of {current.asOfYear}</InfoPill> : null}
    >
      {errorMessage ? <p className="portfolio-error">{errorMessage}</p> : null}
      {!current && isLoading ? (
        <p className="portfolio-empty">Loading citation summary…</p>
      ) : !current ? (
        <p className="portfolio-empty">No citation summary loaded.</p>
      ) : (
        <>
          {isLoading ? <p className="portfolio-small-note">Refreshing citation summary…</p> : null}
          <div className={styles.matrixGrid}>
            <div className={styles.matrixCard}>
              <PortfolioTooltipLabel
                label="Forward citing families"
                tooltip={workspaceTooltipCopy.citation.forwardCitingFamilies}
                textClassName={styles.matrixLabel}
              />
              <div className={styles.matrixValue}>{formatNumber(current.distinctCitingFamilyCount)}</div>
              <p className={styles.matrixCopy}>Family-level breadth of forward attention.</p>
            </div>

            <div className={styles.matrixCard}>
              <PortfolioTooltipLabel
                label="Forward citation events"
                tooltip={workspaceTooltipCopy.citation.forwardCitationEvents}
                textClassName={styles.matrixLabel}
              />
              <div className={styles.matrixValue}>{formatNumber(current.forwardCitationsCleanTotal)}</div>
              <p className={styles.matrixCopy}>Event-level citation intensity after cleaning.</p>
            </div>

            <div className={styles.matrixCard}>
              <PortfolioTooltipLabel
                label="Backward cited families"
                tooltip={workspaceTooltipCopy.citation.backwardCitedFamilies}
                textClassName={styles.matrixLabel}
              />
              <div className={styles.matrixValue}>{formatNumber(current.distinctCitedFamilyCount)}</div>
              <p className={styles.matrixCopy}>Family-level breadth of the cited prior-art neighborhood.</p>
            </div>

            <div className={styles.matrixCard}>
              <PortfolioTooltipLabel
                label="Backward citation events"
                tooltip={workspaceTooltipCopy.citation.backwardCitationEvents}
                textClassName={styles.matrixLabel}
              />
              <div className={styles.matrixValue}>{formatNumber(current.backwardCitationsCleanTotal)}</div>
              <p className={styles.matrixCopy}>Event-level backward citation intensity.</p>
            </div>

            <div className={styles.matrixCard}>
              <PortfolioTooltipLabel
                label="Backward NPL citations"
                tooltip={workspaceTooltipCopy.citation.backwardNplCitations}
                textClassName={styles.matrixLabel}
              />
              <div className={styles.matrixValue}>{formatNumber(current.backwardNplCitationTotal)}</div>
              <p className={styles.matrixCopy}>Science-grounding references.</p>
            </div>

            <div className={styles.matrixCard}>
              <PortfolioTooltipLabel
                label="Citing-owner diversity"
                tooltip={workspaceTooltipCopy.citation.citingOwnerDiversity}
                textClassName={styles.matrixLabel}
              />
              <div className={styles.matrixValue}>{formatDecimal(current.avgCitingAssigneeDiversity, 2)}</div>
              <p className={styles.matrixCopy}>How varied the citing-owner base is across the portfolio.</p>
            </div>
          </div>
        </>
      )}
    </Surface>
  );
}
