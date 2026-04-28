import type { ComponentType } from "react";

import Image from "next/image";
import Link from "next/link";
import {
  ArrowRight,
  BookOpenText,
  BriefcaseBusiness,
  GitCompareArrows,
  Newspaper,
  Radar,
} from "lucide-react";

import { workspaceNavigationItems } from "@/components/ui/workspace-nav-config";

import styles from "./page.module.css";

type SectionHeaderProps = {
  eyebrow: string;
  title: string;
  copy: string;
};

type WorkspaceCard = {
  href: string;
  eyebrow: string;
  title: string;
  copy: string;
  tags: string[];
  actionLabel: string;
  icon: ComponentType<{ className?: string }>;
};

type HeroStat = {
  label: string;
  value: string;
};

type TrustRow = {
  label: string;
  value: string;
};

const heroStats: HeroStat[] = [
  { label: "Technology sectors", value: "10 WIPO fields" },
  { label: "Data window", value: "2007–2026" },
  { label: "Snapshot date", value: "2026-03-15" },
];

const workspaceCards: WorkspaceCard[] = [
  {
    href: "/portfolio",
    eyebrow: "Owner workflows",
    title: "Portfolio Intelligence",
    copy: "Search a harmonized owner to rank their patent families by blocking power and forward citation influence. Move through overview, field structure, citation pressure, and forecast concentration.",
    tags: ["Overview", "Ranking", "Fields", "Citation", "Forecast"],
    actionLabel: "Open portfolio intelligence",
    icon: BriefcaseBusiness,
  },
  {
    href: "/family",
    eyebrow: "Canonical entity",
    title: "Family Evidence",
    copy: "Read legal durability, active jurisdictions, member publications, field assignments, and citation context from a single evidence surface anchored to the canonical family.",
    tags: ["Legal", "Members", "Fields", "Citation"],
    actionLabel: "Inspect family evidence",
    icon: BookOpenText,
  },
  {
    href: "/publication",
    eyebrow: "Document support",
    title: "Publication Evidence",
    copy: "Inspect abstract text, claim 1, legal event chronology, and register evidence when you need document-level proof behind a family-level assessment.",
    tags: ["Abstract", "Claim 1", "Timeline", "Register"],
    actionLabel: "Inspect publication proof",
    icon: Newspaper,
  },
  {
    href: "/market",
    eyebrow: "Field and jurisdiction",
    title: "Market Command",
    copy: "Track field league tables, owner presence by jurisdiction, citation pressure, and CPC group importance across pre-built market marts bounded to 10 WIPO technology sectors.",
    tags: ["Field state", "Owners", "Jurisdictions", "CPC"],
    actionLabel: "Open market command",
    icon: Radar,
  },
  {
    href: "/compare",
    eyebrow: "Peer-aware analysis",
    title: "Compare Workspaces",
    copy: "Contrast families, portfolios, and semantic neighbors across technology, outlook, and evidence dimensions without collapsing them into a single blended score.",
    tags: ["Family compare", "Portfolio compare", "Semantic"],
    actionLabel: "Compare peers",
    icon: GitCompareArrows,
  },
];

const trustRows: TrustRow[] = [
  {
    label: "Source data",
    value: "EPO PATSTAT · EP Register · EPAB fulltext · USPTO ODP",
  },
  {
    label: "Analytical scope",
    value: "10 WIPO technology sectors · 2007–2026 main window · 1996–2006 heritage layer",
  },
];

function SectionHeader({ eyebrow, title, copy }: SectionHeaderProps) {
  return (
    <header className={styles.sectionHeader}>
      <div className={styles.sectionHeaderLead}>
        <div className={styles.sectionEyebrow}>{eyebrow}</div>
        <h2 className={styles.sectionTitle}>{title}</h2>
      </div>
      <p className={styles.sectionCopy}>{copy}</p>
    </header>
  );
}

export default function HomePage() {
  const topLinks = workspaceNavigationItems.filter((item) => item.href !== "/");

  return (
    <main className={styles.page} id="top">
      <header className={styles.header}>
        <div className={styles.headerInner}>
          <Link href="/" className={styles.brand} aria-label="Open PatentIQ home">
            <Image src="/logo.png" width={50} height={50} alt="PatentIQ" className={styles.brandMark} priority />
            <span className={styles.brandCopy}>
              <span className={styles.brandTitle}>PatentIQ</span>
              <span className={styles.brandSubtitle}>Enterprise IP Intelligence</span>
            </span>
          </Link>

          <nav className={styles.topNav} aria-label="Primary">
            {topLinks.map((item) => (
              <Link key={item.href} href={item.href} className={styles.topNavLink}>
                {item.label}
              </Link>
            ))}
          </nav>

          <div className={styles.headerActions}>
            <Link href="#methodology" className={styles.secondaryAction}>
              Methodology
            </Link>
            <Link href="#workspaces" className={styles.primaryAction}>
              Open Workspace
            </Link>
          </div>
        </div>
      </header>

      <section className={styles.hero}>
        <div className={styles.heroCopy}>
          <h1 className={styles.heroTitle}>
            <span>Evidence-backed</span>
            <span>patent intelligence</span>
            <span className={styles.heroTitleOffset}>for portfolio, family,</span>
            <span className={styles.heroTitleAccent}>and market decisions.</span>
          </h1>
          <div className={styles.heroCopySide}>
            <p className={styles.heroDescription}>
              Search any patent owner to rank their families by blocking power and forward citation influence. Open a family to read legal status across jurisdictions, publication coverage, and citation footprint. Track technology field pressure and owner movements across 10 WIPO sectors.
            </p>
            <div className={styles.heroActions}>
              <Link href="#workspaces" className={styles.primaryAction}>
                Explore workspaces
              </Link>
              <Link href="#methodology" className={styles.ghostAction}>
                Review methodology
              </Link>
            </div>
          </div>
        </div>

        <div className={styles.heroStats}>
          {heroStats.map((stat) => (
            <div key={stat.label} className={styles.heroStatItem}>
              <span className={styles.heroStatLabel}>{stat.label}</span>
              <strong className={styles.heroStatValue}>{stat.value}</strong>
            </div>
          ))}
        </div>
      </section>

      <section id="workspaces" className={`${styles.sectionBlock} ${styles.scrollTarget}`}>
        <SectionHeader
          eyebrow="Workspaces"
          title="Five analytical workspaces"
          copy="Each workspace resolves to a concrete evidence model — owner ranking, family legal status, publication proof, market intelligence, or peer comparison."
        />
        <div className={styles.workspaceGrid}>
          {workspaceCards.map((card, index) => {
            const Icon = card.icon;
            return (
              <Link key={card.title} href={card.href} className={styles.workspaceCard}>
                <span className={styles.workspaceIndex}>{String(index + 1).padStart(2, "0")}</span>
                <div className={styles.workspaceCardHead}>
                  <span className={styles.workspaceIconWrap}>
                    <Icon className={styles.workspaceIcon} />
                  </span>
                  <span className={styles.workspaceEyebrow}>{card.eyebrow}</span>
                </div>
                <h3 className={styles.workspaceTitle}>{card.title}</h3>
                <p className={styles.workspaceCopy}>{card.copy}</p>
                <div className={styles.workspaceTags}>
                  {card.tags.map((tag) => (
                    <span key={tag} className={styles.workspaceTag}>
                      {tag}
                    </span>
                  ))}
                </div>
                <span className={styles.workspaceAction}>
                  {card.actionLabel}
                  <ArrowRight className={styles.actionArrow} />
                </span>
              </Link>
            );
          })}
        </div>
      </section>

      <section id="methodology" className={`${styles.methodologySection} ${styles.scrollTarget}`}>
        <div className={styles.methodologyIntro}>
          <SectionHeader
            eyebrow="Methodology"
            title="Data sources and model transparency"
            copy="PatentIQ states what it measures, what data it draws from, and where the model is uncertain — not just the output."
          />
          <div className={styles.methodologyActions}>
            <Link href="/market" className={styles.ghostAction}>
              Open Market
            </Link>
            <Link href="/compare/semantic" className={styles.ghostAction}>
              Open Semantic Workspace
            </Link>
            <Link href="#top" className={styles.secondaryAction}>
              Back to Top
            </Link>
          </div>
        </div>

        <div className={styles.trustBlock}>
          {trustRows.map((row) => (
            <div key={row.label} className={styles.trustRow}>
              <span className={styles.trustLabel}>{row.label}</span>
              <span className={styles.trustValue}>{row.value}</span>
            </div>
          ))}
        </div>
      </section>

      <footer className={styles.footer}>
        <div className={styles.footerBrand}>
          <span className={styles.footerTitle}>PatentIQ</span>
          <p className={styles.footerCopy}>Evidence-backed IP intelligence for portfolio, family, and market decisions.</p>
        </div>

        <nav className={styles.footerNav} aria-label="Footer">
          {topLinks.map((item) => (
            <Link key={item.href} href={item.href} className={styles.footerLink}>
              {item.label}
            </Link>
          ))}
          <Link href="#methodology" className={styles.footerLink}>
            Methodology
          </Link>
        </nav>

        <div className={styles.footerMeta}>Evidence-backed outputs. Explicit caveats. Bounded analytical scope.</div>
      </footer>
    </main>
  );
}
