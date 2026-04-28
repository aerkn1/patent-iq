"use client";

import { Building2, Layers3, Sparkles } from "lucide-react";

import { formatDecimal, formatNumber, formatPercent } from "@/components/portfolio/portfolio-format";
import { PortfolioTooltipLabel } from "@/components/portfolio/portfolio-tooltip-label";
import { FieldPill, InfoPill, StatusPill } from "@/components/ui/data-pill";
import { Surface } from "@/components/ui/surface";
import { workspaceTooltipCopy } from "@/lib/content/workspace-tooltips";
import type { PortfolioPendingGrantResponse, PortfolioPendingGrantRow } from "@/lib/types/portfolio-v2";
import styles from "@/components/portfolio/forecast-panels.module.css";

type PortfolioPendingGrantsPanelProps = {
  pendingGrants: PortfolioPendingGrantResponse;
  selectedJurisdiction: string;
  selectedField: string;
  isLoading?: boolean;
  errorMessage?: string;
  onJurisdictionChange: (value: string) => void;
  onFieldChange: (value: string) => void;
};

function percentileLabel(value: number | undefined): string {
  if (value == null || Number.isNaN(value)) {
    return "—";
  }
  return `${formatDecimal(value, 1)} pct`;
}

function selectedAverageProbability(summary: PortfolioPendingGrantRow | undefined): number | undefined {
  if (!summary) {
    return undefined;
  }
  return summary.horizon === "12m" ? summary.pendingPipelineAvgProbability12m : summary.pendingPipelineAvgProbability24m;
}

function selectedExpectedLikelyGrants(summary: PortfolioPendingGrantRow | undefined): number | undefined {
  if (!summary) {
    return undefined;
  }
  return summary.horizon === "12m"
    ? summary.pendingPipelineExpectedLikelyGrants12m
    : summary.pendingPipelineExpectedLikelyGrants24m;
}

function selectedExpectedForRow(row: PortfolioPendingGrantRow, horizon: string | undefined): number | undefined {
  return horizon === "12m" ? row.expectedLikelyGrants12m : row.expectedLikelyGrants24m;
}

function featureStatusTone(value: string | undefined, servingReady: boolean | undefined): "accent" | "neutral" | "warning" {
  if (servingReady) {
    return "accent";
  }

  if (value?.includes("candidate")) {
    return "warning";
  }

  return "neutral";
}

function selectedAverageForRow(row: PortfolioPendingGrantRow, horizon: string | undefined): number | undefined {
  return horizon === "12m" ? row.avgProbability12m : row.avgProbability24m;
}

export function PortfolioPendingGrantsPanel({
  pendingGrants,
  selectedJurisdiction,
  selectedField,
  isLoading = false,
  errorMessage,
  onJurisdictionChange,
  onFieldChange,
}: PortfolioPendingGrantsPanelProps) {
  const summary = pendingGrants.rows.find((row) => row.kind === "summary");
  const jurisdictionRows = pendingGrants.rows.filter((row) => row.kind === "jurisdiction");
  const fieldRows = pendingGrants.rows.filter((row) => row.kind === "field");
  const branchRows = pendingGrants.rows.filter((row) => row.kind === "branch");
  const selectedExpected = selectedExpectedLikelyGrants(summary);
  const selectedAvgProbability = selectedAverageProbability(summary);
  const currentPendingFamilyCount = summary?.currentPendingFamilyCount;
  const currentPendingBranchCount = summary?.currentPendingBranchCount;
  const familyCoveragePct = summary?.pendingPipelineFamilyCoveragePct;
  const branchCoveragePct = summary?.pendingPipelineBranchCoveragePct;
  const jurisdictionOptions = jurisdictionRows
    .map((row) => row.jurisdictionCode)
    .filter((value): value is string => Boolean(value && value.length > 0));
  const fieldOptions = fieldRows
    .map((row) => row.wipoField)
    .filter((value): value is string => Boolean(value && value.length > 0));

  return (
    <Surface
      className={`portfolio-panel--pending ${styles.pendingSurface}`}
      title={
        <PortfolioTooltipLabel
          label="Pending-grant pipeline"
          tooltip={workspaceTooltipCopy.forecast.pendingGrantPipeline}
        />
      }
      icon={<Sparkles size={15} />}
      badge={
        <InfoPill tone={featureStatusTone(summary?.featureStatus, summary?.servingReady)}>
          {summary?.servingReady ? `${summary.featureStatus ?? "candidate_only"} / scored` : summary?.featureStatus ?? "candidate_only"}
        </InfoPill>
      }
    >
      {errorMessage ? <p className="portfolio-error">{errorMessage}</p> : null}
      {!summary ? (
        <p className="portfolio-empty">
          {isLoading ? "Loading pending-grant contract…" : "Pending-grant contract data is unavailable."}
        </p>
      ) : (
        <>
          {isLoading ? <p className="portfolio-small-note">Refreshing pending-grant contract…</p> : null}
          <div className="portfolio-section-summary">
            <article className="portfolio-section-summary__card">
              <PortfolioTooltipLabel
                label="Expected likely grants"
                tooltip={workspaceTooltipCopy.forecast.expectedLikelyGrants}
                textClassName="portfolio-section-summary__label"
              />
              <strong>{formatDecimal(selectedExpected, 1)}</strong>
              <span>{summary.horizon ?? "24m"} directional planning output.</span>
            </article>
            <article className="portfolio-section-summary__card">
              <PortfolioTooltipLabel
                label="Scored pending branches"
                tooltip={workspaceTooltipCopy.forecast.scoredPendingBranches}
                textClassName="portfolio-section-summary__label"
              />
              <strong>
                {formatNumber(summary.pendingPipelineFamilyCount)} families / {formatNumber(summary.pendingPipelineBranchCount)} branches
              </strong>
              <span>
                {currentPendingFamilyCount || currentPendingBranchCount
                  ? `Out of ${formatNumber(currentPendingFamilyCount)} current families / ${formatNumber(currentPendingBranchCount)} branches in the branch ledger.`
                  : "No current pending branch coverage is available in the branch ledger."}
              </span>
            </article>
            <article className="portfolio-section-summary__card">
              <PortfolioTooltipLabel
                label="Current pending coverage"
                tooltip={workspaceTooltipCopy.forecast.currentPendingCoverage}
                textClassName="portfolio-section-summary__label"
              />
              <strong>
                {formatPercent(familyCoveragePct, 1)} families · {formatPercent(branchCoveragePct, 1)} branches
              </strong>
              <span>
                {summary.pendingPipelinePriorityTier?.toUpperCase() ?? "MONITOR"} priority tier ·{" "}
                {percentileLabel(summary.pendingPipelinePercentile)} · {formatPercent(selectedAvgProbability, 1)} avg probability
              </span>
            </article>
          </div>

          {summary.reason ? <p className={styles.pendingReason}>{summary.reason}</p> : null}

          <div className={styles.pendingGrid}>
            <section className={styles.pendingSection}>
              <div className={styles.pendingHead}>
                <h4>
                  <Building2 size={14} />
                  <PortfolioTooltipLabel label="By office" tooltip={workspaceTooltipCopy.forecast.byOffice} />
                </h4>
              </div>
              {jurisdictionRows.length === 0 ? (
                <p className="portfolio-empty">No office-level scored pending rows loaded.</p>
              ) : (
                <div className="portfolio-scroll-table">
                  <table>
                    <thead>
                      <tr>
                        <th>
                          <PortfolioTooltipLabel label="Office" tooltip={workspaceTooltipCopy.forecast.office} />
                        </th>
                        <th>
                          <PortfolioTooltipLabel
                            label="Expected likely grants"
                            tooltip={workspaceTooltipCopy.forecast.expectedLikelyGrants}
                          />
                        </th>
                        <th>
                          <PortfolioTooltipLabel
                            label="Avg probability"
                            tooltip={workspaceTooltipCopy.forecast.avgProbability}
                          />
                        </th>
                        <th>
                          <PortfolioTooltipLabel label="Families" tooltip={workspaceTooltipCopy.forecast.families} />
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {jurisdictionRows.slice(0, 6).map((row) => {
                        const expected = selectedExpectedForRow(row, summary?.horizon);
                        const avgProbability = selectedAverageForRow(row, summary?.horizon);
                        const officeCode = row.jurisdictionCode ?? "";
                        const isSelected = officeCode.length > 0 && selectedJurisdiction === officeCode;
                        return (
                          <tr
                            key={`office-${row.jurisdictionCode}`}
                            className={isSelected ? styles.tableRowSelected : undefined}
                            onClick={() => onJurisdictionChange(isSelected ? "" : officeCode)}
                          >
                            <td>
                              <button
                                type="button"
                                className={styles.tableFilterButton}
                                onClick={(event) => {
                                  event.stopPropagation();
                                  onJurisdictionChange(isSelected ? "" : officeCode);
                                }}
                              >
                                <span className={styles.tableMetricPrimary}>{row.jurisdictionCode ?? "—"}</span>
                              </button>
                            </td>
                            <td><span className={styles.tableMetricPrimary}>{formatDecimal(expected, 1)}</span></td>
                            <td><span className={styles.tableMetricPrimary}>{formatPercent(avgProbability, 1)}</span></td>
                            <td><span className={styles.tableMetricPrimary}>{formatNumber(row.familyCount)}</span></td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </section>

            <section className={styles.pendingSection}>
              <div className={styles.pendingHead}>
                <h4>
                  <Layers3 size={14} />
                  <PortfolioTooltipLabel label="By field" tooltip={workspaceTooltipCopy.forecast.byField} />
                </h4>
              </div>
              {fieldRows.length === 0 ? (
                <p className="portfolio-empty">No field-level scored pending rows loaded.</p>
              ) : (
                <div className="portfolio-scroll-table">
                  <table>
                    <thead>
                      <tr>
                        <th>
                          <PortfolioTooltipLabel label="Field" tooltip={workspaceTooltipCopy.forecast.field} />
                        </th>
                        <th>
                          <PortfolioTooltipLabel
                            label="Expected likely grants"
                            tooltip={workspaceTooltipCopy.forecast.expectedLikelyGrants}
                          />
                        </th>
                        <th>
                          <PortfolioTooltipLabel
                            label="Avg probability"
                            tooltip={workspaceTooltipCopy.forecast.avgProbability}
                          />
                        </th>
                        <th>
                          <PortfolioTooltipLabel label="Families" tooltip={workspaceTooltipCopy.forecast.families} />
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {fieldRows.slice(0, 6).map((row) => {
                        const expected = selectedExpectedForRow(row, summary?.horizon);
                        const avgProbability = selectedAverageForRow(row, summary?.horizon);
                        const fieldName = row.wipoField ?? "";
                        const isSelected = fieldName.length > 0 && selectedField === fieldName;
                        return (
                          <tr
                            key={`field-${row.wipoField}`}
                            className={isSelected ? styles.tableRowSelected : undefined}
                            onClick={() => onFieldChange(isSelected ? "" : fieldName)}
                          >
                            <td>
                              <button
                                type="button"
                                className={styles.tableFilterButton}
                                onClick={(event) => {
                                  event.stopPropagation();
                                  onFieldChange(isSelected ? "" : fieldName);
                                }}
                              >
                                <FieldPill soft>{row.wipoField ?? "—"}</FieldPill>
                              </button>
                            </td>
                            <td><span className={styles.tableMetricPrimary}>{formatDecimal(expected, 1)}</span></td>
                            <td><span className={styles.tableMetricPrimary}>{formatPercent(avgProbability, 1)}</span></td>
                            <td><span className={styles.tableMetricPrimary}>{formatNumber(row.familyCount)}</span></td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </section>
          </div>

          <section className={`${styles.pendingSection} ${styles.pendingFull}`}>
            <div className={styles.pendingHead}>
              <h4>
                <PortfolioTooltipLabel
                  label="Top scored pending branches"
                  tooltip={workspaceTooltipCopy.forecast.topScoredPendingBranches}
                />
              </h4>
            </div>
            <div className={styles.pendingBranchToolbar}>
              <div className={styles.pendingFiltersBar}>
                <label className={styles.pendingFilterGroup} htmlFor="portfolio-pending-branches-jurisdiction">
                  <PortfolioTooltipLabel label="Jurisdiction" tooltip={workspaceTooltipCopy.forecast.jurisdiction} />
                  <select
                    id="portfolio-pending-branches-jurisdiction"
                    className={styles.pendingFilterSelect}
                    value={selectedJurisdiction}
                    onChange={(event) => onJurisdictionChange(event.target.value)}
                  >
                    <option value="">All jurisdictions</option>
                    {jurisdictionOptions.map((value) => (
                      <option key={value} value={value}>
                        {value}
                      </option>
                    ))}
                  </select>
                </label>
                <label className={styles.pendingFilterGroup} htmlFor="portfolio-pending-branches-field">
                  <PortfolioTooltipLabel label="Field" tooltip={workspaceTooltipCopy.forecast.field} />
                  <select
                    id="portfolio-pending-branches-field"
                    className={styles.pendingFilterSelect}
                    value={selectedField}
                    onChange={(event) => onFieldChange(event.target.value)}
                  >
                    <option value="">All fields</option>
                    {fieldOptions.map((value) => (
                      <option key={value} value={value}>
                        {value}
                      </option>
                    ))}
                  </select>
                </label>
              </div>
            </div>
            {branchRows.length === 0 ? (
              <p className="portfolio-empty">No pending branches loaded for this slice.</p>
            ) : (
              <div className="portfolio-scroll-table">
                <table>
                  <thead>
                    <tr>
                      <th>
                        <PortfolioTooltipLabel label="Rank" tooltip={workspaceTooltipCopy.forecast.rank} />
                      </th>
                      <th>
                        <PortfolioTooltipLabel label="Family" tooltip={workspaceTooltipCopy.forecast.family} />
                      </th>
                      <th>
                        <PortfolioTooltipLabel
                          label="Jurisdiction"
                          tooltip={workspaceTooltipCopy.forecast.jurisdiction}
                        />
                      </th>
                      <th>
                        <PortfolioTooltipLabel label="Field" tooltip={workspaceTooltipCopy.forecast.field} />
                      </th>
                      <th>
                        <PortfolioTooltipLabel label="Priority" tooltip={workspaceTooltipCopy.forecast.priority} />
                      </th>
                      <th>
                        <PortfolioTooltipLabel
                          label="Grant probability"
                          tooltip={workspaceTooltipCopy.forecast.grantProbability}
                        />
                      </th>
                      <th>
                        <PortfolioTooltipLabel label="Percentile" tooltip={workspaceTooltipCopy.forecast.percentile} />
                      </th>
                      <th>
                        <PortfolioTooltipLabel label="Blocking" tooltip={workspaceTooltipCopy.forecast.blocking} />
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {branchRows.map((row, index) => (
                      <tr key={`${row.docdbFamilyId}-${row.jurisdictionCode}-${index}`}>
                        <td><span className={styles.tableMetricPrimary}>#{row.rankWithinOfficeHorizon ?? index + 1}</span></td>
                        <td><span className={styles.tableMetricPrimary}>{row.docdbFamilyId ?? "—"}</span></td>
                        <td><span className={styles.tableMetricPrimary}>{row.jurisdictionCode ?? "—"}</span></td>
                        <td><FieldPill soft>{row.primaryWipoField ?? "—"}</FieldPill></td>
                        <td><StatusPill tone="warning">{row.priorityTier ?? "monitor"}</StatusPill></td>
                        <td><span className={styles.tableMetricPrimary}>{formatPercent(row.selectedProbability, 1)}</span></td>
                        <td><span className={styles.tableMetricPrimary}>{percentileLabel(row.percentileWithinOfficeHorizon)}</span></td>
                        <td><span className={styles.tableMetricPrimary}>{formatDecimal(row.familyBlockingPowerScore, 1)}</span></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          <p className={`portfolio-small-note ${styles.footnote}`}>
            Pending-grant output is directional. Use rank, percentile, and tier as the primary planning cues rather than exact realized grant expectations, and read the scored slice against current branch-ledger coverage.
          </p>
        </>
      )}
    </Surface>
  );
}
