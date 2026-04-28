"use client";

import { Scale, Search, Shuffle } from "lucide-react";
import { type ReactNode, useCallback, useEffect, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";

import { fetchPortfolioCompare, fetchPortfolioCompareLookup } from "@/lib/api/compare-v2";
import { fetchPortfolioOwnerSuggestions } from "@/lib/api/portfolio-v2";
import {
  CompareFieldDivergenceMatrix,
  CompareHeader,
  CompareMethodology,
  ComparePortfolioLifecycleStructure,
  ComparePortfolioTopFamilyFaceoff,
  CompareSummaryCards,
  CompareTabBar,
  type CompareTab,
  type CompareTabSpec,
} from "@/components/compare/compare-rendering";
import { FieldPill, StatusPill, TagPill } from "@/components/ui/data-pill";
import { Surface } from "@/components/ui/surface";
import type { CompareScopeLookup, PortfolioCompareLensRow, PortfolioComparePayload } from "@/lib/types/compare-v2";
import type { PortfolioOwnerSuggestion } from "@/lib/types/portfolio-v2";

import styles from "./compare-workspace.module.css";

const entityTabs: CompareTabSpec[] = [
  { value: "overview", label: "Overview", note: "Summary, lenses, and deltas" },
  { value: "technology", label: "Technology", note: "Field overlap and divergence" },
];

function bandTone(code: string | null | undefined): "positive" | "warning" | "critical" | "neutral" {
  if (code === "very_high" || code === "high") {
    return "positive";
  }
  if (code === "medium") {
    return "warning";
  }
  if (code === "low") {
    return "critical";
  }
  return "neutral";
}

function winnerCopy(row: PortfolioCompareLensRow): string {
  if (row.suppressed && row.suppressionReason) {
    return row.suppressionReason;
  }
  if (row.winner === "left") {
    return row.samePeerBucket ? `${row.leftOwnerLabel} leads on peer percentile` : `${row.leftOwnerLabel} leads on peer band`;
  }
  if (row.winner === "right") {
    return row.samePeerBucket ? `${row.rightOwnerLabel} leads on peer percentile` : `${row.rightOwnerLabel} leads on peer band`;
  }
  return "No clear winner signal";
}

function normalizeSearchToken(value: string) {
  return value.trim().toUpperCase().replace(/[^A-Z0-9]+/g, "_").replace(/^_+|_+$/g, "");
}

function hasText(value: string): boolean {
  return Boolean(value.trim());
}

function portfolioCompareEntityLabel(label: string | null | undefined, fallback: string): string {
  const text = label?.trim();
  return text && text.length > 0 ? text : fallback;
}

function formatLensAggregate(value: number): string {
  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits: 2,
    minimumFractionDigits: value >= 100 ? 0 : 2,
  }).format(value);
}

function portfolioLensMetricTitle(row: PortfolioCompareLensRow): string {
  return row.lens === "density" ? row.metricLabel : "Peer percentile";
}

function portfolioLensDisplayValue(row: PortfolioCompareLensRow, side: "left" | "right"): string {
  const rawValue = side === "left" ? row.leftRawValue : row.rightRawValue;
  const percentile = side === "left" ? row.leftPeerPercentile : row.rightPeerPercentile;
  if (row.lens === "density") {
    return `${(rawValue * 100).toFixed(1)}%`;
  }
  if (percentile != null && Number.isFinite(percentile)) {
    return `${Math.round(percentile)}th pct`;
  }
  return formatLensAggregate(rawValue);
}

function portfolioLensAggregateCopy(row: PortfolioCompareLensRow, side: "left" | "right"): string | null {
  const rawValue = side === "left" ? row.leftRawValue : row.rightRawValue;
  if (row.lens === "density") {
    return null;
  }
  if (row.lens === "mass") {
    return `aggregate mass ${formatLensAggregate(rawValue)}`;
  }
  if (row.lens === "crown_jewel") {
    return `aggregate crown-jewel mass ${formatLensAggregate(rawValue)}`;
  }
  if (row.lens === "current_threat") {
    return `aggregate threat mass ${formatLensAggregate(rawValue)}`;
  }
  return `aggregate ${formatLensAggregate(rawValue)}`;
}

function formatPortfolioLookupText(lookup: CompareScopeLookup | null): string | null {
  if (!lookup) {
    return null;
  }
  if (!lookup.inScope) {
    return lookup.note ?? "Portfolio not in compare scope.";
  }
  const parts = ["In compare scope"];
  if (lookup.label) {
    parts.push(lookup.label);
  }
  if (lookup.familyCount != null) {
    parts.push(`${lookup.familyCount} families`);
  }
  if (lookup.primaryField) {
    parts.push(lookup.primaryField);
  }
  return parts.join(" · ");
}

function portfolioHeaderMeta(payload: PortfolioComparePayload | null, topFamilyLimit: number): string[] {
  if (!payload) {
    return [];
  }

  const bucketFlags = payload.lensRows.map((row) => row.samePeerBucket);
  const bucketLabel = bucketFlags.every(Boolean)
    ? "Same peer bucket"
    : bucketFlags.every((flag) => !flag)
      ? "Cross bucket"
      : "Mixed buckets";

  return ["Entity compare", bucketLabel, `Top ${topFamilyLimit} family preview`];
}

function OwnerLookupField({
  label,
  value,
  suggestions,
  searching,
  helper,
  onChange,
  onSelect,
}: {
  label: string;
  value: string;
  suggestions: PortfolioOwnerSuggestion[];
  searching: boolean;
  helper?: ReactNode;
  onChange: (value: string) => void;
  onSelect: (owner: PortfolioOwnerSuggestion) => void;
}) {
  const [activeIndex, setActiveIndex] = useState(-1);
  const activeOwner = activeIndex >= 0 ? suggestions[activeIndex] : undefined;

  return (
    <label className={styles.fieldStack}>
      <span className={styles.fieldLabel}>{label}</span>
      <div className={styles.fieldStack}>
        <div style={{ position: "relative" }}>
          <input
            className={styles.fieldInput}
            value={value}
            onChange={(event) => onChange(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "ArrowDown") {
                event.preventDefault();
                setActiveIndex((current) => (suggestions.length === 0 ? -1 : current < suggestions.length - 1 ? current + 1 : 0));
                return;
              }
              if (event.key === "ArrowUp") {
                event.preventDefault();
                setActiveIndex((current) => (suggestions.length === 0 ? -1 : current > 0 ? current - 1 : suggestions.length - 1));
                return;
              }
              if (event.key === "Enter" && activeOwner) {
                event.preventDefault();
                onSelect(activeOwner);
              }
            }}
            placeholder="Search owner name or harmonized id"
          />
          {searching ? <span className={styles.fieldHelp}>Searching owners…</span> : null}
          {suggestions.length > 0 ? (
            <div className={styles.lookupMenu}>
              {suggestions.map((owner, index) => (
                <button
                  key={`${label}-${owner.ownerId}`}
                  type="button"
                  className={styles.lookupItem}
                  data-active={activeIndex === index ? "true" : "false"}
                  onClick={() => onSelect(owner)}
                  onMouseEnter={() => setActiveIndex(index)}
                >
                  <span className={styles.lookupLabel}>{owner.label}</span>
                  <span className={styles.lookupMeta}>
                    {owner.ownerId}
                    {owner.familyCount != null ? ` • ${owner.familyCount} families` : ""}
                  </span>
                </button>
              ))}
            </div>
          ) : null}
        </div>
        {helper}
      </div>
    </label>
  );
}

export function PortfolioCompareWorkspace() {
  const router = useRouter();
  const pathname = usePathname() ?? "/compare/portfolios";
  const searchParams = useSearchParams();
  const query = searchParams ?? new URLSearchParams();

  const leftOwnerId = query.get("left_owner_id") ?? "";
  const rightOwnerId = query.get("right_owner_id") ?? "";
  const staleMode = query.get("mode");
  const staleOwnerId = query.get("owner_id") ?? "";
  const staleBaseYear = query.get("base_year") ?? "";
  const staleCompareYear = query.get("compare_year") ?? "";
  const topFamilyLimit = Number(query.get("top_family_limit") ?? "5") || 5;
  const rawTab = query.get("tab");
  const activeTab: CompareTab = rawTab === "technology" ? rawTab : "overview";

  const [leftInput, setLeftInput] = useState(leftOwnerId);
  const [rightInput, setRightInput] = useState(rightOwnerId);
  const [selectedLeftOwnerId, setSelectedLeftOwnerId] = useState(leftOwnerId);
  const [selectedRightOwnerId, setSelectedRightOwnerId] = useState(rightOwnerId);
  const [leftSuggestions, setLeftSuggestions] = useState<PortfolioOwnerSuggestion[]>([]);
  const [rightSuggestions, setRightSuggestions] = useState<PortfolioOwnerSuggestion[]>([]);
  const [leftLookup, setLeftLookup] = useState<CompareScopeLookup | null>(null);
  const [rightLookup, setRightLookup] = useState<CompareScopeLookup | null>(null);
  const [leftLookupLoading, setLeftLookupLoading] = useState(false);
  const [rightLookupLoading, setRightLookupLoading] = useState(false);
  const [leftLookupError, setLeftLookupError] = useState<string | null>(null);
  const [rightLookupError, setRightLookupError] = useState<string | null>(null);
  const [leftSearching, setLeftSearching] = useState(false);
  const [rightSearching, setRightSearching] = useState(false);
  const [payload, setPayload] = useState<PortfolioComparePayload | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const updateQuery = useCallback(
    (updates: Record<string, string | null>) => {
      const params = new URLSearchParams(searchParams?.toString() ?? "");
      Object.entries(updates).forEach(([key, value]) => {
        if (!value) {
          params.delete(key);
          return;
        }
        params.set(key, value);
      });
      const next = params.toString();
      router.replace(next ? `${pathname}?${next}` : pathname, { scroll: false });
    },
    [pathname, router, searchParams],
  );

  useEffect(() => {
    setLeftInput(leftOwnerId);
    setSelectedLeftOwnerId(leftOwnerId);
  }, [leftOwnerId]);

  useEffect(() => {
    setRightInput(rightOwnerId);
    setSelectedRightOwnerId(rightOwnerId);
  }, [rightOwnerId]);

  useEffect(() => {
    const candidate = leftInput.trim();
    if (!candidate) {
      setLeftLookup(null);
      setLeftLookupError(null);
      setLeftLookupLoading(false);
      return;
    }
    let cancelled = false;
    setLeftLookupLoading(true);
    setLeftLookupError(null);
    const timeoutId = window.setTimeout(() => {
      void fetchPortfolioCompareLookup(candidate)
        .then((lookup) => {
          if (!cancelled) {
            setLeftLookup(lookup);
          }
        })
        .catch((ex) => {
          if (!cancelled) {
            setLeftLookup(null);
            setLeftLookupError(ex instanceof Error ? ex.message : "Could not check compare scope.");
          }
        })
        .finally(() => {
          if (!cancelled) {
            setLeftLookupLoading(false);
          }
        });
    }, 220);

    return () => {
      cancelled = true;
      window.clearTimeout(timeoutId);
    };
  }, [leftInput]);

  useEffect(() => {
    const candidate = rightInput.trim();
    if (!candidate) {
      setRightLookup(null);
      setRightLookupError(null);
      setRightLookupLoading(false);
      return;
    }
    let cancelled = false;
    setRightLookupLoading(true);
    setRightLookupError(null);
    const timeoutId = window.setTimeout(() => {
      void fetchPortfolioCompareLookup(candidate)
        .then((lookup) => {
          if (!cancelled) {
            setRightLookup(lookup);
          }
        })
        .catch((ex) => {
          if (!cancelled) {
            setRightLookup(null);
            setRightLookupError(ex instanceof Error ? ex.message : "Could not check compare scope.");
          }
        })
        .finally(() => {
          if (!cancelled) {
            setRightLookupLoading(false);
          }
        });
    }, 220);

    return () => {
      cancelled = true;
      window.clearTimeout(timeoutId);
    };
  }, [rightInput]);

  useEffect(() => {
    const trimmed = leftInput.trim();
    if (trimmed.length < 2 || (selectedLeftOwnerId && normalizeSearchToken(trimmed) === normalizeSearchToken(selectedLeftOwnerId))) {
      setLeftSuggestions([]);
      setLeftSearching(false);
      return;
    }
    const controller = new AbortController();
    let cancelled = false;
    setLeftSearching(true);
    const timeoutId = window.setTimeout(() => {
      void fetchPortfolioOwnerSuggestions(trimmed, 8, controller.signal)
        .then((response) => {
          if (!cancelled) {
            setLeftSuggestions(response.rows);
          }
        })
        .catch(() => {
          if (!cancelled) {
            setLeftSuggestions([]);
          }
        })
        .finally(() => {
          if (!cancelled) {
            setLeftSearching(false);
          }
        });
    }, 180);

    return () => {
      cancelled = true;
      controller.abort();
      window.clearTimeout(timeoutId);
    };
  }, [leftInput, selectedLeftOwnerId]);

  useEffect(() => {
    const trimmed = rightInput.trim();
    if (trimmed.length < 2 || (selectedRightOwnerId && normalizeSearchToken(trimmed) === normalizeSearchToken(selectedRightOwnerId))) {
      setRightSuggestions([]);
      setRightSearching(false);
      return;
    }
    const controller = new AbortController();
    let cancelled = false;
    setRightSearching(true);
    const timeoutId = window.setTimeout(() => {
      void fetchPortfolioOwnerSuggestions(trimmed, 8, controller.signal)
        .then((response) => {
          if (!cancelled) {
            setRightSuggestions(response.rows);
          }
        })
        .catch(() => {
          if (!cancelled) {
            setRightSuggestions([]);
          }
        })
        .finally(() => {
          if (!cancelled) {
            setRightSearching(false);
          }
        });
    }, 180);

    return () => {
      cancelled = true;
      controller.abort();
      window.clearTimeout(timeoutId);
    };
  }, [rightInput, selectedRightOwnerId]);

  useEffect(() => {
    if (!leftOwnerId || !rightOwnerId) {
      setPayload(null);
      setError(null);
      setLoading(false);
      return;
    }

    let cancelled = false;
    setLoading(true);
    setError(null);

    void fetchPortfolioCompare({ leftOwnerId, rightOwnerId, topFamilyLimit })
      .then((response) => {
        if (!cancelled) {
          setPayload(response);
        }
      })
      .catch((ex) => {
        if (!cancelled) {
          setPayload(null);
          setError(ex instanceof Error ? ex.message : "Could not load portfolio compare.");
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [leftOwnerId, rightOwnerId, topFamilyLimit]);

  useEffect(() => {
    if (!staleMode && !staleOwnerId && !staleBaseYear && !staleCompareYear) {
      return;
    }
    updateQuery({
      mode: null,
      owner_id: null,
      base_year: null,
      compare_year: null,
    });
  }, [staleMode, staleOwnerId, staleBaseYear, staleCompareYear, updateQuery]);

  const exactLeft = leftSuggestions.find(
    (owner) => normalizeSearchToken(owner.ownerId) === normalizeSearchToken(leftInput) || normalizeSearchToken(owner.label) === normalizeSearchToken(leftInput),
  );
  const exactRight = rightSuggestions.find(
    (owner) => normalizeSearchToken(owner.ownerId) === normalizeSearchToken(rightInput) || normalizeSearchToken(owner.label) === normalizeSearchToken(rightInput),
  );

  const submitEntity = () => {
    const resolvedLeft = exactLeft?.ownerId ?? leftSuggestions[0]?.ownerId ?? leftInput.trim();
    const resolvedRight = exactRight?.ownerId ?? rightSuggestions[0]?.ownerId ?? rightInput.trim();
    updateQuery({
      left_owner_id: resolvedLeft || null,
      right_owner_id: resolvedRight || null,
      top_family_limit: String(topFamilyLimit),
      mode: null,
      owner_id: null,
      base_year: null,
      compare_year: null,
    });
  };

  const swapSides = () => {
    setLeftInput(rightInput);
    setRightInput(leftInput);
    setSelectedLeftOwnerId(selectedRightOwnerId);
    setSelectedRightOwnerId(selectedLeftOwnerId);
  };

  const canRunEntity =
    hasText(leftInput) &&
    hasText(rightInput) &&
    leftLookup?.inScope === true &&
    rightLookup?.inScope === true;

  const lifecycleRows = payload?.contrastRows.filter(
    (row) => row.key === "active_families" || row.key === "pending_families" || row.key === "abandoned_families",
  ) ?? [];
  const visibleSummaryCards =
    payload?.summaryCards.filter((card) => card.key !== "mass" && card.key !== "density" && card.key !== "heritage") ?? [];
  const leftCompareLabel = portfolioCompareEntityLabel(payload?.leftEntity?.label, "Portfolio left");
  const rightCompareLabel = portfolioCompareEntityLabel(payload?.rightEntity?.label, "Portfolio right");

  return (
    <div className={styles.workspaceStack}>
      <Surface
        className={styles.compactControlSurface}
        title="Select two portfolios"
        eyebrow="Portfolio compare"
        description="Search two harmonized owners and run the current-profile compare."
      >
        <form
          className={styles.controlForm}
          onSubmit={(event) => {
            event.preventDefault();
            if (canRunEntity) {
              submitEntity();
            }
          }}
        >
          <div className={styles.formGrid}>
            <OwnerLookupField
              label="Left portfolio"
              value={leftInput}
              suggestions={leftSuggestions}
              searching={leftSearching}
              helper={
                leftLookupLoading ? (
                  <span className={styles.fieldHelp}>Checking compare scope…</span>
                ) : leftLookupError ? (
                  <span className={styles.fieldHelp}>{leftLookupError}</span>
                ) : hasText(leftInput) && formatPortfolioLookupText(leftLookup) ? (
                  <span className={`${styles.scopeHint} ${leftLookup?.inScope ? styles.scopeHintPositive : styles.scopeHintCritical}`}>
                    {formatPortfolioLookupText(leftLookup)}
                  </span>
                ) : null
              }
              onChange={(value) => {
                if (normalizeSearchToken(value) !== normalizeSearchToken(selectedLeftOwnerId)) {
                  setSelectedLeftOwnerId("");
                }
                setLeftInput(value);
              }}
              onSelect={(owner) => {
                setLeftInput(owner.ownerId);
                setSelectedLeftOwnerId(owner.ownerId);
                setLeftSuggestions([]);
              }}
            />
            <OwnerLookupField
              label="Right portfolio"
              value={rightInput}
              suggestions={rightSuggestions}
              searching={rightSearching}
              helper={
                rightLookupLoading ? (
                  <span className={styles.fieldHelp}>Checking compare scope…</span>
                ) : rightLookupError ? (
                  <span className={styles.fieldHelp}>{rightLookupError}</span>
                ) : hasText(rightInput) && formatPortfolioLookupText(rightLookup) ? (
                  <span className={`${styles.scopeHint} ${rightLookup?.inScope ? styles.scopeHintPositive : styles.scopeHintCritical}`}>
                    {formatPortfolioLookupText(rightLookup)}
                  </span>
                ) : null
              }
              onChange={(value) => {
                if (normalizeSearchToken(value) !== normalizeSearchToken(selectedRightOwnerId)) {
                  setSelectedRightOwnerId("");
                }
                setRightInput(value);
              }}
              onSelect={(owner) => {
                setRightInput(owner.ownerId);
                setSelectedRightOwnerId(owner.ownerId);
                setRightSuggestions([]);
              }}
            />
          </div>
          <div className={styles.actionRow}>
            <label className={styles.fieldStack} style={{ minWidth: 160 }}>
              <span className={styles.fieldLabel}>Top family preview</span>
              <select
                className={styles.fieldSelect}
                value={String(topFamilyLimit)}
                onChange={(event) => updateQuery({ top_family_limit: event.target.value })}
              >
                <option value="3">Top 3 families</option>
                <option value="5">Top 5 families</option>
                <option value="10">Top 10 families</option>
              </select>
            </label>
            <button type="submit" className={styles.actionButton} disabled={!canRunEntity}>
              <Search size={16} />
              Run portfolio compare
            </button>
            <button type="button" className={styles.ghostButton} onClick={swapSides}>
              <Shuffle size={16} />
              Swap sides
            </button>
          </div>
        </form>
      </Surface>

      {leftOwnerId || rightOwnerId ? (
        !payload ? (
          <Surface
            title="Compare context"
            eyebrow="Active query"
            description="The left side can be prefilled directly from a portfolio page. Use the second field to complete the comparison."
          >
            <div className={styles.entityGrid}>
              <article className={styles.entityCard}>
                <span className={styles.entityLabel}>Left portfolio</span>
                <strong className={styles.entityTitle}>{leftOwnerId || "Pending"}</strong>
                <div className={styles.entityMeta}>{leftOwnerId ? <TagPill tone="neutral" monospace>{leftOwnerId}</TagPill> : null}</div>
              </article>
              <article className={styles.entityCard}>
                <span className={styles.entityLabel}>Right portfolio</span>
                <strong className={styles.entityTitle}>{rightOwnerId || "Pending"}</strong>
                <div className={styles.entityMeta}>{rightOwnerId ? <TagPill tone="neutral" monospace>{rightOwnerId}</TagPill> : null}</div>
              </article>
            </div>
          </Surface>
        ) : (
          <CompareHeader
            compareLabel="Portfolio vs portfolio"
            leftEntity={payload.leftEntity}
            rightEntity={payload.rightEntity}
            identityContext={payload.identityContext}
            meta={payload.meta}
            metaItems={portfolioHeaderMeta(payload, topFamilyLimit)}
          />
        )
      ) : null}

      {loading ? <div className={styles.emptyState}>Loading portfolio compare…</div> : null}
      {error ? <div className={styles.emptyState}>{error}</div> : null}

      {!loading && !error && payload ? (
        <>
          <CompareTabBar activeTab={activeTab} onChange={(tab) => updateQuery({ tab })} tabs={entityTabs} />

          {visibleSummaryCards.length ? (
            <CompareSummaryCards cards={visibleSummaryCards} leftLabel={leftCompareLabel} rightLabel={rightCompareLabel} />
          ) : null}

          {activeTab === "overview" ? (
            <>
              <Surface
                title="Portfolio lenses"
                eyebrow="Overview"
                icon={<Scale size={18} />}
                description="Portfolio compare separates blocking footprint, elite density, crown-jewel strength, and current threat context instead of flattening the whole workspace into one score."
              >
                {payload.lensRows.length ? (
                  <div className={`${styles.lensGrid} ${styles.lensGridTwoColumn}`}>
                    {payload.lensRows.map((row) => (
                      <article key={row.lens} className={styles.lensCard}>
                        <div className={styles.lensHeader}>
                          <strong className={styles.lensLabel}>{row.label}</strong>
                          <span className={styles.lensMetric}>{portfolioLensMetricTitle(row)}</span>
                        </div>
                        <div className={styles.lensBody}>
                          <div className={styles.lensSides}>
                            <div className={`${styles.lensSide} ${row.winner === "left" ? styles.sideWinner : ""}`}>
                              <span className={styles.lensSideLabel}>{leftCompareLabel}</span>
                              <strong className={styles.lensValue}>{portfolioLensDisplayValue(row, "left")}</strong>
                              <div className={styles.lensMetaLine}>
                                {row.leftBandLabel ? <StatusPill tone={bandTone(row.leftBandCode)}>{row.leftBandLabel}</StatusPill> : null}
                                {row.leftPeerPercentile != null ? <TagPill tone="neutral">{Math.round(row.leftPeerPercentile)}th pct</TagPill> : null}
                              </div>
                              {row.leftPeerBucketLabel || portfolioLensAggregateCopy(row, "left") ? (
                                <span className={styles.lensMetaCopy}>
                                  {[row.leftPeerBucketLabel, portfolioLensAggregateCopy(row, "left")].filter(Boolean).join(" · ")}
                                </span>
                              ) : null}
                            </div>
                            <div className={`${styles.lensSide} ${row.winner === "right" ? styles.sideWinner : ""}`}>
                              <span className={styles.lensSideLabel}>{rightCompareLabel}</span>
                              <strong className={styles.lensValue}>{portfolioLensDisplayValue(row, "right")}</strong>
                              <div className={styles.lensMetaLine}>
                                {row.rightBandLabel ? <StatusPill tone={bandTone(row.rightBandCode)}>{row.rightBandLabel}</StatusPill> : null}
                                {row.rightPeerPercentile != null ? <TagPill tone="neutral">{Math.round(row.rightPeerPercentile)}th pct</TagPill> : null}
                              </div>
                              {row.rightPeerBucketLabel || portfolioLensAggregateCopy(row, "right") ? (
                                <span className={styles.lensMetaCopy}>
                                  {[row.rightPeerBucketLabel, portfolioLensAggregateCopy(row, "right")].filter(Boolean).join(" · ")}
                                </span>
                              ) : null}
                            </div>
                          </div>
                          <div className={styles.lensFooter}>
                            <div className={styles.lensMetaLine}>
                              <FieldPill soft>{row.samePeerBucket ? "Same peer-bucket compare" : "Cross-bucket band-first compare"}</FieldPill>
                              {row.suppressed ? <TagPill tone="warning">Suppressed</TagPill> : null}
                            </div>
                            <span className={styles.winnerCopy}>{winnerCopy(row)}</span>
                          </div>
                        </div>
                      </article>
                    ))}
                  </div>
                ) : (
                  <p className={styles.emptyState}>No compare-safe portfolio lens rows are available.</p>
                )}
              </Surface>

              {lifecycleRows.length ? (
                <Surface
                  title="Lifecycle structure compare"
                  eyebrow="Portfolio composition"
                  description="Active, pending, and abandoned or lapsed families are shown as mirrored composition, which is more informative than reading the same counts as standalone contrast rows."
                >
                  <ComparePortfolioLifecycleStructure
                    rows={lifecycleRows}
                    leftLabel={payload.leftEntity?.label ?? "Left portfolio"}
                    rightLabel={payload.rightEntity?.label ?? "Right portfolio"}
                  />
                </Surface>
              ) : null}

              {payload.topFamilyRows.length ? (
                <Surface
                  title="Top family faceoff"
                  eyebrow="Crown-jewel context"
                  description="These preview rows show which actual families carry each portfolio’s current edge, so the compare stays grounded in owned assets rather than only peer-relative bands."
                >
                  <ComparePortfolioTopFamilyFaceoff
                    rows={payload.topFamilyRows}
                    leftLabel={payload.leftEntity?.label ?? "Left portfolio"}
                    rightLabel={payload.rightEntity?.label ?? "Right portfolio"}
                  />
                </Surface>
              ) : null}
            </>
          ) : null}

          {activeTab === "technology" ? (
            <Surface
              title="Field divergence matrix"
              eyebrow="Technology shape"
              description="Portfolio technology footprint is shown as a mirrored divergence matrix so shared, left-only, and right-only fields are immediately visible."
            >
              <CompareFieldDivergenceMatrix
                rows={payload.fieldOverlapRows}
                leftLabel={`${leftCompareLabel} share`}
                rightLabel={`${rightCompareLabel} share`}
              />
            </Surface>
          ) : null}

          <Surface
            title="Methodology"
            eyebrow="Bottom notes"
            description="Keep the compare surfaces focused on the evidence. Open this only when you need scope limits or interpretation notes."
          >
            <CompareMethodology meta={payload.meta} />
          </Surface>
        </>
      ) : null}
    </div>
  );
}
