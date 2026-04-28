"use client";

import dynamic from "next/dynamic";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useLocalStorage } from "react-use";

import { PortfolioPrimaryTabs, type PortfolioWorkspaceTab } from "@/components/portfolio/portfolio-primary-tabs";
import { PortfolioWorkspaceControls } from "@/components/portfolio/portfolio-workspace-controls";
import { PortfolioSummaryCards } from "@/components/portfolio/portfolio-summary-cards";
import { PortfolioWorkspaceSkeleton } from "@/components/portfolio/portfolio-workspace-skeleton";
import { useWorkspaceContextOverride } from "@/components/ui/workspace-context";
import {
  fetchPortfolioCitationAttackers,
  fetchPortfolioCitationCpcGroups,
  fetchPortfolioCitationFamilies,
  fetchPortfolioCitationFields,
  fetchPortfolioCitationJurisdictions,
  fetchPortfolioCitationSummary,
  fetchPortfolioCitationTimeseries,
  fetchPortfolioClassification,
  fetchPortfolioDashboard,
  fetchPortfolioFilingTimeseries,
  fetchPortfolioFieldTimeseries,
  fetchPortfolioFields,
  fetchPortfolioFamilies,
  fetchPortfolioJurisdictionUnlockHistory,
  fetchPortfolioForecastContributors,
  fetchPortfolioOwnerSuggestions,
  fetchPortfolioPendingGrants,
  fetchPortfolioStatusTimeseries,
  fetchPortfolioThreats,
} from "@/lib/api/portfolio-v2";
import type {
  PortfolioCitationAttackersResponse,
  PortfolioCitationCpcGroupsResponse,
  PortfolioCitationFamiliesResponse,
  PortfolioCitationFieldsResponse,
  PortfolioCitationJurisdictionsResponse,
  PortfolioCitationSummaryResponse,
  PortfolioCitationTimeseriesResponse,
  PortfolioClassificationResponse,
  PortfolioDashboardPayload,
  PortfolioFilingTimeseriesResponse,
  PortfolioFieldRowsResponse,
  PortfolioFieldTimeseriesResponse,
  PortfolioFamiliesResponse,
  PortfolioForecastPayload,
  PortfolioForecastContributorsResponse,
  PortfolioJurisdictionUnlockHistoryResponse,
  PortfolioOwnerSuggestion,
  PortfolioPendingGrantResponse,
  PortfolioStatusTimeseriesResponse,
  PortfolioThreatsResponse,
} from "@/lib/types/portfolio-v2";

type PortfolioWorkspaceProps = {
  ownerId: string;
};

type SectionErrors = {
  citationSummary?: string;
  citationTimeseries?: string;
  citationFamilies?: string;
  citationAttackers?: string;
  citationFields?: string;
  citationJurisdictions?: string;
  citationCpcGroups?: string;
  families?: string;
  filingTimeseries?: string;
  jurisdictionUnlocks?: string;
  fieldCitationFamilies?: string;
  fieldThreats?: string;
  classification?: string;
  fields?: string;
  fieldTimeseries?: string;
  forecast?: string;
  forecastContributors?: string;
  pendingGrants?: string;
  statusTimeseries?: string;
};

type SectionLoading = {
  [K in keyof SectionErrors]?: boolean;
};

const allowedTabs: PortfolioWorkspaceTab[] = [
  "executive",
  "families",
  "citations",
  "fields",
  "forecast",
];

function TabLoadingState({ label }: { label: string }) {
  return (
    <section className="portfolio-tab-panel">
      <p className="portfolio-small-note">{label}</p>
    </section>
  );
}

const PortfolioExecutiveTab = dynamic(
  () => import("@/components/portfolio/portfolio-executive-tab").then((mod) => mod.PortfolioExecutiveTab),
  { loading: () => <TabLoadingState label="Loading overview…" /> },
);
const PortfolioCitationsTab = dynamic(
  () => import("@/components/portfolio/portfolio-citations-tab").then((mod) => mod.PortfolioCitationsTab),
  { loading: () => <TabLoadingState label="Loading citation…" /> },
);
const PortfolioFamiliesTab = dynamic(
  () => import("@/components/portfolio/portfolio-families-tab").then((mod) => mod.PortfolioFamiliesTab),
  { loading: () => <TabLoadingState label="Loading families…" /> },
);
const PortfolioFieldsTab = dynamic(
  () => import("@/components/portfolio/portfolio-fields-tab").then((mod) => mod.PortfolioFieldsTab),
  { loading: () => <TabLoadingState label="Loading fields…" /> },
);
const PortfolioForecastTab = dynamic(
  () => import("@/components/portfolio/portfolio-forecast-tab").then((mod) => mod.PortfolioForecastTab),
  { loading: () => <TabLoadingState label="Loading forecast…" /> },
);

function parseWorkspaceTab(value: string | null): PortfolioWorkspaceTab {
  if (value === "threats") {
    return "citations";
  }

  if (value === "classification" || value === "compare") {
    return "fields";
  }

  return allowedTabs.includes(value as PortfolioWorkspaceTab) ? (value as PortfolioWorkspaceTab) : "executive";
}

export function PortfolioWorkspace({ ownerId }: PortfolioWorkspaceProps) {
  const router = useRouter();
  const pathname = usePathname() ?? `/portfolio/${encodeURIComponent(ownerId)}`;
  const searchParams = useSearchParams();
  const query = searchParams ?? new URLSearchParams();
  const pageSize = 10;
  const previousOwnerId = useRef(ownerId);

  const [storedOwner, setStoredOwner] = useLocalStorage("portfolio.owner.last", ownerId);
  const [payload, setPayload] = useState<PortfolioDashboardPayload | null>(null);
  const [citationSummary, setCitationSummary] = useState<PortfolioCitationSummaryResponse | null>(null);
  const [citationTimeseries, setCitationTimeseries] = useState<PortfolioCitationTimeseriesResponse | null>(null);
  const [citationFamilies, setCitationFamilies] = useState<PortfolioCitationFamiliesResponse | null>(null);
  const [citationAttackers, setCitationAttackers] = useState<PortfolioCitationAttackersResponse | null>(null);
  const [citationFields, setCitationFields] = useState<PortfolioCitationFieldsResponse | null>(null);
  const [citationJurisdictions, setCitationJurisdictions] = useState<PortfolioCitationJurisdictionsResponse | null>(null);
  const [citationCpcGroups, setCitationCpcGroups] = useState<PortfolioCitationCpcGroupsResponse | null>(null);
  const [families, setFamilies] = useState<PortfolioFamiliesResponse | null>(null);
  const [filingTimeseries, setFilingTimeseries] = useState<PortfolioFilingTimeseriesResponse | null>(null);
  const [statusTimeseries, setStatusTimeseries] = useState<PortfolioStatusTimeseriesResponse | null>(null);
  const [jurisdictionUnlockHistory, setJurisdictionUnlockHistory] = useState<PortfolioJurisdictionUnlockHistoryResponse | null>(null);
  const [fieldCitationFamilies, setFieldCitationFamilies] = useState<PortfolioCitationFamiliesResponse | null>(null);
  const [fieldRows, setFieldRows] = useState<PortfolioFieldRowsResponse | null>(null);
  const [forecast, setForecast] = useState<PortfolioForecastPayload | null>(null);
  const [fieldThreats, setFieldThreats] = useState<PortfolioThreatsResponse | null>(null);
  const [classification, setClassification] = useState<PortfolioClassificationResponse | null>(null);
  const [fieldTimeseries, setFieldTimeseries] = useState<PortfolioFieldTimeseriesResponse | null>(null);
  const [forecastContributors, setForecastContributors] = useState<PortfolioForecastContributorsResponse | null>(null);
  const [pendingGrants, setPendingGrants] = useState<PortfolioPendingGrantResponse | null>(null);
  const [sectionErrors, setSectionErrors] = useState<SectionErrors>({});
  const [sectionLoading, setSectionLoading] = useState<SectionLoading>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [ownerInput, setOwnerInput] = useState<string>(ownerId);
  const [suggestions, setSuggestions] = useState<PortfolioOwnerSuggestion[]>([]);
  const [searching, setSearching] = useState(false);
  const [citationAttackerOffset, setCitationAttackerOffset] = useState(0);
  const [citationFieldOffset, setCitationFieldOffset] = useState(0);
  const [citationJurisdictionOffset, setCitationJurisdictionOffset] = useState(0);
  const [citationCpcOffset, setCitationCpcOffset] = useState(0);
  const [citationFamilyOffset, setCitationFamilyOffset] = useState(0);
  const [citationFamilyField, setCitationFamilyField] = useState("");
  const [citationFamilyStatus, setCitationFamilyStatus] = useState("");
  const [citationFamilySort, setCitationFamilySort] = useState<"forward_clean" | "forward_weighted" | "early_5y" | "early_7y" | "blocking">("forward_clean");
  const [citationAttackerField, setCitationAttackerField] = useState("");
  const [citationAttackerJurisdiction, setCitationAttackerJurisdiction] = useState("");
  const [citationAttackerYear, setCitationAttackerYear] = useState("");
  const [fieldCitationFamilyOffset, setFieldCitationFamilyOffset] = useState(0);
  const [fieldThreatOffset, setFieldThreatOffset] = useState(0);
  const [familyOffset, setFamilyOffset] = useState(0);
  const [familyQuery, setFamilyQuery] = useState("");
  const [familyStatus, setFamilyStatus] = useState("");
  const [familyPrimaryField, setFamilyPrimaryField] = useState("");
  const [familySort, setFamilySort] = useState<"blocking" | "priority_year">("blocking");
  const [classificationOffset, setClassificationOffset] = useState(0);
  const [contributorOffset, setContributorOffset] = useState(0);
  const [forecastHorizon, setForecastHorizon] = useState<"3y" | "5y">("3y");
  const [pendingGrantJurisdiction, setPendingGrantJurisdiction] = useState("");
  const [pendingGrantField, setPendingGrantField] = useState("");

  const activeTab = parseWorkspaceTab(query.get("tab"));
  const activeField = query.get("field") ?? "";
  const citationsTabActive = activeTab === "citations";
  const familiesTabActive = activeTab === "families";
  const fieldsTabActive = activeTab === "fields";
  const forecastTabActive = activeTab === "forecast";

  const updateWorkspaceQuery = useCallback((updates: Record<string, string | null>) => {
    const params = new URLSearchParams(searchParams?.toString() ?? "");
    Object.entries(updates).forEach(([key, value]) => {
      if (!value) {
        params.delete(key);
        return;
      }
      params.set(key, value);
    });
    const nextQuery = params.toString();
    router.replace(nextQuery ? `${pathname}?${nextQuery}` : pathname, { scroll: false });
  }, [pathname, router, searchParams]);

  const updateSectionLoading = useCallback((updates: SectionLoading) => {
    setSectionLoading((current) => ({ ...current, ...updates }));
  }, []);

  useEffect(() => {
    let disposed = false;

    async function loadDashboard() {
      setLoading(true);
      setError(null);
      try {
        const dashboard = await fetchPortfolioDashboard(ownerId);
        if (!disposed) {
          setPayload(dashboard);
          setFamilies(dashboard.families);
          setFieldRows(dashboard.fields);
          setForecast(dashboard.forecast);
        }
      } catch (ex) {
        if (!disposed) {
          setError(ex instanceof Error ? ex.message : "Could not load portfolio workspace.");
        }
      } finally {
        if (!disposed) {
          setLoading(false);
        }
      }
    }

    void loadDashboard();
    return () => {
      disposed = true;
    };
  }, [ownerId]);

  useEffect(() => {
    setOwnerInput(ownerId);
  }, [ownerId]);

  useEffect(() => {
    const ownerChanged = previousOwnerId.current !== ownerId;
    previousOwnerId.current = ownerId;
    if (!ownerChanged) {
      return;
    }
    if (query.get("field")) {
      updateWorkspaceQuery({ field: null });
    }
    setClassification(null);
    setFieldTimeseries(null);
    setCitationAttackerOffset(0);
    setCitationFieldOffset(0);
    setCitationJurisdictionOffset(0);
    setCitationCpcOffset(0);
    setCitationFamilyOffset(0);
    setCitationFamilyField("");
    setCitationFamilyStatus("");
    setCitationFamilySort("forward_clean");
    setCitationAttackerField("");
    setCitationAttackerJurisdiction("");
    setCitationAttackerYear("");
    setFieldCitationFamilyOffset(0);
    setFieldThreatOffset(0);
    setFamilyOffset(0);
    setFamilyQuery("");
    setFamilyStatus("");
    setFamilyPrimaryField("");
    setClassificationOffset(0);
    setContributorOffset(0);
    setForecastHorizon("3y");
    setPendingGrantJurisdiction("");
    setPendingGrantField("");
    setCitationSummary(null);
    setCitationTimeseries(null);
    setCitationFamilies(null);
    setCitationAttackers(null);
    setCitationFields(null);
    setCitationJurisdictions(null);
    setCitationCpcGroups(null);
    setFamilies(null);
    setFilingTimeseries(null);
    setStatusTimeseries(null);
    setJurisdictionUnlockHistory(null);
    setFieldCitationFamilies(null);
    setFieldRows(null);
    setForecast(null);
    setFieldThreats(null);
    setClassification(null);
    setFieldTimeseries(null);
    setForecastContributors(null);
    setPendingGrants(null);
    setSectionErrors({});
    setSectionLoading({});
    setSuggestions([]);
  }, [ownerId, query, updateWorkspaceQuery]);

  useEffect(() => {
    if (!storedOwner) {
      setStoredOwner(ownerId);
      return;
    }

    if (storedOwner !== ownerId) {
      setStoredOwner(ownerId);
    }
  }, [ownerId, setStoredOwner, storedOwner]);

  useEffect(() => {
    if (activeTab !== "executive") {
      return;
    }

    let cancelled = false;
    updateSectionLoading({
      filingTimeseries: true,
      statusTimeseries: true,
      jurisdictionUnlocks: true,
    });

    void Promise.allSettled([
      fetchPortfolioFilingTimeseries(ownerId),
      fetchPortfolioStatusTimeseries(ownerId),
      fetchPortfolioJurisdictionUnlockHistory(ownerId),
    ]).then(([filingResult, statusResult, jurisdictionResult]) => {
      if (cancelled) {
        return;
      }

      if (filingResult.status === "fulfilled") {
        setFilingTimeseries(filingResult.value);
        setSectionErrors((current) => ({ ...current, filingTimeseries: undefined }));
      } else {
        setSectionErrors((current) => ({
          ...current,
          filingTimeseries:
            filingResult.reason instanceof Error ? filingResult.reason.message : "Could not load filing chronology.",
        }));
      }

      if (statusResult.status === "fulfilled") {
        setStatusTimeseries(statusResult.value);
        setSectionErrors((current) => ({ ...current, statusTimeseries: undefined }));
      } else {
        setSectionErrors((current) => ({
          ...current,
          statusTimeseries:
            statusResult.reason instanceof Error ? statusResult.reason.message : "Could not load status chronology.",
        }));
      }

      if (jurisdictionResult.status === "fulfilled") {
        setJurisdictionUnlockHistory(jurisdictionResult.value);
        setSectionErrors((current) => ({ ...current, jurisdictionUnlocks: undefined }));
      } else {
        setSectionErrors((current) => ({
          ...current,
          jurisdictionUnlocks:
            jurisdictionResult.reason instanceof Error
              ? jurisdictionResult.reason.message
              : "Could not load jurisdiction unlock chronology.",
        }));
      }
      updateSectionLoading({
        filingTimeseries: false,
        statusTimeseries: false,
        jurisdictionUnlocks: false,
      });
    });

    return () => {
      cancelled = true;
      updateSectionLoading({
        filingTimeseries: false,
        statusTimeseries: false,
        jurisdictionUnlocks: false,
      });
    };
  }, [activeTab, ownerId, updateSectionLoading]);

  useEffect(() => {
    if (!citationsTabActive) {
      return;
    }

    let cancelled = false;
    updateSectionLoading({ citationSummary: true });

    void fetchPortfolioCitationSummary(ownerId)
      .then((result) => {
        if (!cancelled) {
          setCitationSummary(result);
          setSectionErrors((current) => ({ ...current, citationSummary: undefined }));
        }
      })
      .catch((ex) => {
        if (!cancelled) {
          setSectionErrors((current) => ({
            ...current,
            citationSummary: ex instanceof Error ? ex.message : "Could not load citation summary.",
          }));
        }
      })
      .finally(() => {
        if (!cancelled) {
          updateSectionLoading({ citationSummary: false });
        }
      });

    return () => {
      cancelled = true;
      updateSectionLoading({ citationSummary: false });
    };
  }, [citationsTabActive, ownerId, updateSectionLoading]);

  useEffect(() => {
    if (!citationsTabActive) {
      return;
    }

    let cancelled = false;
    updateSectionLoading({ citationFamilies: true });

    void fetchPortfolioCitationFamilies(ownerId, {
      limit: pageSize,
      offset: citationFamilyOffset,
      wipoField: citationFamilyField || undefined,
      status: citationFamilyStatus || undefined,
      sort: citationFamilySort,
    })
      .then((result) => {
        if (!cancelled) {
          setCitationFamilies(result);
          setSectionErrors((current) => ({ ...current, citationFamilies: undefined }));
        }
      })
      .catch((ex) => {
        if (!cancelled) {
          setSectionErrors((current) => ({
            ...current,
            citationFamilies: ex instanceof Error ? ex.message : "Could not load cited families.",
          }));
        }
      })
      .finally(() => {
        if (!cancelled) {
          updateSectionLoading({ citationFamilies: false });
        }
      });

    return () => {
      cancelled = true;
      updateSectionLoading({ citationFamilies: false });
    };
  }, [
    citationFamilyField,
    citationFamilyOffset,
    citationFamilySort,
    citationFamilyStatus,
    citationsTabActive,
    ownerId,
    pageSize,
    updateSectionLoading,
  ]);

  useEffect(() => {
    if (!citationsTabActive) {
      return;
    }

    let cancelled = false;
    updateSectionLoading({ citationTimeseries: true });

    void fetchPortfolioCitationTimeseries(ownerId)
      .then((result) => {
        if (!cancelled) {
          setCitationTimeseries(result);
          setSectionErrors((current) => ({ ...current, citationTimeseries: undefined }));
        }
      })
      .catch((ex) => {
        if (!cancelled) {
          setSectionErrors((current) => ({
            ...current,
            citationTimeseries: ex instanceof Error ? ex.message : "Could not load citation chronology.",
          }));
        }
      })
      .finally(() => {
        if (!cancelled) {
          updateSectionLoading({ citationTimeseries: false });
        }
      });

    return () => {
      cancelled = true;
      updateSectionLoading({ citationTimeseries: false });
    };
  }, [citationsTabActive, ownerId, updateSectionLoading]);

  useEffect(() => {
    if (!citationsTabActive) {
      return;
    }

    let cancelled = false;
    updateSectionLoading({ citationAttackers: true });

    void fetchPortfolioCitationAttackers(ownerId, {
      limit: pageSize,
      offset: citationAttackerOffset,
      wipoField: citationAttackerField || undefined,
      jurisdictionCode: citationAttackerJurisdiction || undefined,
      yearFrom: citationAttackerYear ? Number(citationAttackerYear) : undefined,
      yearTo: citationAttackerYear ? Number(citationAttackerYear) : undefined,
    })
      .then((result) => {
        if (!cancelled) {
          setCitationAttackers(result);
          setSectionErrors((current) => ({ ...current, citationAttackers: undefined }));
        }
      })
      .catch((ex) => {
        if (!cancelled) {
          setSectionErrors((current) => ({
            ...current,
            citationAttackers: ex instanceof Error ? ex.message : "Could not load citation attackers.",
          }));
        }
      })
      .finally(() => {
        if (!cancelled) {
          updateSectionLoading({ citationAttackers: false });
        }
      });

    return () => {
      cancelled = true;
      updateSectionLoading({ citationAttackers: false });
    };
  }, [
    citationAttackerField,
    citationAttackerJurisdiction,
    citationAttackerOffset,
    citationAttackerYear,
    citationsTabActive,
    ownerId,
    pageSize,
    updateSectionLoading,
  ]);

  useEffect(() => {
    if (!citationsTabActive) {
      return;
    }

    let cancelled = false;
    updateSectionLoading({ citationFields: true });

    void fetchPortfolioCitationFields(ownerId, {
      limit: pageSize,
      offset: citationFieldOffset,
      jurisdictionCode: citationAttackerJurisdiction || undefined,
      yearFrom: citationAttackerYear ? Number(citationAttackerYear) : undefined,
      yearTo: citationAttackerYear ? Number(citationAttackerYear) : undefined,
    })
      .then((result) => {
        if (!cancelled) {
          setCitationFields(result);
          setSectionErrors((current) => ({ ...current, citationFields: undefined }));
        }
      })
      .catch((ex) => {
        if (!cancelled) {
          setSectionErrors((current) => ({
            ...current,
            citationFields: ex instanceof Error ? ex.message : "Could not load citation fields.",
          }));
        }
      })
      .finally(() => {
        if (!cancelled) {
          updateSectionLoading({ citationFields: false });
        }
      });

    return () => {
      cancelled = true;
      updateSectionLoading({ citationFields: false });
    };
  }, [
    citationAttackerJurisdiction,
    citationAttackerYear,
    citationFieldOffset,
    citationsTabActive,
    ownerId,
    pageSize,
    updateSectionLoading,
  ]);

  useEffect(() => {
    if (!citationsTabActive) {
      return;
    }

    let cancelled = false;
    updateSectionLoading({ citationJurisdictions: true });

    void fetchPortfolioCitationJurisdictions(ownerId, {
      limit: pageSize,
      offset: citationJurisdictionOffset,
      wipoField: citationAttackerField || undefined,
      yearFrom: citationAttackerYear ? Number(citationAttackerYear) : undefined,
      yearTo: citationAttackerYear ? Number(citationAttackerYear) : undefined,
    })
      .then((result) => {
        if (!cancelled) {
          setCitationJurisdictions(result);
          setSectionErrors((current) => ({ ...current, citationJurisdictions: undefined }));
        }
      })
      .catch((ex) => {
        if (!cancelled) {
          setSectionErrors((current) => ({
            ...current,
            citationJurisdictions: ex instanceof Error ? ex.message : "Could not load citation jurisdictions.",
          }));
        }
      })
      .finally(() => {
        if (!cancelled) {
          updateSectionLoading({ citationJurisdictions: false });
        }
      });

    return () => {
      cancelled = true;
      updateSectionLoading({ citationJurisdictions: false });
    };
  }, [
    citationAttackerField,
    citationAttackerYear,
    citationJurisdictionOffset,
    citationsTabActive,
    ownerId,
    pageSize,
    updateSectionLoading,
  ]);

  useEffect(() => {
    if (!citationsTabActive) {
      return;
    }

    let cancelled = false;
    updateSectionLoading({ citationCpcGroups: true });

    void fetchPortfolioCitationCpcGroups(ownerId, {
      limit: pageSize,
      offset: citationCpcOffset,
      wipoField: citationAttackerField || undefined,
      jurisdictionCode: citationAttackerJurisdiction || undefined,
      yearFrom: citationAttackerYear ? Number(citationAttackerYear) : undefined,
      yearTo: citationAttackerYear ? Number(citationAttackerYear) : undefined,
    })
      .then((result) => {
        if (!cancelled) {
          setCitationCpcGroups(result);
          setSectionErrors((current) => ({ ...current, citationCpcGroups: undefined }));
        }
      })
      .catch((ex) => {
        if (!cancelled) {
          setSectionErrors((current) => ({
            ...current,
            citationCpcGroups: ex instanceof Error ? ex.message : "Could not load cited CPC groups.",
          }));
        }
      })
      .finally(() => {
        if (!cancelled) {
          updateSectionLoading({ citationCpcGroups: false });
        }
      });

    return () => {
      cancelled = true;
      updateSectionLoading({ citationCpcGroups: false });
    };
  }, [
    citationAttackerField,
    citationAttackerJurisdiction,
    citationAttackerYear,
    citationCpcOffset,
    citationsTabActive,
    ownerId,
    pageSize,
    updateSectionLoading,
  ]);

  useEffect(() => {
    if (!familiesTabActive) {
      return;
    }

    let cancelled = false;
    updateSectionLoading({ families: true });

    void fetchPortfolioFamilies(ownerId, {
      limit: pageSize,
      offset: familyOffset,
      q: familyQuery || undefined,
      status: familyStatus || undefined,
      primaryField: familyPrimaryField || undefined,
      sort: familySort,
    })
      .then((result) => {
        if (!cancelled) {
          setFamilies(result);
          setSectionErrors((current) => ({ ...current, families: undefined }));
        }
      })
      .catch((ex) => {
        if (!cancelled) {
          setSectionErrors((current) => ({
            ...current,
            families: ex instanceof Error ? ex.message : "Could not load families.",
          }));
        }
      })
      .finally(() => {
        if (!cancelled) {
          updateSectionLoading({ families: false });
        }
      });

    return () => {
      cancelled = true;
      updateSectionLoading({ families: false });
    };
  }, [
    familiesTabActive,
    familyOffset,
    familyPrimaryField,
    familyQuery,
    familySort,
    familyStatus,
    ownerId,
    pageSize,
    updateSectionLoading,
  ]);

  useEffect(() => {
    if (!fieldsTabActive) {
      return;
    }

    let cancelled = false;
    updateSectionLoading({ fields: true });

    void fetchPortfolioFields(ownerId)
      .then((result) => {
        if (!cancelled) {
          setFieldRows(result);
          setSectionErrors((current) => ({ ...current, fields: undefined }));
        }
      })
      .catch((ex) => {
        if (!cancelled) {
          setSectionErrors((current) => ({
            ...current,
            fields: ex instanceof Error ? ex.message : "Could not load field exposure.",
          }));
        }
      })
      .finally(() => {
        if (!cancelled) {
          updateSectionLoading({ fields: false });
        }
      });

    return () => {
      cancelled = true;
      updateSectionLoading({ fields: false });
    };
  }, [fieldsTabActive, ownerId, updateSectionLoading]);

  useEffect(() => {
    if (!(fieldsTabActive && activeField.length > 0)) {
      return;
    }

    let cancelled = false;
    updateSectionLoading({ fieldThreats: true });

    void fetchPortfolioThreats(ownerId, {
      limit: pageSize,
      offset: fieldThreatOffset,
      wipoField: activeField,
    })
      .then((result) => {
        if (!cancelled) {
          setFieldThreats(result);
          setSectionErrors((current) => ({ ...current, fieldThreats: undefined }));
        }
      })
      .catch((ex) => {
        if (!cancelled) {
          setSectionErrors((current) => ({
            ...current,
            fieldThreats: ex instanceof Error ? ex.message : "Could not load field-scoped citing owners.",
          }));
        }
      })
      .finally(() => {
        if (!cancelled) {
          updateSectionLoading({ fieldThreats: false });
        }
      });

    return () => {
      cancelled = true;
      updateSectionLoading({ fieldThreats: false });
    };
  }, [activeField, fieldThreatOffset, fieldsTabActive, ownerId, pageSize, updateSectionLoading]);

  useEffect(() => {
    if (!fieldsTabActive) {
      return;
    }

    let cancelled = false;
    updateSectionLoading({ classification: true });

    void fetchPortfolioClassification(ownerId, {
      limit: pageSize,
      offset: classificationOffset,
      classificationType: "CPC_MAIN_GROUP",
      timeseriesFields: 0,
      wipoField: activeField.length > 0 ? activeField : undefined,
    })
      .then((result) => {
        if (!cancelled) {
          setClassification(result);
          setSectionErrors((current) => ({ ...current, classification: undefined }));
        }
      })
      .catch((ex) => {
        if (!cancelled) {
          setSectionErrors((current) => ({
            ...current,
            classification: ex instanceof Error ? ex.message : "Could not load classification.",
          }));
        }
      })
      .finally(() => {
        if (!cancelled) {
          updateSectionLoading({ classification: false });
        }
      });

    return () => {
      cancelled = true;
      updateSectionLoading({ classification: false });
    };
  }, [activeField, classificationOffset, fieldsTabActive, ownerId, pageSize, updateSectionLoading]);

  useEffect(() => {
    if (!(fieldsTabActive && activeField.length > 0)) {
      return;
    }

    let cancelled = false;
    updateSectionLoading({ fieldCitationFamilies: true });

    void fetchPortfolioCitationFamilies(ownerId, {
      limit: pageSize,
      offset: fieldCitationFamilyOffset,
      wipoField: activeField,
      sort: "forward_clean",
    })
      .then((result) => {
        if (!cancelled) {
          setFieldCitationFamilies(result);
          setSectionErrors((current) => ({ ...current, fieldCitationFamilies: undefined }));
        }
      })
      .catch((ex) => {
        if (!cancelled) {
          setSectionErrors((current) => ({
            ...current,
            fieldCitationFamilies: ex instanceof Error ? ex.message : "Could not load field-scoped cited families.",
          }));
        }
      })
      .finally(() => {
        if (!cancelled) {
          updateSectionLoading({ fieldCitationFamilies: false });
        }
      });

    return () => {
      cancelled = true;
      updateSectionLoading({ fieldCitationFamilies: false });
    };
  }, [activeField, fieldCitationFamilyOffset, fieldsTabActive, ownerId, pageSize, updateSectionLoading]);

  useEffect(() => {
    setClassificationOffset(0);
    setFieldCitationFamilyOffset(0);
    setFieldThreatOffset(0);
    setClassification(null);
    setFieldCitationFamilies(null);
    setFieldThreats(null);
    updateSectionLoading({
      classification: false,
      fieldCitationFamilies: false,
      fieldThreats: false,
    });
  }, [activeField, updateSectionLoading]);

  useEffect(() => {
    if (!fieldsTabActive) {
      return;
    }

    let cancelled = false;
    updateSectionLoading({ fieldTimeseries: true });

    void fetchPortfolioFieldTimeseries(ownerId, { limitFields: 64 })
      .then((result) => {
        if (!cancelled) {
          setFieldTimeseries(result);
          setSectionErrors((current) => ({ ...current, fieldTimeseries: undefined }));
        }
      })
      .catch((ex) => {
        if (!cancelled) {
          setSectionErrors((current) => ({
            ...current,
            fieldTimeseries: ex instanceof Error ? ex.message : "Could not load field chronology.",
          }));
        }
      })
      .finally(() => {
        if (!cancelled) {
          updateSectionLoading({ fieldTimeseries: false });
        }
      });

    return () => {
      cancelled = true;
      updateSectionLoading({ fieldTimeseries: false });
    };
  }, [fieldsTabActive, ownerId, updateSectionLoading]);

  useEffect(() => {
    if (!citationsTabActive) {
      return;
    }

    let cancelled = false;
    updateSectionLoading({ forecastContributors: true });

    void fetchPortfolioForecastContributors(ownerId, {
      horizon: forecastHorizon,
      contributorScope: "phase03_future_citations",
      limit: pageSize,
      offset: contributorOffset,
    })
      .then((result) => {
        if (!cancelled) {
          setForecastContributors(result);
          setSectionErrors((current) => ({ ...current, forecastContributors: undefined }));
        }
      })
      .catch((ex) => {
        if (!cancelled) {
          setSectionErrors((current) => ({
            ...current,
            forecastContributors: ex instanceof Error ? ex.message : "Could not load forecast contributors.",
          }));
        }
      })
      .finally(() => {
        if (!cancelled) {
          updateSectionLoading({ forecastContributors: false });
        }
      });

    return () => {
      cancelled = true;
      updateSectionLoading({ forecastContributors: false });
    };
  }, [citationsTabActive, contributorOffset, forecastHorizon, ownerId, pageSize, updateSectionLoading]);

  useEffect(() => {
    if (!forecastTabActive) {
      return;
    }

    let cancelled = false;
    updateSectionLoading({ pendingGrants: true });

    void fetchPortfolioPendingGrants(ownerId, {
      horizon: "24m",
      branchJurisdictionCode: pendingGrantJurisdiction || undefined,
      branchWipoField: pendingGrantField || undefined,
      branchLimit: 25,
    })
      .then((result) => {
        if (!cancelled) {
          setPendingGrants(result);
          setSectionErrors((current) => ({ ...current, pendingGrants: undefined }));
        }
      })
      .catch((ex) => {
        if (!cancelled) {
          setSectionErrors((current) => ({
            ...current,
            pendingGrants: ex instanceof Error ? ex.message : "Could not load pending-grant contract.",
          }));
        }
      })
      .finally(() => {
        if (!cancelled) {
          updateSectionLoading({ pendingGrants: false });
        }
      });

    return () => {
      cancelled = true;
      updateSectionLoading({ pendingGrants: false });
    };
  }, [forecastTabActive, ownerId, pendingGrantField, pendingGrantJurisdiction, updateSectionLoading]);

  useEffect(() => {
    const query = ownerInput.trim();
    if (query.length < 2 || query === ownerId) {
      setSuggestions([]);
      setSearching(false);
      return;
    }

    let cancelled = false;
    setSearching(true);

    const timeoutId = window.setTimeout(() => {
      void fetchPortfolioOwnerSuggestions(query, 8)
        .then((result) => {
          if (!cancelled) {
            setSuggestions(result.rows);
          }
        })
        .catch(() => {
          if (!cancelled) {
            setSuggestions([]);
          }
        })
        .finally(() => {
          if (!cancelled) {
            setSearching(false);
          }
        });
    }, 180);

    return () => {
      cancelled = true;
      window.clearTimeout(timeoutId);
    };
  }, [ownerId, ownerInput]);

  const availableCitationYears = Array.from(
    new Set((citationTimeseries?.rows ?? []).map((row) => row.year).filter((year) => year > 0 && year <= 2024)),
  ).sort((left, right) => right - left);

  useEffect(() => {
    if (!citationAttackerYear) {
      return;
    }
    const selectedYear = Number(citationAttackerYear);
    if (!Number.isFinite(selectedYear) || !availableCitationYears.includes(selectedYear)) {
      setCitationAttackerYear("");
      setCitationFieldOffset(0);
      setCitationJurisdictionOffset(0);
      setCitationAttackerOffset(0);
    }
  }, [availableCitationYears, citationAttackerYear]);

  const navigateToOwner = useCallback((nextOwnerId: string) => {
    const value = nextOwnerId || payload?.overview.identity.id || ownerId;
    if (!value) {
      return;
    }
    setSuggestions([]);
    router.push(`/portfolio/${encodeURIComponent(value)}`);
  }, [ownerId, payload, router]);

  const workspaceContextOverride = useMemo(
    () => {
      const identity = payload?.overview.identity;
      const ownerLabel = typeof identity?.label === "string" && identity.label.trim().length > 0 ? identity.label : ownerId;
      const ownerIdText =
        typeof identity?.id === "string" && identity.id.trim().length > 0 && identity.id !== ownerLabel
          ? identity.id
          : undefined;

      return {
        title: ownerLabel,
        description: ownerIdText,
        actions: (
          <PortfolioWorkspaceControls
            variant="banner"
            ownerInputValue={ownerInput}
            onOwnerInputChange={(value) => setOwnerInput(value)}
            onOwnerSubmit={navigateToOwner}
            onOwnerSelect={(owner) => {
              setOwnerInput(owner.label);
              navigateToOwner(owner.ownerId);
            }}
            suggestions={suggestions}
            searching={searching}
          />
        ),
      };
    },
    [navigateToOwner, ownerId, ownerInput, payload, searching, suggestions],
  );

  useWorkspaceContextOverride(workspaceContextOverride);

  if (loading && payload == null) {
    return <PortfolioWorkspaceSkeleton />;
  }

  if (error && payload == null) {
    return <div className="portfolio-shell">{error}</div>;
  }

  if (payload == null) {
    return <div className="portfolio-shell">No data available. Please choose another owner.</div>;
  }

  const overview = payload.overview;
  const currentCitationSummary = citationSummary ?? { ownerId, summary: null };
  const currentCitationTimeseries = citationTimeseries ?? { ownerId, rows: [] };
  const currentCitationFamilies = citationFamilies ?? { ownerId, rows: [] };
  const currentCitationAttackers = citationAttackers ?? { ownerId, rows: [] };
  const currentCitationFields = citationFields ?? { ownerId, rows: [] };
  const currentCitationJurisdictions = citationJurisdictions ?? { ownerId, rows: [] };
  const currentCitationCpcGroups = citationCpcGroups ?? { ownerId, rows: [] };
  const currentFieldCitationFamilies = fieldCitationFamilies ?? { ownerId, rows: [] };
  const currentFamilies =
    families && families.rows.length > 0
      ? families
      : payload.families.rows.length > 0
        ? payload.families
        : {
            ownerId,
            rows: overview.topFamilyPreview,
            pagination: payload.families.pagination,
          };
  const currentFields =
    fieldRows && fieldRows.rows.length > 0
      ? fieldRows
      : payload.fields.rows.length > 0
        ? payload.fields
        : {
            ownerId,
            rows: payload.forecast.topSegments,
          };
  const currentForecast = forecast ?? payload.forecast;
  const currentFieldThreats = fieldThreats ?? { ownerId, rows: [] };
  const currentClassification = classification ?? payload.classification;
  const currentFilingTimeseries = filingTimeseries ?? { ownerId, rows: [] };
  const currentStatusTimeseries =
    statusTimeseries ?? {
      ownerId,
      rows: [],
      audit: { coverageStatus: "low", coveragePct: 0, supportLevel: "limited" as const },
    };
  const currentJurisdictionUnlockHistory =
    jurisdictionUnlockHistory ?? {
      ownerId,
      summary: null,
      years: [],
      jurisdictions: [],
      audit: { coverageStatus: "low", coveragePct: 0, supportLevel: "limited" as const },
    };
  const currentFieldTimeseries = fieldTimeseries ?? { ownerId, rows: [] };
  const currentForecastContributors = forecastContributors ?? { ownerId, rows: [] };
  const currentPendingGrants = pendingGrants ?? { ownerId, rows: [] };
  const citationYearOptions = availableCitationYears;
  const pointCount = (rows: Array<{ points: Array<{ year: number }> }>) =>
    rows.reduce((total, row) => total + row.points.length, 0);
  const usingClassificationFieldFallback =
    pointCount(currentFieldTimeseries.rows) <= currentFieldTimeseries.rows.length &&
    pointCount(currentClassification.timeseries) > pointCount(currentFieldTimeseries.rows);
  const effectiveFieldTimeseries = usingClassificationFieldFallback
    ? currentClassification.timeseries
    : currentFieldTimeseries.rows;
  const fieldClusterOptions = Array.from(
    new Set(
      [...currentFields.rows.map((row) => row.field), ...effectiveFieldTimeseries.map((series) => series.field)].filter(
        (field) => field.length > 0,
      ),
    ),
  ).slice(0, 8);
  const familyFieldOptions = Array.from(new Set(currentFields.rows.map((row) => row.field).filter((field) => field.length > 0))).sort();
  const threatFields = [...fieldClusterOptions].sort();
  const filteredFieldRows =
    activeField.length > 0 ? currentFields.rows.filter((row) => row.field === activeField) : currentFields.rows;
  const filteredTimeseries =
    activeField.length > 0 && effectiveFieldTimeseries.some((series) => series.field === activeField)
      ? effectiveFieldTimeseries.filter((series) => series.field === activeField)
      : effectiveFieldTimeseries;
  const filingTimeseriesLoading =
    activeTab === "executive" &&
    (Boolean(sectionLoading.filingTimeseries) || (filingTimeseries == null && !sectionErrors.filingTimeseries));
  const statusTimeseriesLoading =
    activeTab === "executive" &&
    (Boolean(sectionLoading.statusTimeseries) || (statusTimeseries == null && !sectionErrors.statusTimeseries));
  const jurisdictionUnlockHistoryLoading =
    activeTab === "executive" &&
    (Boolean(sectionLoading.jurisdictionUnlocks) || (jurisdictionUnlockHistory == null && !sectionErrors.jurisdictionUnlocks));
  const citationSummaryLoading =
    citationsTabActive &&
    (Boolean(sectionLoading.citationSummary) || (citationSummary == null && !sectionErrors.citationSummary));
  const citationTimeseriesLoading =
    citationsTabActive &&
    (Boolean(sectionLoading.citationTimeseries) || (citationTimeseries == null && !sectionErrors.citationTimeseries));
  const forecastContributorsLoading =
    citationsTabActive &&
    (Boolean(sectionLoading.forecastContributors) ||
      (forecastContributors == null && !sectionErrors.forecastContributors));
  const citationFamiliesLoading =
    citationsTabActive &&
    (Boolean(sectionLoading.citationFamilies) || (citationFamilies == null && !sectionErrors.citationFamilies));
  const citationAttackersLoading =
    citationsTabActive &&
    (Boolean(sectionLoading.citationAttackers) || (citationAttackers == null && !sectionErrors.citationAttackers));
  const citationFieldsLoading =
    citationsTabActive &&
    (Boolean(sectionLoading.citationFields) || (citationFields == null && !sectionErrors.citationFields));
  const citationJurisdictionsLoading =
    citationsTabActive &&
    (Boolean(sectionLoading.citationJurisdictions) ||
      (citationJurisdictions == null && !sectionErrors.citationJurisdictions));
  const citationCpcGroupsLoading =
    citationsTabActive &&
    (Boolean(sectionLoading.citationCpcGroups) || (citationCpcGroups == null && !sectionErrors.citationCpcGroups));
  const familiesLoading =
    familiesTabActive && (Boolean(sectionLoading.families) || (families == null && !sectionErrors.families));
  const fieldsLoading =
    fieldsTabActive && (Boolean(sectionLoading.fields) || (fieldRows == null && !sectionErrors.fields));
  const classificationLoading =
    fieldsTabActive && (Boolean(sectionLoading.classification) || (classification == null && !sectionErrors.classification));
  const fieldTimeseriesLoading =
    fieldsTabActive && (Boolean(sectionLoading.fieldTimeseries) || (fieldTimeseries == null && !sectionErrors.fieldTimeseries));
  const fieldCitationFamiliesLoading =
    fieldsTabActive &&
    activeField.length > 0 &&
    (Boolean(sectionLoading.fieldCitationFamilies) ||
      (fieldCitationFamilies == null && !sectionErrors.fieldCitationFamilies));
  const fieldThreatsLoading =
    fieldsTabActive &&
    activeField.length > 0 &&
    (Boolean(sectionLoading.fieldThreats) || (fieldThreats == null && !sectionErrors.fieldThreats));
  const pendingGrantsLoading =
    forecastTabActive && (Boolean(sectionLoading.pendingGrants) || (pendingGrants == null && !sectionErrors.pendingGrants));

  return (
    <div className="portfolio-shell">
      <div className="portfolio-shell__canvas">
        <PortfolioSummaryCards cards={overview.summaryCards} />
        <PortfolioPrimaryTabs
          activeTab={activeTab}
          onTabChange={(tab) => {
            updateWorkspaceQuery({ tab, field: tab === "fields" ? activeField || null : null });
          }}
        />
        {error ? <p className="portfolio-error">{error}</p> : null}

        {activeTab === "executive" ? (
          <PortfolioExecutiveTab
            overview={overview}
            families={currentFamilies}
            fields={currentFields}
            filingTimeseries={currentFilingTimeseries}
            filingTimeseriesLoading={filingTimeseriesLoading}
            statusTimeseries={currentStatusTimeseries}
            statusTimeseriesLoading={statusTimeseriesLoading}
            jurisdictionUnlockHistory={currentJurisdictionUnlockHistory}
            jurisdictionUnlockHistoryLoading={jurisdictionUnlockHistoryLoading}
            threats={payload.threats}
            errorMessages={{
              executive: sectionErrors.families ?? sectionErrors.fields,
              filingTimeseries: sectionErrors.filingTimeseries,
              statusTimeseries: sectionErrors.statusTimeseries,
              jurisdictionUnlocks: sectionErrors.jurisdictionUnlocks,
            }}
          />
        ) : null}

        {activeTab === "citations" ? (
          <PortfolioCitationsTab
            citationSummary={currentCitationSummary}
            citationTimeseries={currentCitationTimeseries}
            citationTimeseriesLoading={citationTimeseriesLoading}
            forecast={currentForecast}
            forecastContributors={currentForecastContributors}
            forecastContributorsLoading={forecastContributorsLoading}
            forecastHorizon={forecastHorizon}
            citationFamilies={currentCitationFamilies}
            citationSummaryLoading={citationSummaryLoading}
            citationFamiliesLoading={citationFamiliesLoading}
            citationCpcGroups={currentCitationCpcGroups}
            citationCpcGroupsLoading={citationCpcGroupsLoading}
            citationAttackers={currentCitationAttackers}
            citationAttackersLoading={citationAttackersLoading}
            citationFields={currentCitationFields}
            citationFieldsLoading={citationFieldsLoading}
            citationJurisdictions={currentCitationJurisdictions}
            citationJurisdictionsLoading={citationJurisdictionsLoading}
            threatFields={threatFields}
            citationYearOptions={citationYearOptions}
            citationFamilyField={citationFamilyField}
            citationFamilyStatus={citationFamilyStatus}
            citationFamilySort={citationFamilySort}
            citationAttackerField={citationAttackerField}
            citationAttackerJurisdiction={citationAttackerJurisdiction}
            citationAttackerYear={citationAttackerYear}
            errorMessages={{
              citationSummary: sectionErrors.citationSummary,
              citationTimeseries: sectionErrors.citationTimeseries,
              forecastContributors: sectionErrors.forecastContributors,
              citationFamilies: sectionErrors.citationFamilies,
              citationCpcGroups: sectionErrors.citationCpcGroups,
              citationAttackers: sectionErrors.citationAttackers,
              citationFields: sectionErrors.citationFields,
              citationJurisdictions: sectionErrors.citationJurisdictions,
            }}
            onForecastHorizonChange={(horizon) => {
              setForecastHorizon(horizon);
              setContributorOffset(0);
            }}
            onForecastContributorPageChange={setContributorOffset}
            onCitationFamilyFieldChange={(value) => {
              setCitationFamilyField(value);
              setCitationFamilyOffset(0);
            }}
            onCitationFamilyStatusChange={(value) => {
              setCitationFamilyStatus(value);
              setCitationFamilyOffset(0);
            }}
            onCitationFamilySortChange={(value) => {
              setCitationFamilySort(value);
              setCitationFamilyOffset(0);
            }}
            onCitationFamilyPageChange={setCitationFamilyOffset}
            onCitationFieldChange={(value) => {
              setCitationAttackerField(value);
              setCitationJurisdictionOffset(0);
              setCitationCpcOffset(0);
              setCitationAttackerOffset(0);
            }}
            onCitationJurisdictionChange={(value) => {
              setCitationAttackerJurisdiction(value);
              setCitationFieldOffset(0);
              setCitationCpcOffset(0);
              setCitationAttackerOffset(0);
            }}
            onCitationYearChange={(value) => {
              setCitationAttackerYear(value);
              setCitationFieldOffset(0);
              setCitationJurisdictionOffset(0);
              setCitationCpcOffset(0);
              setCitationAttackerOffset(0);
            }}
            onCitationFieldPageChange={setCitationFieldOffset}
            onCitationJurisdictionPageChange={setCitationJurisdictionOffset}
            onCitationCpcPageChange={setCitationCpcOffset}
            onCitationAttackerPageChange={setCitationAttackerOffset}
            onClearCitationFilters={() => {
              setCitationAttackerField("");
              setCitationAttackerJurisdiction("");
              setCitationAttackerYear("");
              setCitationFieldOffset(0);
              setCitationJurisdictionOffset(0);
              setCitationCpcOffset(0);
              setCitationAttackerOffset(0);
            }}
          />
        ) : null}

        {activeTab === "families" ? (
          <PortfolioFamiliesTab
            families={currentFamilies}
            familiesLoading={familiesLoading}
            searchValue={familyQuery}
            statusValue={familyStatus}
            primaryFieldValue={familyPrimaryField}
            sortValue={familySort}
            fieldOptions={familyFieldOptions}
            errorMessage={sectionErrors.families}
            onSearchChange={(value) => {
              setFamilyQuery(value);
              setFamilyOffset(0);
            }}
            onStatusChange={(value) => {
              setFamilyStatus(value);
              setFamilyOffset(0);
            }}
            onPrimaryFieldChange={(value) => {
              setFamilyPrimaryField(value);
              setFamilyOffset(0);
            }}
            onSortChange={(value) => {
              setFamilySort(value);
              setFamilyOffset(0);
            }}
            onPageChange={setFamilyOffset}
          />
        ) : null}

        {activeTab === "fields" ? (
          <PortfolioFieldsTab
            fieldClusterOptions={fieldClusterOptions}
            activeField={activeField}
            filteredFieldRows={filteredFieldRows}
            fieldsLoading={fieldsLoading}
            filteredTimeseries={filteredTimeseries}
            fieldTimeseriesLoading={fieldTimeseriesLoading}
            classification={currentClassification}
            classificationLoading={classificationLoading}
            fieldCitationFamilies={currentFieldCitationFamilies}
            fieldThreats={currentFieldThreats}
            fieldCitationFamiliesLoading={fieldCitationFamiliesLoading}
            fieldThreatsLoading={fieldThreatsLoading}
            usingClassificationFieldFallback={usingClassificationFieldFallback}
            errorMessages={{
              classification: sectionErrors.classification,
              fields: sectionErrors.fields,
              fieldTimeseries: sectionErrors.fieldTimeseries,
              fieldCitationFamilies: sectionErrors.fieldCitationFamilies,
              fieldThreats: sectionErrors.fieldThreats,
            }}
            onSelectField={(field) => updateWorkspaceQuery({ tab: "fields", field: field || null })}
            onClassificationPageChange={setClassificationOffset}
            onFieldCitationFamiliesPageChange={setFieldCitationFamilyOffset}
            onFieldThreatsPageChange={setFieldThreatOffset}
          />
        ) : null}

        {activeTab === "forecast" ? (
          <PortfolioForecastTab
            pendingGrants={currentPendingGrants}
            pendingGrantsLoading={pendingGrantsLoading}
            selectedJurisdiction={pendingGrantJurisdiction}
            selectedField={pendingGrantField}
            errorMessages={{
              pendingGrants: sectionErrors.pendingGrants,
            }}
            onJurisdictionChange={setPendingGrantJurisdiction}
            onFieldChange={setPendingGrantField}
          />
        ) : null}
      </div>
    </div>
  );
}
