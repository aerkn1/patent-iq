import { fetchJson } from "@/lib/api/core";

import type {
  MarketApplicationGrantRow,
  MarketCpcCitingOwnerRow,
  MarketCpcJurisdictionRow,
  MarketCpcOwnerRow,
  MarketCpcTrendRow,
  MarketGrantMixRow,
  MarketLeadingJurisdictionRow,
  MarketOverviewHistoryRow,
  MarketSectionResponse,
  MarketWorkspaceResponse,
} from "@/lib/types/market-v2";

type FetchMarketWorkspaceOptions = {
  asOfYear?: number;
  marketState?: string;
  segmentId?: string;
};

export async function fetchMarketWorkspace(
  options: FetchMarketWorkspaceOptions = {},
): Promise<MarketWorkspaceResponse> {
  const params = new URLSearchParams();

  if (options.marketState && options.marketState !== "all") {
    params.set("market_state", options.marketState);
  }

  if (options.segmentId) {
    params.set("segment_id", options.segmentId);
  }

  if (options.asOfYear) {
    params.set("as_of_year", String(options.asOfYear));
  }

  const suffix = params.toString() ? `?${params.toString()}` : "";
  return fetchJson<MarketWorkspaceResponse>(`/api/v1/market-intelligence/workspace${suffix}`);
}

export async function fetchMarketOverviewHistory(): Promise<MarketOverviewHistoryRow[]> {
  const payload = await fetchJson<{ rows?: MarketOverviewHistoryRow[] }>("/api/v1/market-intelligence/overview-history");
  return payload.rows ?? [];
}

async function fetchMarketSection<Row>(path: string): Promise<MarketSectionResponse<Row>> {
  return fetchJson<MarketSectionResponse<Row>>(path);
}

export async function fetchMarketLeadingJurisdictions(
  asOfYear?: number,
  limitPerField = 5,
): Promise<MarketSectionResponse<MarketLeadingJurisdictionRow>> {
  const params = new URLSearchParams();

  if (asOfYear) {
    params.set("as_of_year", String(asOfYear));
  }

  params.set("limit_per_field", String(limitPerField));

  const suffix = params.toString() ? `?${params.toString()}` : "";
  return fetchMarketSection<MarketLeadingJurisdictionRow>(`/api/v1/market-intelligence/leading-jurisdictions${suffix}`);
}

type FetchMarketCpcTrendsOptions = {
  asOfYear?: number;
  limit?: number;
  offset?: number;
};

export async function fetchMarketCpcTrends(
  segmentId: string,
  options: FetchMarketCpcTrendsOptions = {},
): Promise<MarketSectionResponse<MarketCpcTrendRow>> {
  const params = new URLSearchParams();
  params.set("segment_id", segmentId);

  if (options.asOfYear) {
    params.set("as_of_year", String(options.asOfYear));
  }

  if (options.limit) {
    params.set("limit", String(options.limit));
  }

  if (options.offset) {
    params.set("offset", String(options.offset));
  }

  const suffix = params.toString() ? `?${params.toString()}` : "";
  return fetchMarketSection<MarketCpcTrendRow>(`/api/v1/market-intelligence/cpc-trends${suffix}`);
}

type FetchMarketSegmentCpcJurisdictionsOptions = {
  asOfYear?: number;
  cpcMainGroup?: string;
  jurisdictionCode?: string;
  limit?: number;
  offset?: number;
};

export async function fetchMarketSegmentCpcJurisdictions(
  segmentId: string,
  options: FetchMarketSegmentCpcJurisdictionsOptions = {},
): Promise<MarketSectionResponse<MarketCpcJurisdictionRow>> {
  const params = new URLSearchParams();

  if (options.asOfYear) {
    params.set("as_of_year", String(options.asOfYear));
  }

  if (options.cpcMainGroup) {
    params.set("cpc_main_group", options.cpcMainGroup);
  }

  if (options.jurisdictionCode) {
    params.set("jurisdiction_code", options.jurisdictionCode);
  }

  if (options.limit) {
    params.set("limit", String(options.limit));
  }

  if (options.offset) {
    params.set("offset", String(options.offset));
  }

  const suffix = params.toString() ? `?${params.toString()}` : "";
  return fetchMarketSection<MarketCpcJurisdictionRow>(
    `/api/v1/market-intelligence/segments/${encodeURIComponent(segmentId)}/cpc-jurisdictions${suffix}`,
  );
}

type FetchMarketSegmentCpcOwnersOptions = {
  asOfYear?: number;
  limit?: number;
  offset?: number;
};

export async function fetchMarketSegmentCpcOwners(
  segmentId: string,
  cpcMainGroup: string,
  options: FetchMarketSegmentCpcOwnersOptions = {},
): Promise<MarketSectionResponse<MarketCpcOwnerRow>> {
  const params = new URLSearchParams();
  params.set("cpc_main_group", cpcMainGroup);

  if (options.asOfYear) {
    params.set("as_of_year", String(options.asOfYear));
  }

  if (options.limit) {
    params.set("limit", String(options.limit));
  }

  if (options.offset) {
    params.set("offset", String(options.offset));
  }

  const suffix = params.toString() ? `?${params.toString()}` : "";
  return fetchMarketSection<MarketCpcOwnerRow>(
    `/api/v1/market-intelligence/segments/${encodeURIComponent(segmentId)}/cpc-owners${suffix}`,
  );
}

export async function fetchMarketSegmentCpcCitingOwners(
  segmentId: string,
  cpcMainGroup: string,
  options: FetchMarketSegmentCpcOwnersOptions = {},
): Promise<MarketSectionResponse<MarketCpcCitingOwnerRow>> {
  const params = new URLSearchParams();
  params.set("cpc_main_group", cpcMainGroup);

  if (options.asOfYear) {
    params.set("as_of_year", String(options.asOfYear));
  }

  if (options.limit) {
    params.set("limit", String(options.limit));
  }

  if (options.offset) {
    params.set("offset", String(options.offset));
  }

  const suffix = params.toString() ? `?${params.toString()}` : "";
  return fetchMarketSection<MarketCpcCitingOwnerRow>(
    `/api/v1/market-intelligence/segments/${encodeURIComponent(segmentId)}/cpc-citing-owners${suffix}`,
  );
}

type FetchMarketSegmentApplicationsGrantsOptions = {
  yearFrom?: number;
  yearTo?: number;
  jurisdictionLimit?: number;
};

export async function fetchMarketSegmentApplicationsGrants(
  segmentId: string,
  options: FetchMarketSegmentApplicationsGrantsOptions = {},
): Promise<MarketSectionResponse<MarketApplicationGrantRow>> {
  const params = new URLSearchParams();

  if (options.yearFrom) {
    params.set("year_from", String(options.yearFrom));
  }

  if (options.yearTo) {
    params.set("year_to", String(options.yearTo));
  }

  if (options.jurisdictionLimit) {
    params.set("jurisdiction_limit", String(options.jurisdictionLimit));
  }

  const suffix = params.toString() ? `?${params.toString()}` : "";
  return fetchMarketSection<MarketApplicationGrantRow>(
    `/api/v1/market-intelligence/segments/${encodeURIComponent(segmentId)}/applications-grants${suffix}`,
  );
}

type FetchMarketSegmentGrantMixOptions = {
  asOfYear?: number;
  limit?: number;
  offset?: number;
};

export async function fetchMarketSegmentGrantMix(
  segmentId: string,
  options: FetchMarketSegmentGrantMixOptions = {},
): Promise<MarketSectionResponse<MarketGrantMixRow>> {
  const params = new URLSearchParams();

  if (options.asOfYear) {
    params.set("as_of_year", String(options.asOfYear));
  }

  if (options.limit) {
    params.set("limit", String(options.limit));
  }

  if (options.offset) {
    params.set("offset", String(options.offset));
  }

  const suffix = params.toString() ? `?${params.toString()}` : "";
  return fetchMarketSection<MarketGrantMixRow>(
    `/api/v1/market-intelligence/segments/${encodeURIComponent(segmentId)}/grant-mix${suffix}`,
  );
}
