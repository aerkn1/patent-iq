"use client";

import { Scale, Shuffle } from "lucide-react";
import { type ReactNode, useCallback, useEffect, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";

import { fetchFamilyCompare, fetchFamilyCompareLookup, fetchFamilyCompareSuggestions } from "@/lib/api/compare-v2";
import {
  CompareContrastRows,
  CompareFieldDivergenceMatrix,
  CompareHeader,
  CompareLegalFootprintRows,
  CompareMethodology,
  CompareSummaryCards,
  CompareTabBar,
  type CompareTab,
  type CompareTabSpec,
} from "@/components/compare/compare-rendering";
import { StatusPill, TagPill } from "@/components/ui/data-pill";
import { Surface } from "@/components/ui/surface";
import type { CompareScopeLookup, FamilyCompareLensRow, FamilyComparePayload, FamilyCompareSuggestion } from "@/lib/types/compare-v2";

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

function winnerCopy(row: FamilyCompareLensRow): string {
  if (row.winner === "left") {
    return row.sameCohort ? `${row.leftFamilyLabel} leads on peer percentile` : `${row.leftFamilyLabel} leads on cohort band`;
  }
  if (row.winner === "right") {
    return row.sameCohort ? `${row.rightFamilyLabel} leads on peer percentile` : `${row.rightFamilyLabel} leads on cohort band`;
  }
  return "No clear winner signal";
}

function lensValue(row: FamilyCompareLensRow, side: "left" | "right"): string {
  if (row.lens === "legal_durability") {
    const percentile = side === "left" ? row.leftPeerPercentile : row.rightPeerPercentile;
    if (percentile != null) {
      return `${percentile.toFixed(1)} / 100`;
    }
  }
  const value = side === "left" ? row.leftRawValue : row.rightRawValue;
  return value.toFixed(2);
}

function hasText(value: string): boolean {
  return Boolean(value.trim());
}

function looksLikeFamilyId(value: string): boolean {
  return /^\d{6,}$/.test(value.trim());
}

function familyCompareEntityLabel(label: string | null | undefined, fallback: string): string {
  const text = label?.trim();
  return text && text.length > 0 ? text : fallback;
}

function formatLookupText(lookup: CompareScopeLookup | null): string | null {
  if (!lookup) {
    return null;
  }
  if (!lookup.inScope) {
    return lookup.note ?? "Family not in compare scope.";
  }
  const parts = ["In compare scope"];
  if (lookup.primaryField) {
    parts.push(lookup.primaryField);
  }
  if (lookup.status) {
    parts.push(lookup.status.replace(/_/g, " "));
  }
  return parts.join(" · ");
}

function FamilyLookupField({
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
  suggestions: FamilyCompareSuggestion[];
  searching: boolean;
  helper?: ReactNode;
  onChange: (value: string) => void;
  onSelect: (family: FamilyCompareSuggestion) => void;
}) {
  const [activeIndex, setActiveIndex] = useState(-1);
  const activeFamily = activeIndex >= 0 ? suggestions[activeIndex] : undefined;

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
              if (event.key === "Enter" && activeFamily) {
                event.preventDefault();
                onSelect(activeFamily);
              }
            }}
            placeholder="e.g. 57400072"
          />
          {searching ? <span className={styles.fieldHelp}>Searching in-scope families…</span> : null}
          {suggestions.length > 0 ? (
            <div className={styles.lookupMenu}>
              {suggestions.map((family, index) => (
                <button
                  key={`${label}-${family.familyId}`}
                  type="button"
                  className={styles.lookupItem}
                  data-active={activeIndex === index ? "true" : "false"}
                  onClick={() => onSelect(family)}
                  onMouseEnter={() => setActiveIndex(index)}
                >
                  <span className={styles.lookupLabel}>{family.label}</span>
                  <span className={styles.lookupMeta}>
                    {family.ownerLabel ?? "Unknown owner"}
                    {family.primaryField ? ` • ${family.primaryField}` : ""}
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

function familyHeaderMeta(payload: FamilyComparePayload | null): string[] {
  if (!payload) {
    return [];
  }

  const cohortFlags = payload.lensRows.map((row) => row.sameCohort);
  const cohortLabel = cohortFlags.every(Boolean)
    ? "Same cohort"
    : cohortFlags.every((flag) => !flag)
      ? "Cross cohort"
      : "Mixed cohort";

  return ["Entity compare", cohortLabel];
}

export function FamilyCompareWorkspace() {
  const router = useRouter();
  const pathname = usePathname() ?? "/compare/families";
  const searchParams = useSearchParams();
  const query = searchParams ?? new URLSearchParams();

  const leftFamilyId = query.get("left_family_id") ?? "";
  const rightFamilyId = query.get("right_family_id") ?? "";
  const staleMode = query.get("mode");
  const staleTimesliceFamilyId = query.get("family_id") ?? "";
  const staleBaseYear = query.get("base_year") ?? "";
  const staleCompareYear = query.get("compare_year") ?? "";
  const rawTab = query.get("tab");
  const activeTab: CompareTab = rawTab === "technology" ? rawTab : "overview";

  const [leftInput, setLeftInput] = useState(leftFamilyId);
  const [rightInput, setRightInput] = useState(rightFamilyId);
  const [leftSuggestions, setLeftSuggestions] = useState<FamilyCompareSuggestion[]>([]);
  const [rightSuggestions, setRightSuggestions] = useState<FamilyCompareSuggestion[]>([]);
  const [leftSearching, setLeftSearching] = useState(false);
  const [rightSearching, setRightSearching] = useState(false);
  const [payload, setPayload] = useState<FamilyComparePayload | null>(null);
  const [leftLookup, setLeftLookup] = useState<CompareScopeLookup | null>(null);
  const [rightLookup, setRightLookup] = useState<CompareScopeLookup | null>(null);
  const [leftLookupLoading, setLeftLookupLoading] = useState(false);
  const [rightLookupLoading, setRightLookupLoading] = useState(false);
  const [leftLookupError, setLeftLookupError] = useState<string | null>(null);
  const [rightLookupError, setRightLookupError] = useState<string | null>(null);
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
    setLeftInput(leftFamilyId);
  }, [leftFamilyId]);

  useEffect(() => {
    setRightInput(rightFamilyId);
  }, [rightFamilyId]);

  useEffect(() => {
    const candidate = leftInput.trim();
    if (candidate.length < 2 || looksLikeFamilyId(candidate)) {
      setLeftSuggestions([]);
      setLeftSearching(false);
      return;
    }
    let cancelled = false;
    const controller = new AbortController();
    setLeftSearching(true);
    const timeoutId = window.setTimeout(() => {
      void fetchFamilyCompareSuggestions(candidate, 8, controller.signal)
        .then((rows) => {
          if (!cancelled) {
            setLeftSuggestions(rows);
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
  }, [leftInput]);

  useEffect(() => {
    const candidate = rightInput.trim();
    if (candidate.length < 2 || looksLikeFamilyId(candidate)) {
      setRightSuggestions([]);
      setRightSearching(false);
      return;
    }
    let cancelled = false;
    const controller = new AbortController();
    setRightSearching(true);
    const timeoutId = window.setTimeout(() => {
      void fetchFamilyCompareSuggestions(candidate, 8, controller.signal)
        .then((rows) => {
          if (!cancelled) {
            setRightSuggestions(rows);
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
  }, [rightInput]);

  useEffect(() => {
    const candidate = leftInput.trim();
    if (!candidate || !looksLikeFamilyId(candidate)) {
      setLeftLookup(null);
      setLeftLookupError(null);
      setLeftLookupLoading(false);
      return;
    }
    let cancelled = false;
    const controller = new AbortController();
    setLeftLookupLoading(true);
    setLeftLookupError(null);
    const timeoutId = window.setTimeout(() => {
      void fetchFamilyCompareLookup(candidate, controller.signal)
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
    }, 180);

    return () => {
      cancelled = true;
      controller.abort();
      window.clearTimeout(timeoutId);
    };
  }, [leftInput]);

  useEffect(() => {
    const candidate = rightInput.trim();
    if (!candidate || !looksLikeFamilyId(candidate)) {
      setRightLookup(null);
      setRightLookupError(null);
      setRightLookupLoading(false);
      return;
    }
    let cancelled = false;
    const controller = new AbortController();
    setRightLookupLoading(true);
    setRightLookupError(null);
    const timeoutId = window.setTimeout(() => {
      void fetchFamilyCompareLookup(candidate, controller.signal)
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
    }, 180);

    return () => {
      cancelled = true;
      controller.abort();
      window.clearTimeout(timeoutId);
    };
  }, [rightInput]);

  useEffect(() => {
    if (!leftFamilyId || !rightFamilyId) {
      setPayload(null);
      setError(null);
      setLoading(false);
      return;
    }

    let cancelled = false;
    setLoading(true);
    setError(null);

    void fetchFamilyCompare({ leftFamilyId, rightFamilyId })
      .then((response) => {
        if (!cancelled) {
          setPayload(response);
        }
      })
      .catch((ex) => {
        if (!cancelled) {
          setPayload(null);
          setError(ex instanceof Error ? ex.message : "Could not load family compare.");
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
  }, [leftFamilyId, rightFamilyId]);

  useEffect(() => {
    if (!staleMode && !staleTimesliceFamilyId && !staleBaseYear && !staleCompareYear) {
      return;
    }
    updateQuery({
      mode: null,
      family_id: null,
      base_year: null,
      compare_year: null,
    });
  }, [staleMode, staleTimesliceFamilyId, staleBaseYear, staleCompareYear, updateQuery]);

  const submitEntity = () => {
    updateQuery({
      left_family_id: leftInput.trim() || null,
      right_family_id: rightInput.trim() || null,
      mode: null,
      family_id: null,
      base_year: null,
      compare_year: null,
    });
  };

  const swapSides = () => {
    setLeftInput(rightInput);
    setRightInput(leftInput);
  };

  const canRunEntity =
    hasText(leftInput) &&
    hasText(rightInput) &&
    leftLookup?.inScope === true &&
    rightLookup?.inScope === true;
  const activeTabs = entityTabs;
  const legalFootprintRows = payload?.supportRows.filter((row) => row.kind === "jurisdiction_preview") ?? [];
  const visibleContrastRows = payload?.contrastRows.filter((row) => row.key !== "data_completeness") ?? [];
  const visibleSummaryCards =
    payload?.summaryCards.filter(
      (card) =>
        card.key !== "blocking_posture" &&
        card.key !== "legal_durability" &&
        card.key !== "citation_heritage" &&
        card.key !== "family_size" &&
        card.key !== "future_outlook_3y",
    ) ?? [];
  const leftCompareLabel = familyCompareEntityLabel(payload?.leftEntity?.label ?? null, "Left family");
  const rightCompareLabel = familyCompareEntityLabel(payload?.rightEntity?.label ?? null, "Right family");

  return (
    <div className={styles.workspaceStack}>
      <Surface
        className={styles.compactControlSurface}
        title="Select two families"
        eyebrow="Family compare"
        description="Enter two family ids to compare their current profiles."
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
            <FamilyLookupField
              label="Left family"
              value={leftInput}
              suggestions={leftSuggestions}
              searching={leftSearching}
              helper={
                leftLookupLoading ? (
                  <span className={styles.fieldHelp}>Checking compare scope…</span>
                ) : leftLookupError ? (
                  <span className={styles.fieldHelp}>{leftLookupError}</span>
                ) : hasText(leftInput) && !looksLikeFamilyId(leftInput) ? (
                  <span className={styles.fieldHelp}>Pick a suggestion or enter a full family id to check compare scope.</span>
                ) : hasText(leftInput) && formatLookupText(leftLookup) ? (
                  <span className={`${styles.scopeHint} ${leftLookup?.inScope ? styles.scopeHintPositive : styles.scopeHintCritical}`}>
                    {formatLookupText(leftLookup)}
                  </span>
                ) : null
              }
              onChange={setLeftInput}
              onSelect={(family) => {
                setLeftInput(family.familyId);
                setLeftSuggestions([]);
              }}
            />
            <FamilyLookupField
              label="Right family"
              value={rightInput}
              suggestions={rightSuggestions}
              searching={rightSearching}
              helper={
                rightLookupLoading ? (
                  <span className={styles.fieldHelp}>Checking compare scope…</span>
                ) : rightLookupError ? (
                  <span className={styles.fieldHelp}>{rightLookupError}</span>
                ) : hasText(rightInput) && !looksLikeFamilyId(rightInput) ? (
                  <span className={styles.fieldHelp}>Pick a suggestion or enter a full family id to check compare scope.</span>
                ) : hasText(rightInput) && formatLookupText(rightLookup) ? (
                  <span className={`${styles.scopeHint} ${rightLookup?.inScope ? styles.scopeHintPositive : styles.scopeHintCritical}`}>
                    {formatLookupText(rightLookup)}
                  </span>
                ) : null
              }
              onChange={setRightInput}
              onSelect={(family) => {
                setRightInput(family.familyId);
                setRightSuggestions([]);
              }}
            />
          </div>
          <div className={styles.actionRow}>
            <button type="submit" className={styles.actionButton} disabled={!canRunEntity}>
              Run family compare
            </button>
            <button type="button" className={styles.ghostButton} onClick={swapSides}>
              <Shuffle size={16} />
              Swap sides
            </button>
          </div>
        </form>
      </Surface>

      {leftFamilyId || rightFamilyId ? (
        !payload ? (
          <Surface
            title="Compare context"
            eyebrow="Active query"
            description="The left side is the current anchor. If only one family is prefilled, use the second field above to complete the compare."
          >
            <div className={styles.entityGrid}>
              <article className={styles.entityCard}>
                <span className={styles.entityLabel}>Left family</span>
                <strong className={styles.entityTitle}>{leftFamilyId || "Pending"}</strong>
                <div className={styles.entityMeta}>{leftFamilyId ? <TagPill tone="neutral" monospace>{leftFamilyId}</TagPill> : null}</div>
              </article>
              <article className={styles.entityCard}>
                <span className={styles.entityLabel}>Right family</span>
                <strong className={styles.entityTitle}>{rightFamilyId || "Pending"}</strong>
                <div className={styles.entityMeta}>{rightFamilyId ? <TagPill tone="neutral" monospace>{rightFamilyId}</TagPill> : null}</div>
              </article>
            </div>
          </Surface>
        ) : (
          <CompareHeader
            compareLabel="Family vs family"
            leftEntity={payload.leftEntity}
            rightEntity={payload.rightEntity}
            identityContext={payload.identityContext}
            meta={payload.meta}
            metaItems={familyHeaderMeta(payload)}
          />
        )
      ) : null}

      {loading ? <div className={styles.emptyState}>Loading family compare…</div> : null}
      {error ? <div className={styles.emptyState}>{error}</div> : null}

      {!loading && !error && payload ? (
        <>
          <CompareTabBar activeTab={activeTab} onChange={(tab) => updateQuery({ tab })} tabs={activeTabs} />

          {visibleSummaryCards.length ? (
            <CompareSummaryCards cards={visibleSummaryCards} leftLabel={leftCompareLabel} rightLabel={rightCompareLabel} />
          ) : null}

          {activeTab === "overview" ? (
            <>
              <div className={styles.compareSectionGrid}>
                <Surface
                  title="Three family lenses"
                  eyebrow="Overview"
                  icon={<Scale size={18} />}
                  description="Blocking, legal durability, and citation heritage remain separate so the compare does not collapse into one fake precision score."
                >
                  {payload.lensRows.length ? (
                    <div className={styles.lensGrid}>
                      {payload.lensRows.map((row) => (
                        <article key={row.lens} className={styles.lensCard}>
                          <div className={styles.lensHeader}>
                            <strong className={styles.lensLabel}>{row.label}</strong>
                            <span className={styles.lensMetric}>{row.metricLabel}</span>
                          </div>
                          <div className={styles.lensBody}>
                            <div className={styles.lensSides}>
                              <div className={`${styles.lensSide} ${row.winner === "left" ? styles.sideWinner : ""}`}>
                                <span className={styles.lensSideLabel}>{leftCompareLabel}</span>
                                <strong className={styles.lensValue}>{lensValue(row, "left")}</strong>
                                <div className={styles.lensMetaLine}>
                                  {row.leftBandLabel ? <StatusPill tone={bandTone(row.leftBandCode)}>{row.leftBandLabel}</StatusPill> : null}
                                  {row.leftPeerPercentile != null ? <TagPill tone="neutral">{Math.round(row.leftPeerPercentile)}th pct</TagPill> : null}
                                </div>
                                {row.leftPeerCohortLabel ? <span className={styles.lensMetaCopy}>{row.leftPeerCohortLabel}</span> : null}
                              </div>
                              <div className={`${styles.lensSide} ${row.winner === "right" ? styles.sideWinner : ""}`}>
                                <span className={styles.lensSideLabel}>{rightCompareLabel}</span>
                                <strong className={styles.lensValue}>{lensValue(row, "right")}</strong>
                                <div className={styles.lensMetaLine}>
                                  {row.rightBandLabel ? <StatusPill tone={bandTone(row.rightBandCode)}>{row.rightBandLabel}</StatusPill> : null}
                                  {row.rightPeerPercentile != null ? <TagPill tone="neutral">{Math.round(row.rightPeerPercentile)}th pct</TagPill> : null}
                                </div>
                                {row.rightPeerCohortLabel ? <span className={styles.lensMetaCopy}>{row.rightPeerCohortLabel}</span> : null}
                              </div>
                            </div>
                            <div className={styles.lensFooter}>
                              <div className={styles.lensMetaLine}>
                                <TagPill tone="neutral">{row.sameCohort ? "Same cohort percentile compare" : "Cross-cohort band-first compare"}</TagPill>
                                {row.winnerBasis ? <TagPill tone="neutral">{row.winnerBasis}</TagPill> : null}
                              </div>
                              <span className={styles.winnerCopy}>{winnerCopy(row)}</span>
                            </div>
                          </div>
                        </article>
                      ))}
                    </div>
                  ) : (
                    <p className={styles.emptyState}>No compare-safe family lens rows are available.</p>
                  )}
                </Surface>

                <Surface
                  title="Blocking and status contrast"
                  eyebrow="Direct evidence"
                  description="These rows keep the compare grounded in current legal footing, breadth, and coverage rather than only percentile language."
                >
                  <CompareContrastRows rows={visibleContrastRows} leftLabel={leftCompareLabel} rightLabel={rightCompareLabel} />
                </Surface>
              </div>

              <Surface
                title="Legal footprint compare"
                eyebrow="Jurisdiction ladder"
                description="Jurisdiction-level legal rows are the strongest analyst-grade grounding in this family compare, so they are promoted here instead of being left in generic evidence."
              >
                <CompareLegalFootprintRows
                  rows={legalFootprintRows}
                  leftLabel={payload.leftEntity?.label ?? "Left family"}
                  rightLabel={payload.rightEntity?.label ?? "Right family"}
                />
              </Surface>
            </>
          ) : null}

          {activeTab === "technology" ? (
            <Surface
              title="Field divergence matrix"
              eyebrow="Technology shape"
              description="This matrix shows shared, left-only, and right-only field contribution so divergence is readable at a glance instead of as generic overlap cards."
            >
              <CompareFieldDivergenceMatrix rows={payload.fieldOverlapRows} leftLabel={leftCompareLabel} rightLabel={rightCompareLabel} />
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
