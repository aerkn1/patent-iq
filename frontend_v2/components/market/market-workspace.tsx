"use client";

import clsx from "clsx";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useState, type ReactNode } from "react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { DataTableShell, type DataTableColumn } from "@/components/data-table/data-table-shell";
import { formatDecimal, formatNumber, formatPercent } from "@/components/portfolio/portfolio-format";
import { PortfolioTooltipLabel } from "@/components/portfolio/portfolio-tooltip-label";
import { InfoPill, StatusPill } from "@/components/ui/data-pill";
import { DeferredClientComponent } from "@/components/ui/deferred-client-component";
import { Surface } from "@/components/ui/surface";
import {
  workspaceTooltipCopy,
} from "@/lib/content/workspace-tooltips";
import {
  fetchMarketCpcTrends,
  fetchMarketLeadingJurisdictions,
  fetchMarketOverviewHistory,
  fetchMarketSegmentApplicationsGrants,
  fetchMarketSegmentCpcCitingOwners,
  fetchMarketSegmentCpcJurisdictions,
  fetchMarketSegmentCpcOwners,
  fetchMarketSegmentGrantMix,
  fetchMarketWorkspace,
} from "@/lib/api/market-v2";
import { chartTokens, getDirectionColor } from "@/lib/design/chart-tokens";
import type {
  MarketApplicationGrantRow,
  MarketCpcCitingOwnerRow,
  MarketCpcJurisdictionRow,
  MarketCpcOwnerRow,
  MarketCpcTrendRow,
  MarketGrantMixRow,
  MarketLeadingJurisdictionRow,
  MarketOverviewHistoryRow,
  MarketSectionResponse,
  MarketSelectedSegment,
  MarketSparklinePoint,
  MarketWorkspaceResponse,
} from "@/lib/types/market-v2";

import styles from "./market-workspace.module.css";

type MarketWorkspaceTab = "competition" | "jurisdictions" | "technology";
type MarketWorkspaceSection = "overview" | "analysis";
type MarketChronologyView = "mix" | "counts";
type LeadingJurisdictionView = "table" | "pie";
type ApplicationsGrantView = "chart" | "table";
type MarketSectionDescriptor = Pick<
  MarketSectionResponse<unknown>,
  "metric_basis" | "scope_basis" | "sum_safe" | "overlap_policy"
>;

const loadMarketCompetitionSection = () =>
  import("./market-analysis-competition").then((module) => module.MarketAnalysisCompetitionSection);
const loadMarketJurisdictionsSection = () =>
  import("./market-analysis-jurisdictions").then((module) => module.MarketAnalysisJurisdictionsSection);
const loadMarketTechnologySection = () =>
  import("./market-analysis-technology").then((module) => module.MarketAnalysisTechnologySection);

function toneForState(value: string): "positive" | "critical" | "neutral" {
  const normalized = value.toLowerCase();
  if (normalized.includes("heat") || normalized.includes("rise") || normalized.includes("gain")) {
    return "positive";
  }
  if (normalized.includes("cool") || normalized.includes("loss")) {
    return "critical";
  }
  return "neutral";
}

function toneForLifecycle(value: string): "positive" | "critical" | "neutral" | "warning" {
  const normalized = value.toLowerCase();
  if (normalized.includes("active")) {
    return "positive";
  }
  if (normalized.includes("lapsed")) {
    return "warning";
  }
  if (normalized.includes("dead")) {
    return "critical";
  }
  return "neutral";
}

function toneForCrowding(value: string): "positive" | "critical" | "neutral" | "warning" {
  const normalized = value.toLowerCase();
  if (normalized.includes("open")) {
    return "positive";
  }
  if (normalized.includes("crowded")) {
    return "critical";
  }
  if (normalized.includes("concentrated")) {
    return "warning";
  }
  return "neutral";
}

function prettyLabel(value: string): string {
  return value.replace(/_/g, " ");
}

function formatDate(value?: string | null): string {
  if (!value) {
    return "—";
  }
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(parsed);
}

function formatSignedPercent(value?: number | null): string {
  if (value == null || Number.isNaN(value)) {
    return "—";
  }
  const normalized = value > 1 || value < -1 ? value / 100 : value;
  const formatted = formatPercent(Math.abs(normalized));
  return normalized > 0 ? `+${formatted}` : normalized < 0 ? `-${formatted}` : formatted;
}

function formatSignedNumber(value?: number | null): string {
  if (value == null || Number.isNaN(value)) {
    return "—";
  }
  const rounded = Math.round(value);
  const formatted = formatNumber(Math.abs(rounded));
  return rounded > 0 ? `+${formatted}` : rounded < 0 ? `-${formatted}` : formatted;
}

function formatYear(value?: number | null): string {
  if (value == null || Number.isNaN(value)) {
    return "—";
  }
  return String(Math.trunc(value));
}

function MetricLabel({
  label,
  tooltip,
  className,
  textClassName,
}: {
  label: ReactNode;
  tooltip?: string;
  className?: string;
  textClassName?: string;
}) {
  if (tooltip) {
    return (
      <PortfolioTooltipLabel
        label={label}
        tooltip={tooltip}
        className={clsx(className, styles.metricLabelWithTooltip)}
        textClassName={textClassName}
      />
    );
  }

  return (
    <span className={className}>
      <span className={textClassName}>{label}</span>
    </span>
  );
}

function SurfaceBadgeMetric({
  label,
  tooltip,
  value,
}: {
  label: ReactNode;
  tooltip?: string;
  value: ReactNode;
}) {
  return (
    <div className={styles.surfaceBadgeMetric}>
      <MetricLabel label={label} tooltip={tooltip} className={styles.surfaceBadgeMetricLabel} />
      <strong className={styles.surfaceBadgeMetricValue}>{value}</strong>
    </div>
  );
}

function SectionBasisRow({ section }: { section?: MarketSectionDescriptor | null }) {
  if (!section) {
    return null;
  }

  const chips = [
    section.metric_basis ? `Basis: ${section.metric_basis}` : null,
    section.scope_basis ? `Scope: ${section.scope_basis}` : null,
    section.sum_safe == null ? null : section.sum_safe ? "Summation: safe to sum" : "Summation: do not sum rows",
    section.overlap_policy ? section.overlap_policy : null,
  ].filter((value): value is string => Boolean(value));

  if (chips.length === 0) {
    return null;
  }

  return (
    <div className={styles.basisChipRow}>
      {chips.map((chip) => (
        <InfoPill key={chip} tone={chip.startsWith("Summation: do not sum") ? "warning" : "neutral"}>
          {chip}
        </InfoPill>
      ))}
    </div>
  );
}

const marketTooltipCopy = workspaceTooltipCopy.marketView;

function tooltipHeader(label: string, tooltip: string) {
  return () => <PortfolioTooltipLabel label={label} tooltip={tooltip} />;
}

function Sparkline({ points }: { points: MarketSparklinePoint[] }) {
  if (points.length < 2) {
    return <span className={styles.sparklineFallback}>No spark</span>;
  }

  const values = points.map((point) => point.family_count);
  const max = Math.max(...values);
  const min = Math.min(...values);
  const range = max - min || 1;
  const step = 100 / Math.max(points.length - 1, 1);
  const coordinates = points
    .map((point, index) => {
      const x = index * step;
      const y = 24 - ((point.family_count - min) / range) * 22 - 1;
      return `${x},${y}`;
    })
    .join(" ");

  const stroke = getDirectionColor(points[points.length - 1]?.market_state ?? "stable");

  return (
    <svg className={styles.sparkline} viewBox="0 0 100 24" aria-hidden="true">
      <polyline fill="none" stroke={stroke} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" points={coordinates} />
    </svg>
  );
}

export function MarketWorkspace() {
  const router = useRouter();
  const pathname = usePathname() ?? "/market";
  const searchParams = useSearchParams();
  const query = searchParams ?? new URLSearchParams();
  const [workspace, setWorkspace] = useState<MarketWorkspaceResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [marketHistoryRows, setMarketHistoryRows] = useState<MarketOverviewHistoryRow[]>([]);
  const [marketHistoryLoading, setMarketHistoryLoading] = useState(true);
  const [leadingJurisdictions, setLeadingJurisdictions] = useState<MarketSectionResponse<MarketLeadingJurisdictionRow> | null>(null);
  const [leadingJurisdictionsLoading, setLeadingJurisdictionsLoading] = useState(false);
  const [leadingJurisdictionsError, setLeadingJurisdictionsError] = useState<string | null>(null);
  const [applicationsGrants, setApplicationsGrants] = useState<MarketSectionResponse<MarketApplicationGrantRow> | null>(null);
  const [applicationsGrantsLoading, setApplicationsGrantsLoading] = useState(false);
  const [applicationsGrantsError, setApplicationsGrantsError] = useState<string | null>(null);
  const [grantMix, setGrantMix] = useState<MarketSectionResponse<MarketGrantMixRow> | null>(null);
  const [grantMixLoading, setGrantMixLoading] = useState(false);
  const [grantMixError, setGrantMixError] = useState<string | null>(null);
  const [technologyCpcTrends, setTechnologyCpcTrends] = useState<MarketSectionResponse<MarketCpcTrendRow> | null>(null);
  const [technologyCpcTrendsLoading, setTechnologyCpcTrendsLoading] = useState(false);
  const [technologyCpcTrendsError, setTechnologyCpcTrendsError] = useState<string | null>(null);
  const [technologyCpcJurisdictions, setTechnologyCpcJurisdictions] = useState<MarketSectionResponse<MarketCpcJurisdictionRow> | null>(null);
  const [technologyCpcJurisdictionsLoading, setTechnologyCpcJurisdictionsLoading] = useState(false);
  const [technologyCpcJurisdictionsError, setTechnologyCpcJurisdictionsError] = useState<string | null>(null);
  const [technologyCpcOwners, setTechnologyCpcOwners] = useState<MarketSectionResponse<MarketCpcOwnerRow> | null>(null);
  const [technologyCpcOwnersLoading, setTechnologyCpcOwnersLoading] = useState(false);
  const [technologyCpcOwnersError, setTechnologyCpcOwnersError] = useState<string | null>(null);
  const [technologyCpcCitingOwners, setTechnologyCpcCitingOwners] = useState<MarketSectionResponse<MarketCpcCitingOwnerRow> | null>(null);
  const [technologyCpcCitingOwnersLoading, setTechnologyCpcCitingOwnersLoading] = useState(false);
  const [technologyCpcCitingOwnersError, setTechnologyCpcCitingOwnersError] = useState<string | null>(null);
  const [marketChronologyView, setMarketChronologyView] = useState<MarketChronologyView>("mix");
  const [leadingJurisdictionFieldFilter, setLeadingJurisdictionFieldFilter] = useState("");
  const [leadingJurisdictionView, setLeadingJurisdictionView] = useState<LeadingJurisdictionView>("table");
  const [applicationsGrantView, setApplicationsGrantView] = useState<ApplicationsGrantView>("chart");
  const [applicationsGrantJurisdictionFilter, setApplicationsGrantJurisdictionFilter] = useState("all");
  const [technologyYearFilter, setTechnologyYearFilter] = useState<string>("latest");
  const [technologyJurisdictionFilter, setTechnologyJurisdictionFilter] = useState("");
  const [technologyOwnerCpcFilter, setTechnologyOwnerCpcFilter] = useState("");

  const activeState = query.get("state") ?? "all";
  const activeSegment = query.get("segment") ?? undefined;
  const rawSection = query.get("section");
  const activeSection: MarketWorkspaceSection = rawSection === "analysis" ? "analysis" : "overview";
  const rawTab = query.get("tab");
  const activeTab: MarketWorkspaceTab =
    rawTab === "technology" || rawTab === "jurisdictions" ? rawTab : "competition";

  const updateQuery = useCallback(
    (updates: Record<string, string | null>) => {
      const params = new URLSearchParams(searchParams?.toString() ?? "");
      Object.entries(updates).forEach(([key, value]) => {
        if (!value || value === "all") {
          params.delete(key);
          return;
        }
        params.set(key, value);
      });
      const nextQuery = params.toString();
      router.replace(nextQuery ? `${pathname}?${nextQuery}` : pathname, { scroll: false });
    },
    [pathname, router, searchParams],
  );

  useEffect(() => {
    let disposed = false;

    async function loadWorkspace() {
      setLoading(true);
      setError(null);
      try {
        const payload = await fetchMarketWorkspace({
          marketState: activeState,
          segmentId: activeSegment,
        });
        if (!disposed) {
          setWorkspace(payload);
        }
      } catch (ex) {
        if (!disposed) {
          setError(ex instanceof Error ? ex.message : "Could not load market workspace.");
        }
      } finally {
        if (!disposed) {
          setLoading(false);
        }
      }
    }

    void loadWorkspace();
    return () => {
      disposed = true;
    };
  }, [activeSegment, activeState]);

  useEffect(() => {
    let disposed = false;

    async function loadMarketHistory() {
      if (workspace?.overview.market_overview_history?.length) {
        setMarketHistoryRows(workspace.overview.market_overview_history);
        setMarketHistoryLoading(false);
        return;
      }

      setMarketHistoryLoading(true);
      try {
        const rows = await fetchMarketOverviewHistory();
        if (!disposed) {
          setMarketHistoryRows(rows);
        }
      } catch {
        if (!disposed) {
          setMarketHistoryRows([]);
        }
      } finally {
        if (!disposed) {
          setMarketHistoryLoading(false);
        }
      }
    }

    void loadMarketHistory();
    return () => {
      disposed = true;
    };
  }, [workspace?.overview.market_overview_history]);

  useEffect(() => {
    let disposed = false;

    async function loadLeadingJurisdictions() {
      if (activeSection !== "overview") {
        return;
      }

      setLeadingJurisdictionsLoading(true);
      setLeadingJurisdictionsError(null);

      try {
        const payload = await fetchMarketLeadingJurisdictions(workspace?.scope.latest_market_year, 5);
        if (!disposed) {
          setLeadingJurisdictions(payload);
        }
      } catch (ex) {
        if (!disposed) {
          setLeadingJurisdictionsError(ex instanceof Error ? ex.message : "Could not load leading jurisdictions.");
          setLeadingJurisdictions(null);
        }
      } finally {
        if (!disposed) {
          setLeadingJurisdictionsLoading(false);
        }
      }
    }

    void loadLeadingJurisdictions();
    return () => {
      disposed = true;
    };
  }, [activeSection, workspace?.scope.latest_market_year]);

  useEffect(() => {
    let disposed = false;

    async function loadJurisdictionGrantSections() {
      if (activeSection !== "analysis" || activeTab !== "jurisdictions" || !workspace?.selected_segment?.wipo_industry_code) {
        if (!disposed && (activeSection !== "analysis" || activeTab !== "jurisdictions")) {
          setApplicationsGrants(null);
          setGrantMix(null);
        }
        return;
      }

      const selectedSegmentId = workspace.selected_segment.wipo_industry_code;
      setApplicationsGrantsLoading(true);
      setGrantMixLoading(true);
      setApplicationsGrantsError(null);
      setGrantMixError(null);

      try {
        const [applicationsPayload, grantMixPayload] = await Promise.all([
          fetchMarketSegmentApplicationsGrants(selectedSegmentId, {
            yearFrom: workspace.scope.coverage_year_range.start_year,
            yearTo: workspace.scope.latest_market_year,
            jurisdictionLimit: 12,
          }),
          fetchMarketSegmentGrantMix(selectedSegmentId, {
            asOfYear: workspace.scope.latest_market_year,
            limit: 10,
          }),
        ]);

        if (!disposed) {
          setApplicationsGrants(applicationsPayload);
          setGrantMix(grantMixPayload);
        }
      } catch (ex) {
        if (!disposed) {
          const message = ex instanceof Error ? ex.message : "Could not load jurisdiction and grant detail.";
          setApplicationsGrantsError(message);
          setGrantMixError(message);
          setApplicationsGrants(null);
          setGrantMix(null);
        }
      } finally {
        if (!disposed) {
          setApplicationsGrantsLoading(false);
          setGrantMixLoading(false);
        }
      }
    }

    void loadJurisdictionGrantSections();
    return () => {
      disposed = true;
    };
  }, [
    activeSection,
    activeTab,
    workspace?.selected_segment?.wipo_industry_code,
    workspace?.scope.coverage_year_range.start_year,
    workspace?.scope.latest_market_year,
  ]);

  useEffect(() => {
    const latestCpcYear = workspace?.scope.latest_cpc_year;
    if (!latestCpcYear) {
      return;
    }
    setTechnologyYearFilter(String(latestCpcYear));
    setTechnologyJurisdictionFilter("");
  }, [workspace?.selected_segment?.wipo_industry_code, workspace?.scope.latest_cpc_year]);

  useEffect(() => {
    let disposed = false;

    async function loadTechnologySections() {
      if (activeSection !== "analysis" || activeTab !== "technology" || !workspace?.selected_segment?.wipo_industry_code) {
        if (!disposed && (activeSection !== "analysis" || activeTab !== "technology")) {
          setTechnologyCpcTrends(null);
          setTechnologyCpcJurisdictions(null);
        }
        return;
      }

      const selectedSegmentId = workspace.selected_segment.wipo_industry_code;
      const effectiveYear =
        Number.parseInt(technologyYearFilter, 10) ||
        workspace.scope.latest_cpc_year ||
        workspace.scope.latest_market_year;

      setTechnologyCpcTrendsLoading(true);
      setTechnologyCpcJurisdictionsLoading(true);
      setTechnologyCpcTrendsError(null);
      setTechnologyCpcJurisdictionsError(null);

      try {
        const [trendPayload, jurisdictionPayload] = await Promise.all([
          fetchMarketCpcTrends(selectedSegmentId, {
            asOfYear: effectiveYear,
            limit: 25,
          }),
          fetchMarketSegmentCpcJurisdictions(selectedSegmentId, {
            asOfYear: effectiveYear,
            limit: 250,
          }),
        ]);

        if (!disposed) {
          setTechnologyCpcTrends(trendPayload);
          setTechnologyCpcJurisdictions(jurisdictionPayload);
        }
      } catch (ex) {
        if (!disposed) {
          const message = ex instanceof Error ? ex.message : "Could not load CPC technology detail.";
          setTechnologyCpcTrendsError(message);
          setTechnologyCpcJurisdictionsError(message);
          setTechnologyCpcTrends(null);
          setTechnologyCpcJurisdictions(null);
        }
      } finally {
        if (!disposed) {
          setTechnologyCpcTrendsLoading(false);
          setTechnologyCpcJurisdictionsLoading(false);
        }
      }
    }

    void loadTechnologySections();
    return () => {
      disposed = true;
    };
  }, [
    activeSection,
    activeTab,
    technologyYearFilter,
    workspace?.selected_segment?.wipo_industry_code,
    workspace?.scope.latest_cpc_year,
    workspace?.scope.latest_market_year,
  ]);

  useEffect(() => {
    const effectiveYear =
      Number.parseInt(technologyYearFilter, 10) ||
      workspace?.scope.latest_cpc_year ||
      workspace?.scope.latest_market_year;
    const fallbackRows =
      effectiveYear === workspace?.scope.latest_cpc_year ? workspace?.selected_segment?.top_cpcs ?? [] : [];
    const sourceRows = technologyCpcTrends?.rows ?? fallbackRows;
    const ownerOptions = Array.from(new Set(sourceRows.map((row) => row.cpc_main_group).filter(Boolean)));

    setTechnologyOwnerCpcFilter((current) => {
      if (ownerOptions.length === 0) {
        return "";
      }
      return ownerOptions.includes(current) ? current : ownerOptions[0];
    });
  }, [
    technologyCpcTrends?.rows,
    technologyYearFilter,
    workspace?.selected_segment?.top_cpcs,
    workspace?.scope.latest_cpc_year,
    workspace?.scope.latest_market_year,
  ]);

  useEffect(() => {
    let disposed = false;

    async function loadTechnologyOwners() {
      if (
        activeSection !== "analysis" ||
        activeTab !== "technology" ||
        !workspace?.selected_segment?.wipo_industry_code ||
        !technologyOwnerCpcFilter
      ) {
        if (!disposed && (activeSection !== "analysis" || activeTab !== "technology" || !technologyOwnerCpcFilter)) {
          setTechnologyCpcOwners(null);
        }
        return;
      }

      const selectedSegmentId = workspace.selected_segment.wipo_industry_code;
      const effectiveYear =
        Number.parseInt(technologyYearFilter, 10) ||
        workspace.scope.latest_cpc_year ||
        workspace.scope.latest_market_year;

      setTechnologyCpcOwnersLoading(true);
      setTechnologyCpcOwnersError(null);

      try {
        const payload = await fetchMarketSegmentCpcOwners(selectedSegmentId, technologyOwnerCpcFilter, {
          asOfYear: effectiveYear,
          limit: 12,
        });

        if (!disposed) {
          setTechnologyCpcOwners(payload);
        }
      } catch (ex) {
        if (!disposed) {
          setTechnologyCpcOwnersError(ex instanceof Error ? ex.message : "Could not load CPC owner detail.");
          setTechnologyCpcOwners(null);
        }
      } finally {
        if (!disposed) {
          setTechnologyCpcOwnersLoading(false);
        }
      }
    }

    void loadTechnologyOwners();
    return () => {
      disposed = true;
    };
  }, [
    activeSection,
    activeTab,
    technologyOwnerCpcFilter,
    technologyYearFilter,
    workspace?.selected_segment?.wipo_industry_code,
    workspace?.scope.latest_cpc_year,
    workspace?.scope.latest_market_year,
  ]);

  useEffect(() => {
    let disposed = false;

    async function loadTechnologyCitingOwners() {
      if (
        activeSection !== "analysis" ||
        activeTab !== "technology" ||
        !workspace?.selected_segment?.wipo_industry_code ||
        !technologyOwnerCpcFilter
      ) {
        if (!disposed && (activeSection !== "analysis" || activeTab !== "technology" || !technologyOwnerCpcFilter)) {
          setTechnologyCpcCitingOwners(null);
        }
        return;
      }

      const selectedSegmentId = workspace.selected_segment.wipo_industry_code;
      const effectiveYear =
        Number.parseInt(technologyYearFilter, 10) ||
        workspace.scope.latest_cpc_year ||
        workspace.scope.latest_market_year;

      setTechnologyCpcCitingOwnersLoading(true);
      setTechnologyCpcCitingOwnersError(null);

      try {
        const payload = await fetchMarketSegmentCpcCitingOwners(selectedSegmentId, technologyOwnerCpcFilter, {
          asOfYear: effectiveYear,
          limit: 12,
        });

        if (!disposed) {
          setTechnologyCpcCitingOwners(payload);
        }
      } catch (ex) {
        if (!disposed) {
          setTechnologyCpcCitingOwnersError(
            ex instanceof Error ? ex.message : "Could not load CPC citing-owner detail.",
          );
          setTechnologyCpcCitingOwners(null);
        }
      } finally {
        if (!disposed) {
          setTechnologyCpcCitingOwnersLoading(false);
        }
      }
    }

    void loadTechnologyCitingOwners();
    return () => {
      disposed = true;
    };
  }, [
    activeSection,
    activeTab,
    technologyOwnerCpcFilter,
    technologyYearFilter,
    workspace?.selected_segment?.wipo_industry_code,
    workspace?.scope.latest_cpc_year,
    workspace?.scope.latest_market_year,
  ]);

  if (loading && !workspace) {
    return (
      <Surface title="Market workspace" description="Loading live bounded market intelligence data.">
        <p className="portfolio-empty">Loading market intelligence workspace…</p>
      </Surface>
    );
  }

  if (!workspace) {
    return (
      <Surface title="Market workspace" description="The workspace could not be initialized.">
        <p className="portfolio-error">{error ?? "Market workspace unavailable."}</p>
      </Surface>
    );
  }

  const selected = workspace.selected_segment;
  const marketOverviewHistory = marketHistoryRows.length
    ? marketHistoryRows
    : (workspace.overview.market_overview_history ?? []);
  const latestMarketSummary =
    workspace.overview.latest_market_summary ?? marketOverviewHistory[marketOverviewHistory.length - 1] ?? null;
  const selectedSummary = selected?.summary;
  const momentumRows = selected?.timeseries ?? [];
  const latestMomentumRow = momentumRows.length ? momentumRows[momentumRows.length - 1] : null;
  const latestMomentumDelta = latestMomentumRow?.year_over_year_delta_pct ?? null;
  const citationRows = [...(selected?.citation_trend ?? [])].sort((left, right) => left.as_of_year - right.as_of_year);
  const jurisdictionRows = selected?.top_jurisdictions ?? [];
  const attackerRows = selected?.top_attackers ?? [];
  const workspaceCpcRows = selected?.top_cpcs ?? [];
  const ownerRows = selected?.top_owners ?? [];
  const familyRows = selected?.top_families ?? [];
  const fieldJurisdictionRows = selected?.field_jurisdictions ?? [];
  const workspaceCpcJurisdictionRows = selected?.cpc_jurisdictions ?? [];
  const leadingJurisdictionRows = leadingJurisdictions?.rows ?? [];
  const applicationsGrantRows = applicationsGrants?.rows ?? [];
  const grantMixRows = grantMix?.rows ?? [];
  const latestTechnologyYear = workspace.scope.latest_cpc_year || workspace.scope.latest_market_year;
  const effectiveTechnologyYear =
    Number.parseInt(technologyYearFilter, 10) || latestTechnologyYear;
  const technologyYearOptions = Array.from(
    {
      length: Math.max(0, latestTechnologyYear - workspace.scope.coverage_year_range.start_year + 1),
    },
    (_, index) => latestTechnologyYear - index,
  );
  const technologyCpcRows =
    technologyCpcTrends?.rows ??
    (effectiveTechnologyYear === workspace.scope.latest_cpc_year ? workspaceCpcRows : []);
  const technologyCpcJurisdictionSourceRows =
    technologyCpcJurisdictions?.rows ??
    (effectiveTechnologyYear === workspace.scope.latest_cpc_year ? workspaceCpcJurisdictionRows : []);
  const technologyJurisdictionOptions = Array.from(
    new Set(technologyCpcJurisdictionSourceRows.map((row) => row.jurisdiction_code).filter(Boolean)),
  );
  const effectiveTechnologyJurisdictionFilter = technologyJurisdictionOptions.includes(technologyJurisdictionFilter)
    ? technologyJurisdictionFilter
    : (technologyJurisdictionOptions[0] ?? "");
  const technologyCpcJurisdictionRows = effectiveTechnologyJurisdictionFilter
    ? technologyCpcJurisdictionSourceRows.filter((row) => row.jurisdiction_code === effectiveTechnologyJurisdictionFilter)
    : [];
  const technologyOwnerCpcOptions = Array.from(new Set(technologyCpcRows.map((row) => row.cpc_main_group)));
  const technologyCpcOwnerRows = technologyCpcOwners?.rows ?? [];
  const technologyCpcCitingOwnerRows = technologyCpcCitingOwners?.rows ?? [];
  const grantMixChartHeight = Math.max(320, grantMixRows.length * 44);
  const applicationsGrantJurisdictionOptions = Array.from(
    new Set(applicationsGrantRows.map((row) => row.jurisdiction_code)),
  ).sort((left, right) => left.localeCompare(right));
  const effectiveApplicationsGrantJurisdictionFilter = applicationsGrantJurisdictionOptions.includes(applicationsGrantJurisdictionFilter)
    ? applicationsGrantJurisdictionFilter
    : "all";
  const filteredApplicationsGrantRows = [...applicationsGrantRows]
    .filter((row) =>
      effectiveApplicationsGrantJurisdictionFilter === "all"
        ? true
        : row.jurisdiction_code === effectiveApplicationsGrantJurisdictionFilter,
    )
    .sort((left, right) => left.as_of_year - right.as_of_year || left.jurisdiction_code.localeCompare(right.jurisdiction_code));
  const applicationsGrantChartRows =
    effectiveApplicationsGrantJurisdictionFilter === "all"
      ? Array.from(
          filteredApplicationsGrantRows.reduce(
            (map, row) => {
              const existing = map.get(row.as_of_year) ?? {
                as_of_year: row.as_of_year,
                application_count: 0,
                grant_count: 0,
                total_event_count: 0,
              };
              existing.application_count += row.application_count;
              existing.grant_count += row.grant_count;
              existing.total_event_count += row.total_event_count;
              map.set(row.as_of_year, existing);
              return map;
            },
            new Map<number, { as_of_year: number; application_count: number; grant_count: number; total_event_count: number }>(),
          ).values(),
        ).sort((left, right) => left.as_of_year - right.as_of_year)
      : filteredApplicationsGrantRows.map((row) => ({
          as_of_year: row.as_of_year,
          application_count: row.application_count,
          grant_count: row.grant_count,
          total_event_count: row.total_event_count,
        }));
  const leadingJurisdictionFieldOptions = Array.from(new Set(leadingJurisdictionRows.map((row) => row.wipo_field))).sort((left, right) =>
    left.localeCompare(right),
  );
  const effectiveLeadingJurisdictionFieldFilter = leadingJurisdictionFieldOptions.includes(leadingJurisdictionFieldFilter)
    ? leadingJurisdictionFieldFilter
    : (leadingJurisdictionFieldOptions[0] ?? "");
  const filteredLeadingJurisdictionRows = effectiveLeadingJurisdictionFieldFilter
    ? leadingJurisdictionRows.filter((row) => row.wipo_field === effectiveLeadingJurisdictionFieldFilter)
    : [];
  const canShowLeadingJurisdictionPie = filteredLeadingJurisdictionRows.length > 0;
  const isLeadingJurisdictionPieView = leadingJurisdictionView === "pie" && canShowLeadingJurisdictionPie;
  const leadingJurisdictionPiePalette = [
    chartTokens.rank.primary,
    chartTokens.rank.secondary,
    chartTokens.rank.tertiary,
    chartTokens.series.info,
    chartTokens.series.success,
  ];
  const reducedContextMode = Boolean(workspace.meta.reduced_context_mode);
  const activeShare = selectedSummary && selectedSummary.segment_family_count_stock_asof > 0
    ? selectedSummary.segment_active_family_count_asof / selectedSummary.segment_family_count_stock_asof
    : 0;
  const topOwnerShare = selectedSummary?.segment_top_owner_share_hist_proxy ?? 0;
  const fieldBalance = selectedSummary?.segment_field_balance_asof ?? 0;
  const marketMedianCount = latestMomentumRow?.market_median_family_count ?? null;
  const marketMedianGap = latestMomentumRow && marketMedianCount != null ? latestMomentumRow.family_count - marketMedianCount : null;
  const marketFamilyCount = latestMarketSummary?.market_family_count_asof ?? 0;
  const lifecycleMixRows = marketOverviewHistory.map((row) => {
    const total = row.market_family_count_asof || 1;
    return {
      as_of_year: row.as_of_year,
      pending_share: row.pending_family_count_asof / total,
      fully_active_share: row.fully_active_family_count_asof / total,
      partially_lapsed_share: row.partially_lapsed_family_count_asof / total,
      dead_share: row.dead_family_count_asof / total,
      pending_family_count_asof: row.pending_family_count_asof,
      fully_active_family_count_asof: row.fully_active_family_count_asof,
      partially_lapsed_family_count_asof: row.partially_lapsed_family_count_asof,
      dead_family_count_asof: row.dead_family_count_asof,
    };
  });
  const marketCountSeries = [
    {
      key: "market_family_count_asof" as const,
      label: "Families",
      color: chartTokens.series.accent,
      tooltip: marketTooltipCopy.familiesInScope,
    },
    {
      key: "pending_family_count_asof" as const,
      label: "Pending / filing",
      color: chartTokens.series.info,
      tooltip: marketTooltipCopy.pendingFiling,
    },
    {
      key: "fully_active_family_count_asof" as const,
      label: "Fully active",
      color: chartTokens.series.success,
      tooltip: marketTooltipCopy.fullyActive,
    },
    {
      key: "partially_lapsed_family_count_asof" as const,
      label: "Partially lapsed",
      color: chartTokens.series.warning,
      tooltip: marketTooltipCopy.partiallyLapsed,
    },
    {
      key: "dead_family_count_asof" as const,
      label: "Dead",
      color: chartTokens.series.critical,
      tooltip: marketTooltipCopy.dead,
    },
  ].map((series) => {
    const latestRow = marketOverviewHistory[marketOverviewHistory.length - 1] ?? null;
    const priorRow = marketOverviewHistory[marketOverviewHistory.length - 2] ?? null;
    const latestValue = latestRow ? latestRow[series.key] : 0;
    const priorValue = priorRow ? priorRow[series.key] : 0;
    const delta = priorValue > 0 ? (latestValue - priorValue) / priorValue : null;
    return {
      ...series,
      latestValue,
      delta,
    };
  });
  const marketLifecycleCards = latestMarketSummary
    ? [
        {
          key: "pending",
          label: "Pending / filing",
          tooltip: marketTooltipCopy.pendingFiling,
          value: latestMarketSummary.pending_family_count_asof,
          share: marketFamilyCount > 0 ? latestMarketSummary.pending_family_count_asof / marketFamilyCount : 0,
          toneClass: styles.marketStatusCardPending,
        },
        {
          key: "active",
          label: "Fully active",
          tooltip: marketTooltipCopy.fullyActive,
          value: latestMarketSummary.fully_active_family_count_asof,
          share: marketFamilyCount > 0 ? latestMarketSummary.fully_active_family_count_asof / marketFamilyCount : 0,
          toneClass: styles.marketStatusCardActive,
        },
        {
          key: "lapsed",
          label: "Partially lapsed",
          tooltip: marketTooltipCopy.partiallyLapsed,
          value: latestMarketSummary.partially_lapsed_family_count_asof,
          share: marketFamilyCount > 0 ? latestMarketSummary.partially_lapsed_family_count_asof / marketFamilyCount : 0,
          toneClass: styles.marketStatusCardLapsed,
        },
        {
          key: "dead",
          label: "Dead",
          tooltip: marketTooltipCopy.dead,
          value: latestMarketSummary.dead_family_count_asof,
          share: marketFamilyCount > 0 ? latestMarketSummary.dead_family_count_asof / marketFamilyCount : 0,
          toneClass: styles.marketStatusCardDead,
        },
      ]
    : [];
  const marketSignalCards = latestMarketSummary
    ? [
        {
          key: "blocking",
          label: "Avg blocking",
          tooltip: marketTooltipCopy.avgBlocking,
          value: formatDecimal(latestMarketSummary.avg_blocking_power_score_asof, 1),
        },
        {
          key: "enforceability",
          label: "Avg enforceability score",
          tooltip: marketTooltipCopy.avgEnforceability,
          value: formatDecimal(latestMarketSummary.avg_enforceability_score_asof, 2),
        },
        {
          key: "forward",
          label: "Avg forward citations / family",
          tooltip: marketTooltipCopy.avgForwardCitations,
          value: formatDecimal(latestMarketSummary.avg_forward_citations_clean_asof, 1),
        },
        {
          key: "top-owner",
          label: "Top owner share",
          tooltip: marketTooltipCopy.topOwnerShare,
          value: formatPercent(latestMarketSummary.top_owner_share_asof),
        },
      ]
    : [];
  const marketOverviewBadgeMetrics = [
    {
      key: "fields",
      label: "Fields in scope",
      tooltip: marketTooltipCopy.fieldsInScope,
      value: formatNumber(workspace.overview.segment_count),
    },
    {
      key: "rising",
      label: "Rising fields",
      tooltip: marketTooltipCopy.risingFields,
      value: formatNumber(workspace.overview.rising_segment_count),
    },
    {
      key: "cooling",
      label: "Cooling fields",
      tooltip: marketTooltipCopy.coolingFields,
      value: formatNumber(workspace.overview.cooling_segment_count),
    },
  ];
  const tabOptions: Array<{ value: MarketWorkspaceTab; label: string; note: string; tooltip: string }> = [
    {
      value: "competition",
      label: "Competition",
      note: "Owners, pressure, and attackers",
      tooltip: marketTooltipCopy.competition,
    },
    {
      value: "jurisdictions",
      label: "Jurisdictions & Grants",
      note: "Footprint, applications, and grants",
      tooltip: marketTooltipCopy.jurisdictionsAndGrants,
    },
    {
      value: "technology",
      label: "Technology",
      note: "CPC structure and global importance",
      tooltip: marketTooltipCopy.technology,
    },
  ];
  const sectionOptions: Array<{ value: MarketWorkspaceSection; label: string; note: string; tooltip: string }> = [
    {
      value: "overview",
      label: "Overview",
      note: "Market-wide pulse and field league table",
      tooltip: marketTooltipCopy.overview,
    },
    {
      value: "analysis",
      label: "Field analysis",
      note: "Filters, selected field summary, and drilldowns",
      tooltip: marketTooltipCopy.fieldAnalysis,
    },
  ];
  const marketChronologySurface = (
    <Surface
      title={<PortfolioTooltipLabel label="Market-wide chronology" tooltip={marketTooltipCopy.marketWideChronology} />}
      description="Unique family universe across the bounded market scope, capped through 2023 for consistency."
      badge={
        latestMarketSummary ? (
          <SurfaceBadgeMetric
            label="Latest supported year"
            tooltip={marketTooltipCopy.latestSupportedYear}
            value={formatYear(latestMarketSummary.as_of_year)}
          />
        ) : undefined
      }
    >
      {marketHistoryLoading && marketOverviewHistory.length === 0 ? (
        <p className="portfolio-empty">Loading market-wide chronology…</p>
      ) : marketOverviewHistory.length === 0 || !latestMarketSummary ? (
        <p className="portfolio-empty">No market-wide chronology is available.</p>
      ) : (
        <div className={styles.evidenceColumn}>
          <div className={styles.marketChronologyBanner}>
            <article className={styles.marketChronologyLead}>
              <div className={styles.marketChronologyLeadTop}>
                <div className={styles.marketChronologyLeadStat}>
                  <MetricLabel
                    label="Families in scope"
                    tooltip={marketTooltipCopy.familiesInScope}
                    className={styles.metricLabel}
                  />
                  <strong className={styles.marketChronologyLeadValue}>
                    {formatNumber(latestMarketSummary.market_family_count_asof)}
                  </strong>
                </div>
                <div className={styles.marketChronologyLeadStat}>
                  <MetricLabel
                    label="Owners in scope"
                    tooltip={marketTooltipCopy.ownersInScope}
                    className={styles.metricLabel}
                  />
                  <strong className={styles.marketChronologyLeadValue}>
                    {formatNumber(latestMarketSummary.owner_count_asof)}
                  </strong>
                </div>
              </div>

              <div className={styles.marketChronologyLeadMetaRow}>
                <p className={styles.marketChronologyLeadNote}>
                  Unique market families across the bounded field universe in {formatYear(latestMarketSummary.as_of_year)}.
                </p>
                <div className={styles.marketChronologyLeadMetaItem}>
                  <MetricLabel
                    label="Crowding"
                    tooltip={marketTooltipCopy.marketCrowding}
                    className={styles.metricLabel}
                  />
                  <StatusPill tone={toneForCrowding(latestMarketSummary.crowding_label)}>
                    {prettyLabel(latestMarketSummary.crowding_label)}
                  </StatusPill>
                </div>
              </div>

              <div className={styles.marketSignalGrid}>
                {marketSignalCards.map((card) => (
                  <div key={card.key} className={styles.marketSignalCard}>
                    <MetricLabel label={card.label} tooltip={card.tooltip} className={styles.metricLabel} />
                    <strong>{card.value}</strong>
                  </div>
                ))}
              </div>
            </article>

            <div className={styles.marketStatusGrid}>
              {marketLifecycleCards.map((card) => (
                <article key={card.key} className={clsx(styles.marketStatusCard, card.toneClass)}>
                  <MetricLabel label={card.label} tooltip={card.tooltip} className={styles.metricLabel} />
                  <strong className={styles.marketStatusValue}>{formatNumber(card.value)}</strong>
                  <div className={styles.marketStatusMeter}>
                    <span
                      className={styles.marketStatusMeterFill}
                      style={{ width: `${Math.max(8, Math.min(100, card.share * 100))}%` }}
                    />
                  </div>
                  <div className={styles.marketStatusFooter}>
                    <PortfolioTooltipLabel label="Share of market stock" tooltip={marketTooltipCopy.shareOfMarketStock} />
                    <strong>{formatPercent(card.share)}</strong>
                  </div>
                </article>
              ))}
            </div>
          </div>
          <div className={styles.chartSurface}>
            <div className={styles.sectionToggle} role="tablist" aria-label="Market chronology view">
              <button
                type="button"
                role="tab"
                aria-selected={marketChronologyView === "mix"}
                className={clsx(styles.sectionToggleButton, marketChronologyView === "mix" && styles.sectionToggleButtonActive)}
                onClick={() => setMarketChronologyView("mix")}
              >
                <PortfolioTooltipLabel label="Mix" tooltip={marketTooltipCopy.mixView} />
              </button>
              <button
                type="button"
                role="tab"
                aria-selected={marketChronologyView === "counts"}
                className={clsx(styles.sectionToggleButton, marketChronologyView === "counts" && styles.sectionToggleButtonActive)}
                onClick={() => setMarketChronologyView("counts")}
              >
                <PortfolioTooltipLabel label="Counts" tooltip={marketTooltipCopy.countsView} />
              </button>
            </div>

            {marketChronologyView === "mix" ? (
              <ResponsiveContainer width="100%" height={340}>
                <BarChart data={lifecycleMixRows} margin={{ top: 12, right: 12, left: 0, bottom: 4 }} barCategoryGap="12%">
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="as_of_year" />
                  <YAxis tickFormatter={(value: number) => formatPercent(value)} />
                  <Tooltip
                    formatter={(value: number, name: string, item) => {
                      const labelMap: Record<string, string> = {
                        pending_share: "Pending / filing",
                        fully_active_share: "Fully active",
                        partially_lapsed_share: "Partially lapsed",
                        dead_share: "Dead",
                      };
                      const rawValue = item?.payload?.[name.replace("_share", "_family_count_asof")] as number | undefined;
                      return [`${formatPercent(value)} · ${formatNumber(rawValue ?? 0)}`, labelMap[name] ?? name];
                    }}
                  />
                  <Bar dataKey="dead_share" stackId="marketMix" fill="rgba(187, 52, 52, 0.82)" radius={[0, 0, 0, 0]} />
                  <Bar dataKey="partially_lapsed_share" stackId="marketMix" fill="rgba(214, 144, 49, 0.78)" radius={[0, 0, 0, 0]} />
                  <Bar dataKey="fully_active_share" stackId="marketMix" fill="rgba(49, 135, 95, 0.82)" radius={[0, 0, 0, 0]} />
                  <Bar dataKey="pending_share" stackId="marketMix" fill="rgba(79, 124, 185, 0.78)" radius={[8, 8, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className={styles.marketCountsGrid}>
                {marketCountSeries.map((series) => (
                  <article key={series.key} className={styles.marketCountCard}>
                    <div className={styles.marketCountCardHeader}>
                      <MetricLabel label={series.label} tooltip={series.tooltip} className={styles.metricLabel} />
                      <strong>{formatNumber(series.latestValue)}</strong>
                    </div>
                    <div className={styles.marketCountCardMeta}>
                      <PortfolioTooltipLabel label="Latest supported year" tooltip={marketTooltipCopy.latestSupportedYear} />
                      <strong>{formatYear(latestMarketSummary.as_of_year)}</strong>
                      <span>{series.delta == null ? "No prior baseline" : `${formatSignedPercent(series.delta)} vs prior year`}</span>
                    </div>
                    <div className={styles.marketCountMiniChart}>
                      <ResponsiveContainer width="100%" height={112}>
                        <AreaChart data={marketOverviewHistory} margin={{ top: 8, right: 4, left: 0, bottom: 0 }}>
                          <CartesianGrid strokeDasharray="3 3" vertical={false} />
                          <XAxis dataKey="as_of_year" hide />
                          <YAxis hide />
                          <Tooltip formatter={(value: number) => [formatNumber(value), series.label]} />
                          <Area
                            type="monotone"
                            dataKey={series.key}
                            stroke={series.color}
                            fill={series.color}
                            fillOpacity={0.18}
                            strokeWidth={2.2}
                          />
                        </AreaChart>
                      </ResponsiveContainer>
                    </div>
                  </article>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </Surface>
  );
  const segmentColumns: DataTableColumn<MarketWorkspaceResponse["segments"][number]>[] = [
    {
      accessorKey: "wipo_industry_code",
      header: tooltipHeader("Field", marketTooltipCopy.field),
      cell: ({ row }) => {
        const segment = row.original;
        return (
          <button
            type="button"
            className="grid gap-1 bg-transparent p-0 text-left text-inherit"
            onClick={() => updateQuery({ segment: segment.wipo_industry_code })}
          >
            <span className="font-semibold text-slate-900">{segment.wipo_industry_code}</span>
            <small className="text-[11px] uppercase tracking-[0.08em] text-slate-500">
              Comparable through {segment.latest_comparable_year || segment.latest_year}
            </small>
          </button>
        );
      },
    },
    {
      accessorKey: "market_state",
      header: tooltipHeader("State", marketTooltipCopy.marketState),
      cell: ({ row }) => (
        <StatusPill tone={toneForState(row.original.market_state)}>{prettyLabel(row.original.market_state)}</StatusPill>
      ),
    },
    {
      accessorKey: "total_family_count",
      header: tooltipHeader("Families", marketTooltipCopy.families),
      cell: ({ row }) => formatNumber(row.original.total_family_count),
    },
    {
      accessorKey: "momentum_delta_pct",
      header: tooltipHeader("Momentum", marketTooltipCopy.momentum),
      cell: ({ row }) => formatSignedPercent(row.original.momentum_delta_pct),
    },
    {
      accessorKey: "segment_blocking_density_asof",
      header: tooltipHeader("Blocking", marketTooltipCopy.blocking),
      cell: ({ row }) => formatDecimal(row.original.segment_blocking_density_asof, 1),
    },
    {
      accessorKey: "crowding_label",
      header: tooltipHeader("Crowding", marketTooltipCopy.crowding),
      cell: ({ row }) => (
        <InfoPill tone={row.original.whitespace_candidate ? "accent" : "neutral"}>
          {row.original.whitespace_candidate ? "whitespace candidate" : prettyLabel(row.original.crowding_label)}
        </InfoPill>
      ),
    },
    {
      id: "sparkline",
      header: tooltipHeader("Spark", marketTooltipCopy.spark),
      cell: ({ row }) => <Sparkline points={row.original.sparkline} />,
    },
  ];
  const jurisdictionColumns: DataTableColumn<MarketSelectedSegment["top_jurisdictions"][number]>[] = [
    {
      accessorKey: "jurisdiction_code",
      header: tooltipHeader("Jurisdiction", marketTooltipCopy.jurisdiction),
      cell: ({ row }) => <strong className="text-slate-900">{row.original.jurisdiction_code}</strong>,
    },
    {
      accessorKey: "citation_count",
      header: tooltipHeader("Citations", marketTooltipCopy.citations),
      cell: ({ row }) => formatNumber(row.original.citation_count),
    },
    {
      accessorKey: "distinct_citing_assignee_count",
      header: tooltipHeader("Owners", marketTooltipCopy.ownersInScope),
      cell: ({ row }) => formatNumber(row.original.distinct_citing_assignee_count),
    },
    {
      accessorKey: "citation_pressure_index",
      header: tooltipHeader("Pressure", marketTooltipCopy.pressure),
      cell: ({ row }) => formatDecimal(row.original.citation_pressure_index, 1),
    },
    {
      accessorKey: "as_of_year",
      header: tooltipHeader("Year", marketTooltipCopy.year),
      cell: ({ row }) => formatNumber(row.original.as_of_year),
    },
  ];
  const cpcColumns: DataTableColumn<MarketSelectedSegment["top_cpcs"][number]>[] = [
    {
      accessorKey: "cpc_main_group",
      header: tooltipHeader("CPC main group", marketTooltipCopy.cpcMainGroup),
      cell: ({ row }) => (
        <div className="grid gap-1">
          <strong className="text-slate-900">{row.original.cpc_main_group}</strong>
          <small className="text-[11px] text-slate-500">{row.original.cpc_main_group_label}</small>
        </div>
      ),
    },
    {
      accessorKey: "cpc_family_share_within_segment_asof",
      header: tooltipHeader("Share", marketTooltipCopy.cpcShare),
      cell: ({ row }) => formatPercent(row.original.cpc_family_share_within_segment_asof),
    },
    {
      accessorKey: "cpc_growth_index_asof",
      header: tooltipHeader("Growth", marketTooltipCopy.growth),
      cell: ({ row }) => formatSignedPercent(row.original.cpc_growth_index_asof),
    },
    {
      accessorKey: "cpc_blocking_density_asof",
      header: tooltipHeader("Blocking", marketTooltipCopy.blocking),
      cell: ({ row }) => formatDecimal(row.original.cpc_blocking_density_asof, 1),
    },
    {
      accessorKey: "cpc_heat_state_asof",
      header: tooltipHeader("Heat", marketTooltipCopy.heat),
      cell: ({ row }) => (
        <StatusPill tone={toneForState(row.original.cpc_heat_state_asof)}>{prettyLabel(row.original.cpc_heat_state_asof)}</StatusPill>
      ),
    },
  ];
  const fieldJurisdictionColumns: DataTableColumn<MarketSelectedSegment["field_jurisdictions"][number]>[] = [
    {
      accessorKey: "jurisdiction_code",
      header: tooltipHeader("Jurisdiction", marketTooltipCopy.jurisdiction),
      cell: ({ row }) => <strong className="text-slate-900">{row.original.jurisdiction_code}</strong>,
    },
    {
      accessorKey: "jurisdiction_family_count_asof",
      header: tooltipHeader("Families", marketTooltipCopy.families),
      cell: ({ row }) => formatNumber(row.original.jurisdiction_family_count_asof),
    },
    {
      accessorKey: "jurisdiction_active_family_count_asof",
      header: tooltipHeader("Active", marketTooltipCopy.active),
      cell: ({ row }) => formatNumber(row.original.jurisdiction_active_family_count_asof),
    },
    {
      accessorKey: "jurisdiction_family_share_within_segment_asof",
      header: tooltipHeader("Field share", marketTooltipCopy.fieldShare),
      cell: ({ row }) => formatPercent(row.original.jurisdiction_family_share_within_segment_asof),
    },
    {
      accessorKey: "cpc_group_count",
      header: tooltipHeader("CPC groups", marketTooltipCopy.topCpcGroupsInSelectedField),
      cell: ({ row }) => formatNumber(row.original.cpc_group_count),
    },
  ];
  const leadingJurisdictionColumns: DataTableColumn<MarketLeadingJurisdictionRow>[] = [
    {
      accessorKey: "wipo_field",
      header: tooltipHeader("Field", marketTooltipCopy.field),
      cell: ({ row }) => (
        <div className="grid gap-1">
          <strong className="text-slate-900">{row.original.wipo_field}</strong>
          <small className="text-[11px] uppercase tracking-[0.08em] text-slate-500">Rank #{row.original.field_rank_within_year}</small>
        </div>
      ),
    },
    {
      accessorKey: "jurisdiction_code",
      header: tooltipHeader("Jurisdiction", marketTooltipCopy.jurisdiction),
      cell: ({ row }) => <InfoPill tone="neutral">{row.original.jurisdiction_code}</InfoPill>,
    },
    {
      accessorKey: "jurisdiction_family_count_asof",
      header: tooltipHeader("Families", marketTooltipCopy.families),
      cell: ({ row }) => formatNumber(row.original.jurisdiction_family_count_asof),
    },
    {
      accessorKey: "jurisdiction_active_family_count_asof",
      header: tooltipHeader("Active", marketTooltipCopy.active),
      cell: ({ row }) => formatNumber(row.original.jurisdiction_active_family_count_asof),
    },
    {
      accessorKey: "jurisdiction_family_share_within_field_asof",
      header: tooltipHeader("Field share", marketTooltipCopy.fieldShare),
      cell: ({ row }) => formatPercent(row.original.jurisdiction_family_share_within_field_asof),
    },
  ];
  const applicationsGrantColumns: DataTableColumn<MarketApplicationGrantRow>[] = [
    {
      accessorKey: "as_of_year",
      header: tooltipHeader("Year", marketTooltipCopy.year),
      cell: ({ row }) => formatNumber(row.original.as_of_year),
    },
    {
      accessorKey: "jurisdiction_code",
      header: tooltipHeader("Jurisdiction", marketTooltipCopy.jurisdiction),
      cell: ({ row }) => <strong className="text-slate-900">{row.original.jurisdiction_code}</strong>,
    },
    {
      accessorKey: "application_count",
      header: tooltipHeader("Applications", marketTooltipCopy.applications),
      cell: ({ row }) => formatNumber(row.original.application_count),
    },
    {
      accessorKey: "grant_count",
      header: tooltipHeader("Grants", marketTooltipCopy.grants),
      cell: ({ row }) => formatNumber(row.original.grant_count),
    },
    {
      accessorKey: "total_event_count",
      header: tooltipHeader("Total events", marketTooltipCopy.totalEvents),
      cell: ({ row }) => formatNumber(row.original.total_event_count),
    },
  ];
  const cpcJurisdictionColumns: DataTableColumn<MarketSelectedSegment["cpc_jurisdictions"][number]>[] = [
    {
      accessorKey: "cpc_main_group",
      header: tooltipHeader("CPC main group", marketTooltipCopy.cpcMainGroup),
      cell: ({ row }) => <strong className="text-slate-900">{row.original.cpc_main_group}</strong>,
    },
    {
      accessorKey: "jurisdiction_code",
      header: tooltipHeader("Jurisdiction", marketTooltipCopy.jurisdiction),
      cell: ({ row }) => <InfoPill tone="neutral">{row.original.jurisdiction_code}</InfoPill>,
    },
    {
      accessorKey: "family_count_asof",
      header: tooltipHeader("Families", marketTooltipCopy.families),
      cell: ({ row }) => formatNumber(row.original.family_count_asof),
    },
    {
      accessorKey: "family_share_within_slice_asof",
      header: tooltipHeader("Slice share", marketTooltipCopy.sliceShare),
      cell: ({ row }) => formatPercent(row.original.family_share_within_slice_asof),
    },
    {
      accessorKey: "blocking_density_asof",
      header: tooltipHeader("Blocking", marketTooltipCopy.blocking),
      cell: ({ row }) => formatDecimal(row.original.blocking_density_asof, 1),
    },
  ];
  const cpcOwnerColumns: DataTableColumn<MarketCpcOwnerRow>[] = [
    {
      accessorKey: "owner_name",
      header: tooltipHeader("Owner", marketTooltipCopy.owner),
      cell: ({ row }) => (
        <div className="grid gap-1">
          <strong className="text-slate-900">{row.original.owner_name}</strong>
          <small className="text-[11px] uppercase tracking-[0.08em] text-slate-500">Rank #{row.original.leaderboard_rank}</small>
        </div>
      ),
    },
    {
      accessorKey: "owner_family_count_in_cpc_asof",
      header: tooltipHeader("Families", marketTooltipCopy.families),
      cell: ({ row }) => formatNumber(row.original.owner_family_count_in_cpc_asof),
    },
    {
      accessorKey: "owner_family_share_within_cpc_asof",
      header: tooltipHeader("CPC share", marketTooltipCopy.cpcShare),
      cell: ({ row }) => formatPercent(row.original.owner_family_share_within_cpc_asof),
    },
    {
      accessorKey: "owner_active_family_count_in_cpc_asof",
      header: tooltipHeader("Active", marketTooltipCopy.active),
      cell: ({ row }) => formatNumber(row.original.owner_active_family_count_in_cpc_asof),
    },
    {
      accessorKey: "avg_blocking_score_asof",
      header: tooltipHeader("Blocking", marketTooltipCopy.blocking),
      cell: ({ row }) => formatDecimal(row.original.avg_blocking_score_asof, 1),
    },
  ];
  const cpcCitingOwnerColumns: DataTableColumn<MarketCpcCitingOwnerRow>[] = [
    {
      accessorKey: "citing_owner_name",
      header: tooltipHeader("Citing owner", marketTooltipCopy.citingOwner),
      cell: ({ row }) => (
        <div className="grid gap-1">
          <strong className="text-slate-900">{row.original.citing_owner_name}</strong>
          <small className="text-[11px] uppercase tracking-[0.08em] text-slate-500">Rank #{row.original.leaderboard_rank}</small>
        </div>
      ),
    },
    {
      accessorKey: "citation_event_count",
      header: tooltipHeader("Events", marketTooltipCopy.events),
      cell: ({ row }) => formatNumber(row.original.citation_event_count),
    },
    {
      accessorKey: "citation_event_share_within_cpc_asof",
      header: tooltipHeader("Event share", marketTooltipCopy.eventShare),
      cell: ({ row }) => formatPercent(row.original.citation_event_share_within_cpc_asof),
    },
    {
      accessorKey: "distinct_citing_jurisdiction_count",
      header: tooltipHeader("Jurisdictions", marketTooltipCopy.jurisdictions),
      cell: ({ row }) => formatNumber(row.original.distinct_citing_jurisdiction_count),
    },
    {
      accessorKey: "cited_family_count",
      header: tooltipHeader("Cited families", marketTooltipCopy.citedFamilies),
      cell: ({ row }) => formatNumber(row.original.cited_family_count),
    },
    {
      accessorKey: "citation_lethality_sum",
      header: tooltipHeader("Lethality", marketTooltipCopy.lethality),
      cell: ({ row }) => formatDecimal(row.original.citation_lethality_sum, 1),
    },
  ];
  return (
    <div className={styles.workspace}>
      {error ? <p className="portfolio-error">{error}</p> : null}

      <div className={styles.pageSectionBar} role="tablist" aria-label="Market page sections">
        {sectionOptions.map((section) => {
          const isActive = activeSection === section.value;
          return (
            <button
              key={section.value}
              type="button"
              role="tab"
              aria-selected={isActive}
              className={clsx(styles.pageSectionButton, isActive && styles.pageSectionButtonActive)}
              onClick={() => updateQuery({ section: section.value })}
            >
              <strong>
                <PortfolioTooltipLabel label={section.label} tooltip={section.tooltip} />
              </strong>
              <span>{section.note}</span>
            </button>
          );
        })}
      </div>

      {activeSection === "overview" ? (
        <>
          {marketChronologySurface}

          <Surface
            title={<PortfolioTooltipLabel label="Field league table" tooltip={marketTooltipCopy.fieldLeagueTable} />}
            description="Primary selection surface across size, state, momentum, blocking density, and whitespace context."
            badge={
              <div className={styles.surfaceBadgeControls}>
                {marketOverviewBadgeMetrics.map((metric) => (
                  <SurfaceBadgeMetric
                    key={metric.key}
                    label={metric.label}
                    tooltip={metric.tooltip}
                    value={metric.value}
                  />
                ))}
              </div>
            }
          >
            {workspace.segments.length === 0 ? (
              <p className="portfolio-empty">No fields match the current state filter.</p>
            ) : (
              <DataTableShell
                columns={segmentColumns}
                data={workspace.segments}
                emptyMessage="No fields match the current state filter."
                getRowClassName={(segment) =>
                  workspace.filters.selected_segment === segment.wipo_industry_code ? "bg-amber-50/60" : undefined
                }
                getRowKey={(segment) => segment.segment_id}
              />
            )}
          </Surface>

          <Surface
            title={
              <PortfolioTooltipLabel
                label="Leading jurisdictions by field"
                tooltip={marketTooltipCopy.leadingJurisdictionsByField}
              />
            }
            description="Top protection-footprint jurisdictions inside each served field, kept separate from citing-side geography."
          >
            {leadingJurisdictionsLoading && leadingJurisdictionRows.length === 0 ? (
              <p className="portfolio-empty">Loading leading jurisdictions…</p>
            ) : leadingJurisdictionsError ? (
              <p className="portfolio-error">{leadingJurisdictionsError}</p>
            ) : leadingJurisdictionRows.length === 0 ? (
              <p className="portfolio-empty">No field-by-jurisdiction leaderboard rows are available.</p>
            ) : (
              <div className={styles.evidenceColumn}>
                <div className={styles.controlRow}>
                  <label className={styles.controlField}>
                    <PortfolioTooltipLabel label="Field" tooltip={marketTooltipCopy.fieldFilter} />
                    <select
                      aria-label="Leading jurisdiction field filter"
                      value={effectiveLeadingJurisdictionFieldFilter}
                      onChange={(event) => setLeadingJurisdictionFieldFilter(event.target.value)}
                    >
                      {leadingJurisdictionFieldOptions.map((option) => (
                        <option key={option} value={option}>
                          {option}
                        </option>
                      ))}
                    </select>
                  </label>

                  <div className={styles.controlField}>
                    <PortfolioTooltipLabel label="View" tooltip={marketTooltipCopy.view} />
                    <div className={styles.sectionToggle} role="tablist" aria-label="Leading jurisdictions view">
                      <button
                        type="button"
                        role="tab"
                        aria-selected={!isLeadingJurisdictionPieView}
                        className={clsx(styles.sectionToggleButton, !isLeadingJurisdictionPieView && styles.sectionToggleButtonActive)}
                        onClick={() => setLeadingJurisdictionView("table")}
                      >
                        <PortfolioTooltipLabel label="Table" tooltip={marketTooltipCopy.tableView} />
                      </button>
                      <button
                        type="button"
                        role="tab"
                        aria-selected={isLeadingJurisdictionPieView}
                        className={clsx(
                          styles.sectionToggleButton,
                          isLeadingJurisdictionPieView && styles.sectionToggleButtonActive,
                          !canShowLeadingJurisdictionPie && styles.sectionToggleButtonDisabled,
                        )}
                        onClick={() => setLeadingJurisdictionView("pie")}
                        disabled={!canShowLeadingJurisdictionPie}
                      >
                        <PortfolioTooltipLabel label="Pie" tooltip={marketTooltipCopy.pieView} />
                      </button>
                    </div>
                  </div>
                </div>

                {isLeadingJurisdictionPieView ? (
                  <div className={styles.leadingPieLayout}>
                    <article className={styles.leadingPieFigure}>
                      <div className={styles.leadingPieSummary}>
                        <div className={styles.globalHead}>
                          <strong>{effectiveLeadingJurisdictionFieldFilter}</strong>
                        </div>
                        <div className={styles.globalMetrics}>
                          <span>{formatNumber(filteredLeadingJurisdictionRows.length)} jurisdictions in current view</span>
                          <span>Pie view stays available only for a single field so the slices remain comparable.</span>
                        </div>
                      </div>

                      <div className={styles.leadingPieBody}>
                        <div className={styles.chartSurface}>
                          <ResponsiveContainer width="100%" height={320}>
                            <PieChart>
                              <Pie
                                data={filteredLeadingJurisdictionRows}
                                dataKey="jurisdiction_family_count_asof"
                                nameKey="jurisdiction_code"
                                innerRadius={62}
                                outerRadius={110}
                                stroke="rgba(255,255,255,0.94)"
                                strokeWidth={2}
                                paddingAngle={filteredLeadingJurisdictionRows.length > 1 ? 2 : 0}
                                isAnimationActive={false}
                              >
                                {filteredLeadingJurisdictionRows.map((row, index) => (
                                  <Cell
                                    key={`${row.wipo_field}-${row.jurisdiction_code}`}
                                    fill={leadingJurisdictionPiePalette[index % leadingJurisdictionPiePalette.length]}
                                  />
                                ))}
                              </Pie>
                              <Tooltip
                                formatter={(value: number, _name: string, item) => {
                                  const payload = item?.payload as MarketLeadingJurisdictionRow | undefined;
                                  return [
                                    `${formatNumber(value)} families`,
                                    payload ? `${payload.jurisdiction_code} · ${formatPercent(payload.jurisdiction_family_share_within_field_asof)}` : "Jurisdiction",
                                  ];
                                }}
                              />
                            </PieChart>
                          </ResponsiveContainer>
                        </div>

                        <div className={styles.leadingPieLegend}>
                          {filteredLeadingJurisdictionRows.map((row, index) => (
                            <article
                              key={`${row.wipo_field}-${row.jurisdiction_code}-legend`}
                              className={styles.leadingPieLegendItem}
                            >
                              <div className={styles.leadingPieLegendHeader}>
                                <span
                                  className={styles.leadingPieLegendSwatch}
                                  style={{ backgroundColor: leadingJurisdictionPiePalette[index % leadingJurisdictionPiePalette.length] }}
                                />
                                <strong>{row.jurisdiction_code}</strong>
                                <InfoPill tone="neutral">Rank #{row.field_rank_within_year}</InfoPill>
                              </div>
                              <div className={styles.leadingPieMetricGrid}>
                                <div className={styles.leadingPieMetric}>
                                  <PortfolioTooltipLabel
                                    label="Families"
                                    tooltip={marketTooltipCopy.families}
                                    className={styles.leadingPieMetricLabel}
                                  />
                                  <strong className={styles.leadingPieMetricValue}>
                                    {formatNumber(row.jurisdiction_family_count_asof)}
                                  </strong>
                                </div>
                                <div className={styles.leadingPieMetric}>
                                  <PortfolioTooltipLabel
                                    label="Active"
                                    tooltip={marketTooltipCopy.active}
                                    className={styles.leadingPieMetricLabel}
                                  />
                                  <strong className={styles.leadingPieMetricValue}>
                                    {formatNumber(row.jurisdiction_active_family_count_asof)}
                                  </strong>
                                </div>
                                <div className={styles.leadingPieMetric}>
                                  <PortfolioTooltipLabel
                                    label="Field share"
                                    tooltip={marketTooltipCopy.fieldShare}
                                    className={styles.leadingPieMetricLabel}
                                  />
                                  <strong className={styles.leadingPieMetricValue}>
                                    {formatPercent(row.jurisdiction_family_share_within_field_asof)}
                                  </strong>
                                </div>
                              </div>
                            </article>
                          ))}
                        </div>
                      </div>
                    </article>
                  </div>
                ) : (
                  <DataTableShell
                    columns={leadingJurisdictionColumns}
                    data={filteredLeadingJurisdictionRows}
                    emptyMessage="No leading-jurisdiction rows are available for the selected field."
                    getRowKey={(row) => `${row.wipo_field}-${row.field_rank_within_year}-${row.jurisdiction_code}`}
                  />
                )}
              </div>
            )}
          </Surface>
        </>
      ) : null}

      {activeSection === "analysis" ? (
        <>
          <Surface
            title={<PortfolioTooltipLabel label="Market filters" tooltip={marketTooltipCopy.marketFilters} />}
            description="Filter the bounded landscape, pick a field, then inspect the evidence below."
          >
            <div className={styles.controlRow}>
              <label className={styles.controlField}>
                <PortfolioTooltipLabel label="Market state" tooltip={marketTooltipCopy.marketState} />
                <select
                  aria-label="Market state"
                  value={workspace.filters.market_state}
                  onChange={(event) => updateQuery({ state: event.target.value, segment: null })}
                >
                  {workspace.filters.state_options.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label} ({option.count})
                    </option>
                  ))}
                </select>
              </label>
              <label className={styles.controlField}>
                <PortfolioTooltipLabel label="Selected field" tooltip={marketTooltipCopy.selectedField} />
                <select
                  aria-label="Selected field"
                  value={workspace.filters.selected_segment ?? ""}
                  onChange={(event) => updateQuery({ segment: event.target.value || null })}
                >
                  {workspace.filters.segment_options.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
              <div className={styles.controlNote}>
                <PortfolioTooltipLabel label="Freshness" tooltip={marketTooltipCopy.freshness} />
                <strong>{formatDate(workspace.scope.snapshot_date)}</strong>
                <p>State labels default to the latest comparable year even when newer priority years remain incomplete.</p>
              </div>
            </div>
          </Surface>

          <section className={styles.sectionBreak} aria-label="Selected field drilldown">
            <div className={styles.sectionBreakCopy}>
              <span className={styles.sectionBreakEyebrow}>Selected field</span>
              <strong className={styles.sectionBreakTitle}>
                {selected ? `${selected.wipo_industry_code} drilldown` : "Field drilldown"}
              </strong>
              <p className={styles.sectionBreakDescription}>
                The controls above set the field-specific layer below, separate from the market-wide selection layer above.
              </p>
            </div>
            {selected ? (
              <div className={styles.sectionBreakMeta}>
                <StatusPill tone={toneForState(selected.market_state)}>{prettyLabel(selected.market_state)}</StatusPill>
              </div>
            ) : (
              <div className={styles.sectionBreakMeta}>
                <InfoPill tone="neutral">Choose one field to open the field-specific layer</InfoPill>
              </div>
            )}
          </section>

          <Surface
            className={styles.summaryDrawer}
            title={
              <PortfolioTooltipLabel
                label={selected ? `${selected.wipo_industry_code} summary` : "Selected field summary"}
                tooltip={marketTooltipCopy.selectedFieldSummary}
              />
            }
            description="Current read for the selected field before drilling into competition or technology."
            badge={
              selected ? (
                <StatusPill tone={toneForState(selected.market_state)}>{prettyLabel(selected.market_state)}</StatusPill>
              ) : undefined
            }
          >
            {selected ? (
              <div className={styles.drawerStack}>
                <div className={styles.fieldAnalyticsGrid}>
                  <article className={clsx(styles.fieldAnalyticsCard, styles.fieldAnalyticsCardScale)}>
                    <MetricLabel
                      label="Field scale"
                      tooltip={marketTooltipCopy.fieldScale}
                      className={styles.fieldAnalyticsLabel}
                    />
                    <strong className={styles.fieldAnalyticsValue}>{formatNumber(selected.summary.segment_family_count_stock_asof)}</strong>
                    <p className={styles.fieldAnalyticsSupport}>
                      {formatNumber(selected.summary.segment_active_family_count_asof)} active families
                    </p>
                    <div className={styles.fieldMeterTrack}>
                      <span className={styles.fieldMeterFill} style={{ width: `${Math.max(8, Math.min(100, activeShare * 100))}%` }} />
                    </div>
                    <div className={styles.fieldAnalyticsFooter}>
                      <MetricLabel
                        label="Active share"
                        tooltip={marketTooltipCopy.activeShare}
                        className={styles.fieldAnalyticsFooterLabel}
                      />
                      <strong>{formatPercent(activeShare)}</strong>
                    </div>
                  </article>

                  <article className={clsx(styles.fieldAnalyticsCard, styles.fieldAnalyticsCardPressure)}>
                    <MetricLabel
                      label="Competitive pressure"
                      tooltip={marketTooltipCopy.competitivePressure}
                      className={styles.fieldAnalyticsLabel}
                    />
                    <strong className={styles.fieldAnalyticsValue}>{formatNumber(selected.summary.segment_owner_count_hist_proxy_asof)}</strong>
                    <p className={styles.fieldAnalyticsSupport}>owners currently shaping this field</p>
                    <div className={styles.fieldMeterTrack}>
                      <span className={styles.fieldMeterFill} style={{ width: `${Math.max(8, Math.min(100, topOwnerShare * 100))}%` }} />
                    </div>
                    <div className={styles.fieldAnalyticsFooter}>
                      <MetricLabel
                        label="Top owner share"
                        tooltip={marketTooltipCopy.topOwnerShare}
                        className={styles.fieldAnalyticsFooterLabel}
                      />
                      <strong>{formatPercent(topOwnerShare)}</strong>
                    </div>
                  </article>

                  <article className={clsx(styles.fieldAnalyticsCard, styles.fieldAnalyticsCardDefense)}>
                    <MetricLabel
                      label="Defensive posture"
                      tooltip={marketTooltipCopy.defensivePosture}
                      className={styles.fieldAnalyticsLabel}
                    />
                    <strong className={styles.fieldAnalyticsValue}>{formatDecimal(selected.summary.segment_blocking_density_asof, 1)}</strong>
                    <p className={styles.fieldAnalyticsSupport}>blocking density across the current field footprint</p>
                    <div className={styles.fieldAnalyticsSplit}>
                      <div>
                        <MetricLabel
                          label="Active jurisdiction share"
                          tooltip={marketTooltipCopy.activeJurisdictionShare}
                          className={styles.fieldAnalyticsSplitLabel}
                        />
                        <strong>{formatPercent(selected.summary.segment_active_jurisdiction_share_asof)}</strong>
                      </div>
                      <div>
                        <MetricLabel
                          label="Field balance"
                          tooltip={marketTooltipCopy.fieldBalance}
                          className={styles.fieldAnalyticsSplitLabel}
                        />
                        <strong>{formatPercent(fieldBalance)}</strong>
                      </div>
                    </div>
                  </article>

                  <article className={clsx(styles.fieldAnalyticsCard, styles.fieldAnalyticsCardMomentum)}>
                    <MetricLabel
                      label="Momentum"
                      tooltip={marketTooltipCopy.momentum}
                      className={styles.fieldAnalyticsLabel}
                    />
                    <strong className={styles.fieldAnalyticsValue}>{formatSignedPercent(latestMomentumDelta)}</strong>
                    <div className={styles.fieldMomentumRow}>
                      <Sparkline points={momentumRows.slice(-8)} />
                      <div className={styles.fieldMomentumMeta}>
                        <MetricLabel
                          label="Latest year"
                          tooltip={marketTooltipCopy.latestYear}
                          className={styles.fieldMomentumMetaLabel}
                        />
                        <strong>{latestMomentumRow ? formatNumber(latestMomentumRow.year) : "—"}</strong>
                      </div>
                    </div>
                    <div className={styles.fieldAnalyticsSplit}>
                      <div>
                        <MetricLabel
                          label="Current families"
                          tooltip={marketTooltipCopy.currentFamilies}
                          className={styles.fieldAnalyticsSplitLabel}
                        />
                        <strong>{latestMomentumRow ? formatNumber(latestMomentumRow.family_count) : "—"}</strong>
                      </div>
                      <div>
                        <MetricLabel
                          label="Market median"
                          tooltip={marketTooltipCopy.marketMedian}
                          className={styles.fieldAnalyticsSplitLabel}
                        />
                        <strong>{marketMedianCount == null ? "—" : formatNumber(marketMedianCount)}</strong>
                      </div>
                      <div>
                        <MetricLabel
                          label="Vs market median"
                          tooltip={marketTooltipCopy.vsMarketMedian}
                          className={styles.fieldAnalyticsSplitLabel}
                        />
                        <strong>{marketMedianGap == null ? "—" : formatSignedNumber(marketMedianGap)}</strong>
                      </div>
                    </div>
                  </article>
                </div>

                {selected.state_rationale ? (
                  <article className={styles.narrativeCard}>
                    <PortfolioTooltipLabel
                      label="Field rationale"
                      tooltip={marketTooltipCopy.fieldRationale}
                      className={styles.narrativeLabel}
                    />
                    <strong>{selected.state_rationale.headline}</strong>
                    <p>{selected.state_rationale.detail}</p>
                    <div className={styles.evidenceList}>
                      {selected.state_rationale.evidence.map((item) => (
                        <span key={item} className={styles.evidenceItem}>
                          {item}
                        </span>
                      ))}
                    </div>
                  </article>
                ) : null}
              </div>
            ) : (
              <p className="portfolio-empty">Select a field to open the summary drawer.</p>
            )}
          </Surface>

          <div className={styles.tabBar} role="tablist" aria-label="Market evidence views">
            {tabOptions.map((tab) => {
              const isActive = activeTab === tab.value;
              return (
                <button
                  key={tab.value}
                  type="button"
                  role="tab"
                  aria-selected={isActive}
                  className={clsx(styles.tabButton, isActive && styles.tabButtonActive)}
                  onClick={() => updateQuery({ tab: tab.value })}
                >
                  <strong>
                    <PortfolioTooltipLabel label={tab.label} tooltip={tab.tooltip} />
                  </strong>
                  <span>{tab.note}</span>
                </button>
              );
            })}
          </div>
        </>
      ) : null}

      {activeSection === "analysis" && activeTab === "competition" ? (
        <DeferredClientComponent
          loader={loadMarketCompetitionSection}
          componentProps={{
            citationRows,
            ownerRows,
            familyRows,
            attackerRows,
            jurisdictionRows,
            jurisdictionColumns,
            reducedContextMode,
          }}
          fallback={<p className="portfolio-empty">Loading competition analysis…</p>}
        />
      ) : null}

      {activeSection === "analysis" && activeTab === "jurisdictions" ? (
        <DeferredClientComponent
          loader={loadMarketJurisdictionsSection}
          componentProps={{
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
            onApplicationsGrantJurisdictionFilterChange: setApplicationsGrantJurisdictionFilter,
            onApplicationsGrantViewChange: setApplicationsGrantView,
          }}
          fallback={<p className="portfolio-empty">Loading jurisdiction analysis…</p>}
        />
      ) : null}

      {activeSection === "analysis" && activeTab === "technology" ? (
        <DeferredClientComponent
          loader={loadMarketTechnologySection}
          componentProps={{
            reducedContextMode,
            effectiveTechnologyYear,
            technologyYearOptions,
            selectedFieldCode: selected?.wipo_industry_code,
            technologyCpcTrendsLoading,
            technologyCpcTrendsError,
            technologyCpcRows,
            cpcColumns,
            technologyJurisdictionFilter: effectiveTechnologyJurisdictionFilter,
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
            onTechnologyYearFilterChange: setTechnologyYearFilter,
            onTechnologyJurisdictionFilterChange: setTechnologyJurisdictionFilter,
            onTechnologyOwnerCpcFilterChange: setTechnologyOwnerCpcFilter,
          }}
          fallback={<p className="portfolio-empty">Loading technology analysis…</p>}
        />
      ) : null}

    </div>
  );
}
