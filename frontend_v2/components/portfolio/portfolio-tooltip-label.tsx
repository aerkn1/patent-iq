"use client";

import clsx from "clsx";
import type { ReactNode } from "react";

import { PortfolioMetricTooltip } from "@/components/portfolio/portfolio-metric-tooltip";

import styles from "./portfolio-tooltip-label.module.css";

type PortfolioTooltipLabelProps = {
  label: ReactNode;
  tooltip: string;
  className?: string;
  textClassName?: string;
};

export function PortfolioTooltipLabel({
  label,
  tooltip,
  className,
  textClassName,
}: PortfolioTooltipLabelProps) {
  return (
    <span className={clsx(styles.label, className)}>
      <span className={clsx(styles.text, textClassName)}>{label}</span>
      <PortfolioMetricTooltip text={tooltip} />
    </span>
  );
}
