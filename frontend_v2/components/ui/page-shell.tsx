import clsx from "clsx";

import styles from "./page-shell.module.css";

type PageShellProps = {
  eyebrow?: string;
  title?: string;
  description?: string;
  overflowVisible?: boolean;
  children?: React.ReactNode;
};

export function PageShell({ eyebrow, title, description, overflowVisible = false, children }: PageShellProps) {
  const hasHeader = Boolean(eyebrow || title || description);

  return (
    <main className={styles.shell}>
      <section className={clsx(styles.panel, overflowVisible && styles.panelOverflowVisible)}>
        {hasHeader ? (
          <header className={styles.header}>
            {eyebrow ? <div className={styles.eyebrow}>{eyebrow}</div> : null}
            {title ? <h1 className={styles.title}>{title}</h1> : null}
            {description ? <p className={styles.description}>{description}</p> : null}
          </header>
        ) : null}
        {children ? <section className={clsx(styles.content, !hasHeader && styles.contentNoHeader)}>{children}</section> : null}
      </section>
    </main>
  );
}
