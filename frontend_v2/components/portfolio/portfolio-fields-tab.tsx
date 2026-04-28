"use client";

import { PortfolioClassificationPanel } from "@/components/portfolio/portfolio-classification-panel";
import { PortfolioClusterChipRail } from "@/components/portfolio/portfolio-cluster-chip-rail";
import { PortfolioFieldCitationFamiliesPanel } from "@/components/portfolio/portfolio-field-citation-families-panel";
import { PortfolioFieldExposure } from "@/components/portfolio/portfolio-field-exposure";
import { PortfolioFieldThreatsPanel } from "@/components/portfolio/portfolio-field-threats-panel";
import { PortfolioFieldTimeseriesPanel } from "@/components/portfolio/portfolio-field-timeseries";
import type {
  PortfolioCitationFamiliesResponse,
  PortfolioClassificationResponse,
  PortfolioFieldRowsResponse,
  PortfolioFieldTimeseries,
  PortfolioThreatsResponse,
} from "@/lib/types/portfolio-v2";

type PortfolioFieldsTabProps = {
  fieldClusterOptions: string[];
  activeField: string;
  filteredFieldRows: PortfolioFieldRowsResponse["rows"];
  fieldsLoading?: boolean;
  filteredTimeseries: PortfolioFieldTimeseries[];
  fieldTimeseriesLoading?: boolean;
  classification: PortfolioClassificationResponse;
  classificationLoading?: boolean;
  fieldCitationFamilies: PortfolioCitationFamiliesResponse;
  fieldThreats: PortfolioThreatsResponse;
  fieldCitationFamiliesLoading?: boolean;
  fieldThreatsLoading?: boolean;
  usingClassificationFieldFallback: boolean;
  errorMessages: {
    classification?: string;
    fields?: string;
    fieldTimeseries?: string;
    fieldCitationFamilies?: string;
    fieldThreats?: string;
  };
  onSelectField: (field: string) => void;
  onClassificationPageChange: (offset: number) => void;
  onFieldCitationFamiliesPageChange: (offset: number) => void;
  onFieldThreatsPageChange: (offset: number) => void;
};

export function PortfolioFieldsTab({
  fieldClusterOptions,
  activeField,
  filteredFieldRows,
  fieldsLoading = false,
  filteredTimeseries,
  fieldTimeseriesLoading = false,
  classification,
  classificationLoading = false,
  fieldCitationFamilies,
  fieldThreats,
  fieldCitationFamiliesLoading = false,
  fieldThreatsLoading = false,
  usingClassificationFieldFallback,
  errorMessages,
  onSelectField,
  onClassificationPageChange,
  onFieldCitationFamiliesPageChange,
  onFieldThreatsPageChange,
}: PortfolioFieldsTabProps) {
  return (
    <section className="portfolio-tab-panel">
      <PortfolioClusterChipRail fields={fieldClusterOptions} selectedField={activeField} onSelectField={onSelectField} />
      <div className="portfolio-grid portfolio-grid--split">
        <PortfolioFieldExposure rows={filteredFieldRows} isLoading={fieldsLoading} errorMessage={errorMessages.fields} />
        <PortfolioClassificationPanel
          classification={classification}
          isLoading={classificationLoading}
          errorMessage={errorMessages.classification}
          selectedField={activeField}
          onPageChange={onClassificationPageChange}
        />
      </div>
      {activeField ? (
        <PortfolioFieldTimeseriesPanel
          timeseries={filteredTimeseries}
          isLoading={fieldTimeseriesLoading}
          selectedField={activeField}
          onSelectField={onSelectField}
          errorMessage={usingClassificationFieldFallback ? undefined : errorMessages.fieldTimeseries}
          note={
            usingClassificationFieldFallback
              ? "Using classification chronology fallback because the dedicated field timeseries for this owner is still sparse."
              : undefined
          }
        />
      ) : null}
      {activeField ? (
        <div className="portfolio-grid portfolio-grid--split">
          <PortfolioFieldThreatsPanel
            field={activeField}
            threats={fieldThreats}
            isLoading={fieldThreatsLoading}
            errorMessage={errorMessages.fieldThreats}
            onPageChange={onFieldThreatsPageChange}
          />
          <PortfolioFieldCitationFamiliesPanel
            field={activeField}
            families={fieldCitationFamilies}
            isLoading={fieldCitationFamiliesLoading}
            errorMessage={errorMessages.fieldCitationFamilies}
            onPageChange={onFieldCitationFamiliesPageChange}
          />
        </div>
      ) : null}
    </section>
  );
}
