import clsx from "clsx";
import type { ComponentPropsWithoutRef, ReactNode } from "react";

import styles from "./surface.module.css";

type SurfaceProps = Omit<ComponentPropsWithoutRef<"section">, "title"> & {
  actions?: ReactNode;
  badge?: ReactNode;
  description?: ReactNode;
  eyebrow?: ReactNode;
  icon?: ReactNode;
  title?: ReactNode;
};

export function Surface({
  actions,
  badge,
  children,
  className,
  description,
  eyebrow,
  icon,
  title,
  ...props
}: SurfaceProps) {
  const hasHeader = Boolean(title || badge || actions || eyebrow || description);

  return (
    <section className={clsx("panel-shell", styles.surface, className)} {...props}>
      {hasHeader ? (
        <div className={styles.header}>
          <div className={styles.headerMain}>
            {eyebrow ? <div className={styles.eyebrow}>{eyebrow}</div> : null}
            {title ? (
              <div className={styles.titleRow}>
                {icon ? <span className={styles.icon}>{icon}</span> : null}
                <h3 className={styles.title}>{title}</h3>
              </div>
            ) : null}
            {description ? <p className={styles.description}>{description}</p> : null}
          </div>
          {badge || actions ? <div className={styles.meta}>{badge}{actions}</div> : null}
        </div>
      ) : null}
      {children}
    </section>
  );
}
