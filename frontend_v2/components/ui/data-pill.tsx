import clsx from "clsx";
import type { ComponentPropsWithoutRef, ReactNode } from "react";

import type { EnterpriseStatusTone } from "@/lib/design/tokens";

import styles from "./data-pill.module.css";

type DataPillProps = ComponentPropsWithoutRef<"span"> & {
  children: ReactNode;
  monospace?: boolean;
  tone?: EnterpriseStatusTone;
  variant?: "default" | "field";
};

export function DataPill({
  children,
  className,
  monospace = false,
  tone = "neutral",
  variant = "default",
  ...props
}: DataPillProps) {
  return (
    <span
      className={clsx(styles.pill, styles[tone], variant === "field" && styles.field, monospace && styles.mono, className)}
      {...props}
    >
      {children}
    </span>
  );
}

export function FieldPill(props: Omit<DataPillProps, "tone" | "variant"> & { soft?: boolean }) {
  const { soft = false, ...rest } = props;
  return <DataPill tone={soft ? "info" : "accent"} variant="field" {...rest} />;
}

export function InfoPill(props: Omit<DataPillProps, "variant">) {
  return <DataPill variant="default" {...props} />;
}

export function StatusPill(props: Omit<DataPillProps, "variant">) {
  return <DataPill variant="default" {...props} />;
}

export function TagPill(props: Omit<DataPillProps, "variant">) {
  return <DataPill variant="default" {...props} />;
}

