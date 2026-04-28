"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowRight, BookOpenText, GitCompareArrows, Newspaper, Radar, Sparkles } from "lucide-react";
import { useState } from "react";

import { PortfolioEntrySearch } from "@/components/portfolio/portfolio-entry-search";

import styles from "./operator-entry-console.module.css";

function sanitizeIdentifier(value: string) {
  return value.trim();
}

export function OperatorEntryConsole() {
  const router = useRouter();
  const [familyId, setFamilyId] = useState("");
  const [publicationId, setPublicationId] = useState("");

  return (
    <section className={styles.grid}>
      <div className={styles.primary}>
        <PortfolioEntrySearch />
      </div>

      <div className={styles.secondaryRail}>
        <article className={styles.jumpCard}>
          <div className={styles.jumpHeader}>
            <span className={styles.jumpIcon}>
              <BookOpenText className={styles.jumpGlyph} />
            </span>
            <div>
              <h2 className={styles.jumpTitle}>Family jump</h2>
              <p className={styles.jumpCopy}>Open a family evidence workspace directly from a family id.</p>
            </div>
          </div>
          <form
            className={styles.jumpForm}
            onSubmit={(event) => {
              event.preventDefault();
              const next = sanitizeIdentifier(familyId);
              if (!next) {
                return;
              }
              router.push(`/family/${encodeURIComponent(next)}`);
            }}
          >
            <input
              value={familyId}
              onChange={(event) => setFamilyId(event.target.value)}
              placeholder="Enter family id"
              aria-label="Jump to family"
            />
            <button type="submit">Open</button>
          </form>
        </article>

        <article className={styles.jumpCard}>
          <div className={styles.jumpHeader}>
            <span className={styles.jumpIcon}>
              <Newspaper className={styles.jumpGlyph} />
            </span>
            <div>
              <h2 className={styles.jumpTitle}>Publication jump</h2>
              <p className={styles.jumpCopy}>Open a publication evidence page from a bounded publication id.</p>
            </div>
          </div>
          <form
            className={styles.jumpForm}
            onSubmit={(event) => {
              event.preventDefault();
              const next = sanitizeIdentifier(publicationId);
              if (!next) {
                return;
              }
              router.push(`/publication/${encodeURIComponent(next)}`);
            }}
          >
            <input
              value={publicationId}
              onChange={(event) => setPublicationId(event.target.value)}
              placeholder="Enter publication id"
              aria-label="Jump to publication"
            />
            <button type="submit">Open</button>
          </form>
        </article>

        <article className={styles.linkPanel}>
          <header className={styles.linkPanelHeader}>
            <h2 className={styles.linkPanelTitle}>Workflow shortcuts</h2>
            <p className={styles.linkPanelCopy}>Use the existing workspaces directly when you do not need an owner or document jump.</p>
          </header>
          <div className={styles.linkList}>
            <Link href="/market" className={styles.linkItem}>
              <span className={styles.linkLead}>
                <span className={styles.linkLeadTitle}>
                  <Radar className={styles.linkGlyph} />
                  Market command
                </span>
                <span className={styles.linkMeta}>Field and jurisdiction command surface</span>
              </span>
              <ArrowRight className={styles.linkArrow} />
            </Link>
            <Link href="/compare" className={styles.linkItem}>
              <span className={styles.linkLead}>
                <span className={styles.linkLeadTitle}>
                  <GitCompareArrows className={styles.linkGlyph} />
                  Compare workspaces
                </span>
                <span className={styles.linkMeta}>Metric compare and time-slice contrast</span>
              </span>
              <ArrowRight className={styles.linkArrow} />
            </Link>
            <Link href="/compare/semantic" className={styles.linkItem}>
              <span className={styles.linkLead}>
                <span className={styles.linkLeadTitle}>
                  <Sparkles className={styles.linkGlyph} />
                  Semantic workspace
                </span>
                <span className={styles.linkMeta}>Discovery layer with explicit caveats</span>
              </span>
              <ArrowRight className={styles.linkArrow} />
            </Link>
            <Link href="/portfolio" className={styles.linkItem}>
              <span className={styles.linkLead}>
                <span className={styles.linkLeadTitle}>
                  <ArrowRight className={styles.linkGlyph} />
                  Owner search workspace
                </span>
                <span className={styles.linkMeta}>Search a harmonized owner and enter portfolio command</span>
              </span>
              <ArrowRight className={styles.linkArrow} />
            </Link>
          </div>
        </article>
      </div>
    </section>
  );
}
