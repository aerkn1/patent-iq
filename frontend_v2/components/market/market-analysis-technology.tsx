"use client";

import clsx from "clsx";
import { useMemo, useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { DataTableShell, type DataTableColumn } from "@/components/data-table/data-table-shell";
import { formatNumber, formatPercent } from "@/components/portfolio/portfolio-format";
import { PortfolioTooltipLabel } from "@/components/portfolio/portfolio-tooltip-label";
import { Surface } from "@/components/ui/surface";
import { workspaceTooltipCopy } from "@/lib/content/workspace-tooltips";
import { chartTokens } from "@/lib/design/chart-tokens";
import type { MarketCpcCitingOwnerRow, MarketCpcJurisdictionRow, MarketCpcOwnerRow, MarketCpcTrendRow } from "@/lib/types/market-v2";

import styles from "./market-workspace.module.css";

type TechnologyView = "chart" | "table";

type MarketAnalysisTechnologySectionProps = {
  reducedContextMode: boolean;
  effectiveTechnologyYear: number;
  technologyYearOptions: number[];
  selectedFieldCode?: string;
  technologyCpcTrendsLoading: boolean;
  technologyCpcTrendsError: string | null;
  technologyCpcRows: MarketCpcTrendRow[];
  cpcColumns: DataTableColumn<MarketCpcTrendRow>[];
  technologyJurisdictionFilter: string;
  technologyJurisdictionOptions: string[];
  technologyCpcJurisdictionsLoading: boolean;
  technologyCpcJurisdictionsError: string | null;
  technologyCpcJurisdictionRows: MarketCpcJurisdictionRow[];
  cpcJurisdictionColumns: DataTableColumn<MarketCpcJurisdictionRow>[];
  technologyOwnerCpcFilter: string;
  technologyOwnerCpcOptions: string[];
  technologyCpcOwnersLoading: boolean;
  technologyCpcOwnersError: string | null;
  technologyCpcOwnerRows: MarketCpcOwnerRow[];
  cpcOwnerColumns: DataTableColumn<MarketCpcOwnerRow>[];
  technologyCpcCitingOwnersLoading: boolean;
  technologyCpcCitingOwnersError: string | null;
  technologyCpcCitingOwnerRows: MarketCpcCitingOwnerRow[];
  cpcCitingOwnerColumns: DataTableColumn<MarketCpcCitingOwnerRow>[];
  onTechnologyYearFilterChange: (value: string) => void;
  onTechnologyJurisdictionFilterChange: (value: string) => void;
  onTechnologyOwnerCpcFilterChange: (value: string) => void;
};

const marketTooltipCopy = workspaceTooltipCopy.marketView;

export function MarketAnalysisTechnologySection({
  reducedContextMode,
  effectiveTechnologyYear,
  technologyYearOptions,
  selectedFieldCode,
  technologyCpcTrendsLoading,
  technologyCpcTrendsError,
  technologyCpcRows,
  cpcColumns,
  technologyJurisdictionFilter,
  technologyJurisdictionOptions,
  technologyCpcJurisdictionsLoading,
  technologyCpcJurisdictionsError,
  technologyCpcJurisdictionRows,
  cpcJurisdictionColumns,
  technologyOwnerCpcFilter,
  technologyOwnerCpcOptions,
  technologyCpcOwnersLoading,
  technologyCpcOwnersError,
  technologyCpcOwnerRows,
  cpcOwnerColumns,
  technologyCpcCitingOwnersLoading,
  technologyCpcCitingOwnersError,
  technologyCpcCitingOwnerRows,
  cpcCitingOwnerColumns,
  onTechnologyYearFilterChange,
  onTechnologyJurisdictionFilterChange,
  onTechnologyOwnerCpcFilterChange,
}: MarketAnalysisTechnologySectionProps) {
  const [cpcTrendView, setCpcTrendView] = useState<TechnologyView>("chart");
  const [cpcGeographyView, setCpcGeographyView] = useState<TechnologyView>("chart");
  const topCpcChartRows = useMemo(() => technologyCpcRows.slice(0, 12), [technologyCpcRows]);
  const cpcGeographyChartRows = useMemo(() => technologyCpcJurisdictionRows.slice(0, 12), [technologyCpcJurisdictionRows]);
  const topCpcChartHeight = Math.max(320, topCpcChartRows.length * 34);
  const cpcGeographyChartHeight = Math.max(320, cpcGeographyChartRows.length * 34);

  return (
    <div className={styles.tabStack}>
      {!reducedContextMode ? (
        <Surface
          className={styles.detailSurface}
          title={<PortfolioTooltipLabel label="Technology filters" tooltip={marketTooltipCopy.technologyFilters} />}
          description="Selected-year control applied across all technology tables for the current field."
        >
          <div className={styles.controlRow}>
            <label className={styles.controlField}>
              <PortfolioTooltipLabel label="Year" tooltip={marketTooltipCopy.year} />
              <select value={String(effectiveTechnologyYear)} onChange={(event) => onTechnologyYearFilterChange(event.target.value)}>
                {technologyYearOptions.map((year) => (
                  <option key={year} value={year}>
                    {year}
                  </option>
                ))}
              </select>
            </label>

            <div className={styles.controlNote}>
              <PortfolioTooltipLabel label="Selected field" tooltip={marketTooltipCopy.selectedField} />
              <strong>{selectedFieldCode ?? "—"}</strong>
              <p>Changing the year refreshes Top CPC groups, Top owners by CPC, Most citing owners by CPC, and CPC geography within field.</p>
            </div>
          </div>
        </Surface>
      ) : null}

      {!reducedContextMode ? (
        <Surface
          className={styles.detailSurface}
          title={
            <PortfolioTooltipLabel
              label="Top CPC groups in selected field"
              tooltip={marketTooltipCopy.topCpcGroupsInSelectedField}
            />
          }
          description={`Selected-year CPC ranking inside the field, showing which groups define the technical core for ${effectiveTechnologyYear}.`}
          badge={
            <div className={styles.surfaceBadgeControls}>
              <div className={styles.controlField}>
                <PortfolioTooltipLabel label="View" tooltip={marketTooltipCopy.view} />
                <div className={styles.sectionToggle} role="tablist" aria-label="Top CPC groups view">
                  <button
                    type="button"
                    role="tab"
                    aria-selected={cpcTrendView === "chart"}
                    className={clsx(styles.sectionToggleButton, cpcTrendView === "chart" && styles.sectionToggleButtonActive)}
                    onClick={() => setCpcTrendView("chart")}
                  >
                    <PortfolioTooltipLabel label="Chart" tooltip={marketTooltipCopy.chartView} />
                  </button>
                  <button
                    type="button"
                    role="tab"
                    aria-selected={cpcTrendView === "table"}
                    className={clsx(styles.sectionToggleButton, cpcTrendView === "table" && styles.sectionToggleButtonActive)}
                    onClick={() => setCpcTrendView("table")}
                  >
                    <PortfolioTooltipLabel label="Table" tooltip={marketTooltipCopy.tableView} />
                  </button>
                </div>
              </div>
            </div>
          }
        >
          {technologyCpcTrendsLoading && technologyCpcRows.length === 0 ? (
            <p className="portfolio-empty">Loading CPC trend rows…</p>
          ) : technologyCpcTrendsError ? (
            <p className="portfolio-error">{technologyCpcTrendsError}</p>
          ) : technologyCpcRows.length === 0 ? (
            <p className="portfolio-empty">No CPC trend rows are available for this field.</p>
          ) : cpcTrendView === "chart" ? (
            <div className={styles.chartSurface}>
              <ResponsiveContainer width="100%" height={topCpcChartHeight}>
                <BarChart data={topCpcChartRows} layout="vertical" margin={{ top: 8, right: 12, left: 0, bottom: 8 }}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                  <XAxis type="number" tickFormatter={(value: number) => formatNumber(value)} />
                  <YAxis type="category" dataKey="cpc_main_group" width={96} interval={0} tickLine={false} axisLine={false} />
                  <Tooltip
                    formatter={(value: number, name: string, item) => {
                      if (name === "cpc_family_count_asof") {
                        return [formatNumber(value), "Families"];
                      }
                      if (name === "cpc_active_family_count_asof") {
                        return [formatNumber(value), "Active families"];
                      }
                      if (name === "cpc_family_share_within_segment_asof") {
                        return [formatPercent(value), "Field share"];
                      }
                      return [formatNumber(value), name];
                    }}
                    labelFormatter={(_, payload) => payload?.[0]?.payload?.cpc_main_group ?? "CPC main group"}
                  />
                  <Bar dataKey="cpc_family_count_asof" name="Families" fill={chartTokens.series.info} radius={[0, 10, 10, 0]} />
                  <Bar
                    dataKey="cpc_active_family_count_asof"
                    name="Active families"
                    fill={chartTokens.series.success}
                    radius={[0, 10, 10, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <DataTableShell
              columns={cpcColumns}
              data={technologyCpcRows}
              emptyMessage="No CPC trend rows are available for this field."
              getRowKey={(row) => `${row.cpc_main_group}-${row.as_of_year}`}
              pageSize={10}
            />
          )}
        </Surface>
      ) : (
        <Surface
          className={styles.detailSurface}
          title={
            <PortfolioTooltipLabel
              label="Top CPC groups in selected field"
              tooltip={marketTooltipCopy.topCpcGroupsInSelectedField}
            />
          }
          description="This slice is hidden while the workspace is in reduced context mode."
        >
          <p className="portfolio-empty">Reduced context mode is active, so selected-field CPC detail is currently suppressed.</p>
        </Surface>
      )}

      {!reducedContextMode ? (
        <Surface
          className={styles.detailSurface}
          title={
            <PortfolioTooltipLabel
              label="Top owners by CPC main group"
              tooltip={marketTooltipCopy.topOwnersByCpcMainGroup}
            />
          }
          description={`Selected-year owner concentration inside one CPC slice for ${effectiveTechnologyYear}.`}
          badge={
            <label className={styles.controlField}>
              <PortfolioTooltipLabel label="CPC main group" tooltip={marketTooltipCopy.cpcMainGroup} />
              <select
                value={technologyOwnerCpcFilter}
                onChange={(event) => onTechnologyOwnerCpcFilterChange(event.target.value)}
                disabled={technologyOwnerCpcOptions.length === 0}
              >
                {technologyOwnerCpcOptions.length === 0 ? (
                  <option value="">No CPC groups</option>
                ) : (
                  technologyOwnerCpcOptions.map((option) => (
                    <option key={option} value={option}>
                      {option}
                    </option>
                  ))
                )}
              </select>
            </label>
          }
        >
          {technologyOwnerCpcOptions.length === 0 ? (
            <p className="portfolio-empty">No CPC main groups are available for owner analysis in this field-year slice.</p>
          ) : technologyCpcOwnersLoading && technologyCpcOwnerRows.length === 0 ? (
            <p className="portfolio-empty">Loading owner rows…</p>
          ) : technologyCpcOwnersError ? (
            <p className="portfolio-error">{technologyCpcOwnersError}</p>
          ) : technologyCpcOwnerRows.length === 0 ? (
            <p className="portfolio-empty">No owner rows are available for the selected CPC main group.</p>
          ) : (
            <DataTableShell
              columns={cpcOwnerColumns}
              data={technologyCpcOwnerRows}
              emptyMessage="No owner rows are available for the selected CPC main group."
              getRowKey={(row) => `${row.cpc_main_group}-${row.owner_name}-${row.as_of_year}`}
              pageSize={8}
            />
          )}
        </Surface>
      ) : null}

      {!reducedContextMode ? (
        <Surface
          className={styles.detailSurface}
          title={
            <PortfolioTooltipLabel
              label="Most citing owners by selected CPC"
              tooltip={marketTooltipCopy.mostCitingOwnersBySelectedCpc}
            />
          }
          description={`Selected-year external citation pressure into one CPC slice for ${effectiveTechnologyYear}.`}
          badge={
            <label className={styles.controlField}>
              <PortfolioTooltipLabel label="CPC main group" tooltip={marketTooltipCopy.cpcMainGroup} />
              <select
                value={technologyOwnerCpcFilter}
                onChange={(event) => onTechnologyOwnerCpcFilterChange(event.target.value)}
                disabled={technologyOwnerCpcOptions.length === 0}
              >
                {technologyOwnerCpcOptions.length === 0 ? (
                  <option value="">No CPC groups</option>
                ) : (
                  technologyOwnerCpcOptions.map((option) => (
                    <option key={option} value={option}>
                      {option}
                    </option>
                  ))
                )}
              </select>
            </label>
          }
        >
          {technologyOwnerCpcOptions.length === 0 ? (
            <p className="portfolio-empty">No CPC main groups are available for citing-owner analysis in this field-year slice.</p>
          ) : technologyCpcCitingOwnersLoading && technologyCpcCitingOwnerRows.length === 0 ? (
            <p className="portfolio-empty">Loading citing-owner rows…</p>
          ) : technologyCpcCitingOwnersError ? (
            <p className="portfolio-error">{technologyCpcCitingOwnersError}</p>
          ) : technologyCpcCitingOwnerRows.length === 0 ? (
            <p className="portfolio-empty">No citing-owner rows are available for the selected CPC main group.</p>
          ) : (
            <DataTableShell
              columns={cpcCitingOwnerColumns}
              data={technologyCpcCitingOwnerRows}
              emptyMessage="No citing-owner rows are available for the selected CPC main group."
              getRowKey={(row) => `${row.cpc_main_group}-${row.citing_owner_name}-${row.as_of_year}`}
              pageSize={8}
            />
          )}
        </Surface>
      ) : null}

      {!reducedContextMode ? (
        <Surface
          className={styles.featureSurface}
          title={
            <PortfolioTooltipLabel
              label="CPC geography within field"
              tooltip={marketTooltipCopy.cpcGeographyWithinField}
            />
          }
          description={`CPC and jurisdiction slices inside the selected field for ${effectiveTechnologyYear}, ranked by family footprint within the selected jurisdiction.`}
          badge={
            <div className={styles.surfaceBadgeControls}>
              <label className={styles.controlField}>
                <PortfolioTooltipLabel label="Jurisdiction" tooltip={marketTooltipCopy.jurisdiction} />
                <select
                  value={technologyJurisdictionFilter}
                  onChange={(event) => onTechnologyJurisdictionFilterChange(event.target.value)}
                  disabled={technologyJurisdictionOptions.length === 0}
                >
                  {technologyJurisdictionOptions.length === 0 ? (
                    <option value="">No jurisdictions</option>
                  ) : (
                    technologyJurisdictionOptions.map((option) => (
                      <option key={option} value={option}>
                        {option}
                      </option>
                    ))
                  )}
                </select>
              </label>
              <div className={styles.controlField}>
                <PortfolioTooltipLabel label="View" tooltip={marketTooltipCopy.view} />
                <div className={styles.sectionToggle} role="tablist" aria-label="CPC geography view">
                  <button
                    type="button"
                    role="tab"
                    aria-selected={cpcGeographyView === "chart"}
                    className={clsx(
                      styles.sectionToggleButton,
                      cpcGeographyView === "chart" && styles.sectionToggleButtonActive,
                    )}
                    onClick={() => setCpcGeographyView("chart")}
                  >
                    <PortfolioTooltipLabel label="Chart" tooltip={marketTooltipCopy.chartView} />
                  </button>
                  <button
                    type="button"
                    role="tab"
                    aria-selected={cpcGeographyView === "table"}
                    className={clsx(
                      styles.sectionToggleButton,
                      cpcGeographyView === "table" && styles.sectionToggleButtonActive,
                    )}
                    onClick={() => setCpcGeographyView("table")}
                  >
                    <PortfolioTooltipLabel label="Table" tooltip={marketTooltipCopy.tableView} />
                  </button>
                </div>
              </div>
            </div>
          }
        >
          {technologyCpcJurisdictionsLoading && technologyCpcJurisdictionRows.length === 0 ? (
            <p className="portfolio-empty">Loading CPC-by-jurisdiction rows…</p>
          ) : technologyCpcJurisdictionsError ? (
            <p className="portfolio-error">{technologyCpcJurisdictionsError}</p>
          ) : technologyCpcJurisdictionRows.length === 0 ? (
            <p className="portfolio-empty">No CPC-by-jurisdiction rows are available for the selected jurisdiction.</p>
          ) : cpcGeographyView === "chart" ? (
            <div className={styles.chartSurface}>
              <ResponsiveContainer width="100%" height={cpcGeographyChartHeight}>
                <BarChart data={cpcGeographyChartRows} layout="vertical" margin={{ top: 8, right: 12, left: 0, bottom: 8 }}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                  <XAxis type="number" tickFormatter={(value: number) => formatNumber(value)} />
                  <YAxis type="category" dataKey="cpc_main_group" width={96} interval={0} tickLine={false} axisLine={false} />
                  <Tooltip
                    formatter={(value: number, name: string) => {
                      if (name === "family_count_asof") {
                        return [formatNumber(value), "Families"];
                      }
                      if (name === "active_family_count_asof") {
                        return [formatNumber(value), "Active families"];
                      }
                      if (name === "family_share_within_slice_asof") {
                        return [formatPercent(value), "Slice share"];
                      }
                      return [formatNumber(value), name];
                    }}
                    labelFormatter={(_, payload) => payload?.[0]?.payload?.cpc_main_group ?? "CPC main group"}
                  />
                  <Bar dataKey="family_count_asof" name="Families" fill={chartTokens.series.info} radius={[0, 10, 10, 0]} />
                  <Bar
                    dataKey="active_family_count_asof"
                    name="Active families"
                    fill={chartTokens.series.success}
                    radius={[0, 10, 10, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <DataTableShell
              columns={cpcJurisdictionColumns}
              data={technologyCpcJurisdictionRows}
              emptyMessage="No CPC-by-jurisdiction rows are available for the selected jurisdiction."
              getRowKey={(row) => `${row.cpc_main_group}-${row.jurisdiction_code}-${row.as_of_year}`}
              pageSize={10}
            />
          )}
        </Surface>
      ) : null}
    </div>
  );
}
