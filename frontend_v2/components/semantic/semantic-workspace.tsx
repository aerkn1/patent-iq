"use client";

import clsx from "clsx";
import Link from "next/link";
import { useEffect, useMemo, useState, useTransition } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

import { formatDecimal, formatNumber, formatPercent } from "@/components/portfolio/portfolio-format";
import { InfoPill, StatusPill, TagPill } from "@/components/ui/data-pill";
import { fetchFamilyAnchorSemanticSearch, fetchSemanticFamilySuggestions, fetchTextDiscoverySemanticSearch } from "@/lib/api/semantic-v2";
import type {
  SemanticFamilySuggestion,
  SemanticSearchPayload,
  SemanticSummaryCard,
  SemanticVectorSpace,
} from "@/lib/types/semantic-v2";

import styles from "./semantic-workspace.module.css";

function formatMetric(value: number | string | null, displayKind: SemanticSummaryCard["displayKind"]) {
  if (value == null) {
    return "—";
  }
  if (typeof value === "string") {
    return value;
  }
  if (displayKind === "count") {
    return formatNumber(value);
  }
  if (displayKind === "percent") {
    return formatPercent(value);
  }
  return formatDecimal(value, 3);
}

function scoreTone(value: number | null): "neutral" | "positive" | "warning" {
  if (value == null) {
    return "neutral";
  }
  if (value >= 0.85) {
    return "positive";
  }
  if (value >= 0.7) {
    return "warning";
  }
  return "neutral";
}

function similarityWidth(value: number | null | undefined): string {
  const safe = typeof value === "number" && Number.isFinite(value) ? Math.max(0, Math.min(1, value)) : 0;
  return `${safe * 100}%`;
}

function semanticStatusTone(value?: string | null): "positive" | "warning" | "critical" | "neutral" {
  const normalized = (value ?? "").toLowerCase();
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

const semanticCompositionPalette = [
  "#7a3520",
  "#a14f31",
  "#3f6e96",
  "#4f7cb9",
  "#31875f",
  "#d69031",
];

type SemanticQueryMode = "family" | "text";

function buildSearchParams(
  queryMode: SemanticQueryMode,
  familyId: string,
  queryText: string,
  vectorSpace: SemanticVectorSpace,
  sameFieldOnly: boolean,
  excludeSameOwner: boolean,
) {
  const params = new URLSearchParams();
  params.set("mode", queryMode);
  if (queryMode === "family" && familyId.trim()) {
    params.set("familyId", familyId.trim());
  }
  if (queryMode === "text" && queryText.trim()) {
    params.set("queryText", queryText.trim());
  }
  params.set("space", queryMode === "text" ? "abstract" : vectorSpace);
  if (queryMode === "family") {
    if (sameFieldOnly) {
      params.set("sameFieldOnly", "true");
    }
    if (excludeSameOwner) {
      params.set("excludeSameOwner", "true");
    }
  }
  return params;
}

function SemanticLookupField({
  value,
  suggestions,
  searching,
  onChange,
  onSelect,
}: {
  value: string;
  suggestions: SemanticFamilySuggestion[];
  searching: boolean;
  onChange: (value: string) => void;
  onSelect: (family: SemanticFamilySuggestion) => void;
}) {
  const [activeIndex, setActiveIndex] = useState(-1);
  const activeFamily = activeIndex >= 0 ? suggestions[activeIndex] : undefined;

  return (
    <label className={styles.fieldStack}>
      <span className={styles.fieldLabel}>Anchor family id</span>
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
            placeholder="Search semantic-covered family ids"
          />
          {searching ? <span className={styles.fieldHelp}>Searching semantic anchors…</span> : null}
          {suggestions.length > 0 ? (
            <div className={styles.lookupMenu}>
              {suggestions.map((family, index) => (
                <button
                  key={family.familyId}
                  type="button"
                  className={styles.lookupItem}
                  data-active={activeIndex === index ? "true" : "false"}
                  onClick={() => onSelect(family)}
                  onMouseEnter={() => setActiveIndex(index)}
                >
                  <span className={styles.lookupLabel}>{family.label}</span>
                  <span className={styles.lookupMeta}>
                    {family.ownerNameHarmonized ?? "Unknown owner"}
                    {family.primaryWipoField ? ` • ${family.primaryWipoField}` : ""}
                  </span>
                </button>
              ))}
            </div>
          ) : null}
        </div>
        <span className={styles.fieldHelp}>Suggestions are filtered to the currently selected semantic space.</span>
      </div>
    </label>
  );
}

export function SemanticWorkspace() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const query = searchParams ?? new URLSearchParams();
  const [isPending, startTransition] = useTransition();

  const queryMode: SemanticQueryMode = query.get("mode") === "text" ? "text" : "family";
  const familyId = query.get("familyId") ?? "";
  const queryText = query.get("queryText") ?? "";
  const runToken = query.get("run") ?? "";
  const vectorSpace = query.get("space") === "claims" ? "claims" : "abstract";
  const sameFieldOnly = query.get("sameFieldOnly") === "true";
  const excludeSameOwner = query.get("excludeSameOwner") === "true";

  const [draftFamilyId, setDraftFamilyId] = useState(familyId);
  const [draftQueryText, setDraftQueryText] = useState(queryText);
  const [suggestions, setSuggestions] = useState<SemanticFamilySuggestion[]>([]);
  const [suggestionsLoading, setSuggestionsLoading] = useState(false);
  const [searchPayload, setSearchPayload] = useState<SemanticSearchPayload | null>(null);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [searchLoading, setSearchLoading] = useState(false);

  useEffect(() => {
    setDraftFamilyId(familyId);
  }, [familyId]);

  useEffect(() => {
    setDraftQueryText(queryText);
  }, [queryText]);

  useEffect(() => {
    if (queryMode !== "family") {
      setSuggestions([]);
      setSuggestionsLoading(false);
      return;
    }
    const trimmed = draftFamilyId.trim();
    if (trimmed.length < 2) {
      setSuggestions([]);
      setSuggestionsLoading(false);
      return;
    }
    let cancelled = false;
    setSuggestionsLoading(true);
    const timeoutId = window.setTimeout(() => {
      void fetchSemanticFamilySuggestions({ query: trimmed, vectorSpace, limit: 8 })
        .then((rows) => {
          if (!cancelled) {
            setSuggestions(rows);
          }
        })
        .catch(() => {
          if (!cancelled) {
            setSuggestions([]);
          }
        })
        .finally(() => {
          if (!cancelled) {
            setSuggestionsLoading(false);
          }
        });
    }, 180);

    return () => {
      cancelled = true;
      window.clearTimeout(timeoutId);
    };
  }, [draftFamilyId, queryMode, vectorSpace]);

  useEffect(() => {
    if (queryMode === "family" && !familyId) {
      setSearchPayload(null);
      setSearchError(null);
      return;
    }
    if (queryMode === "text" && !queryText) {
      setSearchPayload(null);
      setSearchError(null);
      return;
    }

    let cancelled = false;
    setSearchLoading(true);
    setSearchError(null);
    const searchPromise =
      queryMode === "text"
        ? fetchTextDiscoverySemanticSearch({
            queryText,
            vectorSpace: "abstract",
            limit: 12,
            offset: 0,
          })
        : fetchFamilyAnchorSemanticSearch({
            familyId,
            vectorSpace,
            sameFieldOnly,
            excludeSameOwner,
            limit: 12,
            offset: 0,
          });
    searchPromise
      .then((payload) => {
        if (cancelled) {
          return;
        }
        setSearchPayload(payload);
      })
      .catch((error) => {
        if (cancelled) {
          return;
        }
        setSearchPayload(null);
        setSearchError(error instanceof Error ? error.message : "Semantic search failed.");
      })
      .finally(() => {
        if (!cancelled) {
          setSearchLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [excludeSameOwner, familyId, queryMode, queryText, runToken, sameFieldOnly, vectorSpace]);

  const methodCaveats = useMemo(() => {
    const seen = new Set<string>();
    const merged = [...(searchPayload?.meta.caveats ?? [])];
    return merged.filter((caveat) => {
      if (seen.has(caveat.code)) {
        return false;
      }
      seen.add(caveat.code);
      return true;
    });
  }, [searchPayload]);
  const visibleScopeCards = useMemo(
    () => searchPayload?.summaryCards.filter((card) => card.key === "searchable_families") ?? [],
    [searchPayload],
  );
  const displayedRows = useMemo(() => searchPayload?.resultRows.slice(0, 5) ?? [], [searchPayload]);
  const resultComposition = useMemo(() => {
    const rows = searchPayload?.resultRows ?? [];

    const fieldCounts = new Map<string, number>();

    rows.forEach((row) => {
      const field = row.primaryWipoField ?? "Unknown field";
      fieldCounts.set(field, (fieldCounts.get(field) ?? 0) + 1);
    });

    const rankedFields = [...fieldCounts.entries()]
      .sort((left, right) => right[1] - left[1] || left[0].localeCompare(right[0]))
      .map(([label, count]) => ({ label, count }));
    const topFieldRows = rankedFields.slice(0, 5);
    const otherFieldCount = rankedFields.slice(5).reduce((sum, row) => sum + row.count, 0);
    const fieldRows =
      otherFieldCount > 0
        ? [...topFieldRows, { label: "Other fields", count: otherFieldCount }]
        : topFieldRows;
    const topField = fieldRows[0] ?? null;

    return {
      total: rows.length,
      distinctFieldCount: fieldCounts.size,
      fieldRows,
      topFieldLabel: topField?.label ?? null,
      topFieldShare: topField && rows.length > 0 ? topField.count / rows.length : null,
    };
  }, [searchPayload]);

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const params = buildSearchParams(queryMode, draftFamilyId, draftQueryText, vectorSpace, sameFieldOnly, excludeSameOwner);
    params.set("run", String(Date.now()));
    startTransition(() => {
      router.replace(`/compare/semantic?${params.toString()}`, { scroll: false });
    });
  };

  const handleVectorSpaceChange = (nextVectorSpace: SemanticVectorSpace) => {
    if (queryMode === "text") {
      return;
    }
    const params = buildSearchParams(queryMode, familyId || draftFamilyId, draftQueryText, nextVectorSpace, sameFieldOnly, excludeSameOwner);
    startTransition(() => {
      router.replace(`/compare/semantic?${params.toString()}`, { scroll: false });
    });
  };

  const handleQueryModeChange = (nextMode: SemanticQueryMode) => {
    const nextVectorSpace: SemanticVectorSpace = nextMode === "text" ? "abstract" : vectorSpace;
    const params = buildSearchParams(nextMode, draftFamilyId, draftQueryText, nextVectorSpace, sameFieldOnly, excludeSameOwner);
    startTransition(() => {
      router.replace(`/compare/semantic?${params.toString()}`, { scroll: false });
    });
  };

  const handleToggle = (key: "sameFieldOnly" | "excludeSameOwner", value: boolean) => {
    const nextSameFieldOnly = key === "sameFieldOnly" ? value : sameFieldOnly;
    const nextExcludeSameOwner = key === "excludeSameOwner" ? value : excludeSameOwner;
    const params = buildSearchParams(queryMode, familyId || draftFamilyId, draftQueryText, vectorSpace, nextSameFieldOnly, nextExcludeSameOwner);
    startTransition(() => {
      router.replace(`/compare/semantic?${params.toString()}`, { scroll: false });
    });
  };

  const effectiveVectorSpace: SemanticVectorSpace = queryMode === "text" ? "abstract" : vectorSpace;
  const vectorScopeNote =
    effectiveVectorSpace === "claims"
      ? "Claim scope uses the narrower EPAB-backed similarity subset."
      : queryMode === "text"
        ? "Free-text discovery is intentionally abstract-first in the current corpus."
        : "Abstract scope uses the broader discovery corpus.";

  const freeTextExamples = [
    "battery management for wireless earbuds with adaptive charging",
    "lidar point cloud fusion for obstacle detection in autonomous driving",
    "video compression using neural motion prediction for streaming",
  ];

  return (
    <div className={styles.workspaceStack}>
      <section className={styles.controlCard}>
        <div className={styles.controlHeader}>
          <div>
            <p className={styles.eyebrow}>Search controls</p>
            <h2 className={styles.sectionTitle}>Semantic family search</h2>
          </div>
        </div>

        <div className={styles.scopeSelector}>
          <div className={styles.scopeSelectorHeader}>
            <span className={styles.fieldLabel}>Query mode</span>
            <p className={styles.scopeSelectorNote}>
              Family anchors are the most stable path. Free-text is available only as abstract-first discovery.
            </p>
          </div>
          <div className={styles.toggleRow}>
            <button
              type="button"
              className={clsx(styles.toggleButton, queryMode === "family" && styles.toggleButtonActive)}
              onClick={() => handleQueryModeChange("family")}
            >
              <strong>Anchor family</strong>
              <span>Search from a covered family id</span>
            </button>
            <button
              type="button"
              className={clsx(styles.toggleButton, queryMode === "text" && styles.toggleButtonActive)}
              onClick={() => handleQueryModeChange("text")}
            >
              <strong>Free-text discovery</strong>
              <span>Search from a technical description</span>
            </button>
          </div>
        </div>

        <div className={styles.scopeSelector}>
          <div className={styles.scopeSelectorHeader}>
            <span className={styles.fieldLabel}>Semantic scope</span>
            <p className={styles.scopeSelectorNote}>{vectorScopeNote}</p>
          </div>
          <div className={styles.toggleRow}>
            <button
              type="button"
              className={clsx(styles.toggleButton, effectiveVectorSpace === "abstract" && styles.toggleButtonActive)}
              onClick={() => handleVectorSpaceChange("abstract")}
            >
              <strong>Abstract scope</strong>
              <span>Broader discovery</span>
            </button>
            <button
              type="button"
              className={clsx(styles.toggleButton, effectiveVectorSpace === "claims" && styles.toggleButtonActive)}
              onClick={() => handleVectorSpaceChange("claims")}
              disabled={queryMode === "text"}
            >
              <strong>Claim scope</strong>
              <span>{queryMode === "text" ? "Family-anchor only" : "Narrower similarity"}</span>
            </button>
          </div>
        </div>

        <form className={styles.formGrid} onSubmit={handleSubmit}>
          {queryMode === "family" ? (
            <>
              <SemanticLookupField
                value={draftFamilyId}
                suggestions={suggestions}
                searching={suggestionsLoading}
                onChange={setDraftFamilyId}
                onSelect={(family) => {
                  setDraftFamilyId(family.familyId);
                  setSuggestions([]);
                }}
              />
              <div className={styles.optionStack}>
                <label className={styles.checkboxRow}>
                  <input
                    type="checkbox"
                    checked={sameFieldOnly}
                    onChange={(event) => handleToggle("sameFieldOnly", event.target.checked)}
                  />
                  <span>Keep only same-field candidates</span>
                </label>
                <label className={styles.checkboxRow}>
                  <input
                    type="checkbox"
                    checked={excludeSameOwner}
                    onChange={(event) => handleToggle("excludeSameOwner", event.target.checked)}
                  />
                  <span>Exclude same-owner families</span>
                </label>
              </div>
            </>
          ) : (
            <>
              <label className={styles.fieldStack}>
                <span className={styles.fieldLabel}>Discovery query</span>
                <textarea
                  className={clsx(styles.fieldInput, styles.queryTextarea)}
                  value={draftQueryText}
                  onChange={(event) => setDraftQueryText(event.target.value)}
                  placeholder="Describe the technical idea in one short English sentence"
                />
                <span className={styles.fieldHelp}>Best with short technical descriptions, not ids, owner names, or legal claim wording.</span>
              </label>
              <article className={styles.guidanceCard}>
                <div className={styles.guidanceHeader}>
                  <span className={styles.fieldLabel}>Healthy free-text patterns</span>
                  <InfoPill tone="neutral">Discovery only</InfoPill>
                </div>
                <ul className={styles.guidanceList}>
                  <li>Use short English technical descriptions similar to patent abstracts.</li>
                  <li>Name the core function, components, and outcome in one sentence.</li>
                  <li>Avoid owner names, legal phrases, and vague market or business language.</li>
                </ul>
                <div className={styles.exampleChipRow}>
                  {freeTextExamples.map((example) => (
                    <button
                      key={example}
                      type="button"
                      className={styles.exampleChip}
                      onClick={() => setDraftQueryText(example)}
                    >
                      {example}
                    </button>
                  ))}
                </div>
              </article>
            </>
          )}
          <div className={styles.actionRow}>
            <button type="submit" className={styles.actionButton} disabled={isPending || searchLoading}>
              {searchLoading || isPending ? "Searching…" : queryMode === "text" ? "Run discovery search" : "Run semantic search"}
            </button>
            <p className={styles.actionNote}>
              {queryMode === "text"
                ? "Free-text discovery is abstract-first and corpus-scoped. Use it to discover covered families, not to infer infringement or whitespace."
                : "This workspace is intentionally family-first and evidence-rich. It does not collapse claim and abstract semantics into one blended score."}
            </p>
          </div>
        </form>
      </section>

      {searchError ? (
        <section className={styles.errorCard}>
          <strong>Semantic search unavailable</strong>
          <p>{searchError}</p>
        </section>
      ) : null}

      {searchPayload ? (
        <>
          <section className={styles.contextCard}>
            <div className={styles.contextHeader}>
              <div>
                <p className={styles.eyebrow}>Search scope</p>
                <h3 className={styles.sectionTitle}>{queryMode === "text" ? "Query and corpus scope" : "Anchor and corpus scope"}</h3>
              </div>
              {searchPayload.meta.coverage ? (
                <StatusPill tone={searchPayload.meta.coverage.status === "low" ? "warning" : "neutral"}>
                  {searchPayload.meta.coverage.status} coverage
                </StatusPill>
              ) : null}
            </div>
            <div className={styles.scopeLayout}>
              <div className={styles.contextGrid}>
                {searchPayload.queryContext.map((item) => (
                  <div key={item.key} className={styles.contextItem}>
                    <span>{item.label}</span>
                    <strong>{item.value}</strong>
                  </div>
                ))}
              </div>
              {visibleScopeCards.length > 0 ? (
                <div className={styles.summaryGrid}>
                  {visibleScopeCards.map((card) => (
                    <article key={card.key} className={styles.summaryCard}>
                      <span className={styles.summaryLabel}>{card.label}</span>
                      <strong className={styles.summaryValue}>{formatMetric(card.value, card.displayKind)}</strong>
                      {card.note ? <p className={styles.summaryNote}>{card.note}</p> : null}
                    </article>
                  ))}
                </div>
              ) : null}
              {searchPayload.summary?.anchorTextExcerpt ? (
                <article className={styles.anchorTextCard}>
                  <div className={styles.anchorTextHeader}>
                    <span className={styles.fieldLabel}>Anchor searchable text</span>
                    {searchPayload.summary.anchorTextProvenance ? (
                      <InfoPill tone="neutral">{searchPayload.summary.anchorTextProvenance}</InfoPill>
                    ) : null}
                  </div>
                  <p className={styles.anchorTextExcerpt}>{searchPayload.summary.anchorTextExcerpt}</p>
                </article>
              ) : searchPayload.summary?.queryTextExcerpt ? (
                <article className={styles.anchorTextCard}>
                  <div className={styles.anchorTextHeader}>
                    <span className={styles.fieldLabel}>Search text</span>
                    <InfoPill tone="neutral">Abstract-first discovery</InfoPill>
                  </div>
                  <p className={styles.anchorTextExcerpt}>{searchPayload.summary.queryTextExcerpt}</p>
                </article>
              ) : null}
            </div>
          </section>

          {resultComposition.total > 0 ? (
            <section className={styles.contextCard}>
              <div className={styles.contextHeader}>
                <div>
                  <p className={styles.eyebrow}>Result composition</p>
                  <h3 className={styles.sectionTitle}>Current ranked-set mix</h3>
                </div>
                <InfoPill tone="neutral">{formatNumber(resultComposition.total)} retrieved rows</InfoPill>
              </div>
              <div className={styles.compositionGrid}>
                <article className={styles.compositionCard}>
                  <div className={styles.compositionHeader}>
                    <span className={styles.fieldLabel}>Field mix</span>
                    <p className={styles.scopeSelectorNote}>How the current semantic result set distributes across primary fields.</p>
                  </div>
                  <div className={styles.compositionPieLayout}>
                    <div className={styles.compositionPieChart}>
                      <ResponsiveContainer width="100%" height={220}>
                        <PieChart>
                          <Pie
                            data={resultComposition.fieldRows}
                            dataKey="count"
                            nameKey="label"
                            innerRadius={48}
                            outerRadius={84}
                            stroke="rgba(255,255,255,0.94)"
                            strokeWidth={2}
                            paddingAngle={resultComposition.fieldRows.length > 1 ? 2 : 0}
                            isAnimationActive={false}
                          >
                            {resultComposition.fieldRows.map((row, index) => (
                              <Cell key={`${row.label}-${index}`} fill={semanticCompositionPalette[index % semanticCompositionPalette.length]} />
                            ))}
                          </Pie>
                          <Tooltip
                            formatter={(value: number, _name: string, item) => {
                              const count = Number(value ?? 0);
                              const share = resultComposition.total > 0 ? count / resultComposition.total : 0;
                              return [`${formatNumber(count)} rows · ${formatPercent(share)}`, String(item?.payload?.label ?? "Field")];
                            }}
                          />
                        </PieChart>
                      </ResponsiveContainer>
                    </div>
                    <div className={styles.compositionSideRail}>
                      <div className={styles.compositionHighlights}>
                        <div className={styles.compositionHighlight}>
                          <span>Retrieved rows</span>
                          <strong>{formatNumber(resultComposition.total)}</strong>
                        </div>
                        <div className={styles.compositionHighlight}>
                          <span>Distinct fields</span>
                          <strong>{formatNumber(resultComposition.distinctFieldCount)}</strong>
                        </div>
                        <div className={styles.compositionHighlight}>
                          <span>Leading field</span>
                          <strong>{resultComposition.topFieldLabel ?? "—"}</strong>
                          <small>{resultComposition.topFieldShare != null ? formatPercent(resultComposition.topFieldShare) : "—"}</small>
                        </div>
                      </div>
                      <div className={styles.compositionLegend}>
                        {resultComposition.fieldRows.map((row, index) => (
                          <div
                            key={`${row.label}-legend`}
                            className={styles.compositionLegendItem}
                            style={{ ["--composition-color" as string]: semanticCompositionPalette[index % semanticCompositionPalette.length] }}
                          >
                            <span className={styles.compositionLegendIdentity}>
                              <span
                                className={styles.compositionLegendSwatch}
                                style={{ backgroundColor: semanticCompositionPalette[index % semanticCompositionPalette.length] }}
                              />
                              <span>{row.label}</span>
                            </span>
                            <strong>{formatPercent(resultComposition.total > 0 ? row.count / resultComposition.total : 0)}</strong>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </article>
              </div>
            </section>
          ) : null}

          <section className={styles.resultsCard}>
            <div className={styles.resultsHeader}>
              <div>
                <p className={styles.eyebrow}>Result list</p>
                <h3 className={styles.sectionTitle}>Ranked semantic neighbors</h3>
              </div>
              <div className={styles.resultsHeaderMeta}>
                <InfoPill tone="neutral">
                  {searchPayload.meta.pagination?.totalCount != null ? formatNumber(searchPayload.meta.pagination.totalCount) : "—"} candidates
                </InfoPill>
                <InfoPill tone="neutral">Top 5 shown</InfoPill>
              </div>
            </div>

            <div className={styles.resultsList}>
              {displayedRows.map((row) => (
                <article key={row.familyId} className={styles.resultCard}>
                  <div className={styles.resultHeader}>
                    <div className={styles.resultIdentity}>
                      <strong>{row.familyId}</strong>
                      {row.familyTitle ? <p className={styles.resultTitle}>{row.familyTitle}</p> : null}
                      <p className={styles.resultOwner}>{row.ownerNameHarmonized ?? "Unassigned"}</p>
                    </div>
                    <StatusPill tone={scoreTone(row.semanticSimilarity)}>
                      {row.semanticSimilarity != null ? formatDecimal(row.semanticSimilarity, 3) : "—"}
                    </StatusPill>
                  </div>
                  <div className={styles.resultSignal}>
                    <span className={styles.resultSignalLabel}>Semantic match</span>
                    <div className={styles.resultSignalTrack}>
                      <div className={styles.resultSignalFill} style={{ width: similarityWidth(row.semanticSimilarity) }} />
                    </div>
                  </div>
                  <div className={styles.pillRow}>
                    {row.primaryWipoField ? <TagPill tone="neutral">{row.primaryWipoField}</TagPill> : null}
                    {row.familyCompositeStatus ? <StatusPill tone={semanticStatusTone(row.familyCompositeStatus)}>{row.familyCompositeStatus}</StatusPill> : null}
                  </div>
                  {row.textExcerpt ? <p className={styles.resultExcerpt}>{row.textExcerpt}</p> : null}
                  <div className={styles.resultMetricRow}>
                    <div className={styles.resultMetric}>
                      <span>Blocking</span>
                      <strong>{formatDecimal(row.familyUiBlockingPowerScore, 2)}</strong>
                    </div>
                    <div className={styles.resultMetric}>
                      <span>OECD</span>
                      <strong>{formatPercent(row.oecdQualityPercentile, 1)}</strong>
                    </div>
                  </div>
                  <Link href={`/family/${row.familyId}`} className={styles.sourceLink}>
                    Open family page
                  </Link>
                </article>
              ))}
            </div>
          </section>

          <section className={styles.caveatCard}>
            <div className={styles.resultsHeader}>
              <div>
                <p className={styles.eyebrow}>Methodology</p>
                <h3 className={styles.sectionTitle}>Semantic scope and caveats</h3>
              </div>
            </div>
            <details className={styles.caveatDisclosure}>
              <summary className={styles.caveatDisclosureSummary}>
                <span>{methodCaveats.length} methodology note{methodCaveats.length === 1 ? "" : "s"}</span>
              </summary>
              <div className={styles.caveatList}>
                {methodCaveats.map((caveat) => (
                  <article key={caveat.code} className={styles.caveatItem}>
                    <strong>{caveat.title}</strong>
                    <p>{caveat.detail}</p>
                  </article>
                ))}
              </div>
            </details>
          </section>
        </>
      ) : null}
    </div>
  );
}
