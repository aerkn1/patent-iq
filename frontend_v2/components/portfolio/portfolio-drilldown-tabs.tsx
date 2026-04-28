"use client";

import { Archive } from "lucide-react";
import { useState } from "react";

import { PortfolioClassificationPanel } from "@/components/portfolio/portfolio-classification-panel";
import { PortfolioFieldTimeseriesPanel } from "@/components/portfolio/portfolio-field-timeseries";
import { PortfolioThreatPanel } from "@/components/portfolio/portfolio-threat-panel";
import { PortfolioTopFamiliesTable } from "@/components/portfolio/portfolio-top-families-table";
import { Surface } from "@/components/ui/surface";
import { WorkspaceTabs, type WorkspaceTabItem } from "@/components/ui/workspace-tabs";
import type {
  PortfolioClassificationResponse,
  PortfolioFieldRowsResponse,
  PortfolioFamiliesResponse,
  PortfolioThreatsResponse,
} from "@/lib/types/portfolio-v2";

type PortfolioDrilldownTabsProps = {
  families: PortfolioFamiliesResponse;
  threats: PortfolioThreatsResponse;
  fields: PortfolioFieldRowsResponse;
  classification: PortfolioClassificationResponse;
  threatField?: string;
  threatFieldOptions?: string[];
  onThreatFieldChange?: (value: string) => void;
  onThreatPageChange?: (offset: number) => void;
  onFamilyPageChange?: (offset: number) => void;
  onClassificationPageChange?: (offset: number) => void;
};

type TabId = "families" | "threats" | "fields" | "forecast";

const drilldownTabs: WorkspaceTabItem<TabId>[] = [
  { id: "families", label: "Families", hint: "ranking" },
  { id: "threats", label: "Threats", hint: "pressure" },
  { id: "fields", label: "Fields", hint: "snapshot" },
  { id: "forecast", label: "History", hint: "replay" },
];

export function PortfolioDrilldownTabs({
  families,
  threats,
  fields,
  classification,
  threatField = "",
  threatFieldOptions = [],
  onThreatFieldChange,
  onThreatPageChange,
  onFamilyPageChange,
  onClassificationPageChange,
}: PortfolioDrilldownTabsProps) {
  const [tab, setTab] = useState<TabId>("families");

  return (
    <Surface className="portfolio-drilldown" title="Drilldown workspace">
      <WorkspaceTabs items={drilldownTabs} activeTab={tab} onTabChange={setTab} ariaLabel="Portfolio drilldown sections" />
      {tab === "families" ? (
        <PortfolioTopFamiliesTable
          families={families}
          searchValue=""
          statusValue=""
          primaryFieldValue=""
          sortValue="blocking"
          fieldOptions={[]}
          onSortChange={undefined}
          onPageChange={onFamilyPageChange}
        />
      ) : null}
      {tab === "threats" ? (
        <PortfolioThreatPanel
          threats={threats}
          selectedField={threatField}
          availableFields={threatFieldOptions}
          onFieldChange={onThreatFieldChange}
          onPageChange={onThreatPageChange}
        />
      ) : null}
      {tab === "fields" ? (
        <div className="portfolio-field-mini-rows">
          <Archive size={12} />
          {fields.rows.length === 0 ? <p className="portfolio-empty">No field rows available.</p> : null}
          <ul>
            {fields.rows.map((row) => (
              <li key={row.field}>
                <span>{row.field}</span>
                <span>{Math.round(row.activeShare * 100)}%</span>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
      {tab === "forecast" ? (
        <div className="portfolio-grid-panel">
          <PortfolioClassificationPanel classification={classification} onPageChange={onClassificationPageChange} />
          <PortfolioFieldTimeseriesPanel timeseries={classification.timeseries} />
        </div>
      ) : null}
    </Surface>
  );
}
