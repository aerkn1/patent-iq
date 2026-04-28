"use client";

import Link from "next/link";
import { BookOpenText, FileClock, Landmark } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { formatDecimal, formatNumber } from "@/components/portfolio/portfolio-format";
import { InfoPill, StatusPill, TagPill } from "@/components/ui/data-pill";
import { Surface } from "@/components/ui/surface";
import { useWorkspaceContextOverride } from "@/components/ui/workspace-context";
import { fetchPublicationOverview, fetchPublicationSection } from "@/lib/api/publication-v2";
import type {
  PublicationAvailability,
  PublicationFact,
  PublicationOverviewPayload,
  PublicationSectionPayload,
} from "@/lib/types/publication-v2";

import styles from "./publication-workspace.module.css";

type PublicationWorkspaceProps = {
  publicationId: string;
};

function formatValue(value: unknown): string {
  if (value == null) {
    return "—";
  }
  if (typeof value === "boolean") {
    return value ? "Yes" : "No";
  }
  if (typeof value === "number") {
    return Number.isInteger(value) ? formatNumber(value) : formatDecimal(value, 2);
  }
  return String(value);
}

function toneForAvailability(status: string): "positive" | "warning" | "critical" | "neutral" {
  const normalized = status.toLowerCase();
  if (normalized.includes("available")) {
    return "positive";
  }
  if (normalized.includes("candidate")) {
    return "warning";
  }
  if (normalized.includes("missing") || normalized.includes("not_supported")) {
    return "critical";
  }
  return "neutral";
}

function toneForSupportLevel(value: PublicationOverviewPayload["meta"]["supportLevel"]): "positive" | "warning" | "critical" {
  if (value === "strong") {
    return "positive";
  }
  if (value === "moderate" || value === "candidate_only") {
    return "warning";
  }
  return "critical";
}

function toneForRelatedStage(value: string | null | undefined): "positive" | "info" | "warning" | "neutral" {
  const normalized = String(value ?? "").toLowerCase();
  if (normalized.includes("grant")) {
    return "positive";
  }
  if (normalized.includes("application")) {
    return "info";
  }
  if (normalized.includes("pending")) {
    return "warning";
  }
  return "neutral";
}

function FactList({ facts }: { facts: PublicationFact[] }) {
  if (facts.length === 0) {
    return <p className={styles.stateText}>No factual rows are available.</p>;
  }

  return (
    <div className={styles.factsList}>
      {facts.map((fact) => (
        <article key={fact.label} className={styles.factRow}>
          <span className={styles.factLabel}>{fact.label}</span>
          <strong className={styles.factValue}>{formatValue(fact.value)}</strong>
          {fact.detail ? <p className={styles.factDetail}>{fact.detail}</p> : null}
        </article>
      ))}
    </div>
  );
}

function AvailabilityList({ items }: { items: PublicationAvailability[] }) {
  if (items.length === 0) {
    return <p className={styles.stateText}>No text availability rows are available.</p>;
  }

  return (
    <div className={styles.availabilityList}>
      {items.map((item) => (
        <article key={item.key} className={styles.availabilityCard}>
          <div className={styles.availabilityHead}>
            <strong className={styles.availabilityTitle}>{item.label}</strong>
            <StatusPill tone={toneForAvailability(item.status)}>{item.status.replace(/_/g, " ")}</StatusPill>
          </div>
          {item.detail ? <p className={styles.availabilityDetail}>{item.detail}</p> : null}
        </article>
      ))}
    </div>
  );
}

function SupportDetails({
  supportLevel,
  availability,
  caveats,
}: {
  supportLevel: PublicationOverviewPayload["meta"]["supportLevel"];
  availability: PublicationAvailability[];
  caveats: PublicationOverviewPayload["meta"]["caveats"];
}) {
  const detailCount = availability.length + caveats.length;

  return (
    <section className={styles.supportPanel}>
      <div className={styles.supportPanelHead}>
        <div className={styles.supportPanelCopy}>
          <span className={styles.supportPanelEyebrow}>Support</span>
          <h2 className={styles.supportPanelTitle}>Source and support</h2>
        </div>
        <InfoPill tone="neutral">{detailCount} notes</InfoPill>
      </div>
      <details className={styles.supportDetails}>
        <summary className={styles.supportSummary}>
          <span>Support context</span>
          <StatusPill tone={toneForSupportLevel(supportLevel)}>{supportLevel.replace(/_/g, " ")} support</StatusPill>
        </summary>
        <div className={styles.supportDetailsBody}>
          {availability.length > 0 ? (
            <section className={styles.supportSection}>
              <h3 className={styles.supportHeading}>Availability</h3>
              <AvailabilityList items={availability} />
            </section>
          ) : null}
          {caveats.length > 0 ? (
            <section className={styles.supportSection}>
              <h3 className={styles.supportHeading}>Methodology</h3>
              <div className={styles.factsList}>
                {caveats.map((caveat) => (
                  <article key={`${caveat.code}-${caveat.title}`} className={styles.factRow}>
                    <span className={styles.factLabel}>{caveat.code}</span>
                    <strong className={styles.factValue}>{caveat.title}</strong>
                    <p className={styles.factDetail}>{caveat.detail}</p>
                  </article>
                ))}
              </div>
            </section>
          ) : null}
          {detailCount === 0 ? <p className={styles.stateText}>No support notes are available for this publication.</p> : null}
        </div>
      </details>
    </section>
  );
}

function TextPreviewCard({ section, loading }: { section: PublicationSectionPayload | null; loading: boolean }) {
  if (loading && !section) {
    return (
      <Surface title="Abstract and claims" icon={<BookOpenText size={18} />}>
        <p className={styles.stateText}>Loading abstract and claim text…</p>
      </Surface>
    );
  }

  const rows = section?.rows ?? [];
  const abstractRow = rows.find((row) => String(row.panel_key ?? "") === "abstract");
  const claimRow = rows.find((row) => String(row.panel_key ?? "") === "claim_1");

  return (
    <Surface title="Abstract and claims" icon={<BookOpenText size={18} />}>
      <div className={styles.previewStack}>
        <section className={styles.previewBlock}>
          <div className={styles.previewHead}>
            <h3 className={styles.previewTitle}>Abstract</h3>
            <StatusPill tone={abstractRow?.available ? "positive" : "critical"}>
              {abstractRow?.available ? "Available" : "Missing"}
            </StatusPill>
          </div>
          {abstractRow?.text ? (
            <p className={styles.previewText}>{String(abstractRow.text)}</p>
          ) : (
            <p className={styles.stateText}>No abstract text was returned for this publication.</p>
          )}
        </section>

        <section className={styles.previewBlock}>
          <div className={styles.previewHead}>
            <h3 className={styles.previewTitle}>Claim 1</h3>
            <StatusPill tone={claimRow?.available ? "positive" : "critical"}>
              {claimRow?.available ? "Available" : "Missing"}
            </StatusPill>
          </div>
          {claimRow?.text ? (
            <p className={styles.previewText}>{String(claimRow.text)}</p>
          ) : (
            <p className={styles.stateText}>No claim text was returned for this publication.</p>
          )}
        </section>
      </div>
    </Surface>
  );
}

function TimelinePanel({ section, loading }: { section: PublicationSectionPayload | null; loading: boolean }) {
  if (loading && !section) {
    return (
      <Surface title="Legal and register timeline" description="Loading publication milestones.">
        <p className={styles.stateText}>Loading chronology…</p>
      </Surface>
    );
  }

  const rows = section?.rows ?? [];
  return (
    <Surface
      title="Legal and register timeline"
      icon={<FileClock size={18} />}
      description="Milestone chronology for publication, search, and register events."
      badge={<InfoPill tone="neutral">{rows.length} events</InfoPill>}
    >
      {rows.length === 0 ? (
        <p className={styles.stateText}>No dated events are available for this publication.</p>
      ) : (
        <div className={styles.tableWrap}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Date</th>
                <th>Event</th>
                <th>Detail</th>
                <th>Source</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row, index) => (
                <tr key={`${row.event_type ?? "event"}-${index}`}>
                  <td>{formatValue(row.event_date)}</td>
                  <td>{formatValue(row.event_type)}</td>
                  <td>{formatValue(row.detail)}</td>
                  <td>{formatValue(row.source)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Surface>
  );
}

function RegisterPanel({ section, loading }: { section: PublicationSectionPayload | null; loading: boolean }) {
  if (loading && !section) {
    return (
      <Surface title="Register evidence" description="Loading EP Register evidence.">
        <p className={styles.stateText}>Loading register evidence…</p>
      </Surface>
    );
  }

  const rows = section?.rows ?? [];
  return (
    <Surface
      title="Register evidence"
      icon={<Landmark size={18} />}
      description="EP Register facts, procedure state, and observed operators when available."
      badge={<StatusPill tone={section ? toneForSupportLevel(section.meta.supportLevel) : "neutral"}>{section?.meta.supportLevel ?? "loading"}</StatusPill>}
    >
      {rows.length === 0 ? (
        <p className={styles.stateText}>No register evidence rows were returned for this publication.</p>
      ) : (
        <FactList
          facts={rows.map((row) => ({
            label: String(row.label ?? "Register fact"),
            value: row.value,
            detail: row.detail ? String(row.detail) : undefined,
          }))}
        />
      )}
    </Surface>
  );
}

export function PublicationWorkspace({ publicationId }: PublicationWorkspaceProps) {
  const [overview, setOverview] = useState<PublicationOverviewPayload | null>(null);
  const [sections, setSections] = useState<{
    text: PublicationSectionPayload | null;
    timeline: PublicationSectionPayload | null;
    register: PublicationSectionPayload | null;
  }>({
    text: null,
    timeline: null,
    register: null,
  });
  const [loadingOverview, setLoadingOverview] = useState(true);
  const [loadingTabs, setLoadingTabs] = useState({
    text: false,
    timeline: false,
    register: false,
  });
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoadingOverview(true);
    setError(null);
    setSections({
      text: null,
      timeline: null,
      register: null,
    });
    setLoadingTabs({
      text: false,
      timeline: false,
      register: false,
    });

    async function loadOverview() {
      try {
        const payload = await fetchPublicationOverview(publicationId);
        if (!cancelled) {
          setOverview(payload);
        }
      } catch (requestError) {
        if (!cancelled) {
          setError(requestError instanceof Error ? requestError.message : "Could not load publication overview.");
          setOverview(null);
        }
      } finally {
        if (!cancelled) {
          setLoadingOverview(false);
        }
      }
    }

    void loadOverview();
    return () => {
      cancelled = true;
    };
  }, [publicationId]);

  useEffect(() => {
    if (loadingOverview || !overview) {
      return;
    }

    if (sections.text && sections.timeline && sections.register) {
      return;
    }

    let cancelled = false;
    setLoadingTabs({
      text: !sections.text,
      timeline: !sections.timeline,
      register: !sections.register,
    });

    async function loadSections() {
      const results = await Promise.allSettled([
        sections.text ? Promise.resolve(sections.text) : fetchPublicationSection(publicationId, "text"),
        sections.timeline ? Promise.resolve(sections.timeline) : fetchPublicationSection(publicationId, "legal-timeline"),
        sections.register ? Promise.resolve(sections.register) : fetchPublicationSection(publicationId, "register-evidence"),
      ]);

      if (cancelled) {
        return;
      }

      const [textResult, timelineResult, registerResult] = results;

      if (textResult.status === "fulfilled" && timelineResult.status === "fulfilled" && registerResult.status === "fulfilled") {
        setSections({
          text: textResult.value,
          timeline: timelineResult.value,
          register: registerResult.value,
        });
        setLoadingTabs({
          text: false,
          timeline: false,
          register: false,
        });
        return;
      }

      setLoadingTabs({
        text: false,
        timeline: false,
        register: false,
      });
      setError("Could not load publication evidence sections.");
    }

    void loadSections();
    return () => {
      cancelled = true;
    };
  }, [loadingOverview, overview, publicationId, sections]);

  const combinedCaveats = useMemo(() => {
    return [
      ...(overview?.meta.caveats ?? []),
      ...(sections.text?.meta.caveats ?? []),
      ...(sections.timeline?.meta.caveats ?? []),
      ...(sections.register?.meta.caveats ?? []),
    ];
  }, [overview?.meta.caveats, sections.register?.meta.caveats, sections.text?.meta.caveats, sections.timeline?.meta.caveats]);

  const workspaceContextOverride = useMemo(() => {
    const resolvedPublicationId = overview ? String(overview.overview.publication_id ?? overview.identity.id ?? publicationId) : publicationId;
    const titleText =
      overview && typeof overview.overview.title === "string" && overview.overview.title.trim().length > 0
        ? overview.overview.title.trim()
        : null;
    const fallbackDescription = overview
      ? [
          typeof overview.overview.authority === "string" ? overview.overview.authority : null,
          typeof overview.overview.kind_code === "string" ? overview.overview.kind_code : null,
          typeof overview.overview.publication_date === "string" ? overview.overview.publication_date : null,
        ]
          .filter((value): value is string => Boolean(value && value.trim().length > 0))
          .join(" · ")
      : "";

    return {
      title: resolvedPublicationId,
      description: titleText ?? (fallbackDescription || undefined),
    };
  }, [overview, publicationId]);

  useWorkspaceContextOverride(workspaceContextOverride);

  if (loadingOverview && !overview) {
    return (
      <div className={styles.workspace}>
        <Surface title="Publication evidence workspace" description="Loading publication overview.">
          <p className={styles.stateText}>Loading publication evidence…</p>
        </Surface>
      </div>
    );
  }

  if (!overview) {
    return (
      <div className={styles.workspace}>
        <Surface title="Publication evidence workspace" description="The publication view could not be initialized.">
          <p className={styles.stateText}>{error ?? "Publication workspace unavailable."}</p>
        </Surface>
      </div>
    );
  }

  const familyId = overview.overview.docdb_family_id ? String(overview.overview.docdb_family_id) : null;
  const visibleSummaryCards = overview.summaryCards
    .filter((card) => card.key !== "register_evidence" && card.key !== "text_coverage")
    .flatMap((card) => {
      if (card.key !== "publication_date" && card.key !== "filing_date") {
        return [card];
      }

      const applicationId = overview.overview.appln_id;
      if (applicationId == null) {
        return [card];
      }

      if (card.key === "publication_date" && overview.summaryCards.some((summaryCard) => summaryCard.key === "filing_date")) {
        return [card];
      }

      return [
        card,
        {
          key: "application_id",
          label: "Application id",
          value: String(applicationId),
        },
      ];
    });

  return (
    <div className={styles.workspace}>
      <section className={styles.summaryGrid}>
        {visibleSummaryCards.map((card) => (
          <article key={card.key} className={styles.summaryCard} data-card-key={card.key}>
            <span className={styles.summaryLabel}>{card.label}</span>
            <strong className={styles.summaryValue}>{formatValue(card.value)}</strong>
          </article>
        ))}
      </section>

      <section className={styles.relatedGrid}>
        <TextPreviewCard section={sections.text} loading={loadingTabs.text} />
        <Surface
          title="Family members"
          badge={
            <div className={styles.relatedBadgeRail}>
              <InfoPill tone="neutral">{overview.relatedPublications.length} family members</InfoPill>
              {familyId ? (
                <Link href={`/family/${familyId}`} className={styles.linkPill}>
                  <TagPill tone="warning">Family {familyId}</TagPill>
                </Link>
              ) : null}
            </div>
          }
        >
          {overview.relatedPublications.length === 0 ? (
            <p className={styles.stateText}>No additional family publications were returned.</p>
          ) : (
            <div className={styles.relatedList}>
              {overview.relatedPublications.map((row) => {
                const rowPublicationId = String(row.publication_number_full ?? "");
                return (
                  <article key={rowPublicationId} className={styles.relatedItem}>
                    <main className={styles.relatedMain}>
                      <Link href={`/publication/${rowPublicationId}`} className={styles.relatedTitle}>
                        {rowPublicationId}
                      </Link>
                      <span className={styles.relatedMeta}>
                        {String(row.publn_auth ?? "—")} {String(row.publn_kind ?? "—")} · {String(row.publn_date ?? "—")}
                      </span>
                    </main>
                    <StatusPill tone={toneForRelatedStage(String(row.stage_label ?? ""))}>{String(row.stage_label ?? "Other")}</StatusPill>
                  </article>
                );
              })}
            </div>
          )}
        </Surface>
      </section>

      <TimelinePanel section={sections.timeline} loading={loadingTabs.timeline} />
      <RegisterPanel section={sections.register} loading={loadingTabs.register} />

      <SupportDetails
        supportLevel={sections.register?.meta.supportLevel ?? sections.timeline?.meta.supportLevel ?? sections.text?.meta.supportLevel ?? overview.meta.supportLevel}
        availability={overview.textAvailability}
        caveats={combinedCaveats}
      />
    </div>
  );
}
