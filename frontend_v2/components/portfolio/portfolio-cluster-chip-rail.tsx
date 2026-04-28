"use client";

import clsx from "clsx";

import styles from "@/components/portfolio/technology-panels.module.css";

type PortfolioClusterChipRailProps = {
  fields: string[];
  selectedField: string;
  onSelectField: (field: string) => void;
};

export function PortfolioClusterChipRail({
  fields,
  selectedField,
  onSelectField,
}: PortfolioClusterChipRailProps) {
  return (
    <div className={styles.chipRail} role="tablist" aria-label="Portfolio field clusters">
      <button
        type="button"
        role="tab"
        aria-selected={selectedField.length === 0}
        className={clsx(styles.chip, selectedField.length === 0 && styles.chipSelected)}
        onClick={() => onSelectField("")}
      >
        All
      </button>
      {fields.map((field) => (
        <button
          key={field}
          type="button"
          role="tab"
          aria-selected={selectedField === field}
          className={clsx(styles.chip, selectedField === field && styles.chipSelected)}
          onClick={() => onSelectField(field)}
        >
          {field}
        </button>
      ))}
    </div>
  );
}
