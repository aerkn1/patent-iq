"use client";

import clsx from "clsx";
import Link from "next/link";
import { useState } from "react";
import {
  Bar,
  CartesianGrid,
  Cell,
  ComposedChart,
  Line,
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
import { InfoPill } from "@/components/ui/data-pill";
import { Surface } from "@/components/ui/surface";
import { workspaceTooltipCopy } from "@/lib/content/workspace-tooltips";
import { chartTokens } from "@/lib/design/chart-tokens";
import type { MarketSelectedSegment, MarketTopOwnerRow } from "@/lib/types/market-v2";

import styles from "./market-workspace.module.css";

type OwnerPresenceView = "share" | "blocking";

type MarketAnalysisCompetitionSectionProps = {
  citationRows: MarketSelectedSegment["citation_trend"];
  ownerRows: MarketTopOwnerRow[];
  familyRows: MarketSelectedSegment["top_families"];
  attackerRows: MarketSelectedSegment["top_attackers"];
  jurisdictionRows: MarketSelectedSegment["top_jurisdictions"];
  jurisdictionColumns: DataTableColumn<MarketSelectedSegment["top_jurisdictions"][number]>[];
  reducedContextMode: boolean;
};

const marketTooltipCopy = workspaceTooltipCopy.marketView;

function prettyLabel(value: string): string {
  return value.replace(/_/g, " ");
}

function OwnerPresenceList({ owners }: { owners: MarketTopOwnerRow[] }) {
  const [view, setView] = useState<OwnerPresenceView>("share");

  if (owners.length === 0) {
    return <p className="portfolio-empty">No owner leaderboard rows are available for this field.</p>;
  }

  const palette = [
    chartTokens.rank.primary,
    chartTokens.rank.secondary,
    chartTokens.rank.tertiary,
    chartTokens.series.info,
    chartTokens.series.success,
    chartTokens.series.warning,
    chartTokens.series.critical,
    chartTokens.series.neutral,
  ];
  const rankedByShare = [...owners].sort(
    (left, right) => right.in_segment_family_share_hist_proxy - left.in_segment_family_share_hist_proxy,
  );
  const rankedByBlocking = [...owners].sort(
    (left, right) =>
      right.avg_blocking_score_asof - left.avg_blocking_score_asof ||
      right.in_segment_family_share_hist_proxy - left.in_segment_family_share_hist_proxy,
  );
  const maxBlocking = Math.max(...rankedByBlocking.map((owner) => owner.avg_blocking_score_asof), 0.01);
  const pieBaseRows = rankedByShare.slice(0, 6);
  const otherRows = rankedByShare.slice(6);
  const otherShare = otherRows.reduce((total, owner) => total + owner.in_segment_family_share_hist_proxy, 0);
  const pieRows =
    otherShare > 0
      ? [
          ...pieBaseRows.map((owner) => ({
            key: owner.owner_name,
            label: owner.owner_name,
            value: owner.in_segment_family_share_hist_proxy,
            families: owner.in_segment_family_count_hist_proxy,
          })),
          {
            key: "Other owners",
            label: "Other owners",
            value: otherShare,
            families: otherRows.reduce((total, owner) => total + owner.in_segment_family_count_hist_proxy, 0),
          },
        ]
      : pieBaseRows.map((owner) => ({
          key: owner.owner_name,
          label: owner.owner_name,
          value: owner.in_segment_family_share_hist_proxy,
          families: owner.in_segment_family_count_hist_proxy,
        }));

  return (
    <div className={styles.ownerPresencePanel}>
      <div className={styles.controlField}>
        <PortfolioTooltipLabel label="View" tooltip={marketTooltipCopy.view} />
        <div className={styles.sectionToggle} role="tablist" aria-label="Top owner presence view">
          <button
            type="button"
            role="tab"
            aria-selected={view === "share"}
            className={clsx(styles.sectionToggleButton, view === "share" && styles.sectionToggleButtonActive)}
            onClick={() => setView("share")}
          >
            <PortfolioTooltipLabel label="Field share" tooltip={marketTooltipCopy.fieldShareView} />
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={view === "blocking"}
            className={clsx(styles.sectionToggleButton, view === "blocking" && styles.sectionToggleButtonActive)}
            onClick={() => setView("blocking")}
          >
            <PortfolioTooltipLabel label="Avg blocking" tooltip={marketTooltipCopy.avgBlockingView} />
          </button>
        </div>
      </div>

      {view === "share" ? (
        <div className={styles.ownerShareView}>
          <div className={styles.ownerShareChart}>
            <ResponsiveContainer width="100%" height={290}>
              <PieChart>
                <Pie
                  data={pieRows}
                  dataKey="value"
                  nameKey="label"
                  innerRadius={62}
                  outerRadius={104}
                  stroke="rgba(255,255,255,0.94)"
                  strokeWidth={2}
                  paddingAngle={pieRows.length > 1 ? 2 : 0}
                  isAnimationActive={false}
                >
                  {pieRows.map((row, index) => (
                    <Cell key={`${row.key}-${index}`} fill={palette[index % palette.length]} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(value: number, _name: string, item) => {
                    const payload = item?.payload as { families?: number } | undefined;
                    return [`${formatPercent(value)}`, `${formatNumber(payload?.families ?? 0)} families`];
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className={styles.ownerShareLegend}>
            {pieRows.map((row, index) => (
              <div
                key={`${row.key}-legend`}
                className={styles.ownerShareLegendItem}
                style={{ ["--owner-color" as string]: palette[index % palette.length] }}
              >
                <span className={styles.ownerShareLegendIdentity}>
                  <span className={styles.ownerShareLegendSwatch} style={{ backgroundColor: palette[index % palette.length] }} />
                  <span>{row.label}</span>
                </span>
                <strong>{formatPercent(row.value)}</strong>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className={styles.leaderboardList}>
          {rankedByBlocking.map((owner) => (
            <article key={`${owner.owner_name}-${owner.leaderboard_rank}`} className={clsx(styles.leaderboardCard, styles.leaderboardCardOwner)}>
              <div className={styles.leaderboardHeader}>
                <div className={styles.leaderboardIdentity}>
                  <span className={styles.leaderboardRank}>#{owner.leaderboard_rank}</span>
                  <div className={styles.leaderboardCopy}>
                    {owner.owner_id ? (
                      <Link href={`/portfolio/${encodeURIComponent(owner.owner_id)}`} className={styles.ownerLink}>
                        {owner.owner_name}
                      </Link>
                    ) : (
                      <strong>{owner.owner_name}</strong>
                    )}
                    <span>{formatNumber(owner.in_segment_family_count_hist_proxy)} families in field</span>
                  </div>
                </div>
                <div className={styles.leaderboardValueBlock}>
                  <PortfolioTooltipLabel label="Avg blocking" tooltip={marketTooltipCopy.avgBlocking} />
                  <strong>{formatDecimal(owner.avg_blocking_score_asof, 1)}</strong>
                </div>
              </div>

              <div className={styles.leaderboardTrack}>
                <span
                  className={styles.leaderboardFill}
                  style={{ width: `${Math.max(8, Math.min(100, (owner.avg_blocking_score_asof / maxBlocking) * 100))}%` }}
                />
              </div>

              <div className={styles.leaderboardMeta}>
                <span>
                  {formatPercent(owner.in_segment_family_share_hist_proxy)}{" "}
                  <PortfolioTooltipLabel label="field share" tooltip={marketTooltipCopy.fieldShare} />
                </span>
                <span>
                  {formatDecimal(owner.total_blocking_score_asof, 1)}{" "}
                  <PortfolioTooltipLabel label="total blocking" tooltip={marketTooltipCopy.totalBlocking} />
                </span>
                <div className={styles.leaderboardMetaItem}>
                  <PortfolioTooltipLabel label="Status" tooltip={marketTooltipCopy.status} />
                  <InfoPill tone="neutral">{prettyLabel(owner.family_composite_status_asof)}</InfoPill>
                </div>
              </div>
            </article>
          ))}
        </div>
      )}
    </div>
  );
}

function FamilyPresenceList({ families }: { families: MarketSelectedSegment["top_families"] }) {
  if (families.length === 0) {
    return <p className="portfolio-empty">No top-family rows are available for the selected field.</p>;
  }

  const maxPresence = Math.max(...families.map((family) => family.field_presence_weight_asof), 0.01);

  return (
    <div className={styles.leaderboardList}>
      {families.map((family) => (
        <article key={`${family.docdb_family_id}-${family.leaderboard_rank}`} className={clsx(styles.leaderboardCard, styles.leaderboardCardFamily)}>
          <div className={styles.leaderboardHeader}>
            <div className={styles.leaderboardIdentity}>
              <span className={styles.leaderboardRank}>#{family.leaderboard_rank}</span>
              <div className={styles.leaderboardCopy}>
                <Link href={`/family/${family.docdb_family_id}`} className={styles.ownerLink}>
                  {String(family.docdb_family_id)}
                </Link>
                <span className={styles.familyOwnerLine}>
                  {family.owner_id ? (
                    <Link href={`/portfolio/${encodeURIComponent(family.owner_id)}`} className={styles.ownerLink}>
                      {family.owner_name}
                    </Link>
                  ) : (
                    family.owner_name
                  )}
                </span>
              </div>
            </div>
            <div className={styles.leaderboardValueBlock}>
              <PortfolioTooltipLabel label="Blocking percentile" tooltip={marketTooltipCopy.blocking} />
              <strong>{formatDecimal(family.avg_blocking_score_asof, 1)}</strong>
            </div>
          </div>

          <div className={styles.familyMetricStrip}>
            <div className={styles.familyMetricChip}>
              <PortfolioTooltipLabel label="Field presence" tooltip={marketTooltipCopy.fieldPresence} />
              <strong>{formatPercent(family.field_presence_weight_asof)}</strong>
            </div>
            <div className={styles.familyMetricChip}>
              <PortfolioTooltipLabel label="Total blocking" tooltip={marketTooltipCopy.totalBlocking} />
              <strong>{formatDecimal(family.total_blocking_score_asof, 1)}</strong>
            </div>
            <div className={styles.familyMetricChip}>
              <PortfolioTooltipLabel label="Status" tooltip={marketTooltipCopy.status} />
              <InfoPill tone="neutral">{prettyLabel(family.family_composite_status_asof)}</InfoPill>
            </div>
          </div>

          <div className={styles.familyPresenceRail}>
            <div className={styles.familyPresenceHeader}>
              <PortfolioTooltipLabel label="Field presence weight" tooltip={marketTooltipCopy.fieldPresenceWeight} />
              <strong>{formatPercent(family.field_presence_weight_asof)}</strong>
            </div>
            <div className={styles.leaderboardTrack}>
              <span
                className={styles.leaderboardFill}
                style={{ width: `${Math.max(10, Math.min(100, (family.field_presence_weight_asof / maxPresence) * 100))}%` }}
              />
            </div>
          </div>
        </article>
      ))}
    </div>
  );
}

function CitationOwnerPresenceList({ owners }: { owners: MarketSelectedSegment["top_attackers"] }) {
  if (owners.length === 0) {
    return <p className="portfolio-empty">No citing-owner rows are available for this field.</p>;
  }

  const maxPressure = Math.max(...owners.map((owner) => owner.attacker_pressure_index), 0.01);

  return (
    <div className={styles.leaderboardList}>
      {owners.map((owner, index) => (
        <article key={`${owner.citing_assignee}-${owner.as_of_year}-${index}`} className={clsx(styles.leaderboardCard, styles.leaderboardCardCitation)}>
          <div className={styles.leaderboardHeader}>
            <div className={styles.leaderboardIdentity}>
              <span className={styles.leaderboardRank}>#{index + 1}</span>
              <div className={styles.leaderboardCopy}>
                <strong>{owner.citing_assignee}</strong>
                <span>{formatNumber(owner.citation_count)} citations into the selected field</span>
              </div>
            </div>
          </div>

          <div className={styles.citationMetricStrip}>
            <div className={styles.citationMetricChip}>
              <PortfolioTooltipLabel label="Pressure" tooltip={marketTooltipCopy.pressure} />
              <strong>{formatDecimal(owner.attacker_pressure_index, 1)}</strong>
            </div>
            <div className={styles.citationMetricChip}>
              <PortfolioTooltipLabel label="Citations" tooltip={marketTooltipCopy.citations} />
              <strong>{formatNumber(owner.citation_count)}</strong>
            </div>
            <div className={styles.citationMetricChip}>
              <PortfolioTooltipLabel label="Jurisdictions" tooltip={marketTooltipCopy.jurisdictions} />
              <strong>{formatNumber(owner.distinct_citing_jurisdiction_count)}</strong>
            </div>
            <div className={styles.citationMetricChip}>
              <PortfolioTooltipLabel label="Last seen" tooltip={marketTooltipCopy.lastSeen} />
              <strong>{owner.as_of_year}</strong>
            </div>
          </div>

          <div className={styles.citationPressureRail}>
            <div className={styles.citationPressureHeader}>
              <PortfolioTooltipLabel label="Pressure intensity" tooltip={marketTooltipCopy.pressureIntensity} />
            </div>
            <div className={styles.leaderboardTrack}>
              <span
                className={styles.leaderboardFill}
                style={{ width: `${Math.max(10, Math.min(100, (owner.attacker_pressure_index / maxPressure) * 100))}%` }}
              />
            </div>
          </div>
        </article>
      ))}
    </div>
  );
}

export function MarketAnalysisCompetitionSection({
  citationRows,
  ownerRows,
  familyRows,
  attackerRows,
  jurisdictionRows,
  jurisdictionColumns,
  reducedContextMode,
}: MarketAnalysisCompetitionSectionProps) {
  return (
    <div className={styles.tabStack}>
      <Surface
        className={styles.featureSurface}
        title={<PortfolioTooltipLabel label="Citation pressure chronology" tooltip={marketTooltipCopy.citationPressureChronology} />}
        description="Incoming citation activity into the selected field. Bars show citation events, while the line shows the field's pressure rank within each year."
      >
        {citationRows.length === 0 ? (
          <p className="portfolio-empty">No citation chronology is available for the selected field.</p>
        ) : (
          <div className={styles.chartSurface}>
            <ResponsiveContainer width="100%" height={320}>
              <ComposedChart data={citationRows} margin={{ top: 12, right: 12, left: 0, bottom: 4 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="as_of_year" />
                <YAxis yAxisId="left" tickFormatter={(value: number) => formatDecimal(value, 0)} />
                <YAxis yAxisId="right" orientation="right" tickFormatter={(value: number) => formatNumber(value)} />
                <Tooltip
                  formatter={(value: number, name: string) => {
                    if (name === "citation_pressure_index") {
                      return [formatDecimal(value, 1), "Pressure rank"];
                    }
                    return [formatNumber(value), "Citation events"];
                  }}
                />
                <Bar
                  yAxisId="right"
                  dataKey="citation_event_count"
                  fill="rgba(63, 110, 150, 0.5)"
                  stroke="rgba(42, 79, 122, 0.92)"
                  strokeWidth={1}
                  barSize={18}
                  radius={[10, 10, 0, 0]}
                />
                <Line
                  yAxisId="left"
                  type="monotone"
                  dataKey="citation_pressure_index"
                  stroke={chartTokens.series.warning}
                  strokeWidth={2.5}
                  dot={false}
                />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        )}
      </Surface>

      <div className={styles.detailGrid}>
        {!reducedContextMode ? (
          <Surface
            className={styles.detailSurface}
            title={<PortfolioTooltipLabel label="Top owner presence" tooltip={marketTooltipCopy.topOwnerPresence} />}
            description="Current owner presence inside the selected field, with share and blocking context kept separate from the market state itself."
          >
            <OwnerPresenceList owners={ownerRows} />
          </Surface>
        ) : null}

        <Surface
          className={styles.detailSurface}
          title={
            <PortfolioTooltipLabel
              label="Top families in selected field"
              tooltip={marketTooltipCopy.topFamiliesInSelectedField}
            />
          }
          description="Highest-blocking families inside the selected market field, with current owner attached as the drilldown anchor."
        >
          <FamilyPresenceList families={familyRows} />
        </Surface>
      </div>

      <div className={styles.detailGrid}>
        <Surface
          className={styles.detailSurface}
          title={<PortfolioTooltipLabel label="Top citing owners" tooltip={marketTooltipCopy.topCitingOwners} />}
          description="Latest external owners citing into the selected field, ranked by attacker-pressure index."
        >
          <CitationOwnerPresenceList owners={attackerRows} />
        </Surface>

        <Surface
          className={styles.detailSurface}
          title={
            <PortfolioTooltipLabel
              label="Top citing jurisdictions"
              tooltip={marketTooltipCopy.topCitingJurisdictions}
            />
          }
          description="Latest citing-side geography for the selected field, ranked by clean citation pressure."
        >
          {jurisdictionRows.length === 0 ? (
            <p className="portfolio-empty">No citing-jurisdiction rows are available for this field.</p>
          ) : (
            <DataTableShell
              columns={jurisdictionColumns}
              data={jurisdictionRows}
              emptyMessage="No citing-jurisdiction rows are available for this field."
              getRowKey={(row) => `${row.jurisdiction_code}-${row.as_of_year}`}
            />
          )}
        </Surface>
      </div>
    </div>
  );
}
