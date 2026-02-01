/**
 * API configuration and utilities
 */

import type { PortfolioPatentsResponse } from "./types/patent";

const NGROK_URL = 'https://aurous-byron-disloyally.ngrok-free.dev';
const LOCALHOST_URL = 'http://localhost:8000';

export const API_BASE = NGROK_URL;

export function getPatentUrl(applnId: string): string {
  return `${API_BASE}/api/v1/patents/${encodeURIComponent(applnId)}`;
}

export function getSimilarPatentsUrl(applnId: string): string {
  return `${API_BASE}/api/v1/patents/${encodeURIComponent(applnId)}/similar`;
}

export function getPatentAnalysisUrl(applnId: string): string {
  return `${API_BASE}/api/v1/patents/${encodeURIComponent(applnId)}/analysis`;
}

export function getPortfolioOverviewUrl(ownerId: string | number): string {
  return `${API_BASE}/api/v1/portfolios/${encodeURIComponent(ownerId)}/overview`;
}

export function getPortfolioAnalyticsUrl(ownerId: string | number): string {
  return `${API_BASE}/api/v1/portfolios/${encodeURIComponent(ownerId)}/analytics`;
}

export function getPortfolioLicensingCandidatesUrl(ownerId: string | number, limit: number = 10, offset: number = 0): string {
  const params = new URLSearchParams({
    limit: limit.toString(),
    offset: offset.toString(),
  });
  return `${API_BASE}/api/v1/portfolios/${encodeURIComponent(ownerId)}/licensing-candidates?${params.toString()}`;
}

export function getPortfolioLicensingUrl(ownerId: string | number): string {
  return `${API_BASE}/api/v1/portfolios/${encodeURIComponent(ownerId)}/licensing`;
}

export function getPortfolioDiscoverUrl(dimension: "CPC" | "INDUSTRY" | "COUNTRY", value: string, limit: number = 20): string {
  const params = new URLSearchParams({
    dimension,
    value,
    limit: limit.toString(),
  });
  return `${API_BASE}/api/v1/portfolios/discover?${params.toString()}`;
}

export function getPortfolioPatentsUrl(
  ownerId: string | number,
  options?: {
    category?: string;
    sort?: string;
    order?: "asc" | "desc";
    limit?: number;
    offset?: number;
  }
): string {
  const params = new URLSearchParams();

  if (options) {
    if (options.category) {
      params.append("category", options.category);
    }
    if (options.sort) {
      params.append("sort", options.sort);
    }
    if (options.order) {
      params.append("order", options.order);
    }
    if (options.limit !== undefined) {
      params.append("limit", options.limit.toString());
    }
    if (options.offset !== undefined) {
      params.append("offset", options.offset.toString());
    }
  }

  const queryString = params.toString();
  return `${API_BASE}/api/v1/portfolios/${encodeURIComponent(ownerId)}/patents${queryString ? `?${queryString}` : ""}`;
}

export async function fetchPortfolioCategoryCounts(
  ownerId: string | number
): Promise<{ [key: string]: number }> {
  const categories = ["CROWN_JEWEL", "FORTRESS", "HIDDEN_GEM", "CORE_ASSET", "DEADWOOD"];

  // Fetch all category counts in parallel
  const promises = categories.map(async (category) => {
    try {
      const data = await fetchJson<PortfolioPatentsResponse>(
        getPortfolioPatentsUrl(ownerId, { category, limit: 1, offset: 0 })
      );
      return { category, count: data.pagination.total };
    } catch (err) {
      console.error(`Failed to fetch count for category ${category}:`, err);
      return { category, count: 0 };
    }
  });

  const results = await Promise.all(promises);

  // Convert array to object
  return results.reduce((acc, { category, count }) => {
    acc[category] = count;
    return acc;
  }, {} as { [key: string]: number });
}

/**
 * Fetch JSON from API with proper error handling and fallback mechanism
 */
export async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const fetchWithFallback = async (fetchUrl: string, isRetry: boolean = false): Promise<Response> => {
    try {
      const response = await fetch(fetchUrl, {
        ...options,
        headers: {
          'ngrok-skip-browser-warning': 'true',
          'Content-Type': 'application/json',
          ...options?.headers,
        },
      });
      return response;
    } catch (err) {
      // If network error and using ngrok, try fallback to localhost
      if (!isRetry && fetchUrl.startsWith(NGROK_URL)) {
        console.warn(`Failed to connect to Ngrok URL: ${fetchUrl}. Falling back to localhost...`);
        const fallbackUrl = fetchUrl.replace(NGROK_URL, LOCALHOST_URL);
        return fetchWithFallback(fallbackUrl, true);
      }
      throw err;
    }
  };

  const response = await fetchWithFallback(url);

  // Check content type before parsing
  const contentType = response.headers.get('content-type');
  if (!contentType?.includes('application/json')) {
    const text = await response.text();
    throw new Error(
      `Expected JSON but got ${contentType || 'unknown'}. Response preview: ${text.substring(0, 200)}`
    );
  }

  if (!response.ok) {
    let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
    try {
      const text = await response.text();
      if (text) {
        errorMessage += ` - ${text.substring(0, 200)}`;
      }
    } catch {
      // Ignore errors when reading error response
    }
    throw new Error(errorMessage);
  }

  const json = await response.json();

  // Log the actual response structure for debugging (client-side only)
  if (typeof window !== 'undefined' && process.env.NODE_ENV === 'development') {
    console.log(`[API Response] ${url}:`, JSON.stringify(json, null, 2).substring(0, 500));
  }

  return json as T;
}

