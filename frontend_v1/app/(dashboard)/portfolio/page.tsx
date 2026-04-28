"use client"

import { useState, useEffect, Suspense } from "react"
import { useSearchParams } from "next/navigation"
import Link from "next/link"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Checkbox } from "@/components/ui/checkbox"
import { Label } from "@/components/ui/label"
import { Slider } from "@/components/ui/slider"
import { Separator } from "@/components/ui/separator"
import { fetchJson, getPortfolioOverviewUrl, getPortfolioAnalyticsUrl, getPortfolioPatentsUrl, fetchPortfolioCategoryCounts, getPortfolioLicensingCandidatesUrl, getPortfolioCitationMetricsUrl, getPortfolioCitationTimeSeriesUrl } from "@/lib/api"
import type { PortfolioOverviewResponse, PortfolioAnalyticsResponse, PortfolioPatentsResponse, PortfolioCategoryCounts, PortfolioPatent, PortfolioLicensingCandidatesResponse, LicensingCandidateResult } from "@/lib/types/patent"
import type { PortfolioCitationMetricsResponse, PortfolioCitationTimeSeriesResponse, PortfolioTimeSeriesPoint } from "@/lib/types/portfolio"

import { cn, formatLabel } from "@/lib/utils"
import { getTechnologyInsights, getMarketInsights, getPeerPositioningInsights } from "@/lib/insight-rules"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip"
import { Drawer, DrawerContent, DrawerHeader, DrawerTitle, DrawerDescription, DrawerTrigger, DrawerClose } from "@/components/ui/drawer"
import {
  Shield,
  Building2,
  Users,
  MapPinned,
  FileText,
  TrendingUp,
  Target,
  BarChart3,
  Gauge,
  Info,
  Zap,
  Layers,
  Sparkles,
  ExternalLink,
  Filter,
  ChevronLeft,
  ChevronRight,
  ChevronUp,
  ChevronDown,
  X,
  AlertTriangle,
  Eye,
} from "lucide-react"
import { RadarChart } from "@/components/radar-chart"
import { ResponsivePie } from "@nivo/pie"
import { ResponsiveBar } from "@nivo/bar"
import { motion, AnimatePresence } from "motion/react"
import { getNivoTheme } from "@/lib/nivo-theme"
import { tabVariants, tabTransition } from "@/lib/motion-variants"
import { PortfolioCitationEvolutionChart, type PortfolioCitationYearData } from "@/components/portfolio-citation-evolution-chart"
import { PortfolioHealthCards, type PortfolioLifecycleMetrics } from "@/components/portfolio-health-cards"
import { GaugeChart } from "@/components/gauge-chart"
import { PortfolioOverviewCard } from "@/components/portfolio-overview-card"
import { PortfolioForecastCard } from "@/components/portfolio-forecast-card"
import { GrantCoverageCard } from "@/components/grant-coverage-card"

import { TierBadge } from "@/components/tier-badge"
import { RED_PALETTE } from "@/lib/chart-config"

import { PortfolioSearch } from "@/components/portfolio-search"
import { DistributionChart } from "@/components/distribution-chart"
import { Skeleton } from "@/components/ui/skeleton"

function PortfolioAnalysisContent() {
  const searchParams = useSearchParams()
  const [activeTab, setActiveTab] = useState("overview")
  const [ownerId, setOwnerId] = useState(() => {
    // Get ownerId from URL params if available
    return searchParams?.get("ownerId") || ""
  })
  const [overviewData, setOverviewData] = useState<PortfolioOverviewResponse | null>(null)
  const [analyticsData, setAnalyticsData] = useState<PortfolioAnalyticsResponse | null>(null)
  const [patentsData, setPatentsData] = useState<PortfolioPatentsResponse | null>(null)
  const [licensingData, setLicensingData] = useState<PortfolioLicensingCandidatesResponse | null>(null)




  const [categoryCounts, setCategoryCounts] = useState<PortfolioCategoryCounts | null>(null)
  const [citationMetrics, setCitationMetrics] = useState<PortfolioCitationMetricsResponse | null>(null)
  const [citationTimeSeries, setCitationTimeSeries] = useState<PortfolioCitationTimeSeriesResponse | null>(null)
  const [selectedCandidate, setSelectedCandidate] = useState<LicensingCandidateResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [analyticsLoading, setAnalyticsLoading] = useState(false)
  const [patentsLoading, setPatentsLoading] = useState(false)
  const [licensingLoading, setLicensingLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Patents tab filters and pagination
  const [selectedCategories, setSelectedCategories] = useState<string[]>([])
  const [selectedStatus, setSelectedStatus] = useState<string[]>([])
  const [selectedJurisdictions, setSelectedJurisdictions] = useState<string[]>([])
  const [blockingPowerRange, setBlockingPowerRange] = useState<[number, number]>([0, 100])
  const [innovationScoreRange, setInnovationScoreRange] = useState<[number, number]>([0, 100])
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(25)
  const [sortCol, setSortCol] = useState<"blocking_power_pct" | "innovation_score" | "legal_strength" | "forward_patent_citation_count">("blocking_power_pct")
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc")

  // State for raw patents (fetched from API, unfiltered by client criteria)
  const [rawPatents, setRawPatents] = useState<PortfolioPatent[] | null>(null)

  const fetchPortfolioOverview = async (id: string) => {
    if (!id.trim()) return

    setLoading(true)
    setError(null)
    try {
      const data = await fetchJson<PortfolioOverviewResponse>(getPortfolioOverviewUrl(id))
      setOverviewData(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch portfolio overview")
      setOverviewData(null)
    } finally {
      setLoading(false)
    }
  }

  const fetchPortfolioAnalytics = async (id: string) => {
    if (!id.trim()) return

    setAnalyticsLoading(true)
    try {
      const data = await fetchJson<PortfolioAnalyticsResponse>(getPortfolioAnalyticsUrl(id))
      setAnalyticsData(data)
    } catch (err) {
      console.error("Failed to fetch portfolio analytics:", err)
      setAnalyticsData(null)
    } finally {
      setAnalyticsLoading(false)
    }
  }

  // 1. Fetch ALL patents when owner or category changes
  const fetchRawPatents = async (id: string) => {
    if (!id.trim()) return

    setPatentsLoading(true)
    try {
      const categoriesToFetch = selectedCategories.length > 0 ? selectedCategories : [undefined]

      const promises = categoriesToFetch.map(async (category) => {
        try {
          // Fetch ALL (large limit) to enable client-side pagination/filtering
          const fetchLimit = 10000
          const data = await fetchJson<PortfolioPatentsResponse>(
            getPortfolioPatentsUrl(id, {
              category,
              sort: "blocking_power_pct",
              order: "desc",
              limit: fetchLimit,
              offset: 0,
            })
          )
          return data.patents
        } catch (err) {
          console.error(`Failed to fetch patents for category ${category}:`, err)
          return []
        }
      })

      const allPatentsArrays = await Promise.all(promises)

      // Deduplicate
      const allPatentsMap = new Map<number, PortfolioPatent>()
      allPatentsArrays.flat().forEach((patent) => {
        if (!allPatentsMap.has(patent.appln_id)) {
          allPatentsMap.set(patent.appln_id, patent)
        }
      })

      setRawPatents(Array.from(allPatentsMap.values()))
    } catch (err) {
      console.error("Failed to fetch raw patents:", err)
      setRawPatents(null)
      setPatentsData(null)
    } finally {
      setPatentsLoading(false)
    }
  }

  // 2. Filter and Paginate locally whenever raw data or filters change
  useEffect(() => {
    if (!rawPatents || !ownerId) return

    let filteredPatents = [...rawPatents]

    // Apply client-side filters
    if (selectedStatus.length > 0) {
      filteredPatents = filteredPatents.filter((patent) => {
        const status = patent.is_abandoned ? "ABANDONED" : "ACTIVE"
        return selectedStatus.includes(status)
      })
    }

    if (selectedJurisdictions.length > 0) {
      filteredPatents = filteredPatents.filter((patent) =>
        selectedJurisdictions.includes(patent.publn_auth)
      )
    }

    filteredPatents = filteredPatents.filter((patent) => {
      if (patent.blocking_power_pct === null) return false
      return (
        patent.blocking_power_pct >= blockingPowerRange[0] &&
        patent.blocking_power_pct <= blockingPowerRange[1]
      )
    })

    filteredPatents = filteredPatents.filter((patent) => {
      if (patent.innovation_score === null) return false
      return (
        patent.innovation_score >= innovationScoreRange[0] &&
        patent.innovation_score <= innovationScoreRange[1]
      )
    })

    // Sort by active column
    filteredPatents.sort((a, b) => {
      const aVal = (a[sortCol] ?? 0) as number
      const bVal = (b[sortCol] ?? 0) as number
      return sortDir === "desc" ? bVal - aVal : aVal - bVal
    })

    const total = filteredPatents.length
    const offset = (currentPage - 1) * pageSize
    const paginatedPatents = filteredPatents.slice(offset, offset + pageSize)

    setPatentsData({
      portfolio: { owner_id: Number(ownerId) },
      pagination: {
        total,
        limit: pageSize,
        offset,
      },
      patents: paginatedPatents,
      metadata: {
        contract_version: "v1",
        data_snapshot: new Date().toISOString().split("T")[0],
      },
    })

  }, [
    rawPatents,
    selectedStatus,
    selectedJurisdictions,
    blockingPowerRange,
    innovationScoreRange,
    currentPage,
    pageSize,
    ownerId,
    sortCol,
    sortDir,
  ])

  const fetchCategoryCounts = async (id: string) => {
    if (!id.trim()) return

    try {
      console.log("[Category Counts] Fetching counts for owner:", id)
      const counts = await fetchPortfolioCategoryCounts(id)
      console.log("[Category Counts] Received counts:", counts)
      setCategoryCounts(counts as PortfolioCategoryCounts)
    } catch (err) {
      console.error("Failed to fetch category counts:", err)
      setCategoryCounts(null)
    }
  }

  const fetchCitationData = async (id: string) => {
    if (!id.trim()) return

    try {
      // Fetch metrics
      const metricsData = await fetchJson<PortfolioCitationMetricsResponse>(getPortfolioCitationMetricsUrl(id))
      setCitationMetrics(metricsData)

      // Fetch time series
      const tsData = await fetchJson<PortfolioCitationTimeSeriesResponse>(getPortfolioCitationTimeSeriesUrl(id))
      setCitationTimeSeries(tsData)
    } catch (err) {
      console.error("Failed to fetch citation data:", err)
    }
  }

  const fetchPortfolioLicensing = async (id: string) => {
    if (!id.trim()) return

    setLicensingLoading(true)
    try {
      console.log("[Portfolio Licensing] Fetching licensing data for owner:", id)
      const data = await fetchJson<PortfolioLicensingCandidatesResponse>(getPortfolioLicensingCandidatesUrl(id, 10, 0))

      console.log("[Portfolio Licensing] Received data:", data)
      setLicensingData(data)
    } catch (err) {
      console.error("Failed to fetch portfolio licensing:", err)
      setLicensingData(null)
    } finally {
      setLicensingLoading(false)
    }
  }

  // Sync ownerId with URL params
  useEffect(() => {
    const urlOwnerId = searchParams?.get("ownerId")
    if (urlOwnerId && urlOwnerId !== ownerId) {
      setOwnerId(urlOwnerId)
    }
  }, [searchParams])

  // Master effect: Fetch data when ownerId turns valid or changes
  useEffect(() => {
    if (!ownerId?.trim()) return

    // Reset component states on new owner
    setOverviewData(null)
    setAnalyticsData(null)
    setPatentsData(null)
    setCitationMetrics(null)
    setCitationTimeSeries(null)
    setRawPatents(null)

    // Trigger fetches
    const id = ownerId.trim()
    console.log("[Portfolio Page] Fetching data for owner:", id)

    // Parallel fetch for core data
    fetchPortfolioOverview(id)
    fetchPortfolioAnalytics(id)
    fetchCitationData(id)

  }, [ownerId])

  const handleSearch = (id?: string) => {
    // If triggered by selection, just update state.
    // The master useEffect will handle the fetching.
    if (id && id.trim()) {
      setOwnerId(id)
    }
  }

  // Fetch analytics when switching to analysis tab
  useEffect(() => {
    if (activeTab === "analysis" && ownerId.trim() && !analyticsData && !analyticsLoading) {
      fetchPortfolioAnalytics(ownerId.trim())
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab])

  // Fetch licensing when switching to licensing tab or ownerId changes
  useEffect(() => {
    if (activeTab === "licensing" && ownerId.trim()) {
      // Fetch if no data or if data is for a different owner
      const isDataMismatch = licensingData && licensingData.portfolio.owner_id !== Number(ownerId)

      if ((!licensingData || isDataMismatch) && !licensingLoading) {
        // Clear old data if mismatch to avoid showing wrong data while loading
        if (isDataMismatch) {
          setLicensingData(null)
        }
        fetchPortfolioLicensing(ownerId.trim())
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab, ownerId])

  // Fetch category counts when switching to patents tab
  useEffect(() => {
    if (activeTab === "patents" && ownerId.trim()) {
      fetchCategoryCounts(ownerId.trim())
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab, ownerId])

  // Trigger Fetching
  useEffect(() => {
    if (activeTab === "patents" && ownerId.trim()) {
      fetchRawPatents(ownerId.trim())
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab, ownerId, selectedCategories])

  // Reset page when filters change
  useEffect(() => {
    if (activeTab === "patents") {
      setCurrentPage(1)
    }
  }, [selectedCategories, selectedStatus, selectedJurisdictions, blockingPowerRange, innovationScoreRange, activeTab])

  // Prepare radar chart data
  const radarData = overviewData
    ? [
      { category: "Technology", value: overviewData.radar.technology * 100, max: 100 },
      { category: "Market", value: overviewData.radar.market * 100, max: 100 },
      { category: "Blocking", value: overviewData.radar.blocking, max: 100 },
      { category: "Legal", value: overviewData.radar.legal, max: 100 },
      { category: "Licensing", value: overviewData.radar.licensing, max: 100 },
    ]
    : []

  // Transform API data for Citation Evolution Chart
  const portfolioCitationEvolutionData: PortfolioCitationYearData[] = citationTimeSeries?.series.map(point => ({
    year: point.year.toString(),
    total_cites: point.citations_total,
    avg_cites_per_patent: point.citations_per_patent,
    early_cites: point.early_cites,
    mid_cites: point.mid_cites,
    late_cites: point.late_cites,
    yoy_growth: point.citations_yoy_pct ?? null,
    phase: point.citation_phase
  })) || []

  // Helper to infer trajectory label
  const getTrajectoryLabel = (pct: number): "Rising" | "Flat" | "Falling" => {
    if (pct > 0.66) return "Rising"
    if (pct < 0.33) return "Falling"
    return "Flat"
  }

  // Transform API data for Portfolio Health Cards
  const portfolioLifecycleMetrics: PortfolioLifecycleMetrics | null = citationMetrics ? {
    trajectory: {
      score_avg: Number(citationMetrics.citation_quality_raw.trajectory_score_avg.toFixed(1)),
      score_pct: Number((citationMetrics.citation_quality_percentile.trajectory_score_pct * 100).toFixed(0)),
      label: getTrajectoryLabel(citationMetrics.citation_quality_percentile.trajectory_score_pct)
    },
    durability: {
      score_avg: Number(citationMetrics.citation_quality_raw.durability_score_avg.toFixed(1)),
      score_pct: Number((citationMetrics.citation_quality_percentile.durability_score_pct * 100).toFixed(0))
    },
    sustainability: {
      score_avg: Number((citationMetrics.citation_quality_raw.sustainability_score_avg * 100).toFixed(0)),
      score_pct: Number((citationMetrics.citation_quality_percentile.sustainability_score_pct * 100).toFixed(0)),
      sustaining_share: citationMetrics.portfolio_behavior.sustaining_share
    },
    timing: {
      mode: citationMetrics.portfolio_behavior.timing_class_mode as "EARLY" | "MID" | "LATE",
      score_avg: Number(citationMetrics.citation_quality_raw.timing_score_avg.toFixed(1)),
      score_pct: Number((citationMetrics.citation_quality_percentile.timing_score_pct * 100).toFixed(0))
    },
    early_signal: {
      share: citationMetrics.portfolio_behavior.early_signal_share
    },
    cites_per_patent: {
      overall_avg: citationMetrics.citation_volume.cites_per_patent
    }
  } : null

  const portfolioTypeBreakdown = analyticsData
    ? Object.entries(analyticsData.categories.counts)
        .map(([key, value]) => ({
          id: formatLabel(key),
          value: Number(value),
        }))
        .filter((item) => item.value > 0)
    : []

  return (
    <>
      {/* Search Section */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Search Portfolio</CardTitle>
          <CardDescription>Search by portfolio owner name</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2">
            <PortfolioSearch
              className="flex-1"
              placeholder="Type owner name (e.g. Google)..."
              onSelect={(id) => handleSearch(id)}
            />
            {/* Optional: we can remove the button or keep it for manual ID entry if we kept Input */}
          </div>
          {/* Show current ID if selected? */}
          {ownerId && (
            <div className="mt-2 text-xs text-muted-foreground">
              Selected Owner ID: {ownerId}
            </div>
          )}
        </CardContent>
      </Card>

      {error && (
        <Alert variant="destructive" className="mb-6">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {loading && (
        <div className="space-y-6">
          {/* Overview card skeleton */}
          <Card>
            <CardHeader>
              <Skeleton className="h-7 w-64 mb-2" />
              <Skeleton className="h-4 w-48" />
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-6">
                {Array.from({ length: 6 }).map((_, i) => (
                  <div key={i} className="space-y-2">
                    <Skeleton className="h-3 w-24" />
                    <Skeleton className="h-8 w-20" />
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
          {/* KPI row skeleton */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <Card key={i} className="p-6">
                <Skeleton className="h-3 w-20 mb-3" />
                <Skeleton className="h-8 w-16 mb-2" />
                <Skeleton className="h-2 w-full" />
              </Card>
            ))}
          </div>
          {/* Chart skeleton */}
          <Card>
            <CardHeader>
              <Skeleton className="h-5 w-48" />
              <Skeleton className="h-3 w-64 mt-1" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-[350px] w-full rounded-md" />
            </CardContent>
          </Card>
        </div>
      )}

      {!loading && !error && overviewData && (
        <Card>
          <CardContent className="pt-6">
            <Tabs value={activeTab} onValueChange={setActiveTab} defaultValue="overview">
              <TabsList className="grid w-full grid-cols-6 mb-6">
                <TabsTrigger value="overview">Overview</TabsTrigger>
                <TabsTrigger value="patents">Patents</TabsTrigger>
                <TabsTrigger value="licensing">Licensing</TabsTrigger>
                <TabsTrigger value="analysis">Analysis</TabsTrigger>
                <TabsTrigger value="forecast">Forecast</TabsTrigger>
              </TabsList>

              {/* OVERVIEW TAB */}
              <TabsContent value="overview" className="space-y-6">
                <AnimatePresence mode="wait">
                <motion.div
                  key={activeTab + "-overview"}
                  variants={tabVariants}
                  initial="initial" animate="animate" exit="exit"
                  transition={tabTransition}
                  className="space-y-6"
                >
                {/* Portfolio Overview Card */}
                <PortfolioOverviewCard data={overviewData} />

                {/* Grant Coverage */}
                <div className="h-full">
                  <GrantCoverageCard
                    grantCoverage={overviewData.grant_coverage}
                    grantMix={overviewData.grant_mix}
                  />
                </div>

                {/* Radar Chart */}
                <Card className="h-full">
                  <CardHeader>
                    <CardTitle>Portfolio Strength Radar</CardTitle>
                    <CardDescription>Multi-dimensional percentile visualization (5 key dimensions)</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="grid md:grid-cols-2 gap-6">
                      {/* Radar Chart */}
                      <div className="flex justify-center items-center">
                        <RadarChart data={radarData} />
                      </div>

                      {/* Values Card */}
                      <div className="space-y-4">
                        <h4 className="text-sm font-semibold text-foreground mb-4">Percentile Scores</h4>
                        {radarData.map((item, index) => (
                          <div key={index} className="space-y-2">
                            <div className="flex items-center justify-between">
                              <span className="text-sm font-medium text-foreground">{item.category}</span>
                              <span className="text-lg font-bold text-primary">{item.value.toFixed(1)}/100</span>
                            </div>
                            <Progress value={item.value} className="h-2" />
                          </div>
                        ))}
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Technology & Market Profile */}
                <div className="grid md:grid-cols-2 gap-6">
                  {/* Technology Profile */}
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <Zap className="h-5 w-5 text-primary" />
                        Technology Profile
                      </CardTitle>
                      <CardDescription>CPC class distribution and diversification</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="grid md:grid-cols-2 gap-6">
                        {/* Pie Chart */}
                        <div className="flex items-center justify-center">
                          {/* Donut Chart with Custom Legend */}
                          <div className="flex flex-col items-center justify-center w-full">
                            <div className="h-[200px] w-full">
                              <ResponsivePie
                                data={overviewData.technology_profile.top_cpc_classes.map((cpc, i) => ({
                                  id: cpc.code,
                                  value: cpc.weight * 100,
                                }))}
                                innerRadius={0.6}
                                padAngle={2}
                                colors={RED_PALETTE}
                                enableArcLabels={false}
                                enableArcLinkLabels={false}
                                legends={[]}
                                tooltip={({ datum }) => (
                                  <div className="bg-background border border-border p-2 rounded-lg text-xs">
                                    CPC: {datum.id}: {datum.value.toFixed(1)}%
                                  </div>
                                )}
                              />
                            </div>
                            {/* Custom Legend */}
                            <div className="mt-4 flex flex-wrap justify-center gap-3">
                              {overviewData.technology_profile.top_cpc_classes.map((cpc, index) => (
                                <div key={cpc.code} className="flex items-center gap-1.5 text-xs">
                                  <span
                                    className="h-2.5 w-2.5 rounded-full"
                                    style={{ backgroundColor: RED_PALETTE[index % RED_PALETTE.length] }}
                                  />
                                  <span className="text-muted-foreground">{cpc.code}</span>
                                </div>
                              ))}
                            </div>
                          </div>
                        </div>

                        {/* Diversification Insights - Replaced Raw Metrics */}
                        <div className="space-y-4">
                          <h4 className="text-sm font-semibold flex items-center gap-2">
                            <Sparkles className="h-4 w-4 text-yellow-500" />
                            Key Insights
                          </h4>
                          <ul className="space-y-3">
                            {getTechnologyInsights(overviewData.technology_profile).map((insight, i) => (
                              <li key={i} className="text-sm text-muted-foreground flex gap-2">
                                <span className="text-primary mt-1">•</span>
                                <span>{insight}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  {/* Market Profile */}
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <Layers className="h-5 w-5 text-primary" />
                        Market Profile
                      </CardTitle>
                      <CardDescription>Industry distribution and diversification</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="grid md:grid-cols-2 gap-6">
                        {/* Pie Chart */}
                        <div className="flex items-center justify-center">
                          {/* Donut Chart with Custom Legend */}
                          <div className="flex flex-col items-center justify-center w-full">
                            <div className="h-[200px] w-full">
                              <ResponsivePie
                                data={overviewData.market_profile.top_industries.map((ind) => ({
                                  id: ind.code.replace(/_/g, " "),
                                  value: ind.weight * 100,
                                }))}
                                innerRadius={0.6}
                                padAngle={2}
                                colors={RED_PALETTE}
                                enableArcLabels={false}
                                enableArcLinkLabels={false}
                                legends={[]}
                                tooltip={({ datum }) => (
                                  <div className="bg-background border border-border p-2 rounded-lg text-xs">
                                    {datum.id}: {datum.value.toFixed(1)}%
                                  </div>
                                )}
                              />
                            </div>
                            {/* Custom Legend */}
                            <div className="mt-4 flex flex-wrap justify-center gap-3">
                              {overviewData.market_profile.top_industries.map((ind, index) => (
                                <div key={ind.code} className="flex items-center gap-1.5 text-xs">
                                  <span
                                    className="h-2.5 w-2.5 rounded-full"
                                    style={{ backgroundColor: RED_PALETTE[index % RED_PALETTE.length] }}
                                  />
                                  <span className="text-muted-foreground">{ind.code.replace(/_/g, " ")}</span>
                                </div>
                              ))}
                            </div>
                          </div>
                        </div>

                        {/* Diversification Insights - Replaced Raw Metrics */}
                        <div className="space-y-4">
                          <h4 className="text-sm font-semibold flex items-center gap-2">
                            <Sparkles className="h-4 w-4 text-yellow-500" />
                            Key Insights
                          </h4>
                          <ul className="space-y-3">
                            {getMarketInsights(overviewData.market_profile).map((insight, i) => (
                              <li key={i} className="text-sm text-muted-foreground flex gap-2">
                                <span className="text-primary mt-1">•</span>
                                <span>{insight}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>

                {/* Portfolio Health & Peer Positioning */}
                <div className="grid md:grid-cols-2 gap-6">
                  {/* Portfolio Health */}
                  <Card className="h-full">
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <FileText className="h-5 w-5 text-primary" />
                        Portfolio Health
                      </CardTitle>
                      <CardDescription className="flex items-center gap-2">
                        Status indicators
                        {analyticsData && (
                          <Badge
                            variant="outline"
                            className={cn(
                              "text-xs px-2 py-0.5 ml-auto",
                              analyticsData.legal.maintenance_profile === "STRONGLY_MAINTAINED"
                                ? "bg-green-100 text-green-800 border-green-300"
                                : analyticsData.legal.maintenance_profile === "MODERATELY_MAINTAINED"
                                  ? "bg-yellow-100 text-yellow-800 border-yellow-300"
                                  : "bg-red-100 text-red-800 border-red-300"
                            )}
                          >
                            {formatLabel(analyticsData.legal.maintenance_profile)}
                          </Badge>
                        )}
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-2 gap-4">
                        <div className="flex flex-col items-center">
                          <div className="text-sm text-muted-foreground mb-2">Abandoned Ratio</div>
                          <div className="h-24 w-full flex justify-center">
                            <GaugeChart value={overviewData.health.abandoned_ratio * 100} color="#ef4444" showValue={true} />
                          </div>
                        </div>
                        <div className="flex flex-col items-center">
                          <div className="text-sm text-muted-foreground mb-2">Legal Unknown Ratio</div>
                          <div className="h-24 w-full flex justify-center">
                            <GaugeChart value={overviewData.health.legal_unknown_ratio * 100} color="#f59e0b" showValue={true} />
                          </div>
                        </div>
                      </div>
                    </CardContent>

                  </Card>

                  {/* Peer Positioning */}
                  <Card className="h-full">
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <Users className="h-5 w-5 text-primary" />
                        Peer Positioning
                      </CardTitle>
                      <CardDescription>Comparison with similar portfolios</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        <div className="flex items-center gap-2 mb-4">
                          <Badge variant="outline" className="text-base px-3 py-1">
                            {formatLabel(overviewData.peer_positioning.peer_group_id)}
                          </Badge>
                          <Badge
                            variant="outline"
                            className={cn(
                              "text-base px-3 py-1",
                              overviewData.peer_positioning.peer_class === "ABOVE_AVERAGE" ||
                                overviewData.peer_positioning.peer_class === "HIGH"
                                ? "bg-green-100 text-green-800 border-green-300"
                                : overviewData.peer_positioning.peer_class === "BELOW_AVERAGE" ||
                                  overviewData.peer_positioning.peer_class === "LOW"
                                  ? "bg-red-100 text-red-800 border-red-300"
                                  : "bg-gray-100 text-gray-700 border-gray-300"
                            )}
                          >
                            {formatLabel(overviewData.peer_positioning.peer_class)}
                          </Badge>
                        </div>

                        <h4 className="text-sm font-semibold flex items-center gap-2">
                          <Sparkles className="h-4 w-4 text-yellow-500" />
                          Key Insights
                        </h4>
                        <ul className="space-y-3 mb-6">
                          {getPeerPositioningInsights(overviewData.peer_positioning).map((insight, i) => (
                            <li key={i} className="text-sm text-muted-foreground flex gap-2">
                              <span className="text-primary mt-1">•</span>
                              <span>{insight}</span>
                            </li>
                          ))}
                        </ul>

                        {/* Compact Horizontal Positioning Chart */}
                        <div className="space-y-2">
                          <div className="flex justify-between text-xs text-muted-foreground">
                            <span>Lagging</span>
                            <span>Average</span>
                            <span>Leading</span>
                          </div>
                          <div className="relative h-4 w-full rounded-full bg-gradient-to-r from-red-500 via-yellow-500 to-green-500">
                            <div
                              className="absolute top-0 h-full w-1bg-white border-2 border-primary rounded-full shadow-md transform -translate-x-1/2"
                              style={{
                                left: `${Math.min(Math.max(overviewData.peer_positioning.peer_percentile, 0), 100)}%`,
                                width: '8px',
                                height: '24px',
                                top: '-4px',
                                backgroundColor: 'white'
                              }}
                            />
                          </div>

                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>
                </motion.div>
                </AnimatePresence>
              </TabsContent>

              {/* Patents Tab */}
              <TabsContent value="patents" className="space-y-6">
                <AnimatePresence mode="wait">
                <motion.div
                  key={activeTab + "-patents"}
                  variants={tabVariants}
                  initial="initial" animate="animate" exit="exit"
                  transition={tabTransition}
                  className="space-y-6"
                >
                {patentsLoading && (
                  <div className="space-y-6">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      {Array.from({ length: 4 }).map((_, i) => (
                        <Card key={i} className="p-6">
                          <Skeleton className="h-3 w-20 mb-3" />
                          <Skeleton className="h-8 w-16 mb-2" />
                          <Skeleton className="h-2 w-full" />
                        </Card>
                      ))}
                    </div>
                    <Card>
                      <CardHeader>
                        <Skeleton className="h-5 w-48" />
                        <Skeleton className="h-3 w-64 mt-1" />
                      </CardHeader>
                      <CardContent>
                        <Skeleton className="h-[400px] w-full rounded-md" />
                      </CardContent>
                    </Card>
                  </div>
                )}

                {!patentsLoading && patentsData && (
                  <>
                    {/* Category Summary Strip (Sticky Header) */}
                    {categoryCounts && (
                      <div className="sticky top-0 z-10 bg-background border-b border-border pb-4 mb-6">
                        <div className="flex flex-wrap gap-3">
                          {(() => {
                            const total = Object.values(categoryCounts).reduce((a, b) => a + b, 0)
                            return Object.entries(categoryCounts).map(([category, count]) => {
                              const percentage = total > 0 ? ((count / total) * 100).toFixed(1) : "0"
                              const isSelected = selectedCategories.includes(category as string)

                              return (
                                <div key={category}>
                                  <Tooltip>
                                    <TooltipTrigger asChild>
                                      <Button
                                        variant={isSelected ? "default" : "outline"}
                                        size="sm"
                                        onClick={() => {
                                          if (isSelected) {
                                            setSelectedCategories(selectedCategories.filter((c) => c !== category as string))
                                          } else {
                                            setSelectedCategories([...selectedCategories, category as string])
                                          }
                                        }}
                                        className={cn(
                                          "relative",
                                          isSelected && "bg-primary text-primary-foreground"
                                        )}
                                      >
                                        {formatLabel(category)} ({count})
                                      </Button>
                                    </TooltipTrigger>
                                    <TooltipContent>
                                      <p>{percentage}% of portfolio</p>
                                    </TooltipContent>
                                  </Tooltip>
                                </div>
                              )
                            })
                          })()}
                        </div>
                      </div>
                    )}

                    <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
                      {/* Filters Sidebar */}
                      <div className="lg:col-span-1">
                        <Card>
                          <CardHeader>
                            <CardTitle className="text-lg flex items-center gap-2">
                              <Filter className="h-4 w-4" />
                              Filters
                            </CardTitle>
                          </CardHeader>
                          <CardContent className="space-y-6">
                            {/* Category Filter */}
                            <div>
                              <Label className="text-sm font-semibold mb-3 block">Category</Label>
                              <div className="space-y-2">
                                {categoryCounts ? Object.keys(categoryCounts).map((category) => (
                                  <div key={category} className="flex items-center space-x-2">
                                    <Checkbox
                                      id={`category-${category}`}
                                      checked={selectedCategories.includes(category)}
                                      onCheckedChange={(checked) => {
                                        if (checked) {
                                          setSelectedCategories([...selectedCategories, category])
                                        } else {
                                          setSelectedCategories(selectedCategories.filter((c) => c !== category))
                                        }
                                      }}
                                    />
                                    <Label
                                      htmlFor={`category-${category}`}
                                      className="text-sm cursor-pointer"
                                    >
                                      {formatLabel(category)}
                                    </Label>
                                  </div>
                                )) : (
                                  <div className="text-sm text-muted-foreground">Loading categories...</div>
                                )}
                              </div>
                            </div>

                            <Separator />

                            {/* Status Filter */}
                            <div>
                              <Label className="text-xs font-semibold mb-2 block">Status</Label>
                              <div className="space-y-2">
                                {["ACTIVE", "ABANDONED", "PENDING", "UNKNOWN"].map((status) => (
                                  <div key={status} className="flex items-center space-x-2">
                                    <Checkbox
                                      id={`status-${status}`}
                                      checked={selectedStatus.includes(status)}
                                      onCheckedChange={(checked) => {
                                        if (checked) {
                                          setSelectedStatus([...selectedStatus, status])
                                        } else {
                                          setSelectedStatus(selectedStatus.filter((s) => s !== status))
                                        }
                                      }}
                                    />
                                    <Label
                                      htmlFor={`status-${status}`}
                                      className="text-sm cursor-pointer"
                                    >
                                      {formatLabel(status)}
                                    </Label>
                                  </div>
                                ))}
                              </div>
                            </div>

                            <Separator />

                            {/* Jurisdiction Filter */}
                            <div>
                              <Label className="text-xs font-semibold mb-2 block">Jurisdiction</Label>
                              <div className="space-y-2 max-h-40 overflow-y-auto">
                                {["US", "EP", "WO", "JP", "CN", "KR", "GB", "DE", "FR"].map((jurisdiction) => (
                                  <div key={jurisdiction} className="flex items-center space-x-2">
                                    <Checkbox
                                      id={`jurisdiction-${jurisdiction}`}
                                      checked={selectedJurisdictions.includes(jurisdiction)}
                                      onCheckedChange={(checked) => {
                                        if (checked) {
                                          setSelectedJurisdictions([...selectedJurisdictions, jurisdiction])
                                        } else {
                                          setSelectedJurisdictions(selectedJurisdictions.filter((j) => j !== jurisdiction))
                                        }
                                      }}
                                    />
                                    <Label
                                      htmlFor={`jurisdiction-${jurisdiction}`}
                                      className="text-sm cursor-pointer"
                                    >
                                      {jurisdiction}
                                    </Label>
                                  </div>
                                ))}
                              </div>
                            </div>

                            <Separator />

                            {/* Blocking Power Range */}
                            <div>
                              <Label className="text-xs font-semibold mb-2 block">
                                Blocking: {blockingPowerRange[0]}% - {blockingPowerRange[1]}%
                              </Label>
                              <Slider
                                value={blockingPowerRange}
                                onValueChange={(value) => setBlockingPowerRange(value as [number, number])}
                                min={0}
                                max={100}
                                step={1}
                                className="w-full"
                              />
                            </div>

                            <Separator />

                            {/* Innovation Score Range */}
                            <div>
                              <Label className="text-xs font-semibold mb-2 block">
                                Innovation: {innovationScoreRange[0]}% - {innovationScoreRange[1]}%
                              </Label>
                              <Slider
                                value={innovationScoreRange}
                                onValueChange={(value) => setInnovationScoreRange(value as [number, number])}
                                min={0}
                                max={100}
                                step={1}
                                className="w-full"
                              />
                            </div>

                            {/* Clear Filters */}
                            {(selectedCategories.length > 0 ||
                              selectedStatus.length > 0 ||
                              selectedJurisdictions.length > 0 ||
                              blockingPowerRange[0] > 0 ||
                              blockingPowerRange[1] < 100 ||
                              innovationScoreRange[0] > 0 ||
                              innovationScoreRange[1] < 100) && (
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={() => {
                                    setSelectedCategories([])
                                    setSelectedStatus([])
                                    setSelectedJurisdictions([])
                                    setBlockingPowerRange([0, 100])
                                    setInnovationScoreRange([0, 100])
                                  }}
                                  className="w-full"
                                >
                                  <X className="h-4 w-4 mr-2" />
                                  Clear Filters
                                </Button>
                              )}
                          </CardContent>
                        </Card>
                      </div>

                      {/* Main Content */}
                      <div className="lg:col-span-4 space-y-6">
                        {/* Category Insights Panel */}
                        {selectedCategories.length === 1 && (
                          <Card className="bg-muted/30">
                            <CardContent className="pt-6">
                              {(() => {
                                const category = selectedCategories[0]
                                const insights: Record<string, { title: string; description: string }> = {
                                  CROWN_JEWEL: {
                                    title: "Crown Jewel",
                                    description:
                                      "Exceptional patents combining strong technology, market relevance, legal strength, and impact. Key assets for licensing, enforcement, or strategic positioning.",
                                  },
                                  FORTRESS: {
                                    title: "Fortress",
                                    description:
                                      "Strong defensive and blocking position. These patents provide strong blocking power through legal strength, family breadth, and strategic positioning. Difficult for competitors to design around.",
                                  },
                                  HIDDEN_GEM: {
                                    title: "Hidden Gem",
                                    description:
                                      "Highly innovative patents with relatively weak blocking power. Ideal candidates for continuations, licensing, or claim expansion. Underexploited but high-potential patents.",
                                  },
                                  CORE_ASSET: {
                                    title: "Core Asset",
                                    description:
                                      "Solid, defensible portfolio components. These patents play a stable and meaningful role in the portfolio, contributing to technology coverage and legal strength.",
                                  },
                                  DEADWOOD: {
                                    title: "Deadwood",
                                    description:
                                      "Low strategic and commercial relevance. These patents show limited technological impact, weak market relevance, and low blocking or licensing potential.",
                                  },
                                }
                                const insight = insights[category]
                                return insight ? (
                                  <div>
                                    <h4 className="text-lg font-semibold mb-2">{insight.title}</h4>
                                    <p className="text-sm text-muted-foreground">{insight.description}</p>
                                  </div>
                                ) : null
                              })()}
                            </CardContent>
                          </Card>
                        )}

                        {/* Patent Table */}
                        <Card>
                          <CardHeader>
                            <div className="flex items-center justify-between">
                              <div>
                                <CardTitle>Patents</CardTitle>
                                <CardDescription>
                                  Showing {patentsData.patents.length} of {patentsData.pagination.total} patents
                                </CardDescription>
                              </div>
                              <Select value={pageSize.toString()} onValueChange={(v) => setPageSize(Number(v))}>
                                <SelectTrigger className="w-[120px]">
                                  <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                  <SelectItem value="25">25 per page</SelectItem>
                                  <SelectItem value="50">50 per page</SelectItem>
                                  <SelectItem value="100">100 per page</SelectItem>
                                </SelectContent>
                              </Select>
                            </div>
                          </CardHeader>
                          <CardContent>
                            <div className="border rounded-lg overflow-hidden">
                              <div className="overflow-auto max-h-[600px]">
                                <table className="w-full">
                                  <thead className="bg-card sticky top-0 z-10 border-b border-border">
                                    <tr>
                                      <th className="text-left p-2 text-xs font-medium w-20">ID</th>
                                      <th className="text-left p-2 text-xs font-medium w-[180px]">Title</th>
                                      <th className="text-center p-2 text-xs font-medium w-18">Category</th>
                                      {(["blocking_power_pct", "innovation_score", "legal_strength", "forward_patent_citation_count"] as const).map((col, idx) => {
                                        const labels = ["Block", "Innov", "Legal", "Cite"]
                                        const isActive = sortCol === col
                                        return (
                                          <th
                                            key={col}
                                            className="text-right p-2 text-xs font-medium cursor-pointer select-none hover:text-foreground"
                                            onClick={() => {
                                              if (isActive) {
                                                setSortDir(d => d === "desc" ? "asc" : "desc")
                                              } else {
                                                setSortCol(col)
                                                setSortDir("desc")
                                              }
                                            }}
                                          >
                                            <span className="inline-flex items-center gap-0.5 justify-end">
                                              {labels[idx]}
                                              {isActive ? (
                                                sortDir === "desc"
                                                  ? <ChevronDown className="h-3 w-3 text-primary" />
                                                  : <ChevronUp className="h-3 w-3 text-primary" />
                                              ) : (
                                                <ChevronDown className="h-3 w-3 opacity-30" />
                                              )}
                                            </span>
                                          </th>
                                        )
                                      })}
                                      <th className="text-center p-2 text-xs font-medium w-18">Status</th>
                                      <th className="text-center p-2 text-xs font-medium w-12">Juris</th>
                                      <th className="text-center p-2 text-xs font-medium w-20">Action</th>
                                    </tr>
                                  </thead>
                                  <tbody>
                                    {patentsData.patents.map((patent) => (
                                      <tr
                                        key={patent.appln_id}
                                        className="border-t border-border hover:bg-muted/30"
                                      >
                                        <td className="p-2 text-xs font-mono w-20">{patent.ep_publn_id_full || patent.appln_id}</td>
                                        <td className="p-2 text-xs">

                                          <Tooltip>
                                            <TooltipTrigger asChild>
                                              <span className="truncate block max-w-[180px]">
                                                {patent.appln_title.length > 35
                                                  ? `${patent.appln_title.substring(0, 35)}...`
                                                  : patent.appln_title}
                                              </span>
                                            </TooltipTrigger>
                                            <TooltipContent className="max-w-md">
                                              <p>{patent.appln_title}</p>
                                            </TooltipContent>
                                          </Tooltip>

                                        </td>
                                        <td className="p-2 text-center w-18">
                                          <Badge variant="outline" className="text-xs px-1.5 py-0.5">{formatLabel(patent.patent_category)}</Badge>
                                        </td>
                                        <td className="p-2 text-xs text-right w-16">
                                          {patent.blocking_power_pct !== null
                                            ? `${patent.blocking_power_pct.toFixed(1)}%`
                                            : "N/A"}
                                        </td>
                                        <td className="p-2 text-xs text-right w-16">
                                          {patent.innovation_score !== null
                                            ? `${patent.innovation_score.toFixed(1)}`
                                            : "N/A"}
                                        </td>
                                        <td className="p-2 text-xs text-right w-14">
                                          {patent.legal_strength !== null
                                            ? `${patent.legal_strength.toFixed(1)}`
                                            : "N/A"}
                                        </td>
                                        <td className="p-2 text-xs text-right w-12">{patent.forward_patent_citation_count}</td>
                                        <td className="p-2 text-center w-18">
                                          <Badge
                                            variant={
                                              !patent.is_abandoned
                                                ? "default"
                                                : "destructive"
                                            }
                                            className="text-xs px-1.5 py-0.5"
                                          >
                                            {patent.is_abandoned ? "Abandoned" : "Active"}
                                          </Badge>
                                        </td>
                                        <td className="p-2 text-center w-12">
                                          <Badge variant="outline" className="text-xs px-1 py-0.5">{patent.publn_auth}</Badge>
                                        </td>
                                        <td className="p-2 text-center w-20">
                                          <Button
                                            size="sm"
                                            asChild
                                            className="bg-red-600 hover:bg-red-700 text-white text-xs h-7 px-2"
                                          >
                                            <Link
                                              href={`/lookup?patentId=${patent.appln_id}`}
                                              target="_blank"
                                              rel="noopener noreferrer"
                                              className="flex items-center gap-1"
                                            >
                                              <ExternalLink className="h-3 w-3" />
                                              View
                                            </Link>
                                          </Button>
                                        </td>
                                      </tr>
                                    ))}
                                  </tbody>
                                </table>
                              </div>
                            </div>

                            {/* Pagination */}
                            <div className="flex items-center justify-between mt-4">
                              <div className="text-sm text-muted-foreground">
                                Showing {patentsData.pagination.offset + 1}–{Math.min(patentsData.pagination.offset + patentsData.patents.length, patentsData.pagination.total)} of {patentsData.pagination.total} patents
                              </div>
                              <div className="flex items-center gap-2">
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                                  disabled={currentPage === 1}
                                >
                                  <ChevronLeft className="h-4 w-4" />
                                  Previous
                                </Button>
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={() =>
                                    setCurrentPage((p) => p + 1)
                                  }
                                  disabled={patentsData.pagination.offset + patentsData.pagination.limit >= patentsData.pagination.total}
                                >
                                  Next
                                  <ChevronRight className="h-4 w-4" />
                                </Button>
                              </div>
                            </div>
                          </CardContent>
                        </Card>
                      </div>
                    </div>
                  </>
                )}

                {!patentsLoading && !patentsData && (
                  <Card>
                    <CardContent className="pt-6">
                      <div className="text-center text-muted-foreground py-12">
                        No patents data available. Please ensure the portfolio ID is valid.
                      </div>
                    </CardContent>
                  </Card>
                )}
                </motion.div>
                </AnimatePresence>
              </TabsContent>



              <TabsContent value="licensing" className="space-y-6">
                <AnimatePresence mode="wait">
                <motion.div
                  key={activeTab + "-licensing"}
                  variants={tabVariants}
                  initial="initial" animate="animate" exit="exit"
                  transition={tabTransition}
                  className="space-y-6"
                >
                {licensingLoading && (
                  <div className="text-center py-12">
                    <div className="text-muted-foreground">Loading licensing candidates...</div>
                  </div>
                )}

                {!licensingLoading && licensingData && (
                  <>
                    {/* Title and Subtitle */}
                    <div className="space-y-2">
                      <h2 className="text-2xl font-bold">Licensing Candidates</h2>
                      <p className="text-sm text-muted-foreground">
                        Top candidates ranked by portfolio overlap and strategic proximity.
                      </p>
                    </div>

                    {/* Candidates Table */}
                    <Card>
                      <CardHeader>
                        <CardTitle>Candidates List</CardTitle>
                        <CardDescription>
                          Showing top {licensingData.pagination.returned} results
                        </CardDescription>
                      </CardHeader>
                      <CardContent>
                        <div className="border rounded-lg overflow-hidden">
                          <div className="overflow-x-auto">
                            <table className="w-full">
                              <thead className="bg-muted/50">
                                <tr>
                                  <th className="text-left p-2 text-xs font-medium w-12">Rank</th>
                                  <th className="text-left p-2 text-xs font-medium">Candidate</th>
                                  <th className="text-center p-2 text-xs font-medium">Country</th>
                                  <th className="text-center p-2 text-xs font-medium">Peer Class</th>
                                  <th className="text-center p-2 text-xs font-medium">Size</th>
                                  <th className="text-center p-2 text-xs font-medium">Industry Overlap</th>
                                  <th className="text-center p-2 text-xs font-medium">CPC Overlap</th>
                                  <th className="text-center p-2 text-xs font-medium w-20">Action</th>
                                </tr>
                              </thead>
                              <tbody>
                                {licensingData.results.map((result) => (
                                  <tr
                                    key={result.candidate.owner_id}
                                    className="border-t border-border hover:bg-muted/30 cursor-pointer"
                                    onClick={() => setSelectedCandidate(result)}
                                  >
                                    <td className="p-2 text-xs font-medium">{result.rank}</td>
                                    <td className="p-2 text-sm font-medium text-primary">
                                      {result.candidate.owner_name}
                                    </td>
                                    <td className="p-2 text-center text-xs">{result.candidate.country}</td>
                                    <td className="p-2 text-center">
                                      <Badge variant="outline" className="text-xs">{result.candidate.peer_class}</Badge>
                                    </td>
                                    <td className="p-2 text-center text-xs">{result.candidate.portfolio_size} patents</td>
                                    <td className="p-2 text-center">
                                      <div className="flex flex-col items-center gap-1">
                                        <span className="text-xs font-medium">{result.overlap.industry_overlap_score.toFixed(2)}</span>
                                        <Progress value={result.overlap.industry_overlap_score * 100} className="h-1.5 w-16" />
                                      </div>
                                    </td>
                                    <td className="p-2 text-center">
                                      <div className="flex flex-col items-center gap-1">
                                        <span className="text-xs font-medium">{result.overlap.cpc_overlap_score.toFixed(2)}</span>
                                        <Progress value={result.overlap.cpc_overlap_score * 100} className="h-1.5 w-16" />
                                      </div>
                                    </td>
                                    <td className="p-2 text-center">
                                      <Button
                                        size="sm"
                                        variant="ghost"
                                        className="h-8 w-8 p-0"
                                        onClick={(e) => {
                                          e.stopPropagation()
                                          setSelectedCandidate(result)
                                        }}
                                      >
                                        <Eye className="h-4 w-4" />
                                      </Button>
                                    </td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        </div>
                      </CardContent>
                    </Card>

                    {/* Candidate Detail Drawer */}
                    <Drawer open={!!selectedCandidate} onOpenChange={(open) => !open && setSelectedCandidate(null)}>
                      <DrawerContent className="max-h-[85vh]">
                        <DrawerHeader className="text-left">
                          <DrawerTitle className="text-xl">{selectedCandidate?.candidate.owner_name}</DrawerTitle>
                          <DrawerDescription>Licensing Candidate Analysis</DrawerDescription>
                        </DrawerHeader>

                        {selectedCandidate && (
                          <div className="px-4 pb-8 overflow-y-auto">
                            <div className="space-y-8">
                              {/* Section A — Candidate Snapshot */}
                              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 bg-muted/30 p-4 rounded-lg border">
                                <div>
                                  <div className="text-xs text-muted-foreground mb-1">Owner ID</div>
                                  <div className="font-mono text-sm">{selectedCandidate.candidate.owner_id}</div>
                                </div>
                                <div>
                                  <div className="text-xs text-muted-foreground mb-1">Country</div>
                                  <div className="font-medium">{selectedCandidate.candidate.country}</div>
                                </div>
                                <div>
                                  <div className="text-xs text-muted-foreground mb-1">Peer Class</div>
                                  <Badge variant="secondary">{selectedCandidate.candidate.peer_class}</Badge>
                                </div>
                                <div>
                                  <div className="text-xs text-muted-foreground mb-1">Portfolio Size</div>
                                  <div className="font-medium">{selectedCandidate.candidate.portfolio_size} patents</div>
                                </div>
                              </div>

                              {/* Section B — Overlap Breakdown */}
                              <div>
                                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                                  <Layers className="h-5 w-5 text-primary" />
                                  Overlap Breakdown
                                </h3>
                                <div className="grid md:grid-cols-2 gap-8">
                                  {/* Industry Overlap */}
                                  <Card>
                                    <CardHeader className="pb-2">
                                      <CardTitle className="text-base flex justify-between items-center">
                                        Industry Overlap
                                        <Badge variant="outline" className="text-sm">
                                          Score: {selectedCandidate.overlap.industry_overlap_score.toFixed(2)}
                                        </Badge>
                                      </CardTitle>
                                    </CardHeader>
                                    <CardContent>
                                      <div className="text-sm font-medium text-muted-foreground mb-2">Shared Industries:</div>
                                      <div className="flex flex-wrap gap-2">
                                        {selectedCandidate.overlap.shared_industry_codes.map((code) => (
                                          <Badge key={code} variant="secondary" className="font-normal">
                                            {formatLabel(code)}
                                          </Badge>
                                        ))}
                                      </div>
                                    </CardContent>
                                  </Card>

                                  {/* CPC Overlap */}
                                  <Card>
                                    <CardHeader className="pb-2">
                                      <CardTitle className="text-base flex justify-between items-center">
                                        CPC Overlap
                                        <Badge variant="outline" className="text-sm">
                                          Score: {selectedCandidate.overlap.cpc_overlap_score.toFixed(2)}
                                        </Badge>
                                      </CardTitle>
                                    </CardHeader>
                                    <CardContent>
                                      <div className="text-sm font-medium text-muted-foreground mb-2">Shared CPC Subclasses:</div>
                                      <div className="flex flex-wrap gap-2">
                                        {selectedCandidate.overlap.shared_cpc_codes.map((code) => (
                                          <Badge key={code} variant="secondary" className="font-mono font-normal">
                                            {code}
                                          </Badge>
                                        ))}
                                      </div>
                                    </CardContent>
                                  </Card>
                                </div>
                              </div>

                              {/* Section C — Interpretation */}
                              <div>
                                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                                  <Sparkles className="h-5 w-5 text-primary" />
                                  Interpretation
                                </h3>
                                <Alert className="bg-primary/5 border-primary/20">
                                  <Info className="h-4 w-4 text-primary" />
                                  <AlertDescription className="text-sm leading-relaxed">
                                    This candidate operates in several overlapping industries with
                                    {selectedCandidate.overlap.cpc_overlap_score > 0.5 ? " high " : " moderate "}
                                    technical specificity. The overlap suggests potential licensing compatibility,
                                    especially for cross-industry applications rather than direct substitution.
                                  </AlertDescription>
                                </Alert>
                              </div>
                            </div>
                          </div>
                        )}
                        <div className="p-4 border-t mt-auto">
                          <DrawerClose asChild>
                            <Button variant="outline" className="w-full">Close</Button>
                          </DrawerClose>
                        </div>
                      </DrawerContent>
                    </Drawer>
                  </>
                )}

                {!licensingLoading && !licensingData && (
                  <Card>
                    <CardContent className="pt-6">
                      <div className="text-center text-muted-foreground py-12">
                        No licensing candidates found.
                      </div>
                    </CardContent>
                  </Card>
                )}
                </motion.div>
                </AnimatePresence>
              </TabsContent>

              <TabsContent value="analysis" className="space-y-6">
                <AnimatePresence mode="wait">
                <motion.div
                  key={activeTab + "-analysis"}
                  variants={tabVariants}
                  initial="initial" animate="animate" exit="exit"
                  transition={tabTransition}
                  className="space-y-6"
                >
                {analyticsLoading && (
                  <div className="text-center py-12">
                    <div className="text-muted-foreground">Loading analytics data...</div>
                  </div>
                )}

                {!analyticsLoading && analyticsData && (
                  <>
                    {/* Portfolio Strategy Badge */}
                    <Card className="border-2">
                      <CardContent className="pt-6">
                        <div className="text-center space-y-2">
                          <div className="text-3xl font-bold text-primary">
                            Portfolio Type: {formatLabel(analyticsData.categories.portfolio_category)}
                          </div>
                          <p className="text-muted-foreground text-lg">
                            Majority of patents show low strategic or blocking value.
                          </p>
                        </div>
                        {/* Category Donut Chart */}
                        <div className="mt-6 space-y-4">
                          <div className="mx-auto h-[260px] w-full max-w-[520px]">
                            <ResponsivePie
                              data={portfolioTypeBreakdown}
                              innerRadius={0.67}
                              padAngle={2}
                              colors={RED_PALETTE}
                              enableArcLabels={false}
                              enableArcLinkLabels={false}
                              margin={{ top: 10, right: 20, bottom: 20, left: 20 }}
                              tooltip={({ datum }) => (
                                <div className="bg-background border border-border p-2 rounded-lg text-xs">
                                  {datum.id}: {datum.value} patents
                                </div>
                              )}
                            />
                          </div>
                          <div className="flex flex-wrap items-center justify-center gap-x-4 gap-y-2">
                            {portfolioTypeBreakdown.map((item, index) => (
                              <div key={item.id} className="inline-flex items-center gap-2 text-xs text-muted-foreground">
                                <span
                                  className="h-2.5 w-2.5 rounded-full"
                                  style={{ backgroundColor: RED_PALETTE[index % RED_PALETTE.length] }}
                                />
                                <span className="font-medium text-foreground">{item.id}</span>
                                <span>({item.value})</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      </CardContent>
                    </Card>

                    {/* Citation Mechanics */}
                    <Card>
                      <CardHeader>
                        <CardTitle>EP Citation Mechanics</CardTitle>
                        <CardDescription>Portfolio influence and citation patterns</CardDescription>
                      </CardHeader>
                      <CardContent>
                        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
                          <Card>
                            <CardHeader className="pb-3">
                              <CardTitle className="text-sm font-medium">Forward Citations</CardTitle>
                            </CardHeader>
                            <CardContent>
                              <div className="text-3xl font-bold text-green-600">
                                {analyticsData.citations.forward_total}
                              </div>
                              <p className="text-xs text-muted-foreground mt-2">
                                How much others build on this portfolio
                              </p>
                            </CardContent>
                          </Card>

                          <Card>
                            <CardHeader className="pb-3">
                              <CardTitle className="text-sm font-medium">Backward Citations</CardTitle>
                            </CardHeader>
                            <CardContent>
                              <div className="text-3xl font-bold text-gray-600">
                                {analyticsData.citations.backward_total}
                              </div>
                              <p className="text-xs text-muted-foreground mt-2">
                                How crowded / derivative the portfolio is
                              </p>
                            </CardContent>
                          </Card>

                          <Card>
                            <CardHeader className="pb-3">
                              <CardTitle className="text-sm font-medium">NPL Citations</CardTitle>
                            </CardHeader>
                            <CardContent>
                              <div className="text-3xl font-bold text-blue-600">
                                {analyticsData.citations.backward_npl_total}
                              </div>
                              <p className="text-xs text-muted-foreground mt-2">
                                Scientific grounding
                              </p>
                            </CardContent>
                          </Card>

                          {/* Self-Forward */}
                          <Card>
                            <CardHeader className="pb-3">
                              <CardTitle className="text-sm font-medium">Self-Forward Rate</CardTitle>
                            </CardHeader>
                            <CardContent>
                              <div className="text-3xl font-bold text-purple-600">
                                {(analyticsData.citations.self_citations.self_forward_rate * 100).toFixed(1)}%
                              </div>
                              <p className="text-xs text-muted-foreground mt-2">
                                Independence
                              </p>
                            </CardContent>
                          </Card>

                          {/* Self-Blocking */}
                          <Card>
                            <CardHeader className="pb-3">
                              <CardTitle className="text-sm font-medium">Self-Blocking Rate</CardTitle>
                            </CardHeader>
                            <CardContent>
                              <div className="text-3xl font-bold text-orange-600">
                                {(analyticsData.citations.self_citations.avg_self_blocking_rate * 100).toFixed(1)}%
                              </div>
                              <p className="text-xs text-muted-foreground mt-2">
                                Defensive depth
                              </p>
                            </CardContent>
                          </Card>
                        </div>
                      </CardContent>
                    </Card>

                    {/* Citation Distribution */}
                    <Card>
                      <CardHeader>
                        <CardTitle>EP Citation Distribution</CardTitle>
                        <CardDescription>Depth view of citation patterns</CardDescription>
                      </CardHeader>
                      <CardContent>
                        <div className="grid md:grid-cols-2 gap-6">
                          {/* Forward Citations Histogram */}
                          <div>
                            <h4 className="text-sm font-semibold mb-4 flex items-center gap-2">
                              Forward Citations

                              <Tooltip>
                                <TooltipTrigger asChild>
                                  <Info className="h-3.5 w-3.5 text-muted-foreground cursor-help" />
                                </TooltipTrigger>
                                <TooltipContent>
                                  <p>Most patents receive little or no follow-on innovation.</p>
                                </TooltipContent>
                              </Tooltip>

                            </h4>
                            <div className="h-[250px] w-full">
                              <ResponsiveBar
                                data={analyticsData.citations.distribution.forward_buckets}
                                keys={["count"]}
                                indexBy="bucket"
                                colors={["#10b981"]}
                                theme={getNivoTheme()}
                                margin={{ top: 10, right: 10, bottom: 50, left: 45 }}
                                padding={0.2}
                                enableLabel={false}
                                borderRadius={4}
                                axisBottom={{ tickRotation: -30, tickSize: 0, tickPadding: 6 }}
                                axisLeft={{ tickSize: 0 }}
                              />
                            </div>
                          </div>

                          {/* Backward Citations Histogram */}
                          <div>
                            <h4 className="text-sm font-semibold mb-4 flex items-center gap-2">
                              Backward Citations

                              <Tooltip>
                                <TooltipTrigger asChild>
                                  <Info className="h-3.5 w-3.5 text-muted-foreground cursor-help" />
                                </TooltipTrigger>
                                <TooltipContent>
                                  <p>Portfolio relies heavily on existing prior art.</p>
                                </TooltipContent>
                              </Tooltip>

                            </h4>
                            <div className="h-[250px] w-full">
                              <ResponsiveBar
                                data={analyticsData.citations.distribution.backward_buckets}
                                keys={["count"]}
                                indexBy="bucket"
                                colors={["#6b7280"]}
                                theme={getNivoTheme()}
                                margin={{ top: 10, right: 10, bottom: 50, left: 45 }}
                                padding={0.2}
                                enableLabel={false}
                                borderRadius={4}
                                axisBottom={{ tickRotation: -30, tickSize: 0, tickPadding: 6 }}
                                axisLeft={{ tickSize: 0 }}
                              />
                            </div>
                          </div>
                        </div>
                      </CardContent>
                    </Card>



                    {/* NEW: Portfolio Citation Analytics */}
                    <div className="space-y-6">
                      {/* Header moved to PortfolioHealthCards */}

                      {portfolioLifecycleMetrics && (
                        <PortfolioHealthCards metrics={portfolioLifecycleMetrics} />
                      )}
                      <PortfolioCitationEvolutionChart data={portfolioCitationEvolutionData} />
                    </div>




                    {/* Blocking Power */}
                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                          <Target className="h-5 w-5 text-primary" />
                          Blocking Power (Competitive Control)
                        </CardTitle>
                        <CardDescription>Drivers of portfolio blocking capability</CardDescription>
                      </CardHeader>
                      <CardContent className="space-y-6">
                        {/* Blocking Power Drivers Chart */}
                        <div>
                          <div className="flex items-center justify-between mb-4">
                            <h4 className="text-sm font-semibold">Blocking Power Drivers</h4>
                            {analyticsData.blocking_power.dominant_driver && (
                              <Badge variant="outline" className="bg-primary/10 text-primary border-primary/30">
                                Dominant: {formatLabel(analyticsData.blocking_power.dominant_driver)}
                              </Badge>
                            )}
                          </div>
                          <div className="h-[300px] w-full">
                            <ResponsiveBar
                              data={[
                                { metric: "Forward Impact", value: analyticsData.blocking_power.drivers.forward_impact_score * 100 },
                                { metric: "Family Breadth", value: analyticsData.blocking_power.drivers.family_breadth_normalized * 100 },
                                { metric: "Tech Breadth Penalty", value: analyticsData.blocking_power.drivers.tech_breadth_penalty },
                                { metric: "Self Blocking", value: analyticsData.blocking_power.drivers.self_blocking_rate * 100 },
                              ]}
                              keys={["value"]}
                              indexBy="metric"
                              layout="horizontal"
                              colors={[RED_PALETTE[0]]}
                              theme={getNivoTheme()}
                              margin={{ top: 10, right: 40, bottom: 10, left: 180 }}
                              padding={0.3}
                              borderRadius={4}
                              enableLabel={false}
                              axisBottom={{ tickSize: 0, format: (v: number) => v.toFixed(0) }}
                              axisLeft={{ tickSize: 0 }}
                            />
                          </div>
                        </div>

                        {/* Top Blocking Patents Table */}
                        <div>
                          <h4 className="text-sm font-semibold mb-4">Top Blocking Patents</h4>
                          <div className="border rounded-lg overflow-hidden">
                            <table className="w-full">
                              <thead className="bg-muted/50">
                                <tr>
                                  <th className="text-left p-3 text-sm font-medium">Rank</th>
                                  <th className="text-left p-3 text-sm font-medium">Patent ID</th>
                                  <th className="text-right p-3 text-sm font-medium">Blocking Power %</th>
                                  <th className="text-center p-3 text-sm font-medium">Action</th>
                                </tr>
                              </thead>
                              <tbody>
                                {analyticsData.blocking_power.top_patents.map((patent, index) => (
                                  <tr key={patent.appln_id} className="border-t border-border hover:bg-muted/30">
                                    <td className="p-3 text-sm">{index + 1}</td>
                                    <td className="p-3 text-sm font-mono">{patent.ep_publn_id_full || patent.appln_id}</td>
                                    <td className="p-3 text-sm text-right font-medium">
                                      {patent.blocking_power_pct?.toFixed(1) ?? "N/A"}
                                    </td>
                                    <td className="p-3 text-center">
                                      <Button
                                        size="sm"
                                        asChild
                                        className="bg-red-600 hover:bg-red-700 text-white"
                                      >
                                        <Link
                                          href={`/lookup?patentId=${patent.appln_id}`}
                                          target="_blank"
                                          rel="noopener noreferrer"
                                          className="flex items-center gap-1"
                                        >
                                          <ExternalLink className="h-3.5 w-3.5" />
                                          View Analytics
                                        </Link>
                                      </Button>
                                    </td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        </div>
                      </CardContent>
                    </Card>

                    {/* Innovation Signals */}
                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                          <Sparkles className="h-5 w-5 text-primary" />
                          Innovation Signals (R&D Quality)
                        </CardTitle>
                        <CardDescription>Research and development quality indicators</CardDescription>
                      </CardHeader>
                      <CardContent className="space-y-6">
                        {/* Innovation Summary Cards */}
                        <div className="grid md:grid-cols-3 gap-6">
                          <Card>
                            <CardHeader className="pb-3">
                              <CardTitle className="text-sm font-medium">Avg Innovation Score</CardTitle>
                            </CardHeader>
                            <CardContent>
                              <div className="text-2xl font-bold">
                                {analyticsData.innovation.innovation_score_avg.toFixed(1)}
                              </div>
                              <p className="text-xs text-muted-foreground mt-2">Moderate originality</p>
                            </CardContent>
                          </Card>

                          <Card>
                            <CardHeader className="pb-3">
                              <CardTitle className="text-sm font-medium">H-index Proxy</CardTitle>
                            </CardHeader>
                            <CardContent>
                              <div className="text-2xl font-bold">
                                {analyticsData.innovation.h_index_proxy_avg.toFixed(1)}
                              </div>
                              <p className="text-xs text-muted-foreground mt-2">Few consistently influential patents</p>
                            </CardContent>
                          </Card>

                          <Card>
                            <CardHeader className="pb-3">
                              <CardTitle className="text-sm font-medium">Field-normalized Citations</CardTitle>
                            </CardHeader>
                            <CardContent>
                              <div className="text-2xl font-bold">
                                {analyticsData.innovation.field_normalized_citations_avg.toFixed(1)}
                              </div>
                              <p className="text-xs text-muted-foreground mt-2">Around field median</p>
                            </CardContent>
                          </Card>
                        </div>

                        {/* Top Innovative Patents Table */}
                        <div>
                          <h4 className="text-sm font-semibold mb-4">Top Innovative Patents</h4>
                          <div className="border rounded-lg overflow-hidden">
                            <table className="w-full">
                              <thead className="bg-muted/50">
                                <tr>
                                  <th className="text-left p-3 text-sm font-medium">Rank</th>
                                  <th className="text-left p-3 text-sm font-medium">Patent ID</th>
                                  <th className="text-right p-3 text-sm font-medium">Innovation Score</th>
                                  <th className="text-center p-3 text-sm font-medium">Action</th>
                                </tr>
                              </thead>
                              <tbody>
                                {analyticsData.innovation.top_patents.map((patent, index) => (
                                  <tr key={patent.appln_id} className="border-t border-border hover:bg-muted/30">
                                    <td className="p-3 text-sm">{index + 1}</td>
                                    <td className="p-3 text-sm font-mono">{patent.ep_publn_id_full || patent.appln_id}</td>
                                    <td className="p-3 text-sm text-right font-medium">
                                      {patent.innovation_score?.toFixed(1) ?? "N/A"}
                                    </td>
                                    <td className="p-3 text-center">
                                      <Button
                                        size="sm"
                                        asChild
                                        className="bg-red-600 hover:bg-red-700 text-white"
                                      >
                                        <Link
                                          href={`/lookup?patentId=${patent.appln_id}`}
                                          target="_blank"
                                          rel="noopener noreferrer"
                                          className="flex items-center gap-1"
                                        >
                                          <ExternalLink className="h-3.5 w-3.5" />
                                          View Analytics
                                        </Link>
                                      </Button>
                                    </td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </>
                )}

                {!analyticsLoading && !analyticsData && (
                  <Card>
                    <CardContent className="pt-6">
                      <div className="text-center text-muted-foreground py-12">
                        No analytics data available. Please search for a portfolio first.
                      </div>
                    </CardContent>
                  </Card>
                )}
                </motion.div>
                </AnimatePresence>

              </TabsContent>

              {/* FORECAST TAB */}
              <TabsContent value="forecast" className="space-y-6">
                <AnimatePresence mode="wait">
                <motion.div
                  key={activeTab + "-forecast"}
                  variants={tabVariants}
                  initial="initial" animate="animate" exit="exit"
                  transition={tabTransition}
                  className="space-y-6"
                >
                <div className="text-sm text-muted-foreground mb-4">
                  AI-driven citation forecasts for the next 3-5 years, based on patent characteristics and portfolio composition.
                </div>
                <PortfolioForecastCard ownerId={Number(ownerId)} />
                </motion.div>
                </AnimatePresence>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card >
      )
      }
    </>
  )
}

export default function PortfolioAnalysisPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center">Loading portfolio analysis...</div>}>
      <PortfolioAnalysisContent />
    </Suspense>
  )
}
