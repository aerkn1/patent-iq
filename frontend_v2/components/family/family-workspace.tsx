"use client";

import clsx from "clsx";
import { AlertTriangle, BookOpenText, GitBranch, Radar, ShieldCheck, Sparkles, TableProperties } from "lucide-react";
import Link from "next/link";
import { useEffect, useMemo, useState, type ReactNode } from "react";
import { Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, ComposedChart, Legend, Line, LineChart, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { DataTableShell, type DataTableColumn } from "@/components/data-table/data-table-shell";
import { formatDecimal, formatNumber, formatOrdinal, formatPercent } from "@/components/portfolio/portfolio-format";
import { PortfolioMetricTooltip } from "@/components/portfolio/portfolio-metric-tooltip";
import { PortfolioPaginationControls } from "@/components/portfolio/portfolio-pagination";
import { PortfolioTooltipLabel } from "@/components/portfolio/portfolio-tooltip-label";
import { FieldPill, InfoPill, StatusPill, TagPill } from "@/components/ui/data-pill";
import { Surface } from "@/components/ui/surface";
import { useWorkspaceContextOverride } from "@/components/ui/workspace-context";
import { WorkspaceTabs, type WorkspaceTabItem } from "@/components/ui/workspace-tabs";
import { fetchFamilyOverview, fetchFamilySection } from "@/lib/api/family-v2";
import { workspaceTooltipCopy } from "@/lib/content/workspace-tooltips";
import { chartTokens } from "@/lib/design/chart-tokens";
import type {
  FamilyCaveat,
  FamilyOverviewMetric,
  FamilyOverviewPayload,
  FamilySectionPayload,
  FamilySummaryCard,
  FamilyWorkspaceTab,
} from "@/lib/types/family-v2";

import styles from "./family-workspace.module.css";

type FamilyWorkspaceProps = {
  familyId: string;
};

const tabs: Array<WorkspaceTabItem<FamilyWorkspaceTab> & { loadingLabel: string }> = [
  {
    id: "publications",
    label: <PortfolioTooltipLabel label="Publications" tooltip={workspaceTooltipCopy.familyView.tabPublications} />,
    hint: "family set",
    loadingLabel: "publications",
  },
  {
    id: "legal",
    label: <PortfolioTooltipLabel label="Legal" tooltip={workspaceTooltipCopy.familyView.tabLegal} />,
    hint: "durability",
    loadingLabel: "legal",
  },
  {
    id: "fields",
    label: <PortfolioTooltipLabel label="Fields" tooltip={workspaceTooltipCopy.familyView.tabFields} />,
    hint: "footprint",
    loadingLabel: "fields",
  },
  {
    id: "evidence",
    label: <PortfolioTooltipLabel label="Citation" tooltip={workspaceTooltipCopy.familyView.tabCitation} />,
    hint: "forward",
    loadingLabel: "citation",
  },
];

function emptyFamilySectionPayload(familyId: string): FamilySectionPayload {
  return {
    familyId,
    summary: null,
    rows: [],
    series: [],
    meta: {
      page: "family",
      supportLevel: "limited",
      caveats: [],
      coverage: null,
      pagination: null,
    },
  };
}

function prettyLabel(value: string): string {
  const labelOverrides: Record<string, string> = {
    forward_citation_event_count: "Forward citation events",
    forward_clean_citation_event_count: "Forward clean citation events",
    forward_citations_raw: "Raw citing families",
    forward_citations_clean: "Distinct forward citation count",
    forward_citing_owner_count: "Distinct forward owner count",
    forward_citations_weighted: "Weighted citation mass",
    forward_citations_5y: "Citing families (5y)",
    forward_citations_7y: "Distinct forward citation count (7y)",
    backward_citation_event_count: "Backward citation events",
    backward_clean_citation_event_count: "Backward clean citation events",
    backward_citations_clean: "Distinct backward citation count",
    backward_cited_owner_count: "Distinct backward owner count",
    backward_npl_citation_count: "Distinct backward NPL citation count",
  };
  const override = labelOverrides[value];
  if (override) {
    return override;
  }
  return value
    .replace(/_/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function formatValue(key: string, value: unknown): string {
  if (value == null) {
    return "—";
  }
  if (Array.isArray(value)) {
    return value.map((item) => String(item)).join(", ") || "—";
  }
  if (typeof value === "boolean") {
    return value ? "Yes" : "No";
  }
  if (typeof value === "number") {
    const normalizedKey = key.toLowerCase();
    if (normalizedKey === "legal_durability") {
      return `${formatDecimal(value, 1)} / 100`;
    }
    if (
      normalizedKey.includes("pct") ||
      normalizedKey.includes("share") ||
      normalizedKey.includes("fraction")
    ) {
      return formatPercent(value);
    }
    if (normalizedKey.includes("percentile")) {
      return `${formatOrdinal(value)} percentile`;
    }
    if (
      normalizedKey.includes("score") ||
      normalizedKey.includes("power") ||
      normalizedKey.includes("heritage") ||
      normalizedKey.includes("weighted") ||
      normalizedKey.includes("enforceability")
    ) {
      return formatDecimal(value, 2);
    }
    return Number.isInteger(value) ? formatNumber(value) : formatDecimal(value, 2);
  }
  return String(value);
}

function formatPeerRankOutOf100(value: unknown): string {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return "—";
  }
  const rankValue = value >= 0 && value <= 1 ? value * 100 : value;
  const normalized = Number.isInteger(rankValue) ? formatNumber(rankValue) : formatDecimal(rankValue, 1);
  return `Peer rank ${normalized} / 100`;
}

function formatIndexOutOf100(value: unknown): string {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return "—";
  }
  const indexValue = value >= 0 && value <= 1 ? value * 100 : value;
  const normalized = Number.isInteger(indexValue) ? formatNumber(indexValue) : formatDecimal(indexValue, 1);
  return `${normalized} / 100`;
}

function findOverviewMetricValue(metrics: FamilyOverviewMetric[], label: string): unknown {
  return metrics.find((metric) => metric.label === label)?.value;
}

function supportLabel(value: string): string {
  if (value === "strong") {
    return "Strong support";
  }
  if (value === "high") {
    return "High support";
  }
  if (value === "moderate") {
    return "Moderate support";
  }
  if (value === "candidate_only") {
    return "Candidate-only support";
  }
  return "Limited support";
}

function supportTone(value: string): "positive" | "warning" | "critical" | "neutral" | "info" {
  const normalized = value.toLowerCase();
  if (normalized === "strong" || normalized === "high") {
    return "positive";
  }
  if (normalized === "moderate") {
    return "info";
  }
  if (normalized === "candidate_only") {
    return "critical";
  }
  if (normalized === "limited") {
    return "warning";
  }
  return "neutral";
}

const familyCitationSummaryTooltips: Record<string, string> = {
  forward_citation_event_count: workspaceTooltipCopy.familyView.forwardCitationEvents,
  forward_clean_citation_event_count: workspaceTooltipCopy.familyView.forwardCleanCitationEvents,
  forward_citations_raw: workspaceTooltipCopy.familyView.rawCitingFamilies,
  forward_citations_clean: workspaceTooltipCopy.familyView.distinctForwardCitationCount,
  forward_citing_owner_count: workspaceTooltipCopy.familyView.distinctForwardOwnerCount,
  forward_citations_weighted: workspaceTooltipCopy.familyView.weightedCitationMass,
  forward_citations_5y: workspaceTooltipCopy.familyView.citingFamilies5y,
  forward_citations_7y: workspaceTooltipCopy.familyView.distinctForwardCitationCount7y,
  backward_citation_event_count: workspaceTooltipCopy.familyView.backwardCitationEvents,
  backward_clean_citation_event_count: workspaceTooltipCopy.familyView.backwardCleanCitationEvents,
  backward_citations_clean: workspaceTooltipCopy.familyView.distinctBackwardCitationCount,
  backward_cited_owner_count: workspaceTooltipCopy.familyView.distinctBackwardOwnerCount,
  backward_npl_citation_count: workspaceTooltipCopy.familyView.distinctBackwardNplCitationCount,
};

function branchStateTone(value: string): "positive" | "warning" | "critical" | "neutral" {
  const normalized = value.toLowerCase();
  if (normalized.includes("grant") || normalized.includes("active")) {
    return "positive";
  }
  if (normalized.includes("pending")) {
    return "warning";
  }
  if (normalized.includes("lapse") || normalized.includes("expiry") || normalized.includes("negative")) {
    return "critical";
  }
  return "neutral";
}

function horizonSortValue(value: string): number {
  const match = value.match(/^(\d+)\s*([a-z]+)$/i);
  if (!match) {
    return Number.MAX_SAFE_INTEGER;
  }
  const amount = Number(match[1]);
  const unit = match[2].toLowerCase();
  if (unit === "m") {
    return amount;
  }
  if (unit === "y") {
    return amount * 12;
  }
  return Number.MAX_SAFE_INTEGER;
}

const pressureTooltipText =
  "Pressure sums threat-weighted clean citations. It rises when citations come from stronger stages, higher-value jurisdictions, or hotter fields.";

function SummaryRail({ cards }: { cards: FamilySummaryCard[] }) {
  return (
    <section className={styles.summaryRail}>
      <div className={styles.summaryGrid}>
        {cards.map((card, index) => (
          <article
            key={card.key}
            className={clsx(
              styles.summaryCard,
              card.bandCode === "low" && styles.summaryCardWarning,
              card.bandCode !== "low" && styles.summaryCardNeutral,
            )}
            style={{ animationDelay: `${index * 60}ms` }}
          >
            <div className={styles.summaryLabel}>
              <span>{card.label}</span>
              {card.tooltip ? <PortfolioMetricTooltip text={card.tooltip} /> : null}
            </div>
            <div className={styles.summaryValue}>{formatValue(card.key, card.value)}</div>
            {card.bandLabel ? (
              <div className={styles.summaryMeta}>
                <span className={styles.summaryBandLabel}>{card.bandLabel}</span>
                {card.peerPercentile != null ? <span>{formatOrdinal(card.peerPercentile)} percentile</span> : null}
                {card.peerCohortLabel ? <span>{card.peerCohortLabel}</span> : null}
              </div>
            ) : null}
          </article>
        ))}
      </div>
    </section>
  );
}

function CaveatPanel({ caveats }: { caveats: FamilyCaveat[] }) {
  if (caveats.length === 0) {
    return null;
  }

  return (
    <Surface
      className={clsx("family-panel--caveat", styles.caveatPanel)}
      title={<PortfolioTooltipLabel label="Methodology" tooltip={workspaceTooltipCopy.familyView.methodology} />}
      description="Support notes and scope caveats for the active family view."
    >
      <details className={styles.caveatDisclosure}>
        <summary className={styles.caveatDisclosureSummary}>
          <span>Open support notes</span>
          <InfoPill tone="warning">{formatNumber(caveats.length)} notes</InfoPill>
        </summary>
        <div className={styles.caveatList}>
          {caveats.map((caveat) => (
            <article key={caveat.code} className={styles.caveatCard}>
              <span className={styles.caveatCode}>{caveat.code}</span>
              <strong>{caveat.title}</strong>
              <p>{caveat.detail}</p>
            </article>
          ))}
        </div>
      </details>
    </Surface>
  );
}

function KeyValuePanel({
  title,
  icon,
  values,
  labelOverrides,
  labelTooltips,
  descriptions,
  valueFormatters,
  panelClassName,
  gridClassName,
  meterValues,
}: {
  title: ReactNode;
  icon?: ReactNode;
  values: Record<string, unknown>;
  labelOverrides?: Record<string, string>;
  labelTooltips?: Record<string, string>;
  descriptions?: Record<string, string>;
  valueFormatters?: Record<string, (value: unknown) => string>;
  panelClassName?: string;
  gridClassName?: string;
  meterValues?: Record<string, number | null | undefined>;
}) {
  const entries = Object.entries(values).filter(([, value]) => value !== undefined && value !== null);
  if (entries.length === 0) {
    return null;
  }

  return (
    <Surface className={clsx(styles.detailPanel, panelClassName)} title={title} icon={icon}>
      <dl className={clsx(styles.keyValueGrid, gridClassName)}>
        {entries.map(([key, value]) => (
          <div key={key} className={styles.keyValueItem}>
            <dt>
              {labelTooltips?.[key] ? (
                <PortfolioTooltipLabel
                  label={labelOverrides?.[key] ?? prettyLabel(key)}
                  tooltip={labelTooltips[key]}
                />
              ) : (
                labelOverrides?.[key] ?? prettyLabel(key)
              )}
            </dt>
            <dd>{valueFormatters?.[key] ? valueFormatters[key](value) : formatValue(key, value)}</dd>
            {typeof meterValues?.[key] === "number" ? (
              <div
                className={styles.keyValueMeter}
                role="presentation"
                aria-hidden="true"
              >
                <span
                  className={styles.keyValueMeterFill}
                  style={{ width: `${Math.max(0, Math.min(100, meterValues[key]! >= 0 && meterValues[key]! <= 1 ? meterValues[key]! * 100 : meterValues[key]!))}%` }}
                />
              </div>
            ) : null}
            {descriptions?.[key] ? <p className={styles.keyValueDescription}>{descriptions[key]}</p> : null}
          </div>
        ))}
      </dl>
    </Surface>
  );
}

function FamilyOverviewShell({ overview }: { overview: FamilyOverviewPayload }) {
  const profileValues = {
    owner: findOverviewMetricValue(overview.overviewMetrics, "Primary owner"),
    status: findOverviewMetricValue(overview.overviewMetrics, "Status"),
    earliest_priority_date: findOverviewMetricValue(overview.overviewMetrics, "Earliest priority date"),
    quality_index_6: findOverviewMetricValue(overview.overviewMetrics, "Quality index 6"),
    generality_percentile: findOverviewMetricValue(overview.overviewMetrics, "Generality percentile"),
    originality_percentile: findOverviewMetricValue(overview.overviewMetrics, "Originality percentile"),
    radicalness_percentile: findOverviewMetricValue(overview.overviewMetrics, "Radicalness percentile"),
    science_grounding_percentile: findOverviewMetricValue(overview.overviewMetrics, "Science grounding percentile"),
  };
  const profileLabels = {
    earliest_priority_date: "Earliest priority date",
    quality_index_6: "Quality index 6 (OECD)",
    generality_percentile: "Generality",
    originality_percentile: "Originality",
    radicalness_percentile: "Radicalness",
    science_grounding_percentile: "Science grounding",
  };
  const profileDescriptions = {
    earliest_priority_date: "Earliest observed priority date across the family.",
    quality_index_6: "Composite OECD family-quality index on a 0-100 scale.",
    generality_percentile: "Peer rank within the same priority-year and field cohort for how broadly later citations spread across technology areas. Higher is stronger.",
    originality_percentile: "Peer rank within the same priority-year and field cohort for how diverse the cited prior-art base is. Higher is stronger.",
    radicalness_percentile: "Peer rank within the same priority-year and field cohort for how far the cited prior art departs from the family’s own field mix. Higher is stronger.",
    science_grounding_percentile: "Peer rank within the same priority-year and field cohort for science and NPL grounding. Higher is stronger.",
  };
  const profileMeterValues = {
    generality_percentile: typeof profileValues.generality_percentile === "number" ? profileValues.generality_percentile : null,
    originality_percentile: typeof profileValues.originality_percentile === "number" ? profileValues.originality_percentile : null,
    radicalness_percentile: typeof profileValues.radicalness_percentile === "number" ? profileValues.radicalness_percentile : null,
    science_grounding_percentile:
      typeof profileValues.science_grounding_percentile === "number" ? profileValues.science_grounding_percentile : null,
  };
  const profileValueFormatters = {
    quality_index_6: formatIndexOutOf100,
    generality_percentile: formatPeerRankOutOf100,
    originality_percentile: formatPeerRankOutOf100,
    radicalness_percentile: formatPeerRankOutOf100,
    science_grounding_percentile: formatPeerRankOutOf100,
  };
  return (
    <section className={styles.familyOverviewShell}>
      <div className={styles.familyOverviewStack}>
        <KeyValuePanel
          title={<PortfolioTooltipLabel label="Family profile" tooltip={workspaceTooltipCopy.familyView.familyProfile} />}
          icon={<Radar size={18} />}
          values={profileValues}
          labelOverrides={profileLabels}
          labelTooltips={profileDescriptions}
          descriptions={profileDescriptions}
          valueFormatters={profileValueFormatters}
          meterValues={profileMeterValues}
          panelClassName={styles.familyOverviewBanner}
          gridClassName={styles.familyOverviewBannerGridProfile}
        />
        <SummaryRail cards={overview.summaryCards} />
      </div>
    </section>
  );
}

function GenericTable({
  title,
  titleTooltip,
  rows,
  columns,
  emptyText,
  className,
  embedded = false,
}: {
  title: string;
  titleTooltip?: string;
  rows: Array<Record<string, unknown>>;
  columns: Array<{ key: string; label: ReactNode; render?: (row: Record<string, unknown>) => ReactNode }>;
  emptyText: string;
  className?: string;
  embedded?: boolean;
}) {
  const content = (
    <>
      {rows.length === 0 ? (
        <div className={clsx("family-empty-state", styles.stateText)}>{emptyText}</div>
      ) : (
        <div className={styles.tableWrap}>
          <table className={styles.table}>
            <thead>
              <tr>
                {columns.map((column) => (
                  <th key={column.key}>{column.label}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row, index) => (
                <tr key={`${title}-${index}`}>
                  {columns.map((column) => (
                    <td key={column.key}>
                      {column.render ? column.render(row) : formatValue(column.key, row[column.key])}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );

  if (embedded) {
    return content;
  }

  return (
    <Surface
      className={clsx(className, styles.tablePanel)}
      title={titleTooltip ? <PortfolioTooltipLabel label={title} tooltip={titleTooltip} /> : title}
      badge={<InfoPill tone="neutral">{rows.length} rows</InfoPill>}
    >
      {content}
    </Surface>
  );
}

function BranchStateMixPanel({ rows }: { rows: Array<Record<string, unknown>> }) {
  const chartRows = Object.entries(
    rows.reduce<Record<string, number>>((accumulator, row) => {
      const label = prettyLabel(String(row.branch_state_label ?? row.replay_branch_state ?? "Unknown"));
      accumulator[label] = (accumulator[label] ?? 0) + 1;
      return accumulator;
    }, {}),
  )
    .map(([label, count]) => ({ label, count }))
    .sort((left, right) => right.count - left.count);
  const totalJurisdictions = chartRows.reduce((sum, row) => sum + row.count, 0);
  const leadState = chartRows[0];

  return (
    <Surface
      className="portfolio-panel--coverage"
      title={<PortfolioTooltipLabel label="Branch-state mix" tooltip={workspaceTooltipCopy.familyView.branchStateMix} />}
      icon={<ShieldCheck size={18} />}
    >
      {chartRows.length === 0 ? (
        <div className={clsx("family-empty-state", styles.stateText)}>No jurisdiction state rows are available.</div>
      ) : (
        <>
          <div className={styles.trajectoryGrid}>
            <article className={styles.trajectoryCard}>
              <PortfolioTooltipLabel label="Tracked jurisdictions" tooltip={workspaceTooltipCopy.familyView.trackedJurisdictions} />
              <strong>{formatNumber(totalJurisdictions)}</strong>
              <small>current family legal footprint</small>
            </article>
            <article className={styles.trajectoryCard}>
              <PortfolioTooltipLabel label="Lead branch state" tooltip={workspaceTooltipCopy.familyView.leadBranchState} />
              <strong>{leadState?.label ?? "—"}</strong>
              <small>{formatNumber(leadState?.count ?? 0)} jurisdictions</small>
            </article>
            <article className={styles.trajectoryCard}>
              <PortfolioTooltipLabel label="State bands" tooltip={workspaceTooltipCopy.familyView.stateBands} />
              <strong>{formatNumber(chartRows.length)}</strong>
              <small>visible state groups</small>
            </article>
          </div>
          <div className={styles.trajectoryChart}>
            <ResponsiveContainer width="100%" height={Math.max(240, chartRows.length * 42)}>
              <BarChart data={chartRows} layout="vertical" margin={{ top: 6, right: 18, bottom: 6, left: 4 }}>
                <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                <XAxis type="number" allowDecimals={false} />
                <YAxis type="category" dataKey="label" width={110} tickLine={false} axisLine={false} />
                <Tooltip formatter={(value: number, name: string) => [formatNumber(value), name]} />
                <Bar dataKey="count" name="Jurisdictions" fill={chartTokens.series.success} radius={[0, 10, 10, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </>
      )}
    </Surface>
  );
}

function JurisdictionFootprintPanel({ rows }: { rows: Array<Record<string, unknown>> }) {
  const [viewMode, setViewMode] = useState<"chart" | "table">("chart");
  const topRows = [...rows]
    .sort(
      (left, right) =>
        Number(right.jurisdiction_enforceability_share_of_family ?? 0) -
        Number(left.jurisdiction_enforceability_share_of_family ?? 0),
    )
    .slice(0, 6)
    .map((row) => ({
      jurisdiction: String(row.jurisdiction_code ?? "—"),
      branchState: prettyLabel(String(row.branch_state_label ?? "unknown")),
      sharePct: Number(row.jurisdiction_enforceability_share_of_family ?? 0) * 100,
      contribution: Number(row.jurisdiction_enforceability_contribution_raw ?? 0),
    }));

  const leadJurisdiction = topRows[0];

  return (
    <Surface
      className="portfolio-panel--coverage"
      title={
        <PortfolioTooltipLabel
          label="Jurisdiction legal footprint"
          tooltip={workspaceTooltipCopy.familyView.jurisdictionLegalFootprint}
        />
      }
      icon={<Sparkles size={18} />}
      actions={
        <div className={styles.viewToggle} role="tablist" aria-label="Jurisdiction legal footprint view">
          <button
            type="button"
            role="tab"
            aria-selected={viewMode === "chart"}
            className={clsx(styles.viewToggleButton, viewMode === "chart" && styles.viewToggleButtonActive)}
            onClick={() => setViewMode("chart")}
          >
            Chart
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={viewMode === "table"}
            className={clsx(styles.viewToggleButton, viewMode === "table" && styles.viewToggleButtonActive)}
            onClick={() => setViewMode("table")}
          >
            Table
          </button>
        </div>
      }
    >
      {topRows.length === 0 ? (
        <div className={clsx("family-empty-state", styles.stateText)}>No jurisdiction legal rows are available.</div>
      ) : (
        <>
          <div className={styles.trajectoryGrid}>
            <article className={styles.trajectoryCard}>
              <PortfolioTooltipLabel label="Lead jurisdiction" tooltip={workspaceTooltipCopy.familyView.leadJurisdiction} />
              <strong>{leadJurisdiction?.jurisdiction ?? "—"}</strong>
              <small>{leadJurisdiction ? `${formatDecimal(leadJurisdiction.sharePct, 1)}% of family legal share` : "—"}</small>
            </article>
            <article className={styles.trajectoryCard}>
              <PortfolioTooltipLabel label="Lead branch state" tooltip={workspaceTooltipCopy.familyView.leadBranchState} />
              <strong>{leadJurisdiction?.branchState ?? "—"}</strong>
              <small>{leadJurisdiction ? formatDecimal(leadJurisdiction.contribution, 2) : "—"} contribution</small>
            </article>
            <article className={styles.trajectoryCard}>
              <PortfolioTooltipLabel label="Plotted jurisdictions" tooltip={workspaceTooltipCopy.familyView.jurisdictions} />
              <strong>{formatNumber(topRows.length)}</strong>
              <small>Top legal share rows</small>
            </article>
          </div>
          {viewMode === "chart" ? (
            <div className={styles.trajectoryChart}>
              <ResponsiveContainer width="100%" height={Math.max(250, topRows.length * 42)}>
                <BarChart data={topRows} layout="vertical" margin={{ top: 6, right: 16, bottom: 6, left: 4 }}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                  <XAxis type="number" domain={[0, 100]} tickFormatter={(value: number) => `${value}%`} />
                  <YAxis type="category" dataKey="jurisdiction" width={46} tickLine={false} axisLine={false} />
                  <Tooltip
                    formatter={(value: number, name: string, item) => {
                      const payload = item?.payload as { branchState?: string; contribution?: number } | undefined;
                      if (name === "Family legal share") {
                        return [`${formatDecimal(value, 1)}%`, `${name} · ${payload?.branchState ?? "unknown"}`];
                      }
                      return [formatDecimal(value, 2), name];
                    }}
                  />
                  <Bar dataKey="sharePct" name="Family legal share" fill={chartTokens.series.accent} radius={[0, 10, 10, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className={styles.tableWrap}>
              <table className={styles.table}>
                <thead>
                  <tr>
                    <th><PortfolioTooltipLabel label="Jurisdiction" tooltip={workspaceTooltipCopy.familyView.jurisdictions} /></th>
                    <th><PortfolioTooltipLabel label="Branch state" tooltip={workspaceTooltipCopy.familyView.branchState} /></th>
                    <th><PortfolioTooltipLabel label="Family legal share" tooltip={workspaceTooltipCopy.familyView.familyLegalShare} /></th>
                    <th><PortfolioTooltipLabel label="Legal contribution" tooltip={workspaceTooltipCopy.familyView.legalContribution} /></th>
                    <th><PortfolioTooltipLabel label="Strength band" tooltip={workspaceTooltipCopy.familyView.strengthBand} /></th>
                    <th><PortfolioTooltipLabel label="Last event" tooltip={workspaceTooltipCopy.familyView.lastEvent} /></th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((row, index) => (
                    <tr key={`jurisdiction-footprint-${index}`}>
                      <td>
                        <TagPill tone="neutral" monospace>
                          {String(row.jurisdiction_code ?? "—")}
                        </TagPill>
                      </td>
                      <td>
                        <StatusPill tone={branchStateTone(String(row.branch_state_label ?? "unknown"))}>
                          {prettyLabel(String(row.branch_state_label ?? "unknown"))}
                        </StatusPill>
                      </td>
                      <td>{formatValue("jurisdiction_enforceability_share_of_family", row.jurisdiction_enforceability_share_of_family)}</td>
                      <td>{formatValue("jurisdiction_enforceability_contribution_raw", row.jurisdiction_enforceability_contribution_raw)}</td>
                      <td>
                        <InfoPill tone="neutral">
                          {prettyLabel(String(row.jurisdiction_relative_enforceability_band ?? "unknown"))}
                        </InfoPill>
                      </td>
                      <td>{formatValue("last_event_date", row.last_event_date)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </Surface>
  );
}

function CitationOwnersPanel({ rows }: { rows: Array<Record<string, unknown>> }) {
  const [sortMode, setSortMode] = useState<"pressure" | "citations">("pressure");
  const chartRows = [...rows]
    .sort(
      (left, right) =>
        sortMode === "pressure"
          ? Number(right.citation_lethality_sum ?? 0) - Number(left.citation_lethality_sum ?? 0)
          : Number(right.citing_family_count ?? 0) - Number(left.citing_family_count ?? 0),
    )
    .slice(0, 6)
    .map((row) => ({
      owner: String(row.citing_owner_name ?? "Unknown"),
      pressure: Number(row.citation_lethality_sum ?? 0),
      citations: Number(row.citing_family_count ?? 0),
      citedMembers: Number(row.cited_member_count ?? 0),
    }));
  const chartMetricKey = sortMode === "pressure" ? "pressure" : "citations";
  const chartMetricLabel = sortMode === "pressure" ? "Pressure" : "Citations";
  const leadRow = chartRows[0];
  const ownerAxisWidth = Math.min(
    240,
    Math.max(
      132,
      ...chartRows.map((row) => row.owner.length * 7),
    ),
  );

  return (
    <Surface
      className="portfolio-panel--coverage"
      title={
        <span className={styles.inlineHeaderLabel}>
          <PortfolioTooltipLabel label="Top citing owners" tooltip={workspaceTooltipCopy.familyView.topCitingOwners} />
          <PortfolioMetricTooltip text={pressureTooltipText} />
        </span>
      }
      icon={<BookOpenText size={18} />}
      actions={
        <div className={styles.viewToggle} role="tablist" aria-label="Top citing owners sort">
          <button
            type="button"
            role="tab"
            aria-selected={sortMode === "pressure"}
            className={clsx(styles.viewToggleButton, sortMode === "pressure" && styles.viewToggleButtonActive)}
            onClick={() => setSortMode("pressure")}
          >
            Pressure
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={sortMode === "citations"}
            className={clsx(styles.viewToggleButton, sortMode === "citations" && styles.viewToggleButtonActive)}
            onClick={() => setSortMode("citations")}
          >
            Citations
          </button>
        </div>
      }
    >
      {chartRows.length === 0 ? (
        <div className={clsx("family-empty-state", styles.stateText)}>No ranked citing owners are available.</div>
      ) : (
        <>
          <div className={styles.trajectoryGrid}>
            <article className={styles.trajectoryCard}>
              <PortfolioTooltipLabel label="Lead owner" tooltip={workspaceTooltipCopy.familyView.topCitingOwners} />
              <strong>{leadRow?.owner ?? "—"}</strong>
              <small>
                {sortMode === "pressure"
                  ? `${formatDecimal(leadRow?.pressure ?? 0, 2)} pressure`
                  : `${formatNumber(leadRow?.citations ?? 0)} distinct forward citations`}
              </small>
            </article>
            <article className={styles.trajectoryCard}>
              <PortfolioTooltipLabel
                label={sortMode === "pressure" ? "Lead pressure" : "Lead citation breadth"}
                tooltip={sortMode === "pressure" ? workspaceTooltipCopy.familyView.pressure : workspaceTooltipCopy.familyView.distinctForwardCitationCount}
              />
              <strong>
                {sortMode === "pressure"
                  ? formatDecimal(leadRow?.pressure ?? 0, 2)
                  : formatNumber(leadRow?.citations ?? 0)}
              </strong>
              <small>
                {sortMode === "pressure"
                  ? `${formatNumber(leadRow?.citations ?? 0)} distinct forward citations from the top owner`
                  : `${formatDecimal(leadRow?.pressure ?? 0, 2)} pressure from the top owner`}
              </small>
            </article>
            <article className={styles.trajectoryCard}>
              <PortfolioTooltipLabel label="Cited family members" tooltip={workspaceTooltipCopy.familyView.citedFamilyMembers} />
              <strong>{formatNumber(leadRow?.citedMembers ?? 0)}</strong>
              <small>distinct family members touched by the lead owner</small>
            </article>
          </div>
          <div className={styles.trajectoryChart}>
            <ResponsiveContainer width="100%" height={Math.max(250, chartRows.length * 46)}>
              <BarChart data={chartRows} layout="vertical" margin={{ top: 6, right: 18, bottom: 6, left: 10 }}>
                <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                <XAxis type="number" allowDecimals />
                <YAxis
                  type="category"
                  dataKey="owner"
                  width={ownerAxisWidth}
                  tick={{ fontSize: 11 }}
                  tickLine={false}
                  axisLine={false}
                />
                <Tooltip
                  formatter={(value: number, name: string, item) => {
                    const payload = item?.payload as { citations?: number; citedMembers?: number; pressure?: number } | undefined;
                    return [
                      sortMode === "pressure" ? formatDecimal(value, 2) : formatNumber(value),
                      sortMode === "pressure"
                        ? `${name} · ${formatNumber(payload?.citations ?? 0)} distinct forward citations · ${formatNumber(payload?.citedMembers ?? 0)} cited family members`
                        : `${name} · ${formatDecimal(payload?.pressure ?? 0, 2)} pressure · ${formatNumber(payload?.citedMembers ?? 0)} cited family members`,
                    ];
                  }}
                />
                <Bar
                  dataKey={chartMetricKey}
                  name={chartMetricLabel}
                  fill={sortMode === "pressure" ? chartTokens.series.info : chartTokens.series.accent}
                  radius={[0, 10, 10, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </>
      )}
    </Surface>
  );
}

function PublicationStagePanel({ rows }: { rows: Array<Record<string, unknown>> }) {
  const chartRows = Object.values(
    rows.reduce<Record<string, { office: string; applicationCount: number; grantCount: number; total: number }>>(
      (accumulator, row) => {
        const office = String(row.publn_auth ?? "Unknown");
        const current = accumulator[office] ?? { office, applicationCount: 0, grantCount: 0, total: 0 };
        current.applicationCount += Boolean(row.is_application_stage) ? 1 : 0;
        current.grantCount += Boolean(row.is_grant_stage) ? 1 : 0;
        current.total += 1;
        accumulator[office] = current;
        return accumulator;
      },
      {},
    ),
  )
    .sort((left, right) => right.total - left.total)
    .slice(0, 6);

  const leadOffice = chartRows[0];
  const totalApplications = chartRows.reduce((sum, row) => sum + row.applicationCount, 0);
  const totalGrants = chartRows.reduce((sum, row) => sum + row.grantCount, 0);

  return (
    <Surface
      className="portfolio-panel--coverage"
      title={<PortfolioTooltipLabel label="Publication mix" tooltip={workspaceTooltipCopy.familyView.publicationMix} />}
      icon={<GitBranch size={18} />}
    >
      {chartRows.length === 0 ? (
        <div className={clsx("family-empty-state", styles.stateText)}>No member publications are available.</div>
      ) : (
        <>
          <div className={styles.trajectoryGrid}>
            <article className={styles.trajectoryCard}>
              <PortfolioTooltipLabel label="Lead office" tooltip={workspaceTooltipCopy.familyView.office} />
              <strong>{leadOffice?.office ?? "—"}</strong>
              <small>{formatNumber(leadOffice?.total ?? 0)} visible publications</small>
            </article>
            <article className={styles.trajectoryCard}>
              <PortfolioTooltipLabel label="Application rows" tooltip={workspaceTooltipCopy.familyView.application} />
              <strong>{formatNumber(totalApplications)}</strong>
              <small>visible page slice</small>
            </article>
            <article className={styles.trajectoryCard}>
              <PortfolioTooltipLabel label="Grant rows" tooltip={workspaceTooltipCopy.familyView.grant} />
              <strong>{formatNumber(totalGrants)}</strong>
              <small>visible page slice</small>
            </article>
          </div>
          <div className={styles.trajectoryChart}>
            <ResponsiveContainer width="100%" height={Math.max(250, chartRows.length * 44)}>
              <BarChart data={chartRows} layout="vertical" margin={{ top: 6, right: 18, bottom: 6, left: 4 }}>
                <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                <XAxis type="number" allowDecimals={false} />
                <YAxis type="category" dataKey="office" width={48} tickLine={false} axisLine={false} />
                <Tooltip formatter={(value: number, name: string) => [formatNumber(value), name]} />
                <Legend />
                <Bar dataKey="applicationCount" name="Application rows" stackId="pub-stage" fill={chartTokens.series.warning} radius={[0, 0, 0, 0]} />
                <Bar dataKey="grantCount" name="Grant rows" stackId="pub-stage" fill={chartTokens.series.success} radius={[0, 10, 10, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </>
      )}
    </Surface>
  );
}

function TopCitedMembersPanel({ rows }: { rows: Array<Record<string, unknown>> }) {
  const chartRows = [...rows]
    .sort(
      (left, right) =>
        Number(right.citing_family_count ?? 0) - Number(left.citing_family_count ?? 0),
    )
    .slice(0, 6)
    .map((row) => ({
      publication: String(row.publication_number_full ?? "—"),
      forwardCitationCount: Number(row.citing_family_count ?? 0),
      forwardOwnerCount: Number(row.citing_owner_count ?? 0),
    }));

  return (
    <Surface
      className="portfolio-panel--coverage"
      title={<PortfolioTooltipLabel label="Top cited publications" tooltip={workspaceTooltipCopy.familyView.topCitedPublications} />}
      icon={<BookOpenText size={18} />}
    >
      {chartRows.length === 0 ? (
        <div className={clsx("family-empty-state", styles.stateText)}>No cited family-member ranking is available.</div>
      ) : (
        <>
          <div className={styles.trajectoryGrid}>
            <article className={styles.trajectoryCard}>
              <PortfolioTooltipLabel label="Lead publication" tooltip={workspaceTooltipCopy.familyView.publication} />
              <strong>{chartRows[0]?.publication ?? "—"}</strong>
              <small>{formatNumber(chartRows[0]?.forwardCitationCount ?? 0)} distinct forward citations</small>
            </article>
            <article className={styles.trajectoryCard}>
              <PortfolioTooltipLabel
                label="Lead owner breadth"
                tooltip={workspaceTooltipCopy.familyView.distinctForwardOwnerCount}
              />
              <strong>{formatNumber(chartRows[0]?.forwardOwnerCount ?? 0)}</strong>
              <small>distinct forward owners for top publication</small>
            </article>
            <article className={styles.trajectoryCard}>
              <PortfolioTooltipLabel label="Publications plotted" tooltip={workspaceTooltipCopy.familyView.topCitedPublications} />
              <strong>{formatNumber(chartRows.length)}</strong>
              <small>top ranked members</small>
            </article>
          </div>
          <div className={styles.trajectoryChart}>
            <ResponsiveContainer width="100%" height={Math.max(250, chartRows.length * 44)}>
              <BarChart data={chartRows} layout="vertical" margin={{ top: 6, right: 18, bottom: 6, left: 4 }}>
                <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                <XAxis type="number" allowDecimals={false} />
                <YAxis type="category" dataKey="publication" width={118} tickLine={false} axisLine={false} />
                <Tooltip
                  formatter={(value: number, name: string, item) => {
                    const payload = item?.payload as { forwardOwnerCount?: number } | undefined;
                    return [formatNumber(value), `${name} · ${formatNumber(payload?.forwardOwnerCount ?? 0)} distinct forward owners`];
                  }}
                />
                <Bar
                  dataKey="forwardCitationCount"
                  name="Distinct forward citation count"
                  fill={chartTokens.series.accent}
                  radius={[0, 10, 10, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </>
      )}
    </Surface>
  );
}

function LegalHistorySparkline({
  rows,
  latestEventDate,
  latestEventType,
}: {
  rows: Array<Record<string, unknown>>;
  latestEventDate?: unknown;
  latestEventType?: unknown;
}) {
  const [viewMode, setViewMode] = useState<"chart" | "table">("chart");
  const chartRows = rows.map((row) => ({
    year: Number(row.snapshot_year ?? 0),
    activeJurisdictions: Number(row.active_jurisdiction_count ?? 0),
    activeGrantBranches: Number(row.active_grant_branch_count ?? 0),
    lapsedJurisdictions: Number(row.lapsed_jurisdiction_count ?? 0),
    opposedBranches: Number(row.opposed_branch_count ?? 0),
    status: String(row.family_composite_status ?? "unknown"),
  }));
  const latestRow = chartRows[chartRows.length - 1];
  const firstRow = chartRows[0];

  return (
    <Surface
      className="portfolio-panel--timeline"
      title={<PortfolioTooltipLabel label="Legal history" tooltip={workspaceTooltipCopy.familyView.legalHistory} />}
      icon={<GitBranch size={18} />}
      actions={
        <div className={styles.viewToggle} role="tablist" aria-label="Legal history view">
          <button
            type="button"
            role="tab"
            aria-selected={viewMode === "chart"}
            className={clsx(styles.viewToggleButton, viewMode === "chart" && styles.viewToggleButtonActive)}
            onClick={() => setViewMode("chart")}
          >
            Chart
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={viewMode === "table"}
            className={clsx(styles.viewToggleButton, viewMode === "table" && styles.viewToggleButtonActive)}
            onClick={() => setViewMode("table")}
          >
            Table
          </button>
        </div>
      }
    >
      {chartRows.length === 0 ? (
        <div className={clsx("family-empty-state", styles.stateText)}>No historical legal status rows are available.</div>
      ) : (
        <>
          <div className="portfolio-section-summary">
            <article className="portfolio-section-summary__card">
              <PortfolioTooltipLabel
                label="Observed span"
                tooltip={workspaceTooltipCopy.familyView.observedSpan}
                textClassName="portfolio-section-summary__label"
              />
              <strong>
                {firstRow?.year ?? "—"} to {latestRow?.year ?? "—"}
              </strong>
              <span>{chartRows.length} historical points</span>
            </article>
            <article className="portfolio-section-summary__card">
              <PortfolioTooltipLabel
                label="Latest status"
                tooltip={workspaceTooltipCopy.familyView.latestStatus}
                textClassName="portfolio-section-summary__label"
              />
              <strong>{prettyLabel(latestRow?.status ?? "unknown")}</strong>
              <span>{latestRow ? `${formatNumber(latestRow.activeJurisdictions)} active jurisdictions` : "No latest row"}</span>
            </article>
            <article className="portfolio-section-summary__card">
              <PortfolioTooltipLabel
                label="Last dated event"
                tooltip={workspaceTooltipCopy.familyView.lastDatedEvent}
                textClassName="portfolio-section-summary__label"
              />
              <strong>{formatValue("last_event_date", latestEventDate)}</strong>
              <span>{formatValue("last_event_type", latestEventType)}</span>
            </article>
          </div>
          {viewMode === "chart" ? (
            <div className="portfolio-spark">
              <ResponsiveContainer width="100%" height={220}>
                <ComposedChart data={chartRows}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="year" />
                  <YAxis allowDecimals={false} />
                  <Tooltip
                    formatter={(value: number, name: string) => [formatNumber(value), name]}
                    labelFormatter={(label) => `Year: ${label}`}
                  />
                  <Legend />
                  <Area
                    type="monotone"
                    dataKey="activeJurisdictions"
                    name="Active jurisdictions"
                    fill="rgba(142, 27, 27, 0.12)"
                    stroke="var(--accent)"
                    strokeWidth={2.2}
                    dot={false}
                    isAnimationActive={false}
                  />
                  <Line
                    type="monotone"
                    dataKey="activeGrantBranches"
                    name="Active grant branches"
                    stroke={chartTokens.series.success}
                    strokeWidth={2}
                    dot={false}
                    isAnimationActive={false}
                  />
                  <Line
                    type="monotone"
                    dataKey="lapsedJurisdictions"
                    name="Lapsed jurisdictions"
                    stroke={chartTokens.series.warning}
                    strokeWidth={2}
                    dot={false}
                    isAnimationActive={false}
                  />
                  <Line
                    type="monotone"
                    dataKey="opposedBranches"
                    name="Opposed branches"
                    stroke={chartTokens.series.critical}
                    strokeWidth={2}
                    dot={false}
                    isAnimationActive={false}
                  />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <DataTableShell
              columns={[
                {
                  accessorKey: "year",
                  header: () => <PortfolioTooltipLabel label="Year" tooltip={workspaceTooltipCopy.familyView.year} />,
                },
                {
                  accessorKey: "status",
                  header: () => <PortfolioTooltipLabel label="Status" tooltip={workspaceTooltipCopy.familyView.status} />,
                  cell: ({ row }) => (
                    <StatusPill tone={branchStateTone(String(row.original.status ?? "unknown"))}>
                      {prettyLabel(String(row.original.status ?? "unknown"))}
                    </StatusPill>
                  ),
                },
                {
                  accessorKey: "activeJurisdictions",
                  header: () => <PortfolioTooltipLabel label="Active jurisdictions" tooltip={workspaceTooltipCopy.familyView.activeJurisdictions} />,
                },
                {
                  accessorKey: "activeGrantBranches",
                  header: () => <PortfolioTooltipLabel label="Active grant branches" tooltip={workspaceTooltipCopy.familyView.activeGrantBranches} />,
                },
                {
                  accessorKey: "lapsedJurisdictions",
                  header: () => <PortfolioTooltipLabel label="Lapsed jurisdictions" tooltip={workspaceTooltipCopy.familyView.lapsedJurisdictions} />,
                },
                {
                  accessorKey: "opposedBranches",
                  header: () => <PortfolioTooltipLabel label="Opposed branches" tooltip={workspaceTooltipCopy.familyView.opposedBranches} />,
                },
              ]}
              data={chartRows}
              emptyMessage="No historical legal status rows are available."
              getRowKey={(row) => `legal-history-${row.year}`}
            />
          )}
          <p className="portfolio-small-note">
            This sparkline summarizes family legal status history from yearly status snapshots, not document-by-document event chronology.
          </p>
        </>
      )}
    </Surface>
  );
}

function BlockingTrajectoryPanel({
  rows,
}: {
  rows: Array<Record<string, unknown>>;
}) {
  const chartRows = [...rows]
    .map((row) => ({
      year: Number(row.snapshot_year ?? 0),
      snapshotDate: String(row.snapshot_date ?? "").trim(),
      blockingScore: Number(row.ui_blocking_power_score ?? 0),
      legalScore: Number(row.overall_legal_enforceability_score ?? 0),
    }))
    .filter((row) => row.year > 0)
    .sort((left, right) => left.year - right.year);

  const firstRow = chartRows[0];
  const latestRow = chartRows[chartRows.length - 1];
  const observedSpan =
    firstRow && latestRow ? `${formatNumber(firstRow.year)} to ${formatNumber(latestRow.year)}` : "—";
  const latestSnapshotLabel = latestRow?.snapshotDate || (latestRow ? String(latestRow.year) : "—");

  return (
    <Surface
      className="portfolio-panel--timeline"
      title={<PortfolioTooltipLabel label="Blocking trajectory" tooltip={workspaceTooltipCopy.familyView.blockingTrajectory} />}
      icon={<ShieldCheck size={18} />}
    >
      {chartRows.length === 0 ? (
        <div className={clsx("family-empty-state", styles.stateText)}>No blocking-history rows are available for this family.</div>
      ) : (
        <>
          <div className={styles.trajectoryGrid}>
            <article className={styles.trajectoryCard}>
              <PortfolioTooltipLabel label="Observed span" tooltip={workspaceTooltipCopy.familyView.observedSpan} />
              <strong>{observedSpan}</strong>
              <small>{formatNumber(chartRows.length)} blocking-history points</small>
            </article>
            <article className={styles.trajectoryCard}>
              <PortfolioTooltipLabel label="Latest blocking" tooltip={workspaceTooltipCopy.familyView.latestBlocking} />
              <strong>{formatDecimal(latestRow?.blockingScore ?? 0, 1)}</strong>
              <small>snapshot {latestSnapshotLabel}</small>
            </article>
            <article className={styles.trajectoryCard}>
              <PortfolioTooltipLabel label="Latest legal" tooltip={workspaceTooltipCopy.familyView.latestLegal} />
              <strong>{formatDecimal(latestRow?.legalScore ?? 0, 2)}</strong>
              <small>model score at {latestSnapshotLabel}</small>
            </article>
          </div>
          <div className={styles.trajectoryChart}>
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={chartRows}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="year" />
                <YAxis yAxisId="blocking" domain={[0, 100]} />
                <YAxis yAxisId="legal" orientation="right" />
                <Tooltip
                  formatter={(value: number, name: string) => [
                    name === "Blocking score" ? formatDecimal(value, 1) : formatDecimal(value, 2),
                    name,
                  ]}
                  labelFormatter={(label) => `Year: ${label}`}
                />
                <Legend />
                <Line
                  yAxisId="blocking"
                  type="monotone"
                  dataKey="blockingScore"
                  name="Blocking score"
                  stroke={chartTokens.series.accent}
                  strokeWidth={2.5}
                  dot={false}
                  isAnimationActive={false}
                />
                <Line
                  yAxisId="legal"
                  type="monotone"
                  dataKey="legalScore"
                  name="Legal enforceability"
                  stroke={chartTokens.series.info}
                  strokeWidth={2}
                  dot={false}
                  isAnimationActive={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <p className={clsx("portfolio-small-note", styles.trajectoryNote)}>
            Blocking trajectory comes from the dedicated family blocking-history mart. The latest observed snapshot in this series is {latestSnapshotLabel}.
          </p>
        </>
      )}
    </Surface>
  );
}

function FieldFootprintPanel({
  summary,
  rows,
}: {
  summary?: Record<string, unknown> | null;
  rows: Array<Record<string, unknown>>;
}) {
  const normalizeCodeList = (value: unknown, limit = 8) =>
    Array.isArray(value) ? value.map((item) => String(item).trim()).filter(Boolean).slice(0, limit) : [];
  const primaryField =
    String(summary?.primary_wipo_field_asof ?? summary?.primary_wipo_field ?? "Unknown").trim() || "Unknown";
  const breadthBand = prettyLabel(String(summary?.classification_breadth_band_asof ?? "unknown"));
  const topCpcMainGroup = String(summary?.top_cpc_main_group_asof ?? "—").trim() || "—";
  const topCpcShare = Number(summary?.top_cpc_main_group_share_asof ?? 0);
  const fieldCount = Number(summary?.wipo_field_count_asof ?? summary?.tech_breadth_wipo_count ?? 0);
  const coveredFieldsRaw = summary?.covered_wipo_fields_asof ?? summary?.covered_wipo_fields;
  const coveredFields = normalizeCodeList(coveredFieldsRaw, 6);
  const leadContribution = [...rows]
    .sort(
      (left, right) =>
        Number(right.field_share_asof ?? right.base_fraction ?? 0) - Number(left.field_share_asof ?? left.base_fraction ?? 0),
    )[0];

  return (
    <Surface
      className="portfolio-panel--field"
      title={<PortfolioTooltipLabel label="Field footprint" tooltip={workspaceTooltipCopy.familyView.fieldFootprint} />}
      icon={<Sparkles size={18} />}
    >
      <div className={styles.trajectoryGrid}>
        <article className={styles.trajectoryCard}>
          <PortfolioTooltipLabel label="Primary field" tooltip={workspaceTooltipCopy.familyView.primaryField} />
          <strong>{primaryField}</strong>
          <small>{formatNumber(fieldCount)} WIPO field{fieldCount === 1 ? "" : "s"} visible</small>
        </article>
        <article className={styles.trajectoryCard}>
          <PortfolioTooltipLabel label="Breadth band" tooltip={workspaceTooltipCopy.familyView.breadthBand} />
          <strong>{breadthBand}</strong>
          <small>Current classification spread</small>
        </article>
        <article className={styles.trajectoryCard}>
          <PortfolioTooltipLabel label="Top CPC main group" tooltip={workspaceTooltipCopy.familyView.topCpcMainGroup} />
          <strong>{topCpcMainGroup}</strong>
          <small>{formatPercent(topCpcShare)} of current footprint</small>
        </article>
        <article className={styles.trajectoryCard}>
          <PortfolioTooltipLabel label="Lead field share" tooltip={workspaceTooltipCopy.familyView.leadFieldShare} />
          <strong>{formatPercent(Number(leadContribution?.field_share_asof ?? leadContribution?.base_fraction ?? 0))}</strong>
          <small>{String(leadContribution?.wipo_industry_code ?? primaryField)}</small>
        </article>
      </div>
      {coveredFields.length > 0 ? (
        <div className={styles.fieldChipRow}>
          {coveredFields.map((field) => (
            <FieldPill key={field}>{field}</FieldPill>
          ))}
        </div>
      ) : null}
    </Surface>
  );
}

function ClassificationMapPanel({ summary }: { summary?: Record<string, unknown> | null }) {
  const normalizeCodeList = (value: unknown, limit = 18) =>
    Array.isArray(value) ? value.map((item) => String(item).trim()).filter(Boolean).slice(0, limit) : [];
  const cpcSubclassForCode = (code: string) => code.match(/^[A-Z]\d{2}[A-Z]/)?.[0] ?? code.slice(0, 4);
  const sectionLabel = (section: string) => `Section ${section}`;

  const ipcSubclasses = normalizeCodeList(summary?.ipc_subclasses_asof, 8);
  const cpcSections = normalizeCodeList(summary?.cpc_sections_asof, 10);
  const cpcSubclasses = normalizeCodeList(summary?.cpc_subclasses_asof, 14);
  const cpcMainGroups = normalizeCodeList(summary?.cpc_main_groups_asof, 24);
  const topCpcMainGroup = String(summary?.top_cpc_main_group_asof ?? cpcMainGroups[0] ?? "—").trim() || "—";
  const topCpcShare = Number(summary?.top_cpc_main_group_share_asof ?? 0);
  const primaryField = String(summary?.primary_wipo_field_asof ?? summary?.primary_wipo_field ?? "Unknown").trim() || "Unknown";

  const derivedSubclasses = Array.from(new Set([...cpcSubclasses, ...cpcMainGroups.map(cpcSubclassForCode)])).filter(Boolean);
  const subclassCards = derivedSubclasses.map((subclass) => {
    const section = cpcSections.find((code) => subclass.startsWith(code)) ?? (subclass.slice(0, 1) || "—");
    const mainGroups = cpcMainGroups.filter((code) => cpcSubclassForCode(code) === subclass || code.startsWith(subclass));
    return { subclass, section, mainGroups };
  });
  const sectionCards = Array.from(new Set([...cpcSections, ...subclassCards.map((card) => card.section)])).map((section) => ({
    section,
    subclasses: subclassCards.filter((card) => card.section === section),
  }));
  const maxMainGroups = Math.max(1, ...subclassCards.map((card) => card.mainGroups.length));
  const leadSubclass = subclassCards.find((card) => card.mainGroups.includes(topCpcMainGroup)) ?? subclassCards[0];
  const visibleMainGroups = cpcMainGroups.slice(0, 18);

  if (ipcSubclasses.length === 0 && cpcSubclasses.length === 0 && cpcMainGroups.length === 0) {
    return null;
  }

  return (
    <Surface
      className="portfolio-panel--field"
      title={<PortfolioTooltipLabel label="Classification footprint" tooltip={workspaceTooltipCopy.familyView.ipcCpcMap} />}
      icon={<Sparkles size={18} />}
    >
      <div className={styles.classificationVisualShell}>
        <div className={styles.classificationVisualIntro}>
          <div>
            <span>Technology map</span>
            <p>CPC sections flow into subclasses, then into observed main-group anchors. The dominant main group is highlighted.</p>
          </div>
          <div className={styles.classificationVisualStats}>
            <article>
              <strong>{formatNumber(Number(summary?.cpc_section_count_asof ?? cpcSections.length))}</strong>
              <span>sections</span>
            </article>
            <article>
              <strong>{formatNumber(Number(summary?.cpc_subclass_count_asof ?? cpcSubclasses.length))}</strong>
              <span>subclasses</span>
            </article>
            <article>
              <strong>{formatNumber(Number(summary?.cpc_main_group_count_asof ?? cpcMainGroups.length))}</strong>
              <span>main groups</span>
            </article>
          </div>
        </div>
        <div className={styles.classificationVisualBody}>
          <article className={styles.classificationOrbitCard}>
            <span className={styles.classificationOrbitLabel}>Dominant anchor</span>
            <div className={styles.classificationOrbit} aria-hidden="true">
              <span className={styles.classificationOrbitRingOuter} />
              <span className={styles.classificationOrbitRingInner} />
              <strong>{topCpcMainGroup}</strong>
            </div>
            <div className={styles.classificationOrbitMeta}>
              <strong>{leadSubclass?.subclass ?? "—"}</strong>
              <span>{leadSubclass ? sectionLabel(leadSubclass.section) : "No CPC section"}</span>
              <small>{topCpcShare > 0 ? `${formatPercent(topCpcShare)} of current footprint` : "top observed main group"}</small>
            </div>
          </article>
          <div className={styles.classificationFlowMap}>
            <div className={styles.classificationFlowColumn}>
              <span className={styles.classificationFlowColumnLabel}>1. Sections</span>
              <div className={styles.classificationOrbStack}>
                {sectionCards.length > 0 ? (
                  sectionCards.map((sectionCard, index) => (
                    <div key={sectionCard.section} className={clsx(styles.classificationSectionOrb, index === 0 && styles.classificationSectionOrbLead)}>
                      <strong>{sectionCard.section}</strong>
                      <span>{formatNumber(sectionCard.subclasses.length)}</span>
                    </div>
                  ))
                ) : (
                  <span className={styles.classificationMapEmpty}>No sections</span>
                )}
              </div>
            </div>
            <div className={styles.classificationFlowColumn}>
              <span className={styles.classificationFlowColumnLabel}>2. Subclasses</span>
              <div className={styles.classificationNodeStack}>
                {subclassCards.length > 0 ? (
                  subclassCards.map((card) => (
                    <div key={card.subclass} className={clsx(styles.classificationSubclassNode, card.subclass === leadSubclass?.subclass && styles.classificationSubclassNodeLead)}>
                      <span className={styles.classificationNodeConnector} aria-hidden="true" />
                      <strong>{card.subclass}</strong>
                      <small>{sectionLabel(card.section)}</small>
                    </div>
                  ))
                ) : (
                  <span className={styles.classificationMapEmpty}>No subclasses</span>
                )}
              </div>
            </div>
            <div className={styles.classificationFlowColumnWide}>
              <span className={styles.classificationFlowColumnLabel}>3. Main groups</span>
              <div className={styles.classificationLeafCloud}>
                {visibleMainGroups.length > 0 ? (
                  visibleMainGroups.map((code) => (
                    <span
                      key={code}
                      className={clsx(styles.classificationLeaf, code === topCpcMainGroup && styles.classificationLeafLead)}
                    >
                      {code}
                    </span>
                  ))
                ) : (
                  <span className={styles.classificationMapEmpty}>No main groups</span>
                )}
                {cpcMainGroups.length > visibleMainGroups.length ? (
                  <span className={styles.classificationLeafMore}>+{formatNumber(cpcMainGroups.length - visibleMainGroups.length)}</span>
                ) : null}
              </div>
            </div>
          </div>
        </div>
      </div>
    </Surface>
  );
}

function FieldTrajectoryPanel({
  rows,
  classificationRows,
}: {
  rows: Array<Record<string, unknown>>;
  classificationRows: Array<Record<string, unknown>>;
}) {
  const [viewMode, setViewMode] = useState<"chart" | "table">("chart");
  const normalizedRows = rows
    .map((row) => ({
      year: Number(row.snapshot_year ?? 0),
      field: String(row.wipo_industry_code ?? "").trim(),
      share: Number(row.field_share_asof ?? row.base_fraction ?? 0),
    }))
    .filter((row) => row.year > 0 && row.field);

  const fieldStrength = normalizedRows.reduce<Record<string, number>>((accumulator, row) => {
    accumulator[row.field] = Math.max(accumulator[row.field] ?? 0, row.share);
    return accumulator;
  }, {});

  const topFields = Object.entries(fieldStrength)
    .sort((left, right) => right[1] - left[1])
    .slice(0, 4)
    .map(([field]) => field);

  const years = [...new Set(normalizedRows.map((row) => row.year))].sort((left, right) => left - right);
  const chartRows = years.map((year) => {
    const row: Record<string, number> & { year: number } = { year };
    for (const field of topFields) {
      const match = normalizedRows.find((candidate) => candidate.year === year && candidate.field === field);
      row[field] = (match?.share ?? 0) * 100;
    }
    return row;
  });

  const latestYear = years[years.length - 1];
  const latestLeadField = normalizedRows
    .filter((row) => row.year === latestYear)
    .sort((left, right) => right.share - left.share)[0];
  const hasChartData = chartRows.length > 0;
  const hasTableData = classificationRows.length > 0;

  const palette = [
    chartTokens.series.accent,
    chartTokens.series.info,
    chartTokens.series.success,
    chartTokens.series.warning,
  ];

  return (
    <Surface
      className="portfolio-panel--field"
      title={<PortfolioTooltipLabel label="Field trajectory" tooltip={workspaceTooltipCopy.familyView.fieldTrajectory} />}
      icon={<Sparkles size={18} />}
      actions={
        <div className={styles.viewToggle} role="tablist" aria-label="Field trajectory view">
          <button
            type="button"
            role="tab"
            aria-selected={viewMode === "chart"}
            className={clsx(styles.viewToggleButton, viewMode === "chart" && styles.viewToggleButtonActive)}
            onClick={() => setViewMode("chart")}
          >
            Chart
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={viewMode === "table"}
            className={clsx(styles.viewToggleButton, viewMode === "table" && styles.viewToggleButtonActive)}
            onClick={() => setViewMode("table")}
          >
            Table
          </button>
        </div>
      }
    >
      {!hasChartData && !hasTableData ? (
        <div className={clsx("family-empty-state", styles.stateText)}>No field-history rows are available for this family.</div>
      ) : (
        <>
          <div className={styles.trajectoryGrid}>
            <article className={styles.trajectoryCard}>
              <PortfolioTooltipLabel label="Tracked years" tooltip={workspaceTooltipCopy.familyView.trackedYears} />
              <strong>{formatNumber(Math.max(years.length, classificationRows.length))}</strong>
              <small>
                {hasChartData ? `${years[0]} to ${years[years.length - 1]}` : "classification history"}
              </small>
            </article>
            <article className={styles.trajectoryCard}>
              <PortfolioTooltipLabel label="Tracked fields" tooltip={workspaceTooltipCopy.familyView.trackedFields} />
              <strong>{formatNumber(Object.keys(fieldStrength).length || Number(classificationRows[0]?.wipo_field_count_asof ?? 0))}</strong>
              <small>{hasChartData ? `Top ${formatNumber(topFields.length)} plotted` : "historical classification footprint"}</small>
            </article>
            <article className={styles.trajectoryCard}>
              <PortfolioTooltipLabel label="Latest lead field" tooltip={workspaceTooltipCopy.familyView.latestLeadField} />
              <strong>{latestLeadField?.field ?? String(classificationRows[classificationRows.length - 1]?.primary_wipo_field_asof ?? "—")}</strong>
              <small>{hasChartData ? `${formatPercent(latestLeadField?.share ?? 0)} latest field share` : "latest primary field"}</small>
            </article>
          </div>
          {viewMode === "chart" ? (
            hasChartData ? (
            <div className={styles.trajectoryChart}>
              <ResponsiveContainer width="100%" height={260}>
                <LineChart data={chartRows}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="year" />
                  <YAxis domain={[0, 100]} tickFormatter={(value: number) => `${value}%`} />
                  <Tooltip
                    formatter={(value: number, name: string) => [formatPercent(value / 100), name]}
                    labelFormatter={(label) => `Year: ${label}`}
                  />
                  <Legend />
                  {topFields.map((field, index) => (
                    <Line
                      key={field}
                      type="monotone"
                      dataKey={field}
                      name={field}
                      stroke={palette[index] ?? chartTokens.series.neutral}
                      strokeWidth={2.5}
                      dot={false}
                      activeDot={{ r: 4 }}
                      isAnimationActive={false}
                    />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            </div>
            ) : (
              <div className={clsx("family-empty-state", styles.stateText)}>No field-share trajectory rows are available for chart view.</div>
            )
          ) : (
            <GenericTable
              embedded
              title="Classification chronology"
              titleTooltip={workspaceTooltipCopy.familyView.classificationChronology}
              rows={classificationRows}
              columns={[
                { key: "as_of_year", label: <PortfolioTooltipLabel label="Year" tooltip={workspaceTooltipCopy.familyView.year} /> },
                {
                  key: "primary_wipo_field_asof",
                  label: <PortfolioTooltipLabel label="Primary field" tooltip={workspaceTooltipCopy.familyView.primaryField} />,
                },
                {
                  key: "classification_breadth_band_asof",
                  label: <PortfolioTooltipLabel label="Breadth band" tooltip={workspaceTooltipCopy.familyView.breadthBand} />,
                },
                {
                  key: "top_cpc_main_group_asof",
                  label: <PortfolioTooltipLabel label="Top CPC main group" tooltip={workspaceTooltipCopy.familyView.topCpcMainGroup} />,
                },
                {
                  key: "top_cpc_main_group_share_asof",
                  label: <PortfolioTooltipLabel label="Top CPC share" tooltip={workspaceTooltipCopy.familyView.topCpcShare} />,
                },
              ]}
              emptyText="No classification timeline rows are available."
            />
          )}
          <p className={clsx("portfolio-small-note", styles.trajectoryNote)}>
            {viewMode === "chart"
              ? "Field trajectory uses the family field-contribution timeseries mart and plots application-weighted field share over time when available, with legacy base fractions only as fallback."
              : "Table view shows the historical classification snapshot by year for the same family footprint."}
          </p>
        </>
      )}
    </Surface>
  );
}

function CurrentFieldContributionPanel({ rows }: { rows: Array<Record<string, unknown>> }) {
  const palette = [
    chartTokens.series.accent,
    chartTokens.series.info,
    chartTokens.series.success,
    chartTokens.series.warning,
    chartTokens.series.neutral,
  ];

  const normalizeContributionRows = (key: "enforceability_contribution_score" | "heritage_contribution_score") => {
    const prepared = rows
      .map((row) => ({
        field: String(row.wipo_industry_code ?? "Unknown").trim() || "Unknown",
        rawValue: Math.max(0, Number(row[key] ?? 0)),
      }))
      .filter((row) => row.rawValue > 0)
      .sort((left, right) => right.rawValue - left.rawValue);

    if (prepared.length === 0) {
      return { total: 0, rows: [] as Array<{ field: string; rawValue: number; sharePct: number }> };
    }

    const topRows = prepared.slice(0, 5);
    const otherValue = prepared.slice(5).reduce((sum, row) => sum + row.rawValue, 0);
    const collapsed = otherValue > 0 ? [...topRows, { field: "Other", rawValue: otherValue }] : topRows;
    const total = collapsed.reduce((sum, row) => sum + row.rawValue, 0);

    return {
      total,
      rows: collapsed.map((row) => ({
        ...row,
        sharePct: total > 0 ? (row.rawValue / total) * 100 : 0,
      })),
    };
  };

  const legal = normalizeContributionRows("enforceability_contribution_score");
  const heritage = normalizeContributionRows("heritage_contribution_score");

  const renderPie = (
    title: string,
    rowsForMetric: Array<{ field: string; rawValue: number; sharePct: number }>,
    rawLabel: string,
  ) => (
    <article className={styles.contributionMetricCard}>
      <div className={styles.contributionMetricHeader}>
        <PortfolioTooltipLabel
          label={title}
          tooltip={
            title === "Legal contribution share"
              ? workspaceTooltipCopy.familyView.legalContributionShare
              : workspaceTooltipCopy.familyView.heritageContributionShare
          }
        />
      </div>
      {rowsForMetric.length > 0 ? (
        <div className={styles.contributionMetricBody}>
          <div className={styles.contributionPieChart}>
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie
                  data={rowsForMetric}
                  dataKey="sharePct"
                  nameKey="field"
                  innerRadius={52}
                  outerRadius={82}
                  stroke="rgba(255,255,255,0.92)"
                  strokeWidth={2}
                  paddingAngle={rowsForMetric.length > 1 ? 2 : 0}
                >
                  {rowsForMetric.map((row, index) => (
                    <Cell key={`${title}-${row.field}`} fill={palette[index % palette.length]} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(value: number, _name: string, item) => {
                    const payload = item?.payload as { rawValue?: number } | undefined;
                    return [`${formatDecimal(value, 1)}%`, `${rawLabel} · ${formatDecimal(payload?.rawValue ?? 0, 2)}`];
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className={styles.contributionLegendCompact}>
            {rowsForMetric.map((row, index) => (
              <span key={`${title}-${row.field}-legend`} className={styles.contributionLegendChip}>
                <span
                  className={styles.contributionLegendSwatch}
                  style={{ backgroundColor: palette[index % palette.length] }}
                />
                {row.field}
              </span>
            ))}
          </div>
        </div>
      ) : (
        <div className={clsx("family-empty-state", styles.stateText)}>No positive contribution rows are available for this metric.</div>
      )}
    </article>
  );

  return (
    <Surface
      className="portfolio-panel--field"
      title={
        <PortfolioTooltipLabel
          label="Current field contributions"
          tooltip={workspaceTooltipCopy.familyView.currentFieldContributions}
        />
      }
      icon={<Sparkles size={18} />}
    >
      <div className={styles.contributionGrid}>
        {renderPie("Legal contribution share", legal.rows, "Raw legal contribution")}
        {renderPie("Heritage contribution share", heritage.rows, "Raw heritage contribution")}
      </div>
    </Surface>
  );
}

function CitationChronologyPanel({
  rows,
  summary,
  forecastRows = [],
}: {
  rows: Array<Record<string, unknown>>;
  summary?: Record<string, unknown> | null;
  forecastRows?: Array<Record<string, unknown>>;
}) {
  const [viewMode, setViewMode] = useState<"chart" | "table">("chart");
  const chartRows = [...rows]
    .map((row) => ({
      year: Number(row.as_of_year ?? 0),
      asOfDate: String(row.as_of_date ?? ""),
      forwardCitationCount: Number(row.pre_asof_unique_citing_family_count ?? 0),
      forwardCitationCount7y: Number(row.pre_asof_forward_clean_7y ?? 0),
      forwardOwnerCount: Number(row.pre_asof_unique_citing_owner_count ?? 0),
      backwardCitationCount: Number(row.pre_asof_distinct_cited_family_count ?? 0),
      firstForwardCitationDate: String(row.first_forward_citation_date_asof ?? ""),
      latestForwardCitationDate: String(row.latest_forward_citation_date_asof ?? ""),
      window7yClosed: Boolean(row.window_7y_closed),
      historicalCitationSafe: Boolean(row.historical_citation_safe),
      chronologySupportLevel: String(row.chronology_support_level ?? "limited"),
    }))
    .filter((row) => row.year > 0)
    .sort((left, right) => left.year - right.year);

  const firstRow = chartRows[0];
  const latestRow = chartRows[chartRows.length - 1];
  const observedSpan =
    firstRow && latestRow
      ? `${firstRow.asOfDate || String(firstRow.year)} to ${latestRow.asOfDate || String(latestRow.year)}`
      : "—";
  const latestSupportLevel = latestRow?.chronologySupportLevel ?? "limited";
  const latestForwardDate = latestRow?.latestForwardCitationDate || "—";
  const firstForwardDate = latestRow?.firstForwardCitationDate || "—";
  const latestSummaryForwardCitationCount7y =
    summary?.forward_citations_7y == null ? null : Number(summary.forward_citations_7y);
  const latestForwardCitationCount7yDisplay =
    latestSummaryForwardCitationCount7y != null && Number.isFinite(latestSummaryForwardCitationCount7y)
      ? latestSummaryForwardCitationCount7y
      : (latestRow?.forwardCitationCount7y ?? 0);
  const forecastProjectionRows = latestRow
    ? [...forecastRows]
        .reduce<Array<{ horizon: string; year: number; midpoint: number; lower: number; upper: number }>>((acc, row) => {
          const horizon = String(row.horizon ?? "").trim().toLowerCase();
          const horizonMonths = horizonSortValue(horizon);
          if (!Number.isFinite(horizonMonths) || horizonMonths <= 0 || horizonMonths % 12 !== 0) {
            return acc;
          }
          const pointForecast = Number(row.point_forecast ?? Number.NaN);
          const intervalLower = Number(row.interval_lower ?? Number.NaN);
          const intervalUpper = Number(row.interval_upper ?? Number.NaN);
          if (!Number.isFinite(pointForecast) || !Number.isFinite(intervalLower) || !Number.isFinite(intervalUpper)) {
            return acc;
          }
          const horizonYears = horizonMonths / 12;
          acc.push({
            horizon,
            year: latestRow.year + horizonYears,
            midpoint: latestRow.forwardCitationCount + pointForecast,
            lower: latestRow.forwardCitationCount + intervalLower,
            upper: latestRow.forwardCitationCount + intervalUpper,
          });
          return acc;
        }, [])
        .sort((left, right) => left.year - right.year)
    : [];
  const chartData: Array<{
    year: number;
    asOfDate: string;
    forwardCitationCount: number | null;
    forwardCitationCount7y: number | null;
    forwardOwnerCount: number | null;
    backwardCitationCount: number | null;
    firstForwardCitationDate: string;
    latestForwardCitationDate: string;
    window7yClosed: boolean;
    historicalCitationSafe: boolean;
    chronologySupportLevel: string;
    forecastMidpoint: number | null;
    forecastLower: number | null;
    forecastRange: number | null;
  }> = [...chartRows].map((row) => ({
    ...row,
    forecastMidpoint: null,
    forecastLower: null,
    forecastRange: null,
  }));
  if (latestRow && forecastProjectionRows.length > 0) {
    const latestIndex = chartData.findIndex((row) => row.year === latestRow.year);
    if (latestIndex >= 0) {
      chartData[latestIndex] = {
        ...chartData[latestIndex],
        forecastMidpoint: latestRow.forwardCitationCount,
        forecastLower: latestRow.forwardCitationCount,
        forecastRange: 0,
      };
    }
    forecastProjectionRows.forEach((projection) => {
      chartData.push({
        year: projection.year,
        asOfDate: "",
        forwardCitationCount: null,
        forwardCitationCount7y: null,
        forwardOwnerCount: null,
        backwardCitationCount: null,
        firstForwardCitationDate: "",
        latestForwardCitationDate: "",
        window7yClosed: false,
        historicalCitationSafe: false,
        chronologySupportLevel: latestSupportLevel,
        forecastMidpoint: projection.midpoint,
        forecastLower: projection.lower,
        forecastRange: Math.max(projection.upper - projection.lower, 0),
      });
    });
  }
  chartData.sort((left, right) => left.year - right.year);
  const tableRows = chartRows.map((row, index) => ({
    ...row,
    forwardCitationCount7yDisplay:
      index === chartRows.length - 1 &&
      latestSummaryForwardCitationCount7y != null &&
      Number.isFinite(latestSummaryForwardCitationCount7y)
        ? latestSummaryForwardCitationCount7y
        : row.forwardCitationCount7y,
  }));
  const sevenYearWindowLabel = latestRow
    ? latestRow.window7yClosed
      ? `${formatNumber(latestForwardCitationCount7yDisplay)} closed-window citations`
      : `${formatNumber(latestForwardCitationCount7yDisplay)} so far · window open`
    : "—";
  return (
    <Surface
      className="portfolio-panel--timeline"
      title={<PortfolioTooltipLabel label="Citation chronology" tooltip={workspaceTooltipCopy.familyView.citationChronology} />}
      icon={<BookOpenText size={18} />}
      badge={<InfoPill tone={supportTone(latestSupportLevel)}>{supportLabel(latestSupportLevel)}</InfoPill>}
      actions={
        <div className={styles.viewToggle} role="tablist" aria-label="Citation chronology view">
          <button
            type="button"
            role="tab"
            aria-selected={viewMode === "chart"}
            className={clsx(styles.viewToggleButton, viewMode === "chart" && styles.viewToggleButtonActive)}
            onClick={() => setViewMode("chart")}
          >
            Chart
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={viewMode === "table"}
            className={clsx(styles.viewToggleButton, viewMode === "table" && styles.viewToggleButtonActive)}
            onClick={() => setViewMode("table")}
          >
            Table
          </button>
        </div>
      }
    >
      {chartRows.length === 0 ? (
        <div className={clsx("family-empty-state", styles.stateText)}>No citation chronology rows are available for this family.</div>
      ) : (
        <>
          <div className={styles.trajectoryGrid}>
            <article className={styles.trajectoryCard}>
              <PortfolioTooltipLabel label="Observed span" tooltip={workspaceTooltipCopy.familyView.observedSpan} />
              <strong>{observedSpan}</strong>
              <small>{formatNumber(chartRows.length)} yearly chronology rows</small>
            </article>
            <article className={styles.trajectoryCard}>
              <PortfolioTooltipLabel
                label="Latest distinct forward citation count"
                tooltip={workspaceTooltipCopy.familyView.latestDistinctForwardCitationCount}
              />
              <strong>{formatNumber(latestRow?.forwardCitationCount ?? 0)}</strong>
              <small>{sevenYearWindowLabel}</small>
            </article>
            <article className={styles.trajectoryCard}>
              <PortfolioTooltipLabel
                label="Latest distinct backward citation count"
                tooltip={workspaceTooltipCopy.familyView.latestDistinctBackwardCitationCount}
              />
              <strong>{formatNumber(latestRow?.backwardCitationCount ?? 0)}</strong>
              <small>{formatNumber(latestRow?.forwardOwnerCount ?? 0)} distinct forward owners</small>
            </article>
          </div>
          {viewMode === "chart" ? (
            <div className={styles.trajectoryChart}>
              <ResponsiveContainer width="100%" height={280}>
                <ComposedChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="year" />
                  <YAxis allowDecimals={false} />
                  <Tooltip
                    formatter={(value: number, name: string) => [formatNumber(value), name]}
                    labelFormatter={(label) => `Year: ${label}`}
                  />
                  <Legend />
                  <Area
                    type="monotone"
                    dataKey="forecastLower"
                    stackId="forecastBand"
                    stroke="none"
                    fill="transparent"
                    isAnimationActive={false}
                    legendType="none"
                  />
                  <Area
                    type="monotone"
                    dataKey="forecastRange"
                    name="Future citation outlook interval"
                    stackId="forecastBand"
                    stroke="none"
                    fill={chartTokens.series.success}
                    fillOpacity={0.12}
                    isAnimationActive={false}
                    legendType="none"
                  />
                  <Line
                    type="monotone"
                    dataKey="forwardCitationCount"
                    name="Distinct forward citation count"
                    stroke={chartTokens.series.accent}
                    strokeWidth={2.5}
                    dot={false}
                    isAnimationActive={false}
                  />
                  <Line
                    type="monotone"
                    dataKey="forecastMidpoint"
                    name="Future citation outlook"
                    stroke={chartTokens.series.success}
                    strokeWidth={2.3}
                    strokeDasharray="6 4"
                    dot={false}
                    isAnimationActive={false}
                  />
                  <Line
                    type="monotone"
                    dataKey="forwardOwnerCount"
                    name="Distinct forward owner count"
                    stroke={chartTokens.series.info}
                    strokeWidth={2.2}
                    dot={false}
                    isAnimationActive={false}
                  />
                  <Line
                    type="monotone"
                    dataKey="backwardCitationCount"
                    name="Distinct backward citation count"
                    stroke={chartTokens.series.neutral}
                    strokeWidth={1.9}
                    dot={false}
                    isAnimationActive={false}
                  />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className={styles.tableWrap}>
              <table className={styles.table}>
                <thead>
                  <tr>
                    <th><PortfolioTooltipLabel label="Year" tooltip={workspaceTooltipCopy.familyView.year} /></th>
                    <th><PortfolioTooltipLabel label="Support" tooltip={workspaceTooltipCopy.familyView.status} /></th>
                    <th>
                      <PortfolioTooltipLabel
                        label="Distinct forward citation count"
                        tooltip={workspaceTooltipCopy.familyView.distinctForwardCitationCount}
                      />
                    </th>
                    <th>
                      <PortfolioTooltipLabel
                        label="Distinct forward citation count (7y)"
                        tooltip={workspaceTooltipCopy.familyView.distinctForwardCitationCount7y}
                      />
                    </th>
                    <th>
                      <PortfolioTooltipLabel
                        label="Distinct forward owner count"
                        tooltip={workspaceTooltipCopy.familyView.distinctForwardOwnerCount}
                      />
                    </th>
                    <th>
                      <PortfolioTooltipLabel
                        label="Distinct backward citation count"
                        tooltip={workspaceTooltipCopy.familyView.distinctBackwardCitationCount}
                      />
                    </th>
                    <th>
                      <PortfolioTooltipLabel
                        label="Latest forward citation date"
                        tooltip={workspaceTooltipCopy.familyView.latestForwardCitationDate}
                      />
                    </th>
                    <th><PortfolioTooltipLabel label="7y window" tooltip={workspaceTooltipCopy.familyView.sevenYearWindow} /></th>
                    <th>
                      <PortfolioTooltipLabel
                        label="Historical safety"
                        tooltip={workspaceTooltipCopy.familyView.historicalSafety}
                      />
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {tableRows.map((row, index) => (
                    <tr key={`citation-chronology-${index}`}>
                      <td>{formatNumber(row.year)}</td>
                      <td>
                        <StatusPill tone={supportTone(row.chronologySupportLevel)}>
                          {supportLabel(row.chronologySupportLevel)}
                        </StatusPill>
                      </td>
                      <td>{formatNumber(row.forwardCitationCount)}</td>
                      <td>{formatNumber(row.forwardCitationCount7yDisplay)}</td>
                      <td>{formatNumber(row.forwardOwnerCount)}</td>
                      <td>{formatNumber(row.backwardCitationCount)}</td>
                      <td>{row.latestForwardCitationDate || "—"}</td>
                      <td>
                        <StatusPill tone={row.window7yClosed ? "positive" : "warning"}>
                          {row.window7yClosed ? formatNumber(row.forwardCitationCount7yDisplay) : `${formatNumber(row.forwardCitationCount7yDisplay)} so far`}
                        </StatusPill>
                      </td>
                      <td>
                        <StatusPill tone={row.historicalCitationSafe ? "positive" : "warning"}>
                          {row.historicalCitationSafe ? "Safe" : "Caveat"}
                        </StatusPill>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          <p className={clsx("portfolio-small-note", styles.trajectoryNote)}>
            Family-collapsed citation timeline. First forward citation seen {firstForwardDate}; latest forward citation seen {latestForwardDate}; 7-year forward citation count {sevenYearWindowLabel}.
            {forecastProjectionRows.length > 0 ? " Forecast overlay adds the current family outlook from the latest forecast artifact." : ""}
          </p>
        </>
      )}
    </Surface>
  );
}

export function FamilyWorkspace({ familyId }: FamilyWorkspaceProps) {
  const [activeTab, setActiveTab] = useState<FamilyWorkspaceTab>("publications");
  const [memberOffset, setMemberOffset] = useState(0);
  const [citationOffset, setCitationOffset] = useState(0);
  const [citationOwnerFilter, setCitationOwnerFilter] = useState("");
  const [overview, setOverview] = useState<FamilyOverviewPayload | null>(null);
  const [legal, setLegal] = useState<FamilySectionPayload | null>(null);
  const [fields, setFields] = useState<FamilySectionPayload | null>(null);
  const [timeseries, setTimeseries] = useState<FamilySectionPayload | null>(null);
  const [members, setMembers] = useState<FamilySectionPayload | null>(null);
  const [citations, setCitations] = useState<FamilySectionPayload | null>(null);
  const [classification, setClassification] = useState<FamilySectionPayload | null>(null);
  const [forecast, setForecast] = useState<FamilySectionPayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [memberLoading, setMemberLoading] = useState(true);
  const [citationLoading, setCitationLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    setMemberOffset(0);
    setCitationOffset(0);
    setCitationOwnerFilter("");
    setOverview(null);
    setLegal(null);
    setFields(null);
    setTimeseries(null);
    setMembers(null);
    setCitations(null);
    setClassification(null);
    setForecast(null);

    async function loadSection(
      section: string,
      setter: (payload: FamilySectionPayload) => void,
      failureMessage: string,
    ) {
      try {
        const payload = await fetchFamilySection(familyId, section);
        if (!cancelled) {
          setter(payload);
        }
      } catch (requestError) {
        if (!cancelled) {
          setter(emptyFamilySectionPayload(familyId));
          setError((current) =>
            current ?? (requestError instanceof Error ? requestError.message : failureMessage),
          );
        }
      }
    }

    async function loadWorkspace() {
      try {
        const payload = await fetchFamilyOverview(familyId);
        if (!cancelled) {
          setOverview(payload);
        }
      } catch (requestError) {
        if (!cancelled) {
          setError(requestError instanceof Error ? requestError.message : "Could not load family workspace.");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void loadSection("legal", setLegal, "Could not load family legal section.");
    void loadSection("fields", setFields, "Could not load family fields section.");
    void loadSection("timeseries", setTimeseries, "Could not load family timeseries section.");
    void loadSection("classification", setClassification, "Could not load family classification section.");
    void loadSection("forecasts", setForecast, "Could not load family forecast section.");

    void loadWorkspace();

    return () => {
      cancelled = true;
    };
  }, [familyId]);

  useEffect(() => {
    let cancelled = false;
    setMemberLoading(true);

    async function loadMembers() {
      try {
        const payload = await fetchFamilySection(familyId, "members", { limit: 10, offset: memberOffset });
        if (!cancelled) {
          setMembers(payload);
        }
      } catch (requestError) {
        if (!cancelled) {
          setError(requestError instanceof Error ? requestError.message : "Could not load family members.");
        }
      } finally {
        if (!cancelled) {
          setMemberLoading(false);
        }
      }
    }

    void loadMembers();

    return () => {
      cancelled = true;
    };
  }, [familyId, memberOffset]);

  useEffect(() => {
    setCitationOffset(0);
  }, [citationOwnerFilter]);

  useEffect(() => {
    let cancelled = false;
    setCitationLoading(true);

    async function loadCitations() {
      try {
        const payload = await fetchFamilySection(familyId, "citations", {
          limit: 1000,
          offset: 0,
        });
        if (!cancelled) {
          setCitations(payload);
        }
      } catch (requestError) {
        if (!cancelled) {
          setError(requestError instanceof Error ? requestError.message : "Could not load family citations.");
        }
      } finally {
        if (!cancelled) {
          setCitationLoading(false);
        }
      }
    }

    void loadCitations();

    return () => {
      cancelled = true;
    };
  }, [familyId]);

  const representativeTitle = overview
    ? findOverviewMetricValue(overview.overviewMetrics, "Representative publication title")
    : undefined;
  const legalStatusHistory = (legal?.series ?? []).filter((row) => row.series_kind === "status_history");
  const citingFamilyRows = (citations?.series ?? []).filter((row) => row.series_kind === "citing_family");
  const topCitedMemberRows = (citations?.series ?? []).filter((row) => row.series_kind === "top_cited_member");
  const topCitingOwnerRows = (citations?.series ?? []).filter((row) => row.series_kind === "top_citing_owner");
  const blockingHistoryRows = (timeseries?.series ?? []).filter((row) => row.series_kind === "blocking_history");
  const fieldHistoryRows = (timeseries?.series ?? []).filter((row) => row.series_kind === "field_history");
  const citingOwnerOptions = useMemo(
    () =>
      [...new Set(topCitingOwnerRows.map((row) => String(row.citing_owner_name ?? "").trim()).filter(Boolean))].sort((left, right) =>
        left.localeCompare(right),
      ),
    [topCitingOwnerRows],
  );
  const filteredCitingFamilyRows = useMemo(
    () =>
      citationOwnerFilter
        ? citingFamilyRows.filter((row) => String(row.citing_assignee_name ?? "").trim() === citationOwnerFilter)
        : citingFamilyRows,
    [citationOwnerFilter, citingFamilyRows],
  );
  const paginatedCitingFamilyRows = useMemo(
    () => filteredCitingFamilyRows.slice(citationOffset, citationOffset + 10),
    [citationOffset, filteredCitingFamilyRows],
  );
  const citingFamiliesPagination = useMemo(
    () => ({
      limit: 10,
      offset: citationOffset,
      returnedCount: paginatedCitingFamilyRows.length,
      totalCount: filteredCitingFamilyRows.length,
    }),
    [citationOffset, filteredCitingFamilyRows.length, paginatedCitingFamilyRows.length],
  );
  const activeTabDefinition = tabs.find((tab) => tab.id === activeTab) ?? tabs[0];
  const activeTabLoading =
    !loading &&
    ((activeTab === "publications" && members == null) ||
      (activeTab === "legal" && (legal == null || timeseries == null)) ||
      (activeTab === "fields" && (fields == null || classification == null)) ||
      (activeTab === "evidence" && (citations == null || forecast == null)));

  const workspaceContextOverride = overview
    ? {
        title: `Family ${String(overview.identity.id || familyId)}`,
        description:
          typeof representativeTitle === "string" && representativeTitle.trim().length > 0 ? representativeTitle : undefined,
      }
    : null;

  useWorkspaceContextOverride(workspaceContextOverride);

  const activeCaveats = useMemo(() => {
    const base = overview?.meta.caveats ?? [];
    if (activeTab === "publications") {
      return [...base, ...(members?.meta.caveats ?? [])];
    }
    if (activeTab === "legal") {
      return [...base, ...(legal?.meta.caveats ?? []), ...(timeseries?.meta.caveats ?? [])];
    }
    if (activeTab === "fields") {
      return [...base, ...(fields?.meta.caveats ?? []), ...(classification?.meta.caveats ?? [])];
    }
    if (activeTab === "evidence") {
      return [
        ...base,
        ...(members?.meta.caveats ?? []),
        ...(citations?.meta.caveats ?? []),
        ...(forecast?.meta.caveats ?? []),
      ];
    }
    return base;
	  }, [activeTab, citations?.meta.caveats, classification?.meta.caveats, fields?.meta.caveats, forecast?.meta.caveats, legal?.meta.caveats, members?.meta.caveats, overview?.meta.caveats, timeseries?.meta.caveats]);

  const memberPublicationColumns: DataTableColumn<Record<string, unknown>>[] = [
    {
      accessorKey: "publication_number_full",
      header: () => <PortfolioTooltipLabel label="Publication" tooltip={workspaceTooltipCopy.familyView.publication} />,
      cell: ({ row }) => {
          const publicationId = String(row.original.publication_number_full ?? "").trim();
          if (!publicationId) {
            return "—";
          }
          return (
            <Link href={`/publication/${publicationId}`} className={styles.publicationLink}>
              {publicationId}
            </Link>
          );
        },
    },
    { accessorKey: "publn_auth", header: () => <PortfolioTooltipLabel label="Office" tooltip={workspaceTooltipCopy.familyView.office} /> },
    { accessorKey: "publn_kind", header: () => <PortfolioTooltipLabel label="Kind" tooltip={workspaceTooltipCopy.familyView.kind} /> },
    {
      accessorKey: "publn_date",
      header: () => <PortfolioTooltipLabel label="Publication date" tooltip={workspaceTooltipCopy.familyView.publicationDate} />,
      cell: ({ row }) => formatValue("publn_date", row.original.publn_date),
    },
    {
      accessorKey: "is_application_stage",
      header: () => <PortfolioTooltipLabel label="Application" tooltip={workspaceTooltipCopy.familyView.application} />,
      cell: ({ row }) => <InfoPill tone={Boolean(row.original.is_application_stage) ? "info" : "neutral"}>{Boolean(row.original.is_application_stage) ? "Yes" : "No"}</InfoPill>,
    },
    {
      accessorKey: "is_grant_stage",
      header: () => <PortfolioTooltipLabel label="Grant" tooltip={workspaceTooltipCopy.familyView.grant} />,
      cell: ({ row }) => <InfoPill tone={Boolean(row.original.is_grant_stage) ? "positive" : "neutral"}>{Boolean(row.original.is_grant_stage) ? "Yes" : "No"}</InfoPill>,
    },
  ];

		  return (
    <main className="portfolio-shell family-workspace">
	        {!loading && overview ? <FamilyOverviewShell overview={overview} /> : null}

	      <WorkspaceTabs items={tabs} activeTab={activeTab} onTabChange={setActiveTab} ariaLabel="Family workspace sections" />

	      {loading ? <section className={clsx("panel-shell family-empty-state", styles.statePanel)}>Loading family workspace…</section> : null}
      {error ? (
        <Surface className={clsx("family-panel--caveat", styles.statePanel)} title="Workspace warning" icon={<AlertTriangle size={18} />}>
          <p className={clsx("family-empty-state", styles.stateText)}>{error}</p>
        </Surface>
      ) : null}

      {!loading && activeTabLoading ? (
        <section className={clsx("panel-shell family-empty-state", styles.statePanel)}>
          Loading {activeTabDefinition.loadingLabel} data…
        </section>
      ) : null}

      {!loading && !activeTabLoading && activeTab === "publications" ? (
        <div className={styles.tabStack}>
          <PublicationStagePanel rows={members?.rows ?? []} />
          <Surface
            className={styles.detailPanel}
            title={<PortfolioTooltipLabel label="Member publications" tooltip={workspaceTooltipCopy.familyView.memberPublications} />}
            description="Current family publication set and publication drill-through."
            icon={<TableProperties size={18} />}
            actions={<InfoPill tone="neutral">{formatNumber(members?.rows.length ?? 0)} rows</InfoPill>}
          >
            <DataTableShell
              columns={memberPublicationColumns}
              data={members?.rows ?? []}
              emptyMessage={memberLoading ? "Loading member publications…" : "No member publications are available."}
              getRowKey={(row, index) => `${String(row.publication_number_full ?? "publication")}-${index}`}
            />
            <PortfolioPaginationControls pagination={members?.meta.pagination ?? undefined} onPageChange={setMemberOffset} />
          </Surface>
        </div>
      ) : null}

	      {!loading && !activeTabLoading && activeTab === "legal" && legal ? (
	        <div className={styles.tabStack}>
            <div className={styles.legalOverviewRow}>
              <BranchStateMixPanel rows={legal.rows} />
              <JurisdictionFootprintPanel rows={legal.rows} />
            </div>
            <LegalHistorySparkline
              rows={legalStatusHistory}
              latestEventDate={legal.summary?.last_event_date}
              latestEventType={legal.summary?.last_event_type}
            />
            <BlockingTrajectoryPanel rows={blockingHistoryRows} />
	        </div>
	      ) : null}

	      {!loading && !activeTabLoading && activeTab === "fields" && fields ? (
	        <div className={styles.tabStack}>
            <FieldFootprintPanel summary={fields.summary ?? null} rows={fields.rows} />
            <ClassificationMapPanel summary={fields.summary ?? null} />
            <FieldTrajectoryPanel rows={fieldHistoryRows} classificationRows={classification?.rows ?? []} />
            <CurrentFieldContributionPanel rows={fields.rows} />
	          <div className={styles.tabDetailStack}>
          </div>
        </div>
	      ) : null}

      {!loading && !activeTabLoading && activeTab === "evidence" ? (
        <div className={styles.tabStack}>
          <div className={styles.tabMain}>
            <KeyValuePanel
              title={<PortfolioTooltipLabel label="Citation summary" tooltip={workspaceTooltipCopy.familyView.citationSummary} />}
              icon={<BookOpenText size={18} />}
              values={citations?.summary ?? {}}
              labelTooltips={familyCitationSummaryTooltips}
            />
            <CitationChronologyPanel
              rows={citations?.rows ?? []}
              summary={citations?.summary ?? null}
              forecastRows={forecast?.rows ?? []}
            />
            <CitationOwnersPanel rows={topCitingOwnerRows} />
          </div>
	          <div className={styles.tabDetailStack}>
            <Surface
              className={styles.detailPanel}
              title={<PortfolioTooltipLabel label="Citation leaderboards" tooltip={workspaceTooltipCopy.familyView.citationLeaderboards} />}
              description="Top cited publications for the current family."
              badge={<InfoPill tone="neutral">{formatNumber(topCitedMemberRows.length)} rows</InfoPill>}
            >
              <div className={styles.disclosureGrid}>
                <TopCitedMembersPanel rows={topCitedMemberRows} />
                <GenericTable
                  embedded
                  title="Top cited family members"
                  rows={topCitedMemberRows}
                  columns={[
                    {
                      key: "publication_number_full",
                      label: <PortfolioTooltipLabel label="Publication" tooltip={workspaceTooltipCopy.familyView.publication} />,
                      render: (row) => {
                        const publicationId = String(row.publication_number_full ?? "").trim();
                        if (!publicationId) {
                          return "—";
                        }
                        return (
                          <Link href={`/publication/${publicationId}`} className={styles.publicationLink}>
                            {publicationId}
                          </Link>
                        );
                      },
                    },
                    { key: "focal_publication_office", label: <PortfolioTooltipLabel label="Office" tooltip={workspaceTooltipCopy.familyView.office} /> },
                    { key: "focal_publication_kind", label: <PortfolioTooltipLabel label="Kind" tooltip={workspaceTooltipCopy.familyView.kind} /> },
                    {
                      key: "citing_family_count",
                      label: <PortfolioTooltipLabel label="Distinct forward citation count" tooltip={workspaceTooltipCopy.familyView.distinctForwardCitationCount} />,
                    },
                    {
                      key: "citing_owner_count",
                      label: <PortfolioTooltipLabel label="Distinct forward owner count" tooltip={workspaceTooltipCopy.familyView.distinctForwardOwnerCount} />,
                    },
                    { key: "latest_citation_date", label: <PortfolioTooltipLabel label="Latest seen" tooltip={workspaceTooltipCopy.familyView.latestSeen} /> },
                  ]}
                  emptyText={citationLoading ? "Loading cited family members…" : "No cited family-member ranking is available."}
                />
              </div>
            </Surface>
            <Surface
              className={styles.detailPanel}
              title={<PortfolioTooltipLabel label="Citing families" tooltip={workspaceTooltipCopy.familyView.citingFamilies} />}
              description="Clean external families citing this family, with owner reference and distinct breadth across cited family members."
              badge={<InfoPill tone="neutral">{formatNumber(filteredCitingFamilyRows.length)} matches</InfoPill>}
            >
              <div className={styles.filterToolbar}>
                <label className={styles.filterField}>
                  <PortfolioTooltipLabel
                    label="Owner filter"
                    tooltip={workspaceTooltipCopy.familyView.ownerFilter}
                    textClassName={styles.filterLabel}
                  />
                  <select
                    value={citationOwnerFilter}
                    onChange={(event) => setCitationOwnerFilter(event.target.value)}
                    aria-label="Filter citing families by owner"
                    className={styles.filterSelect}
                  >
                    <option value="">All owners</option>
                    {citingOwnerOptions.map((owner) => (
                      <option key={owner} value={owner}>
                        {owner}
                      </option>
                    ))}
                  </select>
                </label>
              </div>
              <GenericTable
                embedded
                title="Citing families"
                rows={paginatedCitingFamilyRows}
                columns={[
                  {
                    key: "citing_docdb_family_id",
                    label: <PortfolioTooltipLabel label="Citing family" tooltip={workspaceTooltipCopy.familyView.citingFamily} />,
                    render: (row) => {
                      const citingFamilyId = String(row.citing_docdb_family_id ?? "").trim();
                      if (!citingFamilyId) {
                        return "—";
                      }
                      return <Link href={`/family/${citingFamilyId}`}>{citingFamilyId}</Link>;
                    },
                  },
                  { key: "citing_assignee_name", label: <PortfolioTooltipLabel label="Citing owner" tooltip={workspaceTooltipCopy.familyView.citingOwner} /> },
                  {
                    key: "distinct_cited_member_count",
                    label: <PortfolioTooltipLabel label="Distinct cited family member count" tooltip={workspaceTooltipCopy.familyView.distinctCitedFamilyMemberCount} />,
                  },
                  {
                    key: "distinct_citing_publication_count",
                    label: <PortfolioTooltipLabel label="Distinct citing publication count" tooltip={workspaceTooltipCopy.familyView.distinctCitingPublicationCount} />,
                  },
                  { key: "first_citation_date", label: <PortfolioTooltipLabel label="First seen" tooltip={workspaceTooltipCopy.familyView.firstSeen} /> },
                  { key: "latest_citation_date", label: <PortfolioTooltipLabel label="Latest seen" tooltip={workspaceTooltipCopy.familyView.latestSeen} /> },
                ]}
                emptyText={
                  citationLoading
                    ? "Loading citing families…"
                    : citationOwnerFilter
                      ? "No citing families match this owner filter."
                      : "No citing-family list is available."
                }
              />
              <PortfolioPaginationControls pagination={citingFamiliesPagination} onPageChange={setCitationOffset} />
            </Surface>
          </div>
        </div>
      ) : null}

      {!loading && !activeTabLoading && activeTab !== "publications" ? <CaveatPanel caveats={activeCaveats} /> : null}
    </main>
  );
}
