"use client";

import { PortfolioPaginationControls } from "@/components/portfolio/portfolio-pagination";
import { formatDecimal, formatPercent } from "@/components/portfolio/portfolio-format";
import { InfoPill } from "@/components/ui/data-pill";
import { Surface } from "@/components/ui/surface";
import type { ForecastHorizon, PortfolioForecastContributorsResponse } from "@/lib/types/portfolio-v2";
import styles from "@/components/portfolio/forecast-panels.module.css";

type PortfolioForecastContributorsPanelProps = {
  contributors: PortfolioForecastContributorsResponse;
  contributorScope: string;
  horizon: ForecastHorizon;
  onContributorScopeChange: (scope: string) => void;
  onPageChange?: (offset: number) => void;
  errorMessage?: string;
};

export function PortfolioForecastContributorsPanel({
  contributors,
  contributorScope,
  horizon,
  onContributorScopeChange,
  onPageChange,
  errorMessage,
}: PortfolioForecastContributorsPanelProps) {
  return (
    <Surface
      className="portfolio-panel--contributors"
      title="Forecast contributors"
      actions={
        <div className="portfolio-inline-filters">
          <label className="portfolio-inline-filters__label" htmlFor="portfolio-contributor-scope">
            Scope
          </label>
          <select
            id="portfolio-contributor-scope"
            value={contributorScope}
            onChange={(event) => onContributorScopeChange(event.target.value)}
          >
            <option value="phase03_future_citations">Citation forecast</option>
            <option value="phase04_lapse_risk">Lapse risk</option>
          </select>
        </div>
      }
      badge={
        <InfoPill tone="neutral">
          {contributors.pagination?.totalCount != null
            ? `${contributors.pagination.totalCount} total`
            : `${contributors.rows.length} rows`}
        </InfoPill>
      }
    >
      {errorMessage ? <p className="portfolio-error">{errorMessage}</p> : null}
      {contributors.rows.length === 0 ? (
        <p className="portfolio-empty">No contributor rows available.</p>
      ) : (
        <>
          <p className="portfolio-small-note">
            Ranked contributors for the selected {horizon} forecast horizon and scope.
          </p>
          <div className="portfolio-scroll-table">
            <table>
              <thead>
                <tr>
                  <th>Rank</th>
                  <th>Contributor</th>
                  <th>Scope</th>
                  <th>Jurisdiction</th>
                  <th>Contribution</th>
                  <th>Share</th>
                </tr>
              </thead>
              <tbody>
                {contributors.rows.map((row) => (
                  <tr key={`${row.horizon}-${row.contributorScope}-${row.contributorEntityId}-${row.contributorRank}`}>
                    <td><span className={styles.tableMetricPrimary}>#{row.contributorRank}</span></td>
                    <td><strong className={styles.tableCellStrong}>{row.contributorEntityId}</strong></td>
                    <td><span className={styles.tableMetricPrimary}>{row.contributorScope}</span></td>
                    <td><span className={styles.tableMetricPrimary}>{row.jurisdictionCode || "—"}</span></td>
                    <td><span className={styles.tableMetricPrimary}>{formatDecimal(row.contributionValue, 2)}</span></td>
                    <td><span className={styles.tableMetricPrimary}>{formatPercent(row.contributionShare, 2)}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
      <p className={`portfolio-small-note ${styles.footnote}`}>
        Contributor ids are current mart identifiers and may represent internal family-level entities rather than named external organizations.
      </p>
      <PortfolioPaginationControls pagination={contributors.pagination} onPageChange={onPageChange} />
    </Surface>
  );
}
