"use client";

import { PortfolioTooltipLabel } from "@/components/portfolio/portfolio-tooltip-label";
import { WorkspaceTabs, type WorkspaceTabItem } from "@/components/ui/workspace-tabs";
import { workspaceTooltipCopy } from "@/lib/content/workspace-tooltips";

export type PortfolioWorkspaceTab =
  | "executive"
  | "families"
  | "citations"
  | "fields"
  | "forecast";

type PortfolioPrimaryTabsProps = {
  activeTab: PortfolioWorkspaceTab;
  onTabChange: (tab: PortfolioWorkspaceTab) => void;
};

const tabOrder: WorkspaceTabItem<PortfolioWorkspaceTab>[] = [
  {
    id: "executive",
    label: <PortfolioTooltipLabel label="Overview" tooltip={workspaceTooltipCopy.tabs.overview} />,
    hint: "briefing",
  },
  {
    id: "families",
    label: <PortfolioTooltipLabel label="Families" tooltip={workspaceTooltipCopy.tabs.families} />,
    hint: "ranking",
  },
  {
    id: "fields",
    label: <PortfolioTooltipLabel label="Fields" tooltip={workspaceTooltipCopy.tabs.fields} />,
    hint: "structure",
  },
  {
    id: "citations",
    label: <PortfolioTooltipLabel label="Citation" tooltip={workspaceTooltipCopy.tabs.citation} />,
    hint: "pressure",
  },
  {
    id: "forecast",
    label: <PortfolioTooltipLabel label="Forecast" tooltip={workspaceTooltipCopy.tabs.forecast} />,
    hint: "outlook",
  },
];

export function PortfolioPrimaryTabs({ activeTab, onTabChange }: PortfolioPrimaryTabsProps) {
  return <WorkspaceTabs items={tabOrder} activeTab={activeTab} onTabChange={onTabChange} ariaLabel="Portfolio workspace sections" />;
}
