"use client";

import { PortfolioTopFamiliesTable } from "@/components/portfolio/portfolio-top-families-table";
import type { PortfolioFamiliesResponse } from "@/lib/types/portfolio-v2";

type PortfolioFamiliesTabProps = {
  families: PortfolioFamiliesResponse;
  familiesLoading?: boolean;
  searchValue: string;
  statusValue: string;
  primaryFieldValue: string;
  sortValue: "blocking" | "priority_year";
  fieldOptions: string[];
  errorMessage?: string;
  onSearchChange: (value: string) => void;
  onStatusChange: (value: string) => void;
  onPrimaryFieldChange: (value: string) => void;
  onSortChange: (value: "blocking" | "priority_year") => void;
  onPageChange: (offset: number) => void;
};

export function PortfolioFamiliesTab({
  families,
  familiesLoading = false,
  searchValue,
  statusValue,
  primaryFieldValue,
  sortValue,
  fieldOptions,
  errorMessage,
  onSearchChange,
  onStatusChange,
  onPrimaryFieldChange,
  onSortChange,
  onPageChange,
}: PortfolioFamiliesTabProps) {
  return (
    <section className="portfolio-tab-panel">
      <PortfolioTopFamiliesTable
        families={families}
        isLoading={familiesLoading}
        searchValue={searchValue}
        statusValue={statusValue}
        primaryFieldValue={primaryFieldValue}
        sortValue={sortValue}
        fieldOptions={fieldOptions}
        onSearchChange={onSearchChange}
        onStatusChange={onStatusChange}
        onPrimaryFieldChange={onPrimaryFieldChange}
        onSortChange={onSortChange}
        onPageChange={onPageChange}
      />
      {errorMessage ? <p className="portfolio-error">{errorMessage}</p> : null}
    </section>
  );
}
