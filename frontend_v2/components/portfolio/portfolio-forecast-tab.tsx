"use client";

import { PortfolioPendingGrantsPanel } from "@/components/portfolio/portfolio-pending-grants-panel";
import type { PortfolioPendingGrantResponse } from "@/lib/types/portfolio-v2";

type PortfolioForecastTabProps = {
  pendingGrants: PortfolioPendingGrantResponse;
  pendingGrantsLoading?: boolean;
  selectedJurisdiction: string;
  selectedField: string;
  errorMessages: {
    pendingGrants?: string;
  };
  onJurisdictionChange: (value: string) => void;
  onFieldChange: (value: string) => void;
};

export function PortfolioForecastTab({
  pendingGrants,
  pendingGrantsLoading = false,
  selectedJurisdiction,
  selectedField,
  errorMessages,
  onJurisdictionChange,
  onFieldChange,
}: PortfolioForecastTabProps) {
  return (
    <section className="portfolio-tab-panel">
      <PortfolioPendingGrantsPanel
        pendingGrants={pendingGrants}
        isLoading={pendingGrantsLoading}
        selectedJurisdiction={selectedJurisdiction}
        selectedField={selectedField}
        errorMessage={errorMessages.pendingGrants}
        onJurisdictionChange={onJurisdictionChange}
        onFieldChange={onFieldChange}
      />
    </section>
  );
}
