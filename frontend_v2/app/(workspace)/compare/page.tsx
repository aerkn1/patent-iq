import Link from "next/link";

import styles from "@/components/compare/compare-workspace.module.css";
import { PageShell } from "@/components/ui/page-shell";

const compareRoutes = [
  {
    href: "/compare/families",
    title: "Family Compare",
    eyebrow: "Lens-by-lens",
    description: "Compare two families side by side with cohort-aware lenses, direct evidence, and field divergence.",
    tags: ["Blocking posture", "Legal durability", "Field divergence"],
  },
  {
    href: "/compare/portfolios",
    title: "Portfolio Compare",
    eyebrow: "Peer-aware",
    description: "Compare two owner portfolios side by side with peer-aware lenses, lifecycle structure, and top-family support.",
    tags: ["Footprint", "Density", "Top families"],
  },
  {
    href: "/compare/semantic",
    title: "Semantic Workspace",
    eyebrow: "Family-anchor",
    description: "Search semantic neighbors from one family anchor, switch vector spaces explicitly, and inspect a split semantic compare rollup for the selected match.",
    tags: ["Abstract vs claim", "Exact vector runtime", "Discovery caveats"],
  },
];

export default function ComparePage() {
  return (
    <PageShell>
      <div className={styles.routeGrid}>
        {compareRoutes.map((route) => (
          <Link key={route.title} href={route.href} className={styles.routeCard}>
            <div className={styles.routeEyebrow}>{route.eyebrow}</div>
            <h2 className={styles.routeTitle}>{route.title}</h2>
            <p className={styles.routeCopy}>{route.description}</p>
            <div className={styles.routeTags}>
              {route.tags.map((tag) => (
                <span key={tag} className={styles.routeTag}>
                  {tag}
                </span>
              ))}
            </div>
            <span className={styles.routeAction}>Open workflow</span>
          </Link>
        ))}
      </div>
    </PageShell>
  );
}
