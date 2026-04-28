"use client";

import styles from "./portfolio-workspace-skeleton.module.css";

export function PortfolioWorkspaceSkeleton() {
  return (
    <div className={`portfolio-shell ${styles.shell}`} aria-hidden="true">
      <section className={`panel-shell ${styles.controls}`}>
        <div className={styles.search}>
          <div className={`${styles.block} ${styles.searchField}`} />
          <div className={`${styles.block} ${styles.searchButton}`} />
        </div>
      </section>

      <div className={styles.tabs}>
        {Array.from({ length: 5 }).map((_, index) => (
          <span key={index} className={`${styles.pill} ${styles.tabPill}`} />
        ))}
      </div>

      <section className={`panel-shell ${styles.card}`}>
        <div className={styles.summary}>
          {Array.from({ length: 3 }).map((_, index) => (
            <div key={index} className={styles.tile} />
          ))}
        </div>
        <div className={styles.grid}>
          {Array.from({ length: 4 }).map((_, index) => (
            <div key={index} className={styles.panel} />
          ))}
        </div>
      </section>
    </div>
  );
}
