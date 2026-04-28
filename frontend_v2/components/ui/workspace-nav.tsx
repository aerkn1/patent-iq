"use client";

import clsx from "clsx";
import Image from "next/image";
import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";

import { workspaceNavigationItems } from "./workspace-nav-config";
import styles from "./workspace-nav.module.css";

type NavChildLink = {
  href: string;
  label: string;
};

type SearchParamReader = Pick<URLSearchParams, "entries" | "get" | "has">;

const queryLabelMap: Record<string, string> = {
  field: "Field",
  state: "State",
  segment: "Segment",
  tab: "Tab",
  mode: "Mode",
  horizon: "Horizon",
};

function humanizeToken(value: string) {
  const decoded = decodeURIComponent(value);
  return decoded.replace(/_/g, " ");
}

function buildContextTitle(pathname: string): string {
  const segments = pathname.split("/").filter(Boolean);

  if (segments[0] === "portfolio" && segments[1]) {
    return humanizeToken(segments[1]);
  }

  if (segments[0] === "family" && segments[1]) {
    return `Family ${humanizeToken(segments[1])}`;
  }

  if (segments[0] === "publication" && segments[1]) {
    return humanizeToken(segments[1]);
  }

  if (segments[0] === "compare" && segments[1]) {
    return `${humanizeToken(segments[1])} compare`;
  }

  if (segments[0] === "market") {
    return "Market landscape";
  }

  if (segments[0] === "portfolio") {
    return "Portfolio";
  }

  if (segments[0] === "family") {
    return "Family";
  }

  if (segments[0] === "publication") {
    return "Publication";
  }

  if (segments[0] === "compare") {
    return "Compare";
  }

  return "Home";
}

function buildQuerySummary(searchParams: SearchParamReader): string {
  return Array.from(searchParams.entries())
    .filter(([key, value]) => value && queryLabelMap[key])
    .slice(0, 3)
    .map(([key, value]) => `${queryLabelMap[key]} ${humanizeToken(value)}`)
    .join(" · ");
}

function buildActiveChildren(pathname: string): NavChildLink[] {
  const segments = pathname.split("/").filter(Boolean);

  if (segments[0] === "portfolio" && segments[1]) {
    const base = `/portfolio/${encodeURIComponent(segments[1])}`;
    return [
      { href: base, label: "Overview" },
      { href: `${base}?tab=families`, label: "Families" },
      { href: `${base}?tab=fields`, label: "Fields" },
      { href: `${base}?tab=citations`, label: "Citation" },
      { href: `${base}?tab=forecast`, label: "Forecast" },
    ];
  }

  if (segments[0] === "market") {
    return [
      { href: "/market", label: "Overview" },
      { href: "/market?section=analysis&tab=competition", label: "Competition" },
      { href: "/market?section=analysis&tab=jurisdictions", label: "Jurisdictions" },
      { href: "/market?section=analysis&tab=technology", label: "Technology" },
    ];
  }

  if (segments[0] === "compare") {
    return [
      { href: "/compare", label: "Hub" },
      { href: "/compare/families", label: "Families" },
      { href: "/compare/portfolios", label: "Portfolios" },
      { href: "/compare/semantic", label: "Semantic" },
    ];
  }

  return [];
}

function isHrefActive(pathname: string, searchParams: SearchParamReader, href: string): boolean {
  const [targetPathname, queryString] = href.split("?");

  if (pathname !== targetPathname) {
    return false;
  }

  if (!queryString) {
    return !["mode", "section", "tab"].some((key) => searchParams.has(key));
  }

  const targetParams = new URLSearchParams(queryString);
  return Array.from(targetParams.entries()).every(([key, value]) => searchParams.get(key) === value);
}

export function WorkspaceNav() {
  const pathname = usePathname() ?? "/";
  const searchParams = useSearchParams();
  const query = searchParams ?? new URLSearchParams();
  const activeItem = workspaceNavigationItems.find((item) => item.match(pathname)) ?? workspaceNavigationItems[0];
  const activeChildren = buildActiveChildren(pathname);
  const contextTitle = buildContextTitle(pathname);
  const querySummary = buildQuerySummary(query);
  const showContextNote = pathname !== "/" || querySummary.length > 0;

  return (
    <aside className={styles.shell}>
      <div className={styles.inner}>
        <Link href="/" className={styles.brand} aria-label="Open PatentIQ home">
          <Image src="/logo.png" width={40} height={40} alt="PatentIQ" className={styles.brandMark} priority />
          <span className={styles.brandCopy}>
            <span className={styles.brandTitle}>PatentIQ</span>
            <span className={styles.brandSubtitle}>V2 Workspace</span>
          </span>
        </Link>

        <nav className={styles.nav} aria-label="Primary">
          {workspaceNavigationItems.map((item) => {
            const Icon = item.icon;
            const isActive = item.match(pathname);

            return (
              <div key={item.href} className={styles.navGroup}>
                <Link
                  href={item.href}
                  className={clsx(styles.navLink, isActive && styles.navLinkActive)}
                  aria-current={isActive ? "page" : undefined}
                >
                  <span className={styles.navIcon}>
                    <Icon className={styles.navIconGlyph} />
                  </span>
                  <span className={styles.navLabel}>{item.label}</span>
                </Link>

                {isActive && activeChildren.length > 0 ? (
                  <div className={styles.subnav}>
                    {activeChildren.map((child) => {
                      const childActive = isHrefActive(pathname, query, child.href);
                      return (
                        <Link
                          key={child.href}
                          href={child.href}
                          className={clsx(styles.subnavLink, childActive && styles.subnavLinkActive)}
                          aria-current={childActive ? "page" : undefined}
                        >
                          {child.label}
                        </Link>
                      );
                    })}
                  </div>
                ) : null}
              </div>
            );
          })}
        </nav>

        {showContextNote ? (
          <div className={styles.contextNote}>
            <span className={styles.sectionLabel}>Current</span>
            <strong className={styles.contextTitle}>{contextTitle}</strong>
            {querySummary ? <span className={styles.contextMeta}>{querySummary}</span> : null}
          </div>
        ) : null}
      </div>
    </aside>
  );
}
