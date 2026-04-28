"use client";

import { PortfolioFilingStrengthPanel } from "@/components/portfolio/portfolio-filing-strength-panel";
import { PortfolioJurisdictionUnlockPanel } from "@/components/portfolio/portfolio-jurisdiction-unlock-panel";
import { PortfolioOverviewBrief } from "@/components/portfolio/portfolio-overview-brief";
import { PortfolioStatusDistributionPanel } from "@/components/portfolio/portfolio-status-distribution-panel";
import { PortfolioStatusChronologyPanel } from "@/components/portfolio/portfolio-status-chronology-panel";
import type {
  PortfolioFamiliesResponse,
  PortfolioFieldRowsResponse,
  PortfolioFilingTimeseriesResponse,
  PortfolioJurisdictionUnlockHistoryResponse,
  PortfolioOverviewPayload,
  PortfolioStatusTimeseriesResponse,
  PortfolioThreatsResponse,
} from "@/lib/types/portfolio-v2";

type PortfolioExecutiveTabProps = {
  overview: PortfolioOverviewPayload;
  families: PortfolioFamiliesResponse;
  fields: PortfolioFieldRowsResponse;
  filingTimeseries: PortfolioFilingTimeseriesResponse;
  filingTimeseriesLoading?: boolean;
  statusTimeseries: PortfolioStatusTimeseriesResponse;
  statusTimeseriesLoading?: boolean;
  jurisdictionUnlockHistory: PortfolioJurisdictionUnlockHistoryResponse;
  jurisdictionUnlockHistoryLoading?: boolean;
  threats: PortfolioThreatsResponse;
  errorMessages?: {
    executive?: string;
    filingTimeseries?: string;
    statusTimeseries?: string;
    jurisdictionUnlocks?: string;
  };
};

export function PortfolioExecutiveTab({
  overview,
  families,
  fields,
  filingTimeseries,
  filingTimeseriesLoading = false,
  statusTimeseries,
  statusTimeseriesLoading = false,
  jurisdictionUnlockHistory,
  jurisdictionUnlockHistoryLoading = false,
  threats,
  errorMessages,
}: PortfolioExecutiveTabProps) {
  return (
    <div className="portfolio-tab-panel">
      <PortfolioStatusDistributionPanel
        slices={overview.statusMix}
        unclassifiedFamilyCount={overview.countScopes.unclassifiedFamilyCount}
      />
      <PortfolioOverviewBrief families={families} fields={fields} threats={threats} />
      <PortfolioFilingStrengthPanel
        timeseries={filingTimeseries}
        isLoading={filingTimeseriesLoading}
        errorMessage={errorMessages?.filingTimeseries}
      />
      <PortfolioStatusChronologyPanel
        history={statusTimeseries}
        isLoading={statusTimeseriesLoading}
        errorMessage={errorMessages?.statusTimeseries}
      />
      <PortfolioJurisdictionUnlockPanel
        history={jurisdictionUnlockHistory}
        isLoading={jurisdictionUnlockHistoryLoading}
        errorMessage={errorMessages?.jurisdictionUnlocks}
      />
      {errorMessages?.executive ? <p className="portfolio-error">{errorMessages.executive}</p> : null}
    </div>
  );
}
