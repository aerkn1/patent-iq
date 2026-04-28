"use client";

import { PortfolioCitationAttackersPanel } from "@/components/portfolio/portfolio-citation-attackers-panel";
import { PortfolioCitationCpcPanel } from "@/components/portfolio/portfolio-citation-cpc-panel";
import { PortfolioCitationFamiliesPanel } from "@/components/portfolio/portfolio-citation-families-panel";
import { PortfolioCitationFieldsPanel } from "@/components/portfolio/portfolio-citation-fields-panel";
import { PortfolioCitationJurisdictionsPanel } from "@/components/portfolio/portfolio-citation-jurisdictions-panel";
import { PortfolioCitationQualityPanel } from "@/components/portfolio/portfolio-citation-quality-panel";
import { PortfolioCitationSummaryPanel } from "@/components/portfolio/portfolio-citation-summary-panel";
import { PortfolioCitationTimeseriesPanel } from "@/components/portfolio/portfolio-citation-timeseries-panel";
import type {
  ForecastHorizon,
  PortfolioCitationAttackersResponse,
  PortfolioCitationCpcGroupsResponse,
  PortfolioCitationFamiliesResponse,
  PortfolioCitationFieldsResponse,
  PortfolioCitationJurisdictionsResponse,
  PortfolioCitationSummaryResponse,
  PortfolioCitationTimeseriesResponse,
  PortfolioForecastContributorsResponse,
  PortfolioForecastPayload,
} from "@/lib/types/portfolio-v2";

type PortfolioCitationsTabProps = {
  citationSummary: PortfolioCitationSummaryResponse;
  citationTimeseries: PortfolioCitationTimeseriesResponse;
  citationTimeseriesLoading?: boolean;
  forecast: PortfolioForecastPayload;
  forecastContributors: PortfolioForecastContributorsResponse;
  forecastContributorsLoading?: boolean;
  forecastHorizon: ForecastHorizon;
  citationFamilies: PortfolioCitationFamiliesResponse;
  citationSummaryLoading?: boolean;
  citationFamiliesLoading?: boolean;
  citationCpcGroups: PortfolioCitationCpcGroupsResponse;
  citationCpcGroupsLoading?: boolean;
  citationAttackers: PortfolioCitationAttackersResponse;
  citationAttackersLoading?: boolean;
  citationFields: PortfolioCitationFieldsResponse;
  citationFieldsLoading?: boolean;
  citationJurisdictions: PortfolioCitationJurisdictionsResponse;
  citationJurisdictionsLoading?: boolean;
  threatFields: string[];
  citationYearOptions: number[];
  citationFamilyField: string;
  citationFamilyStatus: string;
  citationFamilySort: "forward_clean" | "forward_weighted" | "early_5y" | "early_7y" | "blocking";
  citationAttackerField: string;
  citationAttackerJurisdiction: string;
  citationAttackerYear: string;
  errorMessages: {
    citationSummary?: string;
    citationTimeseries?: string;
    forecastContributors?: string;
    citationFamilies?: string;
    citationCpcGroups?: string;
    citationAttackers?: string;
    citationFields?: string;
    citationJurisdictions?: string;
  };
  onForecastHorizonChange: (horizon: ForecastHorizon) => void;
  onForecastContributorPageChange: (offset: number) => void;
  onCitationFamilyFieldChange: (value: string) => void;
  onCitationFamilyStatusChange: (value: string) => void;
  onCitationFamilySortChange: (value: "forward_clean" | "forward_weighted" | "early_5y" | "early_7y" | "blocking") => void;
  onCitationFamilyPageChange: (offset: number) => void;
  onCitationFieldChange: (value: string) => void;
  onCitationJurisdictionChange: (value: string) => void;
  onCitationYearChange: (value: string) => void;
  onCitationFieldPageChange: (offset: number) => void;
  onCitationJurisdictionPageChange: (offset: number) => void;
  onCitationCpcPageChange: (offset: number) => void;
  onCitationAttackerPageChange: (offset: number) => void;
  onClearCitationFilters: () => void;
};

export function PortfolioCitationsTab({
  citationSummary,
  citationTimeseries,
  citationTimeseriesLoading = false,
  forecast,
  forecastContributors,
  forecastContributorsLoading = false,
  forecastHorizon,
  citationFamilies,
  citationSummaryLoading = false,
  citationFamiliesLoading = false,
  citationCpcGroups,
  citationCpcGroupsLoading = false,
  citationAttackers,
  citationAttackersLoading = false,
  citationFields,
  citationFieldsLoading = false,
  citationJurisdictions,
  citationJurisdictionsLoading = false,
  threatFields,
  citationYearOptions,
  citationFamilyField,
  citationFamilyStatus,
  citationFamilySort,
  citationAttackerField,
  citationAttackerJurisdiction,
  citationAttackerYear,
  errorMessages,
  onForecastHorizonChange,
  onForecastContributorPageChange,
  onCitationFamilyFieldChange,
  onCitationFamilyStatusChange,
  onCitationFamilySortChange,
  onCitationFamilyPageChange,
  onCitationFieldChange,
  onCitationJurisdictionChange,
  onCitationYearChange,
  onCitationFieldPageChange,
  onCitationJurisdictionPageChange,
  onCitationCpcPageChange,
  onCitationAttackerPageChange,
  onClearCitationFilters,
}: PortfolioCitationsTabProps) {
  const jurisdictionOptions = Array.from(
    new Set(
      [
        ...citationJurisdictions.rows.map((row) => row.jurisdictionCode).filter((value) => value.length > 0),
        citationAttackerJurisdiction,
      ].filter((value) => value.length > 0),
    ),
  ).sort();

  return (
    <section className="portfolio-tab-panel">
      <PortfolioCitationSummaryPanel
        summary={citationSummary}
        isLoading={citationSummaryLoading}
        errorMessage={errorMessages.citationSummary}
      />
      <PortfolioCitationTimeseriesPanel
        timeseries={citationTimeseries}
        forecast={forecast}
        forecastContributors={forecastContributors}
        isLoading={citationTimeseriesLoading}
        forecastContributorsLoading={forecastContributorsLoading}
        forecastHorizon={forecastHorizon}
        errorMessage={errorMessages.citationTimeseries}
        forecastContributorsError={errorMessages.forecastContributors}
        onForecastHorizonChange={onForecastHorizonChange}
        onForecastContributorPageChange={onForecastContributorPageChange}
      />
      <PortfolioCitationQualityPanel
        summary={citationSummary}
        isLoading={citationSummaryLoading}
        errorMessage={errorMessages.citationSummary}
      />
      <PortfolioCitationFamiliesPanel
        families={citationFamilies}
        isLoading={citationFamiliesLoading}
        fieldOptions={threatFields}
        selectedField={citationFamilyField}
        selectedStatus={citationFamilyStatus}
        selectedSort={citationFamilySort}
        errorMessage={errorMessages.citationFamilies}
        onFieldChange={onCitationFamilyFieldChange}
        onStatusChange={onCitationFamilyStatusChange}
        onSortChange={onCitationFamilySortChange}
        onPageChange={onCitationFamilyPageChange}
      />
      <PortfolioCitationAttackersPanel
        attackers={citationAttackers}
        isLoading={citationAttackersLoading}
        fieldOptions={threatFields}
        jurisdictionOptions={jurisdictionOptions}
        yearOptions={citationYearOptions}
        selectedField={citationAttackerField}
        selectedJurisdiction={citationAttackerJurisdiction}
        selectedYear={citationAttackerYear}
        errorMessage={errorMessages.citationAttackers}
        onFieldChange={onCitationFieldChange}
        onJurisdictionChange={onCitationJurisdictionChange}
        onYearChange={onCitationYearChange}
        onClearFilters={onClearCitationFilters}
        onPageChange={onCitationAttackerPageChange}
      />
      <PortfolioCitationCpcPanel
        cpcGroups={citationCpcGroups}
        selectedField={citationAttackerField}
        selectedJurisdiction={citationAttackerJurisdiction}
        selectedYear={citationAttackerYear}
        isLoading={citationCpcGroupsLoading}
        errorMessage={errorMessages.citationCpcGroups}
        onPageChange={onCitationCpcPageChange}
      />
      <div className="portfolio-grid portfolio-grid--split">
        <PortfolioCitationFieldsPanel
          fields={citationFields}
          isLoading={citationFieldsLoading}
          selectedJurisdiction={citationAttackerJurisdiction}
          selectedField={citationAttackerField}
          selectedYear={citationAttackerYear}
          errorMessage={errorMessages.citationFields}
          onFieldSelect={onCitationFieldChange}
          onPageChange={onCitationFieldPageChange}
        />
        <PortfolioCitationJurisdictionsPanel
          jurisdictions={citationJurisdictions}
          isLoading={citationJurisdictionsLoading}
          selectedField={citationAttackerField}
          selectedJurisdiction={citationAttackerJurisdiction}
          selectedYear={citationAttackerYear}
          errorMessage={errorMessages.citationJurisdictions}
          onJurisdictionSelect={onCitationJurisdictionChange}
          onPageChange={onCitationJurisdictionPageChange}
        />
      </div>
    </section>
  );
}
