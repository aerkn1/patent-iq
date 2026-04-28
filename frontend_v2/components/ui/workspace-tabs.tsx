"use client";

import clsx from "clsx";
import type { ReactNode } from "react";

import styles from "./workspace-tabs.module.css";

export type WorkspaceTabItem<TTab extends string> = {
  hint: string;
  id: TTab;
  label: ReactNode;
};

type WorkspaceTabsProps<TTab extends string> = {
  activeTab: TTab;
  ariaLabel: string;
  className?: string;
  items: WorkspaceTabItem<TTab>[];
  onTabChange: (tab: TTab) => void;
};

export function WorkspaceTabs<TTab extends string>({
  activeTab,
  ariaLabel,
  className,
  items,
  onTabChange,
}: WorkspaceTabsProps<TTab>) {
  return (
    <div className={clsx(styles.tabs, className)} role="tablist" aria-label={ariaLabel}>
      {items.map((tab) => (
        <button
          key={tab.id}
          type="button"
          role="tab"
          aria-selected={activeTab === tab.id}
          className={clsx(styles.tabButton, activeTab === tab.id && styles.tabButtonActive)}
          onClick={() => onTabChange(tab.id)}
        >
          <span className={styles.label}>{tab.label}</span>
          <span className={styles.hint}>{tab.hint}</span>
        </button>
      ))}
    </div>
  );
}
