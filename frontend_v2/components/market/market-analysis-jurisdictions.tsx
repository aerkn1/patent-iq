"use client";

import clsx from "clsx";
import {
  CartesianGrid,
  ComposedChart,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  Bar,
  BarChart,
} from "recharts";

import { DataTableShell, type DataTableColumn } from "@/components/data-table/data-table-shell";
import { formatNumber } from "@/components/portfolio/portfolio-format";
import { PortfolioTooltipLabel } from "@/components/portfolio/portfolio-tooltip-label";
import { Surface } from "@/components/ui/surface";
import { workspaceTooltipCopy } from "@/lib/content/workspace-tooltips";
import { chartTokens } from "@/lib/design/chart-tokens";
import type { MarketApplicationGrantRow, MarketGrantMixRow, MarketSelectedSegment } from "@/lib/types/market-v2";

import styles from "./market-workspace.module.css";

type ApplicationsGrantView = "chart" | "table";

type ApplicationsGrantChartRow = {
  as_of_year: number;
  application_count: number;
  grant_count: number;
  total_event_count: number;
};

type MarketAnalysisJurisdictionsSectionProps = {
  fieldJurisdictionRows: MarketSelectedSegment["field_jurisdictions"];
  fieldJurisdictionColumns: DataTableColumn<MarketSelectedSegment["field_jurisdictions"][number]>[];
  grantMixLoading: boolean;
  grantMixError: string | null;
  grantMixRows: MarketGrantMixRow[];
  grantMixChartHeight: number;
  applicationsGrantsLoading: boolean;
  applicationsGrantsError: string | null;
  applicationsGrantRows: MarketApplicationGrantRow[];
  applicationsGrantJurisdictionOptions: string[];
  effectiveApplicationsGrantJurisdictionFilter: string;
  applicationsGrantView: ApplicationsGrantView;
  applicationsGrantChartRows: ApplicationsGrantChartRow[];
  applicationsGrantColumns: DataTableColumn<MarketApplicationGrantRow>[];
  filteredApplicationsGrantRows: MarketApplicationGrantRow[];
  onApplicationsGrantJurisdictionFilterChange: (value: string) => void;
  onApplicationsGrantViewChange: (view: ApplicationsGrantView) => void;
};

const marketTooltipCopy = workspaceTooltipCopy.marketView;

export function MarketAnalysisJurisdictionsSection({
  fieldJurisdictionRows,
  fieldJurisdictionColumns,
  grantMixLoading,
  grantMixError,
  grantMixRows,
  grantMixChartHeight,
  applicationsGrantsLoading,
  applicationsGrantsError,
  applicationsGrantRows,
  applicationsGrantJurisdictionOptions,
  effectiveApplicationsGrantJurisdictionFilter,
  applicationsGrantView,
  applicationsGrantChartRows,
  applicationsGrantColumns,
  filteredApplicationsGrantRows,
  onApplicationsGrantJurisdictionFilterChange,
  onApplicationsGrantViewChange,
}: MarketAnalysisJurisdictionsSectionProps) {
  return (
    <div className={styles.tabStack}>
      <div className={styles.detailGrid}>
        <Surface
          className={styles.detailSurface}
          title={
            <PortfolioTooltipLabel
              label="Field footprint by jurisdiction"
              tooltip={marketTooltipCopy.fieldFootprintByJurisdiction}
            />
          }
          description="Unique family geography for the selected field across jurisdictions, without summing CPC overlaps."
        >
          {fieldJurisdictionRows.length === 0 ? (
            <p className="portfolio-empty">No field-by-jurisdiction rows are available for this field.</p>
          ) : (
            <DataTableShell
              columns={fieldJurisdictionColumns}
              data={fieldJurisdictionRows}
              emptyMessage="No field-by-jurisdiction rows are available for this field."
              getRowKey={(row) => `${row.jurisdiction_code}-${row.as_of_year}`}
            />
          )}
        </Surface>

        <Surface
          className={styles.detailSurface}
          title={<PortfolioTooltipLabel label="Grant mix by office" tooltip={marketTooltipCopy.grantMixByOffice} />}
          description="Current selected-year application and grant publication mix by office for the selected field."
        >
          {grantMixLoading && grantMixRows.length === 0 ? (
            <p className="portfolio-empty">Loading grant-mix rows…</p>
          ) : grantMixError ? (
            <p className="portfolio-error">{grantMixError}</p>
          ) : grantMixRows.length === 0 ? (
            <p className="portfolio-empty">No grant-mix rows are available for this field.</p>
          ) : (
            <div className={styles.chartSurface}>
              <ResponsiveContainer width="100%" height={grantMixChartHeight}>
                <BarChart data={grantMixRows} layout="vertical" margin={{ top: 8, right: 12, left: 0, bottom: 8 }}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                  <XAxis type="number" tickFormatter={(value: number) => formatNumber(value)} />
                  <YAxis type="category" dataKey="jurisdiction_code" width={60} interval={0} tickLine={false} axisLine={false} />
                  <Tooltip
                    formatter={(value: number, name: string) => {
                      if (name === "grant_count") {
                        return [formatNumber(value), "Grants"];
                      }
                      if (name === "application_count") {
                        return [formatNumber(value), "Applications"];
                      }
                      return [formatNumber(value), name];
                    }}
                  />
                  <Bar dataKey="grant_count" fill={chartTokens.series.success} radius={[0, 10, 10, 0]} />
                  <Bar dataKey="application_count" fill={chartTokens.series.info} radius={[0, 10, 10, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </Surface>
      </div>

      <div className={styles.detailGrid}>
        <Surface
          className={styles.detailSurface}
          title={
            <PortfolioTooltipLabel
              label="Applications and grants by jurisdiction"
              tooltip={marketTooltipCopy.applicationsAndGrantsByJurisdiction}
            />
          }
          description="Year-by-year office event flow for the selected field, kept separate from unique-family stock metrics."
        >
          {applicationsGrantsLoading && applicationsGrantRows.length === 0 ? (
            <p className="portfolio-empty">Loading applications and grants…</p>
          ) : applicationsGrantsError ? (
            <p className="portfolio-error">{applicationsGrantsError}</p>
          ) : applicationsGrantRows.length === 0 ? (
            <p className="portfolio-empty">No application/grant rows are available for this field.</p>
          ) : (
            <div className={styles.evidenceColumn}>
              <div className={styles.controlRow}>
                <label className={styles.controlField}>
                  <PortfolioTooltipLabel label="Jurisdiction" tooltip={marketTooltipCopy.jurisdiction} />
                  <select
                    aria-label="Applications and grants jurisdiction filter"
                    value={effectiveApplicationsGrantJurisdictionFilter}
                    onChange={(event) => onApplicationsGrantJurisdictionFilterChange(event.target.value)}
                  >
                    <option value="all">All jurisdictions</option>
                    {applicationsGrantJurisdictionOptions.map((option) => (
                      <option key={option} value={option}>
                        {option}
                      </option>
                    ))}
                  </select>
                </label>

                <div className={styles.controlField}>
                  <PortfolioTooltipLabel label="View" tooltip={marketTooltipCopy.view} />
                  <div className={styles.sectionToggle} role="tablist" aria-label="Applications and grants view">
                    <button
                      type="button"
                      role="tab"
                      aria-selected={applicationsGrantView === "chart"}
                      className={clsx(styles.sectionToggleButton, applicationsGrantView === "chart" && styles.sectionToggleButtonActive)}
                      onClick={() => onApplicationsGrantViewChange("chart")}
                    >
                      <PortfolioTooltipLabel label="Chart" tooltip={marketTooltipCopy.chartView} />
                    </button>
                    <button
                      type="button"
                      role="tab"
                      aria-selected={applicationsGrantView === "table"}
                      className={clsx(styles.sectionToggleButton, applicationsGrantView === "table" && styles.sectionToggleButtonActive)}
                      onClick={() => onApplicationsGrantViewChange("table")}
                    >
                      <PortfolioTooltipLabel label="Table" tooltip={marketTooltipCopy.tableView} />
                    </button>
                  </div>
                </div>
              </div>

              {applicationsGrantView === "chart" ? (
                applicationsGrantChartRows.length === 0 ? (
                  <p className="portfolio-empty">No application/grant chronology is available for the selected jurisdiction.</p>
                ) : (
                  <div className={styles.chartSurface}>
                    <ResponsiveContainer width="100%" height={320}>
                      <ComposedChart data={applicationsGrantChartRows} margin={{ top: 12, right: 12, left: 0, bottom: 8 }}>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} />
                        <XAxis dataKey="as_of_year" tickLine={false} axisLine={false} />
                        <YAxis tickFormatter={(value: number) => formatNumber(value)} tickLine={false} axisLine={false} />
                        <Tooltip
                          labelFormatter={(value: number) => `Year ${formatNumber(value)}`}
                          formatter={(value: number, name: string) => {
                            if (name === "application_count" || name === "Applications") {
                              return [formatNumber(value), "Applications"];
                            }
                            if (name === "grant_count" || name === "Grants") {
                              return [formatNumber(value), "Grants"];
                            }
                            return [formatNumber(value), name];
                          }}
                        />
                        <Line
                          type="monotone"
                          dataKey="application_count"
                          name="Applications"
                          stroke={chartTokens.series.info}
                          strokeWidth={3}
                          dot={{ r: 3 }}
                          activeDot={{ r: 5 }}
                        />
                        <Line
                          type="monotone"
                          dataKey="grant_count"
                          name="Grants"
                          stroke={chartTokens.series.success}
                          strokeWidth={3}
                          dot={{ r: 3 }}
                          activeDot={{ r: 5 }}
                        />
                      </ComposedChart>
                    </ResponsiveContainer>
                  </div>
                )
              ) : (
                <DataTableShell
                  columns={applicationsGrantColumns}
                  data={filteredApplicationsGrantRows}
                  emptyMessage="No application/grant rows are available for the selected jurisdiction."
                  getRowKey={(row) => `${row.as_of_year}-${row.jurisdiction_code}`}
                />
              )}
            </div>
          )}
        </Surface>
      </div>
    </div>
  );
}
