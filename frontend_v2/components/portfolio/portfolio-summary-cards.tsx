"use client";

import clsx from "clsx";

import { formatNumber, formatOrdinal } from "@/components/portfolio/portfolio-format";
import { PortfolioMetricTooltip } from "@/components/portfolio/portfolio-metric-tooltip";
import type { PortfolioSummaryCard } from "@/lib/types/portfolio-v2";

import styles from "./portfolio-summary-cards.module.css";

type PortfolioSummaryCardsProps = {
  cards: PortfolioSummaryCard[];
};

const toneClass: Record<NonNullable<PortfolioSummaryCard["tone"]>, string> = {
  neutral: "portfolio-card--neutral",
  positive: "portfolio-card--positive",
  warning: "portfolio-card--warning",
  critical: "portfolio-card--critical",
};

function SummaryCard({ card, index }: { card: PortfolioSummaryCard; index: number }) {
  const hasPercent = card.value.includes("%");
  const normalized = Number(card.value.replace?.(/[,%]/g, "") ?? "");
  const displayValue = Number.isFinite(normalized)
    ? hasPercent
      ? `${normalized}%`
      : formatNumber(normalized)
    : card.value;

  return (
    <div
      className={clsx("portfolio-card", toneClass[card.tone ?? "neutral"])}
      style={{ animationDelay: `${index * 60}ms` }}
    >
      <div className="portfolio-card__label">
        <span>{card.label}</span>
        {card.tooltip ? <PortfolioMetricTooltip text={card.tooltip} /> : null}
      </div>
      <div className="portfolio-card__value">{displayValue}</div>
      {card.bandLabel ? (
        <div className="portfolio-card__band">
          <span className="portfolio-card__band-label">{card.bandLabel}</span>
          {card.peerPercentile != null ? <span>{formatOrdinal(card.peerPercentile)} percentile</span> : null}
          {card.peerBucketLabel ? <span>{card.peerBucketLabel}</span> : null}
        </div>
      ) : null}
      {card.delta !== undefined ? (
        <div className={clsx("portfolio-card__delta", card.delta >= 0 ? "positive" : "negative")}>
          {card.delta >= 0 ? "+" : ""}
          {card.delta}% {card.deltaLabel ?? "vs peers"}
        </div>
      ) : null}
      {card.caveat ? <div className="portfolio-card__caveat">{card.caveat}</div> : null}
    </div>
  );
}

export function PortfolioSummaryCards({ cards }: PortfolioSummaryCardsProps) {
  const visibleCards = cards.filter(
    (card) =>
      card.key !== "portfolio_family_count_within_mega_cluster" &&
      card.key !== "portfolio_primary_owner_family_count" &&
      card.key !== "portfolio_pending_family_count" &&
      card.key !== "semantic_candidate_family_count",
  );

  return (
    <section className="portfolio-grid-panel">
      <h2 className={styles.title}>Portfolio summary</h2>
      <div className="portfolio-summary-grid">
        {visibleCards.map((card, index) => (
          <SummaryCard key={card.key} card={card} index={index} />
        ))}
      </div>
    </section>
  );
}
