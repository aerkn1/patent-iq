"use client";

import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";

import styles from "./workspace-context.module.css";

type Crumb = {
  href?: string;
  label: string;
};

type WorkspaceContextModel = {
  eyebrow: string;
  title: string;
  description: string;
  crumbs: Crumb[];
};

type WorkspaceContextOverride = Partial<Pick<WorkspaceContextModel, "eyebrow" | "title" | "description">> & {
  actions?: ReactNode;
};

const WorkspaceContextOverrideState = createContext<{
  override: WorkspaceContextOverride | null;
  setOverride: (value: WorkspaceContextOverride | null) => void;
} | null>(null);

function humanizeToken(value: string) {
  const decoded = decodeURIComponent(value);
  return decoded.replace(/_/g, " ");
}

function titleForPath(pathname: string): WorkspaceContextModel {
  const segments = pathname.split("/").filter(Boolean);

  if (segments[0] === "portfolio" && segments[1]) {
    const ownerLabel = humanizeToken(segments[1]);
    return {
      eyebrow: "Portfolio workspace",
      title: ownerLabel,
      description: "Owner-scoped intelligence across filing strength, field structure, citation pressure, and forecast lanes.",
      crumbs: [
        { href: "/", label: "Home" },
        { href: "/portfolio", label: "Portfolio" },
        { label: ownerLabel },
      ],
    };
  }

  if (segments[0] === "portfolio") {
    return {
      eyebrow: "Portfolio workspace",
      title: "Portfolio intelligence",
      description: "Search harmonized owners and open ranked portfolio workspaces with field, citation, and forecast drilldowns.",
      crumbs: [
        { href: "/", label: "Home" },
        { label: "Portfolio" },
      ],
    };
  }

  if (segments[0] === "family" && segments[1]) {
    const familyId = humanizeToken(segments[1]);
    return {
      eyebrow: "Family workspace",
      title: `Family ${familyId}`,
      description: "Evidence-first family analysis with legal posture, jurisdiction anchors, classification spread, and forecast support.",
      crumbs: [
        { href: "/", label: "Home" },
        { href: "/family", label: "Family" },
        { label: familyId },
      ],
    };
  }

  if (segments[0] === "family") {
    return {
      eyebrow: "Family workspace",
      title: "Family evidence workspace",
      description: "Open a family directly to inspect legal posture, classification spread, citation chronology, and forecast support.",
      crumbs: [
        { href: "/", label: "Home" },
        { label: "Family" },
      ],
    };
  }

  if (segments[0] === "publication" && segments[1]) {
    const publicationId = humanizeToken(segments[1]);
    return {
      eyebrow: "Publication workspace",
      title: publicationId,
      description: "Document-level register, text, and provenance evidence with family-member navigation.",
      crumbs: [
        { href: "/", label: "Home" },
        { href: "/publication", label: "Publication" },
        { label: publicationId },
      ],
    };
  }

  if (segments[0] === "publication") {
    return {
      eyebrow: "Publication workspace",
      title: "Publication evidence workspace",
      description: "Open a publication directly to inspect register facts, text evidence, and family-member navigation.",
      crumbs: [
        { href: "/", label: "Home" },
        { label: "Publication" },
      ],
    };
  }

  if (segments[0] === "market") {
    return {
      eyebrow: "Market intelligence",
      title: "Market landscape",
      description: "Field and jurisdiction command with state filters, CPC structure, and competitive overlays.",
      crumbs: [
        { href: "/", label: "Home" },
        { label: "Market" },
      ],
    };
  }

  if (segments[0] === "compare" && segments[1] === "families") {
    return {
      eyebrow: "Compare workspace",
      title: "Family compare",
      description: "Compare two families through blocking posture, legal durability, and citation heritage with explicit cohort context.",
      crumbs: [
        { href: "/", label: "Home" },
        { href: "/compare", label: "Compare" },
        { label: "Families" },
      ],
    };
  }

  if (segments[0] === "compare" && segments[1] === "portfolios") {
    return {
      eyebrow: "Compare workspace",
      title: "Portfolio compare",
      description: "Peer-aware portfolio comparison across footprint, density, and top-family support.",
      crumbs: [
        { href: "/", label: "Home" },
        { href: "/compare", label: "Compare" },
        { label: "Portfolios" },
      ],
    };
  }

  if (segments[0] === "compare") {
    return {
      eyebrow: "Compare workspace",
      title: "Compare workspaces",
      description: "Metric-driven analytical compare surfaces for families and portfolios. Semantic compare follows after runtime wiring.",
      crumbs: [
        { href: "/", label: "Home" },
        { label: "Compare" },
      ],
    };
  }

  return {
    eyebrow: "Workspace",
    title: "PatentIQ workspace",
    description: "Enterprise patent intelligence surfaces for portfolios, families, publications, market context, and compare flows.",
    crumbs: [
      { href: "/", label: "Home" },
      { label: "Workspace" },
    ],
  };
}

const queryLabelMap: Record<string, string> = {
  field: "Field",
  state: "State",
  segment: "Field",
  tab: "Tab",
  horizon: "Horizon",
};

export function WorkspaceContext() {
  const pathname = usePathname() ?? "/";
  const searchParams = useSearchParams();
  const query = searchParams ?? new URLSearchParams();
  const overrideState = useContext(WorkspaceContextOverrideState);
  const baseModel = titleForPath(pathname);
  const model = {
    ...baseModel,
    ...(overrideState?.override ?? {}),
  };
  const chips = Array.from(query.entries())
    .filter(([key, value]) => value && queryLabelMap[key])
    .slice(0, 4)
    .map(([key, value]) => ({
      key,
      label: queryLabelMap[key],
      value: humanizeToken(value),
    }));

  return (
    <>
      {overrideState?.override?.actions ? (
        <div className={styles.actionBar}>
          <div className={styles.actionInner}>{overrideState.override.actions}</div>
        </div>
      ) : null}
      <section className={styles.bar}>
        <div className={styles.inner}>
          <nav className={styles.crumbs} aria-label="Breadcrumb">
            {model.crumbs.map((crumb, index) => (
              <span key={`${crumb.label}-${index}`} className={styles.crumbItem}>
                {crumb.href ? (
                  <Link href={crumb.href} className={styles.crumbLink}>
                    {crumb.label}
                  </Link>
                ) : (
                  <span className={styles.crumbCurrent}>{crumb.label}</span>
                )}
                {index < model.crumbs.length - 1 ? <span className={styles.crumbDivider}>/</span> : null}
              </span>
            ))}
          </nav>

          <div className={styles.summary}>
            <div className={styles.copy}>
              <span className={styles.eyebrow}>{model.eyebrow}</span>
              <h1 className={styles.title}>{model.title}</h1>
              <p className={styles.description}>{model.description}</p>
            </div>
            <div className={styles.meta}>
              <div className={styles.metaLabel}>Active scope</div>
              <div className={styles.chips}>
                {chips.length > 0 ? (
                  chips.map((chip) => (
                    <span key={chip.key} className={styles.chip}>
                      <strong>{chip.label}</strong>
                      {chip.value}
                    </span>
                  ))
                ) : (
                  <span className={styles.metaHint}>No additional filters are active.</span>
                )}
              </div>
            </div>
          </div>
        </div>
      </section>
    </>
  );
}

export function WorkspaceContextProvider({ children }: { children: ReactNode }) {
  const [override, setOverride] = useState<WorkspaceContextOverride | null>(null);

  return (
    <WorkspaceContextOverrideState.Provider value={{ override, setOverride }}>
      {children}
    </WorkspaceContextOverrideState.Provider>
  );
}

export function useWorkspaceContextOverride(override: WorkspaceContextOverride | null) {
  const state = useContext(WorkspaceContextOverrideState);
  const setOverride = state?.setOverride;
  const eyebrow = override?.eyebrow ?? null;
  const title = override?.title ?? null;
  const description = override?.description ?? null;
  const actions = override?.actions ?? null;

  useEffect(() => {
    if (!setOverride) {
      return;
    }
    setOverride(
      override
        ? {
            eyebrow: eyebrow ?? undefined,
            title: title ?? undefined,
            description: description ?? undefined,
            actions: actions ?? undefined,
          }
        : null,
    );
    return () => {
      setOverride(null);
    };
  }, [actions, description, eyebrow, setOverride, title]);
}
