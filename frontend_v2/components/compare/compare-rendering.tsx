"use client";

import clsx from "clsx";
import Link from "next/link";

import { formatDecimal, formatNumber, formatPercent } from "@/components/portfolio/portfolio-format";
import { FieldPill, InfoPill, StatusPill, TagPill } from "@/components/ui/data-pill";
import type {
  CompareFieldOverlapRow,
  CompareForecastRow,
  CompareIdentity,
  CompareIdentityContext,
  CompareMeta,
  CompareMetricRow,
  CompareSupportRow,
  PortfolioCompareTopFamilyRow,
} from "@/lib/types/compare-v2";

import styles from "./compare-workspace.module.css";

export type CompareTab = "overview" | "technology" | "outlook" | "evidence";
export type CompareTabSpec = { value: CompareTab; label: string; note: string };
export type CompareTimesliceProfileDimension = {
  key: string;
  label: string;
  note?: string | null;
  displayKind: "count" | "decimal" | "percent";
  leftValue: number | null;
  rightValue: number | null;
  leftScore: number;
  rightScore: number;
};

export const COMPARE_TABS: CompareTabSpec[] = [
  { value: "overview", label: "Overview", note: "Summary, lenses, and deltas" },
  { value: "technology", label: "Technology", note: "Field overlap and divergence" },
  { value: "outlook", label: "Outlook", note: "Forecast intervals and direction" },
  { value: "evidence", label: "Evidence", note: "Support rows and caveats" },
];

function compareValue(
  value: number | string | null | undefined,
  displayKind: CompareMetricRow["displayKind"] | CompareForecastRow["displayKind"],
  key?: string,
): string {
  if (value == null) {
    return "—";
  }
  if (typeof value === "string") {
    return value;
  }
  if (key === "legal_durability") {
    return `${formatDecimal(value, 1)} / 100`;
  }
  if (displayKind === "count") {
    return formatNumber(value);
  }
  if (displayKind === "percent") {
    return formatPercent(value);
  }
  return formatDecimal(value, 2);
}

function compareDelta(value?: number | null, displayKind: CompareMetricRow["displayKind"] = "decimal", key?: string): string {
  if (value == null || Number.isNaN(value)) {
    return "No delta";
  }
  const prefix = value > 0 ? "+" : "";
  if (key === "legal_durability") {
    return `${prefix}${formatDecimal(value, 1)} pts`;
  }
  if (displayKind === "count") {
    return `${prefix}${formatNumber(value)}`;
  }
  if (displayKind === "percent") {
    return `${prefix}${formatPercent(value)}`;
  }
  return `${prefix}${formatDecimal(value, 2)}`;
}

function rangeLabel(low?: number | null, high?: number | null, displayKind: CompareForecastRow["displayKind"] = "decimal"): string {
  if (low == null || high == null) {
    return "Interval unavailable";
  }
  return `${compareValue(low, displayKind)} to ${compareValue(high, displayKind)}`;
}

function supportMetricValue(label: string | null | undefined, value: number | string | null | undefined): string {
  if (value == null) {
    return "—";
  }
  if (typeof value === "string") {
    return value;
  }
  const normalized = (label ?? "").toLowerCase();
  if (normalized.includes("share") || normalized.includes("coverage")) {
    return formatPercent(value);
  }
  if (normalized.includes("count") || normalized.includes("famil")) {
    return formatNumber(value);
  }
  return formatDecimal(value, 2);
}

function overlapTone(presence: string): "accent" | "neutral" | "warning" {
  if (presence === "shared") {
    return "accent";
  }
  if (presence === "empty") {
    return "neutral";
  }
  return "warning";
}

function supportTone(value?: string | null): "positive" | "warning" | "critical" | "neutral" {
  const normalized = (value ?? "").toLowerCase();
  if (normalized.includes("dominant") || normalized.includes("strong") || normalized.includes("active")) {
    return "positive";
  }
  if (normalized.includes("support") || normalized.includes("limited") || normalized.includes("monitor")) {
    return "warning";
  }
  if (normalized.includes("inactive") || normalized.includes("dead")) {
    return "critical";
  }
  return "neutral";
}

function compactWinnerLabel(label: string | undefined, fallback: string): string {
  const text = label?.trim();
  if (!text) {
    return fallback;
  }
  return text.length > 28 ? `${text.slice(0, 28)}…` : text;
}

function winnerLabel(value: CompareMetricRow["winner"] | null | undefined, leftLabel?: string, rightLabel?: string): string {
  if (value === "left") {
    return `${compactWinnerLabel(leftLabel, "Left")} leads`;
  }
  if (value === "right") {
    return `${compactWinnerLabel(rightLabel, "Right")} leads`;
  }
  return "Balanced";
}

function sideContext(contexts: CompareIdentityContext[], side: "left" | "right") {
  return contexts.find((item) => item.side === side) ?? null;
}

function statusTone(value: string): "positive" | "warning" | "critical" | "neutral" {
  const normalized = value.toLowerCase();
  if (normalized.includes("active")) {
    return "positive";
  }
  if (normalized.includes("pending")) {
    return "warning";
  }
  if (normalized.includes("dead") || normalized.includes("lapsed") || normalized.includes("abandon")) {
    return "critical";
  }
  return "neutral";
}

export function CompareHeader(props: {
  compareLabel: string;
  leftEntity: CompareIdentity | null;
  rightEntity: CompareIdentity | null;
  identityContext: CompareIdentityContext[];
  meta: CompareMeta;
  metaItems?: string[];
}) {
  const left = sideContext(props.identityContext, "left");
  const right = sideContext(props.identityContext, "right");

  const renderSide = (side: "left" | "right", entity: CompareIdentity | null, context: CompareIdentityContext | null) => (
    <article className={styles.compareSideCard}>
      <span className={styles.compareSideLabel}>
        {entity?.pageKind === "portfolio" ? "Portfolio" : entity?.pageKind === "family" ? "Family" : "Compared entity"}
      </span>
      <strong className={styles.compareSideTitle}>{context?.title ?? entity?.label ?? "Pending"}</strong>
      {context?.subtitle ? <p className={styles.compareSideSubtitle}>{context.subtitle}</p> : null}
      <div className={styles.compareBadgeRow}>
        {(context?.badges ?? []).map((badge) => (
          <TagPill key={`${side}-${badge}`} tone="neutral">
            {badge}
          </TagPill>
        ))}
      </div>
      {context?.href ? (
        <Link href={context.href} className={styles.compareSideAction}>
          Open source page
        </Link>
      ) : null}
    </article>
  );

  return (
    <section className={styles.compareHero}>
      {renderSide("left", props.leftEntity, left)}
      {renderSide("right", props.rightEntity, right)}
    </section>
  );
}

export function ComparePortfolioTopFamilyFaceoff(props: {
  rows: PortfolioCompareTopFamilyRow[];
  leftLabel: string;
  rightLabel: string;
}) {
  if (props.rows.length === 0) {
    return <p className={styles.emptyState}>No top-family preview rows are available for this compare.</p>;
  }

  const groups = [
    { side: "left" as const, title: props.leftLabel, rows: props.rows.filter((row) => row.side === "left") },
    { side: "right" as const, title: props.rightLabel, rows: props.rows.filter((row) => row.side === "right") },
  ].filter((group) => group.rows.length > 0);

  return (
    <div className={styles.previewGrid}>
      {groups.map((group) => (
        <article key={group.side} className={styles.previewCard}>
          <div className={styles.previewHeader}>
            <span className={styles.entityLabel}>Portfolio</span>
            <strong>{group.title}</strong>
          </div>
          <div className={styles.previewRows}>
            {group.rows.map((row) => (
              <article key={`${row.side}-${row.rank}-${row.familyId}`} className={styles.previewRow}>
                <div className={styles.previewRowHead}>
                  <div className={styles.previewIdentity}>
                    <strong>Family {row.familyId}</strong>
                    <span>{row.primaryField}</span>
                  </div>
                  <div className={styles.previewRowMeta}>
                    <TagPill tone="neutral">#{row.rank}</TagPill>
                    <StatusPill tone={statusTone(row.status)}>{row.status}</StatusPill>
                  </div>
                </div>
                <div className={styles.previewStats}>
                  <div className={styles.previewStat}>
                    <span>Blocking</span>
                    <strong>{formatDecimal(row.blockingScore, 2)}</strong>
                  </div>
                  <div className={styles.previewStat}>
                    <span>Forecast contribution</span>
                    <strong>{formatDecimal(row.forecastContributor, 2)}</strong>
                  </div>
                </div>
                <Link className={styles.entityAction} href={`/family/${encodeURIComponent(row.familyId)}`}>
                  Open family page
                </Link>
              </article>
            ))}
          </div>
        </article>
      ))}
    </div>
  );
}

export function ComparePortfolioLifecycleStructure(props: {
  rows: CompareMetricRow[];
  leftLabel: string;
  rightLabel: string;
}) {
  if (props.rows.length === 0) {
    return <p className={styles.emptyState}>No lifecycle structure rows are available for this compare.</p>;
  }

  const toCount = (value: number | string | null): number => (typeof value === "number" && Number.isFinite(value) ? value : 0);
  const leftTotal = props.rows.reduce((sum, row) => sum + toCount(row.leftValue), 0);
  const rightTotal = props.rows.reduce((sum, row) => sum + toCount(row.rightValue), 0);

  const renderSide = (side: "left" | "right", label: string, total: number) => (
    <article
      className={clsx(
        styles.lifecycleCard,
        side === "left" ? styles.lifecycleCardLeft : styles.lifecycleCardRight,
      )}
    >
      <div className={styles.lifecycleHeader}>
        <div className={styles.lifecycleIdentity}>
          <span className={styles.entityLabel}>Portfolio</span>
          <strong>{label}</strong>
        </div>
        <InfoPill tone="neutral">{formatNumber(total)} tracked families</InfoPill>
      </div>

      <div className={styles.lifecycleStackTrack}>
        {props.rows.map((row) => {
          const value = side === "left" ? toCount(row.leftValue) : toCount(row.rightValue);
          const share = total > 0 ? (value / total) * 100 : 0;
          const toneClass =
            row.key === "active_families"
              ? styles.lifecycleSegmentPositive
              : row.key === "pending_families"
                ? styles.lifecycleSegmentWarning
                : styles.lifecycleSegmentNeutral;
          return <div key={`${side}-${row.key}`} className={clsx(styles.lifecycleSegment, toneClass)} style={{ width: `${share}%` }} />;
        })}
      </div>

      <div className={styles.lifecycleRows}>
        {props.rows.map((row) => {
          const value = side === "left" ? toCount(row.leftValue) : toCount(row.rightValue);
          const share = total > 0 ? value / total : 0;
          const toneClass =
            row.key === "active_families"
              ? styles.lifecycleDotPositive
              : row.key === "pending_families"
                ? styles.lifecycleDotWarning
                : styles.lifecycleDotNeutral;
          return (
            <div key={`${side}-${row.key}`} className={styles.lifecycleRow}>
              <div className={styles.lifecycleRowLabel}>
                <span className={clsx(styles.lifecycleDot, toneClass)} />
                <strong>{row.label}</strong>
              </div>
              <div className={styles.lifecycleRowValues}>
                <span>{formatNumber(value)}</span>
                <small>{formatPercent(share)}</small>
              </div>
            </div>
          );
        })}
      </div>
    </article>
  );

  return (
    <div className={styles.lifecycleGrid}>
      {renderSide("left", props.leftLabel, leftTotal)}
      {renderSide("right", props.rightLabel, rightTotal)}
    </div>
  );
}

export function CompareLensMetricCard(props: {
  row: CompareMetricRow;
  leftLabel: string;
  rightLabel: string;
  eyebrow?: string;
}) {
  const { row, leftLabel, rightLabel, eyebrow = "Direct evidence" } = props;

  return (
    <article className={styles.lensCard}>
      <div className={styles.lensHeader}>
        <strong className={styles.lensLabel}>{row.label}</strong>
        <span className={styles.lensMetric}>{eyebrow}</span>
      </div>
      <div className={styles.lensBody}>
        <div className={styles.lensSides}>
          <div className={`${styles.lensSide} ${row.winner === "left" ? styles.sideWinner : ""}`}>
            <span className={styles.lensSideLabel}>{leftLabel}</span>
            <strong className={styles.lensValue}>{compareValue(row.leftValue, row.displayKind, row.key)}</strong>
            {row.leftNote ? <span className={styles.lensMetaCopy}>{row.leftNote}</span> : null}
          </div>
          <div className={`${styles.lensSide} ${row.winner === "right" ? styles.sideWinner : ""}`}>
            <span className={styles.lensSideLabel}>{rightLabel}</span>
            <strong className={styles.lensValue}>{compareValue(row.rightValue, row.displayKind, row.key)}</strong>
            {row.rightNote ? <span className={styles.lensMetaCopy}>{row.rightNote}</span> : null}
          </div>
        </div>
        <div className={styles.lensFooter}>
          <div className={styles.lensMetaLine}>
            <FieldPill soft>{compareDelta(row.deltaValue, row.displayKind, row.key)}</FieldPill>
            {row.winner && row.winner !== "tie" ? (
              <StatusPill tone="neutral">{row.winner === "left" ? compactWinnerLabel(leftLabel, "Left") : compactWinnerLabel(rightLabel, "Right")}</StatusPill>
            ) : null}
          </div>
          {row.note ? <span className={styles.winnerCopy}>{row.note}</span> : row.winnerBasis ? <span className={styles.winnerCopy}>{row.winnerBasis}</span> : null}
        </div>
      </div>
    </article>
  );
}

export function CompareSummaryCards({
  cards,
  leftLabel = "Left",
  rightLabel = "Right",
}: {
  cards: CompareMetricRow[];
  leftLabel?: string;
  rightLabel?: string;
}) {
  if (cards.length === 0) {
    return <p className={styles.emptyState}>No summary cards are available for this comparison.</p>;
  }
  return (
    <div className={styles.summaryCompareGrid}>
      {cards.map((card) => (
        <article
          key={card.key}
          className={clsx(
            styles.summaryCompareCard,
            card.winner === "left" && styles.summaryCompareCardLeft,
            card.winner === "right" && styles.summaryCompareCardRight,
            (!card.winner || card.winner === "tie") && styles.summaryCompareCardTie,
          )}
        >
          <div className={styles.summaryCompareHeader}>
            <span className={styles.summaryCompareLabel}>{card.label}</span>
            <StatusPill tone="neutral">{winnerLabel(card.winner, leftLabel, rightLabel)}</StatusPill>
          </div>
          <div className={styles.summaryCompareBoard}>
            <div className={clsx(styles.summaryCompareSidePanel, styles.summaryCompareSidePanelLeft)}>
              <span className={styles.summaryCompareSide}>{leftLabel}</span>
              <strong>{compareValue(card.leftValue, card.displayKind, card.key)}</strong>
              {card.leftNote ? <small>{card.leftNote}</small> : null}
            </div>
            <div className={styles.summaryCompareDeltaChip}>{compareDelta(card.deltaValue, card.displayKind, card.key)}</div>
            <div className={clsx(styles.summaryCompareSidePanel, styles.summaryCompareSidePanelRight)}>
              <span className={styles.summaryCompareSide}>{rightLabel}</span>
              <strong>{compareValue(card.rightValue, card.displayKind, card.key)}</strong>
              {card.rightNote ? <small>{card.rightNote}</small> : null}
            </div>
          </div>
        </article>
      ))}
    </div>
  );
}

function timesliceDeltaCenterLabel(row: CompareMetricRow): string {
  if (row.displayKind === "text") {
    return "Historical state";
  }
  return compareDelta(row.deltaValue, row.displayKind, row.key);
}

export function CompareTimesliceDeltaCards({
  rows,
  leftLabel = "Left",
  rightLabel = "Right",
}: {
  rows: CompareMetricRow[];
  leftLabel?: string;
  rightLabel?: string;
}) {
  if (rows.length === 0) {
    return <p className={styles.emptyState}>No historical delta rows are available for this compare.</p>;
  }

  return (
    <div className={styles.timesliceDeltaGrid}>
      {rows.map((row) => (
        <article
          key={row.key}
          className={clsx(
            styles.summaryCompareCard,
            row.winner === "left" && styles.summaryCompareCardLeft,
            row.winner === "right" && styles.summaryCompareCardRight,
            (!row.winner || row.winner === "tie") && styles.summaryCompareCardTie,
          )}
        >
          <div className={styles.summaryCompareHeader}>
            <span className={styles.summaryCompareLabel}>{row.label}</span>
            {row.winner && row.winner !== "tie" ? (
              <StatusPill tone="neutral">{row.winner === "left" ? compactWinnerLabel(leftLabel, "Left") : compactWinnerLabel(rightLabel, "Right")}</StatusPill>
            ) : (
              <InfoPill tone="neutral">Time-slice</InfoPill>
            )}
          </div>
          <div className={styles.summaryCompareBoard}>
            <div className={clsx(styles.summaryCompareSidePanel, styles.summaryCompareSidePanelLeft)}>
              <span className={styles.summaryCompareSide}>{leftLabel}</span>
              <strong>{compareValue(row.leftValue, row.displayKind, row.key)}</strong>
              {row.leftNote ? <small>{row.leftNote}</small> : null}
            </div>
            <div className={styles.summaryCompareDeltaChip}>{timesliceDeltaCenterLabel(row)}</div>
            <div className={clsx(styles.summaryCompareSidePanel, styles.summaryCompareSidePanelRight)}>
              <span className={styles.summaryCompareSide}>{rightLabel}</span>
              <strong>{compareValue(row.rightValue, row.displayKind, row.key)}</strong>
              {row.rightNote ? <small>{row.rightNote}</small> : null}
            </div>
          </div>
          {row.note ? <p className={styles.summaryCompareNote}>{row.note}</p> : null}
        </article>
      ))}
    </div>
  );
}

export function CompareTabBar(props: {
  activeTab: CompareTab;
  onChange: (tab: CompareTab) => void;
  tabs?: CompareTabSpec[];
}) {
  const tabs = props.tabs ?? COMPARE_TABS;
  return (
    <div className={styles.compareTabBar} role="tablist" aria-label="Compare views">
      {tabs.map((tab) => {
        const active = tab.value === props.activeTab;
        return (
          <button
            key={tab.value}
            type="button"
            role="tab"
            aria-selected={active}
            className={clsx(styles.compareTabButton, active && styles.compareTabButtonActive)}
            onClick={() => props.onChange(tab.value)}
          >
            <strong>{tab.label}</strong>
            <span>{tab.note}</span>
          </button>
        );
      })}
    </div>
  );
}

export function CompareContrastRows({
  rows,
  leftLabel = "Left",
  rightLabel = "Right",
}: {
  rows: CompareMetricRow[];
  leftLabel?: string;
  rightLabel?: string;
}) {
  if (rows.length === 0) {
    return <p className={styles.emptyState}>No compare evidence rows are available.</p>;
  }
  return (
    <div className={styles.lensGrid}>
      {rows.map((row) => (
        <article key={row.key} className={styles.lensCard}>
          <div className={styles.lensHeader}>
            <strong className={styles.lensLabel}>{row.label}</strong>
            <span className={styles.lensMetric}>Direct evidence</span>
          </div>
          <div className={styles.lensBody}>
            <div className={styles.lensSides}>
              <div className={clsx(styles.lensSide, row.winner === "left" && styles.sideWinner)}>
                <span className={styles.lensSideLabel}>{leftLabel}</span>
                <strong className={styles.lensValue}>{compareValue(row.leftValue, row.displayKind, row.key)}</strong>
                {row.leftNote ? <span className={styles.lensMetaCopy}>{row.leftNote}</span> : null}
              </div>
              <div className={clsx(styles.lensSide, row.winner === "right" && styles.sideWinner)}>
                <span className={styles.lensSideLabel}>{rightLabel}</span>
                <strong className={styles.lensValue}>{compareValue(row.rightValue, row.displayKind, row.key)}</strong>
                {row.rightNote ? <span className={styles.lensMetaCopy}>{row.rightNote}</span> : null}
              </div>
            </div>
            <div className={styles.lensFooter}>
              <div className={styles.lensMetaLine}>
                <FieldPill soft>{row.displayKind === "text" ? "Current state" : compareDelta(row.deltaValue, row.displayKind, row.key)}</FieldPill>
                {row.winner && row.winner !== "tie" ? (
                  <StatusPill tone="neutral">{row.winner === "left" ? compactWinnerLabel(leftLabel, "Left") : compactWinnerLabel(rightLabel, "Right")}</StatusPill>
                ) : null}
                {row.winnerBasis ? <TagPill tone="neutral">{row.winnerBasis.replace(/_/g, " ")}</TagPill> : null}
              </div>
              {row.note ? <span className={styles.winnerCopy}>{row.note}</span> : null}
            </div>
          </div>
        </article>
      ))}
    </div>
  );
}

export function CompareFieldOverlapRows(props: {
  rows: CompareFieldOverlapRow[];
  leftLabel: string;
  rightLabel: string;
}) {
  if (props.rows.length === 0) {
    return <p className={styles.emptyState}>No field overlap rows are available yet.</p>;
  }
  return (
    <div className={styles.overlapGrid}>
      {props.rows.map((row) => (
        <article key={row.key} className={styles.overlapCard}>
          <div className={styles.overlapHeader}>
            <strong>{row.label}</strong>
            <StatusPill tone={overlapTone(row.presence)}>{row.presence.replace(/_/g, " ")}</StatusPill>
          </div>
          <div className={styles.overlapMetrics}>
            <div>
              <span>{props.leftLabel}</span>
              <strong>{formatPercent(row.leftShare)}</strong>
              {row.leftNote ? <small>{row.leftNote}</small> : null}
            </div>
            <div>
              <span>{props.rightLabel}</span>
              <strong>{formatPercent(row.rightShare)}</strong>
              {row.rightNote ? <small>{row.rightNote}</small> : null}
            </div>
          </div>
          <div className={styles.overlapBars}>
            <div className={styles.overlapTrack}>
              <div className={styles.overlapFillLeft} style={{ width: `${Math.min(row.leftShare * 100, 100)}%` }} />
            </div>
            <div className={styles.overlapTrack}>
              <div className={styles.overlapFillRight} style={{ width: `${Math.min(row.rightShare * 100, 100)}%` }} />
            </div>
          </div>
          <div className={styles.overlapFooter}>
            <span>Shared depth {formatPercent(row.overlapShare)}</span>
            <span>
              {row.leftRank ? `L#${row.leftRank}` : "L—"} / {row.rightRank ? `R#${row.rightRank}` : "R—"}
            </span>
          </div>
        </article>
      ))}
    </div>
  );
}

export function CompareFieldDivergenceMatrix(props: {
  rows: CompareFieldOverlapRow[];
  leftLabel: string;
  rightLabel: string;
}) {
  if (props.rows.length === 0) {
    return <p className={styles.emptyState}>No field overlap rows are available yet.</p>;
  }

  const sharedCount = props.rows.filter((row) => row.presence === "shared").length;
  const leftOnlyCount = props.rows.filter((row) => row.presence === "left_only").length;
  const rightOnlyCount = props.rows.filter((row) => row.presence === "right_only").length;

  return (
    <div className={styles.divergenceMatrixStack}>
      <div className={styles.divergenceSummaryRow}>
        <InfoPill tone="neutral">{sharedCount} shared</InfoPill>
        <InfoPill tone="neutral">{leftOnlyCount} left-only</InfoPill>
        <InfoPill tone="neutral">{rightOnlyCount} right-only</InfoPill>
      </div>
      <div className={styles.divergenceMatrix}>
        {props.rows.map((row) => (
          <article key={row.key} className={styles.divergenceRow}>
            <div className={clsx(styles.divergenceSide, styles.divergenceSideLeft)}>
              <span className={styles.divergenceSideLabel}>{props.leftLabel}</span>
              <strong>{formatPercent(row.leftShare)}</strong>
              <div className={styles.divergenceTrack}>
                <div className={styles.divergenceFillLeft} style={{ width: `${Math.min(row.leftShare * 100, 100)}%` }} />
              </div>
              <small>{row.leftRank ? `Rank #${row.leftRank}` : "Not present"}</small>
              {row.leftNote ? <small>{row.leftNote}</small> : null}
            </div>
            <div className={styles.divergenceCenter}>
              <div className={styles.divergenceCenterHead}>
                <strong>{row.label}</strong>
                <StatusPill tone={overlapTone(row.presence)}>{row.presence.replace(/_/g, " ")}</StatusPill>
              </div>
              <div className={styles.divergenceCenterMeta}>
                <span>Shared depth {formatPercent(row.overlapShare)}</span>
                <span>
                  {row.leftRank ? `L#${row.leftRank}` : "L—"} / {row.rightRank ? `R#${row.rightRank}` : "R—"}
                </span>
              </div>
            </div>
            <div className={clsx(styles.divergenceSide, styles.divergenceSideRight)}>
              <span className={styles.divergenceSideLabel}>{props.rightLabel}</span>
              <strong>{formatPercent(row.rightShare)}</strong>
              <div className={styles.divergenceTrack}>
                <div className={styles.divergenceFillRight} style={{ width: `${Math.min(row.rightShare * 100, 100)}%` }} />
              </div>
              <small>{row.rightRank ? `Rank #${row.rightRank}` : "Not present"}</small>
              {row.rightNote ? <small>{row.rightNote}</small> : null}
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}

export function CompareFamilyOutlookRows(props: {
  rows: CompareForecastRow[];
  leftLabel: string;
  rightLabel: string;
  mode: "entity" | "timeslice";
}) {
  if (props.rows.length === 0) {
    return <p className={styles.emptyState}>No family outlook rows are available for this compare.</p>;
  }

  return (
    <div className={styles.familyOutlookGrid}>
      {props.rows.map((row) => {
        const maxValue = Math.max(
          1,
          ...[
            row.leftValue,
            row.rightValue,
            row.leftRangeLow,
            row.leftRangeHigh,
            row.rightRangeLow,
            row.rightRangeHigh,
          ].flatMap((value) => (typeof value === "number" && value > 0 ? [value] : [])),
        );

        const leftPointPct = typeof row.leftValue === "number" ? Math.max(0, Math.min((row.leftValue / maxValue) * 100, 100)) : 0;
        const rightPointPct = typeof row.rightValue === "number" ? Math.max(0, Math.min((row.rightValue / maxValue) * 100, 100)) : 0;
        const leftRangeStart =
          typeof row.leftRangeLow === "number" ? Math.max(0, Math.min((row.leftRangeLow / maxValue) * 100, 100)) : leftPointPct;
        const leftRangeEnd =
          typeof row.leftRangeHigh === "number" ? Math.max(leftRangeStart, Math.min((row.leftRangeHigh / maxValue) * 100, 100)) : leftPointPct;
        const rightRangeStart =
          typeof row.rightRangeLow === "number" ? Math.max(0, Math.min((row.rightRangeLow / maxValue) * 100, 100)) : rightPointPct;
        const rightRangeEnd =
          typeof row.rightRangeHigh === "number" ? Math.max(rightRangeStart, Math.min((row.rightRangeHigh / maxValue) * 100, 100)) : rightPointPct;
        const leftRangeAvailable = typeof row.leftRangeLow === "number" && typeof row.leftRangeHigh === "number";
        const rightRangeAvailable = typeof row.rightRangeLow === "number" && typeof row.rightRangeHigh === "number";

        return (
          <article key={row.key} className={styles.familyOutlookCard}>
            <div className={styles.familyOutlookHeader}>
              <div className={styles.familyOutlookTitleBlock}>
                <strong>{row.label}</strong>
                <span>{props.mode === "entity" ? "Interval-first family outlook" : "Historical family trajectory"}</span>
              </div>
              {row.overlapState ? <InfoPill tone="neutral">{row.overlapState}</InfoPill> : null}
            </div>

            <div className={styles.familyOutlookSides}>
              <div className={clsx(styles.familyOutlookSide, styles.familyOutlookSideLeft)}>
                <div className={styles.familyOutlookIdentity}>
                  <span>{props.leftLabel}</span>
                  <strong>{compareValue(row.leftValue, row.displayKind)}</strong>
                </div>
                <div className={styles.familyOutlookTrack}>
                  {leftRangeAvailable ? (
                    <div
                      className={styles.familyOutlookRangeLeft}
                      style={{ left: `${leftRangeStart}%`, width: `${Math.max(leftRangeEnd - leftRangeStart, 2)}%` }}
                    />
                  ) : (
                    <div className={styles.familyOutlookBarLeft} style={{ width: `${leftPointPct}%` }} />
                  )}
                  <div className={styles.familyOutlookMarker} style={{ left: `${leftPointPct}%` }} />
                </div>
                <small>
                  {leftRangeAvailable ? rangeLabel(row.leftRangeLow, row.leftRangeHigh, row.displayKind) : "Point comparison"}
                </small>
                {row.leftNote ? <small>{row.leftNote}</small> : null}
              </div>

              <div className={clsx(styles.familyOutlookSide, styles.familyOutlookSideRight)}>
                <div className={styles.familyOutlookIdentity}>
                  <span>{props.rightLabel}</span>
                  <strong>{compareValue(row.rightValue, row.displayKind)}</strong>
                </div>
                <div className={styles.familyOutlookTrack}>
                  {rightRangeAvailable ? (
                    <div
                      className={styles.familyOutlookRangeRight}
                      style={{ left: `${rightRangeStart}%`, width: `${Math.max(rightRangeEnd - rightRangeStart, 2)}%` }}
                    />
                  ) : (
                    <div className={styles.familyOutlookBarRight} style={{ width: `${rightPointPct}%` }} />
                  )}
                  <div className={styles.familyOutlookMarker} style={{ left: `${rightPointPct}%` }} />
                </div>
                <small>
                  {rightRangeAvailable ? rangeLabel(row.rightRangeLow, row.rightRangeHigh, row.displayKind) : "Point comparison"}
                </small>
                {row.rightNote ? <small>{row.rightNote}</small> : null}
              </div>
            </div>

            {row.note ? <p className={styles.summaryCompareNote}>{row.note}</p> : null}
          </article>
        );
      })}
    </div>
  );
}

export function CompareForecastRows({
  rows,
  leftLabel = "Left",
  rightLabel = "Right",
}: {
  rows: CompareForecastRow[];
  leftLabel?: string;
  rightLabel?: string;
}) {
  if (rows.length === 0) {
    return <p className={styles.emptyState}>No forecast contrast rows are available for this compare.</p>;
  }
  return (
    <div className={styles.forecastCompareGrid}>
      {rows.map((row) => (
        <article key={row.key} className={styles.forecastCompareCard}>
          <div className={styles.forecastCompareHeader}>
            <strong>{row.label}</strong>
            {row.overlapState ? <InfoPill tone="neutral">{row.overlapState}</InfoPill> : null}
          </div>
          <div className={styles.forecastCompareValues}>
            <div>
              <span>{leftLabel}</span>
              <strong>{compareValue(row.leftValue, row.displayKind)}</strong>
              <small>{rangeLabel(row.leftRangeLow, row.leftRangeHigh, row.displayKind)}</small>
              {row.leftNote ? <small>{row.leftNote}</small> : null}
            </div>
            <div>
              <span>{rightLabel}</span>
              <strong>{compareValue(row.rightValue, row.displayKind)}</strong>
              <small>{rangeLabel(row.rightRangeLow, row.rightRangeHigh, row.displayKind)}</small>
              {row.rightNote ? <small>{row.rightNote}</small> : null}
            </div>
          </div>
          {row.note ? <p className={styles.summaryCompareNote}>{row.note}</p> : null}
        </article>
      ))}
    </div>
  );
}

export function CompareLegalFootprintRows(props: {
  rows: CompareSupportRow[];
  leftLabel: string;
  rightLabel: string;
}) {
  const groups = [
    { side: "left" as const, label: props.leftLabel, rows: props.rows.filter((row) => row.side === "left") },
    { side: "right" as const, label: props.rightLabel, rows: props.rows.filter((row) => row.side === "right") },
  ];

  if (groups.every((group) => group.rows.length === 0)) {
    return <p className={styles.emptyState}>No jurisdiction-level legal rows are available for this compare.</p>;
  }

  return (
    <div className={styles.legalFootprintGrid}>
      {groups.map((group) => (
        <article
          key={group.side}
          className={clsx(
            styles.legalFootprintCard,
            group.side === "left" ? styles.legalFootprintCardLeft : styles.legalFootprintCardRight,
          )}
        >
          <div className={styles.legalFootprintHeader}>
            <div className={styles.legalFootprintIdentity}>
              <span className={styles.compareHeroEyebrow}>Compared entity</span>
              <strong>{group.label}</strong>
            </div>
            <InfoPill tone="neutral">{group.rows.length} jurisdictions</InfoPill>
          </div>
          {group.rows.length ? (
            <div className={styles.legalFootprintRows}>
              {group.rows.map((row) => {
                const shareValue = typeof row.primaryMetricValue === "number" ? Math.max(0, Math.min(row.primaryMetricValue * 100, 100)) : null;
                return (
                  <article key={`${group.side}-${row.kind}-${row.title}`} className={styles.legalFootprintRow}>
                    <div className={styles.legalFootprintRowHeader}>
                      <strong>{row.title}</strong>
                      {row.badge ? <StatusPill tone={supportTone(row.badge)}>{row.badge}</StatusPill> : null}
                    </div>
                    {row.subtitle ? <p className={styles.legalFootprintRowSubtitle}>{row.subtitle}</p> : null}
                    <div className={styles.legalFootprintMetricRow}>
                      {row.primaryMetricLabel ? (
                        <div className={styles.legalFootprintMetric}>
                          <span>{row.primaryMetricLabel}</span>
                          <strong>{supportMetricValue(row.primaryMetricLabel, row.primaryMetricValue)}</strong>
                        </div>
                      ) : null}
                      {row.secondaryMetricLabel ? (
                        <div className={styles.legalFootprintMetric}>
                          <span>{row.secondaryMetricLabel}</span>
                          <strong>{supportMetricValue(row.secondaryMetricLabel, row.secondaryMetricValue)}</strong>
                        </div>
                      ) : null}
                    </div>
                    {shareValue != null ? (
                      <div className={styles.legalFootprintTrack}>
                        <div
                          className={group.side === "left" ? styles.legalFootprintFillLeft : styles.legalFootprintFillRight}
                          style={{ width: `${shareValue}%` }}
                        />
                      </div>
                    ) : null}
                  </article>
                );
              })}
            </div>
          ) : (
            <p className={styles.emptyState}>No jurisdiction-level legal rows are available for this side of the compare.</p>
          )}
        </article>
      ))}
    </div>
  );
}

export function CompareTimesliceProfile(props: {
  dimensions: CompareTimesliceProfileDimension[];
  leftLabel: string;
  rightLabel: string;
}) {
  if (props.dimensions.length === 0) {
    return <p className={styles.emptyState}>No normalized time-slice profile rows are available for this compare.</p>;
  }

  return (
    <div className={styles.timesliceProfileGrid}>
      {props.dimensions.map((dimension) => (
        <article key={dimension.key} className={styles.timesliceProfileCard}>
          <div className={styles.timesliceProfileHeader}>
            <strong>{dimension.label}</strong>
            <InfoPill tone="neutral">0–100 normalized</InfoPill>
          </div>
          {dimension.note ? <p className={styles.timesliceProfileNote}>{dimension.note}</p> : null}
          <div className={styles.timesliceProfileRows}>
            <div className={styles.timesliceProfileRow}>
              <div className={styles.timesliceProfileIdentity}>
                <span>{props.leftLabel}</span>
                <strong>{compareValue(dimension.leftValue, dimension.displayKind, dimension.key)}</strong>
              </div>
              <div className={styles.timesliceProfileTrack}>
                <div className={styles.timesliceProfileFillLeft} style={{ width: `${Math.max(0, Math.min(dimension.leftScore, 100))}%` }} />
              </div>
            </div>
            <div className={styles.timesliceProfileRow}>
              <div className={styles.timesliceProfileIdentity}>
                <span>{props.rightLabel}</span>
                <strong>{compareValue(dimension.rightValue, dimension.displayKind, dimension.key)}</strong>
              </div>
              <div className={styles.timesliceProfileTrack}>
                <div className={styles.timesliceProfileFillRight} style={{ width: `${Math.max(0, Math.min(dimension.rightScore, 100))}%` }} />
              </div>
            </div>
          </div>
        </article>
      ))}
    </div>
  );
}

export function CompareSupportRows({
  rows,
  leftLabel = "Left",
  rightLabel = "Right",
}: {
  rows: CompareSupportRow[];
  leftLabel?: string;
  rightLabel?: string;
}) {
  if (rows.length === 0) {
    return <p className={styles.emptyState}>No support rows are available for this compare.</p>;
  }

  const groups = [
    { side: "left" as const, title: `${leftLabel} evidence`, rows: rows.filter((row) => row.side === "left") },
    { side: "right" as const, title: `${rightLabel} evidence`, rows: rows.filter((row) => row.side === "right") },
  ].filter((group) => group.rows.length > 0);

  return (
    <div className={styles.supportGroupGrid}>
      {groups.map((group) => (
        <article key={group.side} className={styles.supportGroupCard}>
          <div className={styles.supportGroupHeader}>
            <strong>{group.title}</strong>
            <InfoPill tone="neutral">{group.rows.length} rows</InfoPill>
          </div>
          <div className={styles.supportRowList}>
            {group.rows.map((row) => {
              const body = (
                <>
                  <div className={styles.supportRowHeader}>
                    <strong>{row.title}</strong>
                    {row.badge ? <StatusPill tone={supportTone(row.badge)}>{row.badge}</StatusPill> : null}
                  </div>
                  {row.subtitle ? <p className={styles.supportRowSubtitle}>{row.subtitle}</p> : null}
                  <div className={styles.supportRowMetrics}>
                    {row.primaryMetricLabel ? (
                      <div>
                        <span>{row.primaryMetricLabel}</span>
                        <strong>{supportMetricValue(row.primaryMetricLabel, row.primaryMetricValue)}</strong>
                      </div>
                    ) : null}
                    {row.secondaryMetricLabel ? (
                      <div>
                        <span>{row.secondaryMetricLabel}</span>
                        <strong>{supportMetricValue(row.secondaryMetricLabel, row.secondaryMetricValue)}</strong>
                      </div>
                    ) : null}
                  </div>
                </>
              );
              return row.href ? (
                <Link key={`${group.side}-${row.kind}-${row.title}`} href={row.href} className={styles.supportRowCard}>
                  {body}
                </Link>
              ) : (
                <article key={`${group.side}-${row.kind}-${row.title}`} className={styles.supportRowCard}>
                  {body}
                </article>
              );
            })}
          </div>
        </article>
      ))}
    </div>
  );
}

export function CompareMethodology({ meta }: { meta: CompareMeta }) {
  if (!meta.caveats.length) {
    return <p className={styles.emptyState}>No methodology notes were returned for this compare.</p>;
  }

  return (
    <details className={styles.caveatDisclosure}>
      <summary className={styles.caveatDisclosureSummary}>
        <span>{meta.caveats.length} methodology note{meta.caveats.length === 1 ? "" : "s"}</span>
      </summary>
      <div className={styles.caveatGrid}>
        {meta.caveats.map((caveat) => (
          <article key={caveat.code} className={styles.caveatCard}>
            <span className={styles.caveatCode}>{caveat.code}</span>
            <strong>{caveat.title}</strong>
            <p>{caveat.detail}</p>
          </article>
        ))}
      </div>
    </details>
  );
}
