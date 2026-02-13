"use client"

import type React from "react"

import { useState, useEffect } from "react"
import { useSearchParams } from "next/navigation"
import Link from "next/link"
import { Input } from "@/components/ui/input"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { fetchJson, getPatentUrl, getPatentAnalysisUrl, getPatentCitationMetricsUrl, getPatentCitationTimeSeriesUrl, getPatentAdvisoryUrl } from "@/lib/api"
import type { PatentPageResponse, PatentAnalysisResponse } from "@/lib/types/patent"
import type { CitationMetricsResponse, CitationTimeSeriesResponse } from "@/lib/types/citation"
import type { PatentAdvisoryOutput } from "@/lib/types/advisory"
import { cn, formatLabel } from "@/lib/utils"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import {
  ArrowLeft,
  Calendar,
  Award,
  TrendingUp,
  Target,
  Shield,
  Activity,
  Sparkles,
  BarChart3,
  CheckCircle2,
  XCircle,
  Info,
  Zap,
  Layers,
  Users,
  GitBranch,
  Clock,
  Scale,
  FileWarning,
  Wrench,
  Eye,
  Gauge,
  Link2,
  MapPinned,
  Search,
  FileText,
  Settings,
  Gem,
  Crown,
} from "lucide-react"
import { RadarChart } from "@/components/radar-chart"
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip as RechartsTooltip, Legend } from "recharts"
import { BarChart, Bar, CartesianGrid, XAxis, YAxis } from "recharts"
import { CitationEvolutionChart, type CitationYearData } from "@/components/citation-evolution-chart"
import { PatentLegalFamilyStrength } from "@/components/patent-legal-family-strength"
import { TrajectoryLifecycleCards, type LifecycleMetrics } from "@/components/trajectory-lifecycle-cards"
import { ForecastCard } from "@/components/forecast-card"
import { CitationForecastChart } from "@/components/citation-forecast-chart"
import { AiInsightCard } from "@/components/ai-insight-card"
import { llmQueue } from "@/lib/api/llm-queue"

function MetricWithTooltip({
  label,
  value,
  tooltip,
  percentile,
  tier,
  icon: Icon,
  rawValue,
}: {
  label: string
  value: string | number
  tooltip: string
  percentile?: number
  tier?: string
  icon?: React.ElementType
  rawValue?: string | number
}) {
  return (
    <TooltipProvider>
      <div className="space-y-2">
        <div className="flex items-center gap-2">
          {Icon && <Icon className="h-4 w-4 text-muted-foreground" />}
          <span className="text-sm font-medium">{label}</span>
          <Tooltip>
            <TooltipTrigger asChild>
              <Info className="h-3.5 w-3.5 text-muted-foreground cursor-help" />
            </TooltipTrigger>
            <TooltipContent className="max-w-xs">
              <p>{tooltip}</p>
            </TooltipContent>
          </Tooltip>
        </div>
        <div className="text-2xl font-bold">{value}</div>
        {percentile !== undefined && (
          <div className="space-y-1">
            <div className="flex items-center justify-between text-xs">
              <span className="text-muted-foreground">Global Percentile</span>
              <span className="font-semibold">{percentile.toFixed(1)}/100</span>
            </div>
            <Progress value={percentile} className="h-1.5" />
          </div>
        )}
        {tier && (
          <Badge
            variant="secondary"
            className={
              tier.includes("HIGH") || tier.includes("STRONG") || tier.includes("ABOVE_AVERAGE")
                ? "bg-green-100 text-green-800 border-green-300"
                : tier.includes("LOW") || tier.includes("WEAK") || tier.includes("BELOW_AVERAGE")
                  ? "bg-red-100 text-red-800 border-red-300"
                  : "bg-gray-100 text-gray-700 border-gray-300"
            }
          >
            {formatLabel(tier)}
          </Badge>
        )}
        {rawValue !== undefined && <p className="text-xs text-muted-foreground">Raw: {rawValue}</p>}
      </div>
    </TooltipProvider>
  )
}

export default function PatentLookupPage() {
  const searchParams = useSearchParams()
  const [activeTab, setActiveTab] = useState("overview")
  const [patentId, setPatentId] = useState(() => {
    // Get patentId from URL params if available, otherwise use default
    return searchParams?.get("patentId") || "482020668"
  })
  const [loading, setLoading] = useState(false)
  const [analysisLoading, setAnalysisLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [analysisError, setAnalysisError] = useState<string | null>(null)
  const [advisoryLoading, setAdvisoryLoading] = useState(false)
  const [advisoryError, setAdvisoryError] = useState<string | null>(null)
  const [advisoryData, setAdvisoryData] = useState<Partial<PatentAdvisoryOutput> | null>(null)
  const [loadingBuckets, setLoadingBuckets] = useState<Record<string, boolean>>({})

  const [patentData, setPatentData] = useState<PatentPageResponse | null>(null)
  const [analysisData, setAnalysisData] = useState<PatentAnalysisResponse | null>(null)
  const [citationMetrics, setCitationMetrics] = useState<CitationMetricsResponse | null>(null)
  const [metricsLoading, setMetricsLoading] = useState(false)
  const [citationTimeSeries, setCitationTimeSeries] = useState<CitationTimeSeriesResponse | null>(null)
  const [timeSeriesLoading, setTimeSeriesLoading] = useState(false)

  // Sync patentId with URL params
  useEffect(() => {
    const urlPatentId = searchParams?.get("patentId")
    if (urlPatentId && urlPatentId !== patentId) {
      setPatentId(urlPatentId)
    }
  }, [searchParams])

  // Fetch patent data
  useEffect(() => {
    if (patentId.trim()) {
      setLoading(true)
      setError(null)
      setPatentData(null)
      setAnalysisData(null)
      setAnalysisError(null)
      setAdvisoryData(null)
      setAdvisoryError(null)

      fetchJson<PatentPageResponse>(getPatentUrl(patentId))
        .then((data) => {
          setPatentData(data)
        })
        .catch((e: Error) => {
          setError(e.message || "Failed to fetch patent data")
        })
        .finally(() => {
          setLoading(false)
        })
    }
  }, [patentId])

  // Fetch citation metrics and time series
  useEffect(() => {
    if (patentData?.patent.appln_id) {
      setMetricsLoading(true)
      setCitationMetrics(null)
      setTimeSeriesLoading(true)
      setCitationTimeSeries(null)

      // Fetch Metrics
      fetchJson<CitationMetricsResponse>(getPatentCitationMetricsUrl(patentData.patent.appln_id.toString()))
        .then(data => {
          setCitationMetrics(data)
        })
        .catch(e => {
          console.error("Failed to fetch citation metrics:", e)
        })
        .finally(() => {
          setMetricsLoading(false)
        })

      // Fetch Time Series
      fetchJson<CitationTimeSeriesResponse>(getPatentCitationTimeSeriesUrl(patentData.patent.appln_id.toString()))
        .then(data => {
          setCitationTimeSeries(data)
        })
        .catch(e => {
          console.error("Failed to fetch citation time series:", e)
        })
        .finally(() => {
          setTimeSeriesLoading(false)
        })
    }
  }, [patentData?.patent.appln_id])

  // Fetch analysis data when advanced tab is active
  useEffect(() => {
    if (activeTab === "advanced" && patentData && !analysisData && !analysisLoading && !analysisError) {
      setAnalysisLoading(true)
      setAnalysisError(null)

      fetchJson<PatentAnalysisResponse>(getPatentAnalysisUrl(patentData.patent.appln_id.toString()))
        .then((data) => {
          setAnalysisData(data)
        })
        .catch((e: Error) => {
          setAnalysisError(e.message || "Failed to fetch analysis data")
        })
        .finally(() => {
          setAnalysisLoading(false)
        })
    }
  }, [activeTab, patentData, analysisData, analysisLoading, analysisError])

  // Automatic advisory fetching removed in favor of granular on-demand generation
  /*
  useEffect(() => {
    if (patentData && !advisoryData && !advisoryLoading && !advisoryError) {
      setAdvisoryLoading(true)
      setAdvisoryError(null)

      fetchJson<PatentAdvisoryOutput>(getPatentAdvisoryUrl(patentData.patent.appln_id))
        .then((data) => {
          setAdvisoryData(data)
        })
        .catch((e: Error) => {
          setAdvisoryError(e.message || "Failed to fetch advisory")
        })
        .finally(() => {
          setAdvisoryLoading(false)
        })
    }
  }, [patentData, advisoryData, advisoryLoading, advisoryError])
  */

  const generateInsight = async (bucket: string) => {
    if (!patentData?.patent.appln_id) return

    setLoadingBuckets((prev) => ({ ...prev, [bucket]: true }))
    setAdvisoryError(null)

    try {
      await llmQueue.enqueue(async () => {
        const url = `${getPatentAdvisoryUrl(patentData.patent.appln_id)}?bucket=${bucket}`
        const data = await fetchJson<Partial<PatentAdvisoryOutput>>(url)
        setAdvisoryData((prev) => ({ ...prev, ...data }))
      })
    } catch (e: any) {
      console.error(e)
      setAdvisoryError(e.message || `Failed to generate ${bucket} insight`)
    } finally {
      setLoadingBuckets((prev) => ({ ...prev, [bucket]: false }))
    }
  }

  // Use real data from API
  const overviewData = patentData

  // Use real analysis data from API
  const advancedData = analysisData

  // Prepare radar chart data
  const radarData = overviewData
    ? [
      { category: "Technology", value: overviewData.technology.percentile_global, max: 100 },
      { category: "Market", value: overviewData.market.percentile_global, max: 100 },
      { category: "Blocking", value: overviewData.scores.blocking_power.percentile, max: 100 },
      { category: "Licensing", value: overviewData.scores.licensing_readiness.percentile, max: 100 },
      { category: "Legal", value: overviewData.scores.legal_strength.percentile, max: 100 },
    ]
    : []

  // Prepare pie chart data for advanced view
  const cpcPieData =
    advancedData?.technology?.distribution?.cpc_subclasses?.map((cpc) => ({
      name: cpc.code,
      value: cpc.weight * 100,
    })) || []

  const industryPieData =
    advancedData?.market?.distribution?.industries?.slice(0, 10).map((ind) => ({
      name: ind.code.replace(/_/g, " "),
      value: ind.weight * 100,
    })) || []

  // Transform API data for chart
  const citationEvolutionData: CitationYearData[] = citationTimeSeries?.series.map(point => ({
    year: citationTimeSeries.filing_date + point.age_year,
    early: 0, // Not available in API yet
    mid: point.new_forward_cites, // Treat all as mid/total for now to show color
    late: 0, // Not available in API yet
    total: point.new_forward_cites
  })) || []

  // Transform API data to LifecycleMetrics
  const lifecycleMetrics: LifecycleMetrics = citationMetrics ? {
    trajectory: {
      score: Number(citationMetrics.trajectory_score.toFixed(1)),
      percentile: Number((citationMetrics.trajectory_score_pct * 100).toFixed(0)),
      label: citationMetrics.trajectory_score >= 80 ? "Rising" : citationMetrics.trajectory_score <= 40 ? "Falling" : "Flat"
    },
    durability: {
      score: Number(citationMetrics.durability_score.toFixed(1)),
      percentile: Number((citationMetrics.durability_score_pct * 100).toFixed(0)),
      spanYears: citationMetrics.citation_span_years
    },
    sustainability: {
      score: Number(citationMetrics.sustainability_score_ui.toFixed(0)),
      percentile: Number((citationMetrics.sustainability_score_pct * 100).toFixed(0)),
      isSustaining: citationMetrics.is_sustaining
    },
    timing: {
      score: Number(citationMetrics.timing_score.toFixed(1)),
      percentile: Number((citationMetrics.timing_score_pct * 100).toFixed(0)),
      class: citationMetrics.timing_class as "EARLY" | "MID" | "LATE"
    },
    peakAge: citationMetrics.peak_age,
    // Per user request: sum of parts
    totalCitations: citationMetrics.early_cites + citationMetrics.mid_cites + citationMetrics.late_cites
  } : {
    // Fallback/Loading state placeholder
    trajectory: { score: 0, percentile: 0, label: "Flat" },
    durability: { score: 0, percentile: 0, spanYears: 0 },
    sustainability: { score: 0, percentile: 0, isSustaining: false },
    timing: { score: 0, percentile: 0, class: "MID" },
    peakAge: 0,
    totalCitations: 0
  }

  // Red and grey color palette for charts
  const COLORS = [
    "#dc2626", // Red 600
    "#ef4444", // Red 500
    "#f87171", // Red 400
    "#9ca3af", // Gray 400
    "#6b7280", // Gray 500
    "#4b5563", // Gray 600
    "#991b1b", // Red 800
    "#7f1d1d", // Red 900
    "#374151", // Gray 700
  ]

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="sm" asChild>
              <Link href="/">
                <ArrowLeft className="mr-2 h-4 w-4" />
                Back
              </Link>
            </Button>
            <div className="flex items-center gap-2">
              <Shield className="h-6 w-6 text-primary" />
              <h1 className="text-xl font-bold">Patent Analysis</h1>
            </div>
          </div>
          <nav className="flex items-center gap-6">
            <Link href="/explore" className="text-sm text-muted-foreground hover:text-foreground">
              Portfolio Explorer
            </Link>
            <Link href="/portfolio" className="text-sm text-muted-foreground hover:text-foreground">
              Portfolio Analysis
            </Link>
            <Link href="/hidden-gems" className="text-sm text-muted-foreground hover:text-foreground">
              Hidden Gems
            </Link>
          </nav>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        {/* Search Input */}
        <Card className="mb-8">
          <CardContent className="pt-6">
            <div className="flex gap-2">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Enter patent ID (e.g., 482020668)"
                  value={patentId}
                  onChange={(e) => setPatentId(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && patentId.trim()) {
                      setPatentId(patentId.trim())
                    }
                  }}
                  className="pl-9"
                  disabled={loading}
                />
              </div>
              <Button onClick={() => patentId.trim() && setPatentId(patentId.trim())} disabled={loading || !patentId.trim()}>
                {loading ? "Loading..." : "Analyze Patent"}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Error Display */}
        {error && (
          <Alert variant="destructive" className="mb-6">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* Loading State */}
        {loading && (
          <div className="text-center py-12">
            <div className="text-muted-foreground">Loading patent data...</div>
          </div>
        )}

        {/* Patent Data Display */}
        {!loading && !error && overviewData && (
          <div className="space-y-6">
            {/* Patent Metadata */}
            <Card className="mb-6">
              <CardHeader>
                <CardTitle className="text-2xl mb-2">{overviewData.patent.title}</CardTitle>
                <div className="flex flex-wrap items-center gap-4 text-sm">
                  <div className="flex items-center gap-2">
                    <span className="text-muted-foreground">Application ID:</span>
                    <span className="font-semibold font-mono">{overviewData.patent.appln_id}</span>
                  </div>
                  {overviewData.patent.owners.length > 0 && (
                    <div className="flex items-center gap-2">
                      <span className="text-muted-foreground">Owners:</span>
                      <div className="flex flex-wrap gap-1">
                        {overviewData.patent.owners.map((o, idx) => (
                          <Badge key={idx} variant="outline" className="font-normal">
                            {o.name} {o.country && `(${o.country})`}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">
                  <div className="grid md:grid-cols-5 gap-4">
                    <div>
                      <div className="text-sm text-muted-foreground mb-1">Application Date</div>
                      <div className="font-medium">{overviewData.patent.application_date.split(" ")[0]}</div>
                    </div>
                    <div>
                      <div className="text-sm text-muted-foreground mb-1">Publication Date</div>
                      <div className="font-medium">{overviewData.patent.publication_date.split(" ")[0]}</div>
                    </div>
                    <div>
                      <div className="text-sm text-muted-foreground mb-1">Grant Date</div>
                      <div className="font-medium">{overviewData.patent.grant_date.split(" ")[0]}</div>
                    </div>
                    <div>
                      <div className="text-sm text-muted-foreground mb-1">Jurisdiction</div>
                      <Badge variant="outline">{overviewData.patent.jurisdiction}</Badge>
                    </div>
                    <div>
                      <div className="text-sm text-muted-foreground mb-1">Status</div>
                      <Badge
                        variant="outline"
                        className={
                          overviewData.patent.status?.toUpperCase().includes("GRANTED") ||
                            overviewData.patent.status?.toUpperCase().includes("ACTIVE")
                            ? "bg-green-100 text-green-800 border-green-300 font-medium"
                            : overviewData.patent.status?.toUpperCase().includes("ABANDONED") ||
                              overviewData.patent.status?.toUpperCase().includes("LAPSED") ||
                              overviewData.patent.status?.toUpperCase().includes("EXPIRED")
                              ? "bg-red-100 text-red-800 border-red-300 font-medium"
                              : "bg-gray-100 text-gray-700 border-gray-300 font-medium"
                        }
                      >
                        {overviewData.patent.status}
                      </Badge>
                    </div>
                  </div>

                  {/* New Family & Legal Strength Component */}
                  <PatentLegalFamilyStrength
                    familyData={overviewData.family}
                    legalStrengthScore={overviewData.scores?.legal_strength?.raw}
                  />
                </div>
              </CardContent>
            </Card>

            {/* Patent Category Card */}
            {overviewData.patent.patent_category && (
              (() => {
                const PATENT_CATEGORY_UI_MAP = {
                  DEADWOOD: {
                    label: "Deadwood",
                    shortDescription: "Low strategic and commercial relevance",
                    longDescription:
                      "This patent shows limited technological impact, weak market relevance, and low blocking or licensing potential. It is unlikely to justify maintenance or monetization costs.",
                    color: "gray",
                    badgeVariant: "neutral",
                    icon: "log",
                    riskLevel: "LOW_UPSIDE",
                    recommendedActions: [
                      "Consider abandonment",
                      "Exclude from licensing strategy",
                      "Use only for defensive coverage if bundled",
                    ],
                  },
                  CORE_ASSET: {
                    label: "Core Asset",
                    shortDescription: "Solid, defensible portfolio component",
                    longDescription:
                      "This patent plays a stable and meaningful role in the portfolio. It contributes to technology coverage and legal strength but is not a singular market or blocking leader.",
                    color: "blue",
                    badgeVariant: "primary",
                    icon: "settings",
                    riskLevel: "STABLE",
                    recommendedActions: [
                      "Maintain protection",
                      "Include in portfolio licensing",
                      "Monitor competitors",
                    ],
                  },
                  FORTRESS: {
                    label: "Fortress",
                    shortDescription: "Strong defensive and blocking position",
                    longDescription:
                      "This patent provides strong blocking power through legal strength, family breadth, and strategic positioning. It is difficult for competitors to design around.",
                    color: "purple",
                    badgeVariant: "strong",
                    icon: "shield",
                    riskLevel: "DEFENSIVE_ADVANTAGE",
                    recommendedActions: [
                      "Defensive enforcement",
                      "Use as negotiation leverage",
                      "Protect aggressively",
                    ],
                  },
                  HIDDEN_GEM: {
                    label: "Hidden Gem",
                    shortDescription: "Underexploited but high-potential patent",
                    longDescription:
                      "This patent shows strong technological or innovation signals but has not yet translated into market dominance or licensing activity. It represents latent value.",
                    color: "green",
                    badgeVariant: "success",
                    icon: "gem",
                    riskLevel: "HIGH_UPSIDE",
                    recommendedActions: [
                      "Evaluate licensing opportunities",
                      "Explore new market applications",
                      "Increase visibility in deal screening",
                    ],
                  },
                  CROWN_JEWEL: {
                    label: "Crown Jewel",
                    shortDescription: "Exceptional strategic and commercial value",
                    longDescription:
                      "This patent combines strong technology, market relevance, legal strength, and impact. It is a key asset for licensing, enforcement, or strategic positioning.",
                    color: "gold",
                    badgeVariant: "premium",
                    icon: "crown",
                    riskLevel: "CRITICAL_ASSET",
                    recommendedActions: [
                      "Prioritize for licensing and enforcement",
                      "Protect across jurisdictions",
                      "Use as flagship portfolio asset",
                    ],
                  },
                } as const;

                const categoryKey = overviewData.patent.patent_category;
                const categoryInfo = PATENT_CATEGORY_UI_MAP[categoryKey as keyof typeof PATENT_CATEGORY_UI_MAP];

                if (!categoryInfo) {
                  return (
                    <div className="rounded-xl p-6 border-2 mb-6 bg-gray-50 border-gray-200">
                      <div className="text-muted-foreground">
                        Unknown category: {categoryKey}
                      </div>
                    </div>
                  );
                }

                const iconMap: Record<string, React.ElementType> = {
                  log: FileText,
                  settings: Settings,
                  shield: Shield,
                  gem: Gem,
                  crown: Crown,
                };

                const IconComponent = iconMap[categoryInfo.icon] || Award;

                const bgColors: Record<string, string> = {
                  gray: "bg-gray-50 border-gray-200",
                  blue: "bg-blue-50 border-blue-200",
                  purple: "bg-purple-50 border-purple-200",
                  green: "bg-emerald-50 border-emerald-200",
                  gold: "bg-amber-50 border-amber-200",
                };

                const textColors: Record<string, string> = {
                  gray: "text-gray-700",
                  blue: "text-blue-700",
                  purple: "text-purple-700",
                  green: "text-emerald-700",
                  gold: "text-amber-700",
                };

                const badgeColors: Record<string, string> = {
                  neutral: "bg-gray-100 text-gray-800 border-gray-300",
                  primary: "bg-blue-100 text-blue-800 border-blue-300",
                  strong: "bg-purple-100 text-purple-800 border-purple-300",
                  success: "bg-green-100 text-green-800 border-green-300",
                  premium: "bg-amber-100 text-amber-800 border-amber-300",
                };

                return (
                  <div
                    className={cn(
                      "rounded-xl p-6 border-2 mb-6",
                      bgColors[categoryInfo.color] || "bg-gray-50 border-gray-200"
                    )}
                  >
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <IconComponent className={cn("h-8 w-8", textColors[categoryInfo.color] || "text-gray-700")} />
                        <h2 className={cn("text-2xl font-bold", textColors[categoryInfo.color] || "text-gray-700")}>
                          {categoryInfo.label.toUpperCase()}
                        </h2>
                      </div>
                      <Badge className={cn("text-xs font-semibold", badgeColors[categoryInfo.badgeVariant] || badgeColors.neutral)}>
                        {formatLabel(categoryInfo.riskLevel)}
                      </Badge>
                    </div>

                    <p className="text-sm font-medium text-foreground/90 mb-3">
                      {categoryInfo.shortDescription}
                    </p>

                    <p className="text-foreground/80 leading-relaxed mb-6">
                      {categoryInfo.longDescription}
                    </p>

                    {categoryInfo.recommendedActions.length > 0 && (
                      <div className="space-y-2">
                        <span className="text-sm font-semibold text-muted-foreground">Recommended Actions:</span>
                        <ul className="list-disc list-inside space-y-1 text-sm text-foreground/70">
                          {categoryInfo.recommendedActions.map((action, idx) => (
                            <li key={idx}>{action}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                );
              })()
            )}

            {/* Main Tabs: Overview and Advanced */}
            <Card>
              <CardContent className="pt-6">
                <Tabs value={activeTab} onValueChange={setActiveTab} defaultValue="overview">
                  <TabsList className="grid w-full grid-cols-2 mb-6">
                    <TabsTrigger value="overview">Overview</TabsTrigger>
                    <TabsTrigger value="advanced">Advanced</TabsTrigger>
                  </TabsList>

                  {/* OVERVIEW TAB */}
                  <TabsContent value="overview" className="space-y-6">
                    {/* Key Scores */}
                    <div className="grid md:grid-cols-3 gap-6">
                      <Card>
                        <CardHeader className="pb-3">
                          <CardTitle className="text-sm font-medium flex items-center gap-2">
                            <Target className="h-4 w-4 text-primary" />
                            Blocking Power
                          </CardTitle>
                        </CardHeader>
                        <CardContent>
                          <MetricWithTooltip
                            icon={Target}
                            label="BPI Score"
                            value={`${overviewData.scores.blocking_power.percentile.toFixed(1)}/100`}
                            tooltip="Blocking Power Index measures a patent's ability to prevent competitors from operating in its technology space. Higher percentiles indicate stronger blocking potential."
                            percentile={overviewData.scores.blocking_power.percentile}
                            tier={overviewData.scores.blocking_power.tier}
                            rawValue={overviewData.scores.blocking_power.raw.toFixed(3)}
                          />
                        </CardContent>
                      </Card>

                      <Card>
                        <CardHeader className="pb-3">
                          <CardTitle className="text-sm font-medium flex items-center gap-2">
                            <TrendingUp className="h-4 w-4 text-primary" />
                            Licensing Readiness
                          </CardTitle>
                        </CardHeader>
                        <CardContent>
                          <MetricWithTooltip
                            icon={Award}
                            label="Licensing Score"
                            value={`${overviewData.scores.licensing_readiness.percentile.toFixed(1)}/100`}
                            tooltip="Licensing Readiness indicates how well-positioned this patent is for commercial licensing. Considers legal strength, market relevance, and citation impact."
                            percentile={overviewData.scores.licensing_readiness.percentile}
                            tier={overviewData.scores.licensing_readiness.tier}
                            rawValue={overviewData.scores.licensing_readiness.raw.toFixed(3)}
                          />
                        </CardContent>
                      </Card>

                      <Card>
                        <CardHeader className="pb-3">
                          <CardTitle className="text-sm font-medium flex items-center gap-2">
                            <BarChart3 className="h-4 w-4 text-muted-foreground" />
                            Legal Strength
                          </CardTitle>
                        </CardHeader>
                        <CardContent>
                          <MetricWithTooltip
                            icon={Shield}
                            label="Legal Score"
                            value={`${overviewData.scores.legal_strength.percentile.toFixed(1)}/100`}
                            tooltip="Legal Strength assesses enforceability based on claim scope, prosecution history, oppositions, and legal events. Higher scores indicate more defensible patents."
                            percentile={overviewData.scores.legal_strength.percentile}
                            tier="STANDARD"
                            rawValue={overviewData.scores.legal_strength.raw}
                          />
                        </CardContent>
                      </Card>
                    </div>

                    {/* Technology & Market Positioning */}
                    <div className="grid md:grid-cols-2 gap-6">
                      <Card>
                        <CardHeader>
                          <CardTitle className="flex items-center gap-2">
                            <Zap className="h-5 w-5 text-primary" />
                            Technology Positioning
                          </CardTitle>
                          <CardDescription>Technical strength and innovation level</CardDescription>
                        </CardHeader>
                        <CardContent>
                          <TooltipProvider>
                            <div className="space-y-4">
                              <div>
                                <div className="flex items-center justify-between mb-2">
                                  <div className="flex items-center gap-2">
                                    <span className="text-sm font-medium">Technology Score</span>
                                    <Tooltip>
                                      <TooltipTrigger asChild>
                                        <Info className="h-3.5 w-3.5 text-muted-foreground cursor-help" />
                                      </TooltipTrigger>
                                      <TooltipContent className="max-w-xs">
                                        <p>
                                          Composite measure of technical novelty, citation quality, CPC diversity, and
                                          technological impact. Normalized against global patent database.
                                        </p>
                                      </TooltipContent>
                                    </Tooltip>
                                  </div>
                                  <span className="text-lg font-bold text-primary">
                                    {overviewData.technology.percentile_global.toFixed(1)}/100
                                  </span>
                                </div>
                                <Progress value={overviewData.technology.percentile_global} className="h-2" />
                                <p className="text-xs text-muted-foreground mt-1">
                                  Raw Score: {overviewData.technology.axis_score.toFixed(3)}
                                </p>
                              </div>
                              <Badge
                                variant="outline"
                                className={
                                  overviewData.technology.tier === "ABOVE_AVERAGE" ||
                                    overviewData.technology.tier === "HIGH"
                                    ? "bg-green-100 text-green-800 border-green-300"
                                    : overviewData.technology.tier === "BELOW_AVERAGE" ||
                                      overviewData.technology.tier === "LOW"
                                      ? "bg-red-100 text-red-800 border-red-300"
                                      : "bg-gray-100 text-gray-700 border-gray-300"
                                }
                              >
                                {formatLabel(overviewData.technology.tier)}
                              </Badge>
                            </div>
                          </TooltipProvider>
                        </CardContent>
                      </Card>

                      <Card>
                        <CardHeader>
                          <CardTitle className="flex items-center gap-2">
                            <Users className="h-5 w-5 text-primary" />
                            Market Positioning
                          </CardTitle>
                          <CardDescription>Commercial relevance and market coverage</CardDescription>
                        </CardHeader>
                        <CardContent>
                          <TooltipProvider>
                            <div className="space-y-4">
                              <div>
                                <div className="flex items-center justify-between mb-2">
                                  <div className="flex items-center gap-2">
                                    <span className="text-sm font-medium">Market Score</span>
                                    <Tooltip>
                                      <TooltipTrigger asChild>
                                        <Info className="h-3.5 w-3.5 text-muted-foreground cursor-help" />
                                      </TooltipTrigger>
                                      <TooltipContent className="max-w-xs">
                                        <p>
                                          Measures market breadth through industry coverage, jurisdictional reach, and
                                          economic sector alignment. Higher scores indicate broader commercial
                                          applicability.
                                        </p>
                                      </TooltipContent>
                                    </Tooltip>
                                  </div>
                                  <span className="text-lg font-bold text-primary">
                                    {overviewData.market.percentile_global.toFixed(1)}/100
                                  </span>
                                </div>
                                <Progress value={overviewData.market.percentile_global} className="h-2" />
                                <p className="text-xs text-muted-foreground mt-1">
                                  Raw Score: {overviewData.market.axis_score.toFixed(3)}
                                </p>
                              </div>
                              <Badge
                                variant="outline"
                                className={
                                  overviewData.market.tier === "ABOVE_AVERAGE" || overviewData.market.tier === "HIGH"
                                    ? "bg-green-100 text-green-800 border-green-300"
                                    : overviewData.market.tier === "BELOW_AVERAGE" || overviewData.market.tier === "LOW"
                                      ? "bg-red-100 text-red-800 border-red-300"
                                      : "bg-gray-100 text-gray-700 border-gray-300"
                                }
                              >
                                {formatLabel(overviewData.market.tier)}
                              </Badge>
                            </div>
                          </TooltipProvider>
                        </CardContent>
                      </Card>
                    </div>

                    {/* Radar Chart Overview */}
                    <Card>
                      <CardHeader>
                        <CardTitle>Patent Strength Radar</CardTitle>
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

                    {/* Citations Overview */}
                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                          <Activity className="h-5 w-5 text-primary" />
                          Citation Analysis
                        </CardTitle>
                        <CardDescription>Patent influence and reference patterns</CardDescription>
                      </CardHeader>
                      <CardContent>
                        <TooltipProvider>
                          <div className="grid md:grid-cols-3 gap-4">
                            <div className="text-center p-4 bg-muted/50 rounded-lg">
                              <Tooltip>
                                <TooltipTrigger asChild>
                                  <div className="cursor-help">
                                    <div className="text-3xl font-bold text-primary mb-1 flex items-center justify-center gap-2">
                                      {overviewData.citations.backward.count}
                                      <Info className="h-4 w-4 text-muted-foreground" />
                                    </div>
                                    <p className="text-sm text-muted-foreground">Backward Citations</p>
                                    <p className="text-xs text-muted-foreground mt-1">
                                      {overviewData.citations.backward.x_normalized.toFixed(1)}/100
                                    </p>
                                  </div>
                                </TooltipTrigger>
                                <TooltipContent className="max-w-xs">
                                  <p>
                                    Number of prior art references cited. Indicates research depth and technological
                                    foundation. Normalized score shows relative citation density.
                                  </p>
                                </TooltipContent>
                              </Tooltip>
                            </div>

                            <div className="text-center p-4 bg-muted/50 rounded-lg">
                              <Tooltip>
                                <TooltipTrigger asChild>
                                  <div className="cursor-help">
                                    <div className="text-3xl font-bold text-primary mb-1 flex items-center justify-center gap-2">
                                      {overviewData.citations.forward.count}
                                      <Info className="h-4 w-4 text-muted-foreground" />
                                    </div>
                                    <p className="text-sm text-muted-foreground">Forward Citations</p>
                                    <p className="text-xs text-muted-foreground mt-1">
                                      {overviewData.citations.forward.x_normalized.toFixed(1)}/100
                                    </p>
                                  </div>
                                </TooltipTrigger>
                                <TooltipContent className="max-w-xs">
                                  <p>
                                    Number of later patents citing this invention. Measures technological impact and
                                    influence. Higher counts indicate foundational innovations.
                                  </p>
                                </TooltipContent>
                              </Tooltip>
                            </div>

                            <div className="text-center p-4 bg-muted/50 rounded-lg">
                              <Tooltip>
                                <TooltipTrigger asChild>
                                  <div className="cursor-help">
                                    <div className="text-3xl font-bold text-muted-foreground mb-1 flex items-center justify-center gap-2">
                                      {overviewData.citations.family_citations}
                                      <Info className="h-4 w-4 text-muted-foreground" />
                                    </div>
                                    <p className="text-sm text-muted-foreground">Family Citations</p>
                                  </div>
                                </TooltipTrigger>
                                <TooltipContent className="max-w-xs">
                                  <p>
                                    Citations across related patent family members (US, EP, JP filings). Indicates global
                                    technology recognition and international impact.
                                  </p>
                                </TooltipContent>
                              </Tooltip>
                            </div>
                          </div>
                        </TooltipProvider>
                      </CardContent>
                    </Card>

                    {/* Relative Positioning */}
                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                          <GitBranch className="h-5 w-5 text-primary" />
                          Relative Positioning
                        </CardTitle>
                        <CardDescription>How this patent ranks globally</CardDescription>
                      </CardHeader>
                      <CardContent>
                        <div className="grid md:grid-cols-2 gap-6">
                          <TooltipProvider>
                            <div className="space-y-3">
                              <div className="flex items-center gap-2">
                                <Target className="h-5 w-5 text-primary" />
                                <h4 className="font-semibold">Blocking Power</h4>
                                <Tooltip>
                                  <TooltipTrigger asChild>
                                    <Info className="h-3.5 w-3.5 text-muted-foreground cursor-help" />
                                  </TooltipTrigger>
                                  <TooltipContent className="max-w-xs">
                                    <p>
                                      Percentile rank among all patents in the database. Shows competitive positioning for
                                      blocking potential in technology landscape.
                                    </p>
                                  </TooltipContent>
                                </Tooltip>
                              </div>
                              <div className="flex items-center justify-between">
                                <span className="text-sm text-muted-foreground">Percentile</span>
                                <span className="font-bold">
                                  {overviewData.relative_positioning.blocking_power.percentile_global.toFixed(1)}/100
                                </span>
                              </div>
                              <Progress value={overviewData.relative_positioning.blocking_power.percentile_global} />
                              <Badge
                                variant="outline"
                                className={
                                  overviewData.relative_positioning.blocking_power.tier === "ABOVE_AVERAGE" ||
                                    overviewData.relative_positioning.blocking_power.tier === "HIGH"
                                    ? "bg-green-100 text-green-800 border-green-300"
                                    : overviewData.relative_positioning.blocking_power.tier === "BELOW_AVERAGE" ||
                                      overviewData.relative_positioning.blocking_power.tier === "LOW"
                                      ? "bg-red-100 text-red-800 border-red-300"
                                      : "bg-gray-100 text-gray-700 border-gray-300"
                                }
                              >
                                {formatLabel(overviewData.relative_positioning.blocking_power.tier)}
                              </Badge>
                            </div>
                          </TooltipProvider>

                          <TooltipProvider>
                            <div className="space-y-3">
                              <div className="flex items-center gap-2">
                                <TrendingUp className="h-5 w-5 text-primary" />
                                <h4 className="font-semibold">Licensing Readiness</h4>
                                <Tooltip>
                                  <TooltipTrigger asChild>
                                    <Info className="h-3.5 w-3.5 text-muted-foreground cursor-help" />
                                  </TooltipTrigger>
                                  <TooltipContent className="max-w-xs">
                                    <p>
                                      Composite ranking for licensing attractiveness. Considers legal status, market
                                      alignment, technological value, and commercial readiness.
                                    </p>
                                  </TooltipContent>
                                </Tooltip>
                              </div>
                              <div className="flex items-center justify-between">
                                <span className="text-sm text-muted-foreground">Percentile</span>
                                <span className="font-bold">
                                  {overviewData.relative_positioning.licensing_readiness.percentile_global.toFixed(1)}/100
                                </span>
                              </div>
                              <Progress value={overviewData.relative_positioning.licensing_readiness.percentile_global} />
                              <Badge
                                variant="outline"
                                className={
                                  overviewData.relative_positioning.licensing_readiness.tier === "ABOVE_AVERAGE" ||
                                    overviewData.relative_positioning.licensing_readiness.tier === "HIGH"
                                    ? "bg-green-100 text-green-800 border-green-300"
                                    : overviewData.relative_positioning.licensing_readiness.tier === "BELOW_AVERAGE" ||
                                      overviewData.relative_positioning.licensing_readiness.tier === "LOW"
                                      ? "bg-red-100 text-red-800 border-red-300"
                                      : "bg-gray-100 text-gray-700 border-gray-300"
                                }
                              >
                                {formatLabel(overviewData.relative_positioning.licensing_readiness.tier)}
                              </Badge>
                            </div>
                          </TooltipProvider>
                        </div>
                      </CardContent>
                    </Card>

                    <div className="grid md:grid-cols-2 gap-6">
                      <AiInsightCard
                        title="Strategy Insight"
                        insight={advisoryData?.strategic_value}
                        loading={loadingBuckets["strategy"]}
                        onGenerate={() => generateInsight("strategy")}
                      />
                      <AiInsightCard
                        title="Technology Insight"
                        insight={advisoryData?.technology_insight}
                        loading={loadingBuckets["technology"]}
                        onGenerate={() => generateInsight("technology")}
                      />
                      <AiInsightCard
                        title="Market Insight"
                        insight={advisoryData?.market_insight}
                        loading={loadingBuckets["market"]}
                        onGenerate={() => generateInsight("market")}
                      />
                      <AiInsightCard
                        title="Legal Insight"
                        insight={advisoryData?.blocking_insight || advisoryData?.legal_health_note}
                        loading={loadingBuckets["legal"]}
                        onGenerate={() => generateInsight("legal")}
                      />
                    </div>
                  </TabsContent>

                  {/* ADVANCED TAB */}
                  <TabsContent value="advanced" className="space-y-6">
                    {analysisLoading && (
                      <div className="text-center py-12">
                        <div className="text-muted-foreground">Loading analysis data...</div>
                      </div>
                    )}
                    {analysisError && (
                      <Alert variant="destructive">
                        <AlertDescription>{analysisError}</AlertDescription>
                      </Alert>
                    )}
                    {!analysisLoading && !analysisError && !advancedData && (
                      <div className="text-center py-12">
                        <div className="text-muted-foreground">No analysis data available</div>
                      </div>
                    )}
                    {!analysisLoading && !analysisError && advancedData && (
                      <>
                        {/* Technology Distribution */}
                        <Card>
                          <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                              <Layers className="h-5 w-5 text-primary" />
                              Technology Distribution
                            </CardTitle>
                            <CardDescription>CPC subclass coverage and diversification analysis</CardDescription>
                          </CardHeader>
                          <CardContent>
                            <div className="grid md:grid-cols-2 gap-6">
                              <div>
                                <h4 className="font-semibold mb-4">CPC Subclass Breakdown</h4>
                                <ResponsiveContainer width="100%" height={300}>
                                  <PieChart>
                                    <Pie
                                      data={cpcPieData}
                                      cx="50%"
                                      cy="50%"
                                      labelLine={true}
                                      label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(1)}%`}
                                      outerRadius={100}
                                      fill="#dc2626"
                                      dataKey="value"
                                    >
                                      {cpcPieData.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                      ))}
                                    </Pie>
                                    <RechartsTooltip
                                      contentStyle={{
                                        backgroundColor: "white",
                                        border: "1px solid #e2e8f0",
                                        borderRadius: "6px",
                                      }}
                                      formatter={(value: any) => [`${Number(value).toFixed(1)}%`, "Weight"]}
                                    />
                                    <Legend />
                                  </PieChart>
                                </ResponsiveContainer>
                              </div>
                              <div className="space-y-4">
                                <TooltipProvider>
                                  <h4 className="font-semibold mb-4">Diversification Metrics</h4>
                                  <div className="space-y-3">
                                    <div>
                                      <div className="flex items-center gap-2 mb-1">
                                        <span className="text-sm">Entropy</span>
                                        <Tooltip>
                                          <TooltipTrigger asChild>
                                            <Info className="h-3.5 w-3.5 text-muted-foreground cursor-help" />
                                          </TooltipTrigger>
                                          <TooltipContent className="max-w-xs">
                                            <p>
                                              Shannon entropy measures technology spread across CPC classes. Higher values
                                              (closer to max ~3.5) indicate broader technical scope.
                                            </p>
                                          </TooltipContent>
                                        </Tooltip>
                                        <span className="text-sm font-bold ml-auto">
                                          {advancedData.technology.diversification.entropy?.toFixed(3) ?? "N/A"}
                                        </span>
                                      </div>
                                      <Progress
                                        value={advancedData.technology.diversification.entropy ? (advancedData.technology.diversification.entropy / 3.5) * 100 : 0}
                                        className="h-2"
                                      />
                                    </div>
                                    <div>
                                      <div className="flex items-center gap-2 mb-1">
                                        <span className="text-sm">Normalized Score</span>
                                        <Tooltip>
                                          <TooltipTrigger asChild>
                                            <Info className="h-3.5 w-3.5 text-muted-foreground cursor-help" />
                                          </TooltipTrigger>
                                          <TooltipContent className="max-w-xs">
                                            <p>
                                              Entropy normalized to 0-1 scale for easier interpretation. Values above 0.7
                                              indicate high diversification across multiple technology areas.
                                            </p>
                                          </TooltipContent>
                                        </Tooltip>
                                        <span className="text-sm font-bold ml-auto">
                                          {advancedData.technology.diversification.normalized?.toFixed(3) ?? "N/A"}
                                        </span>
                                      </div>
                                      <Progress
                                        value={advancedData.technology.diversification.normalized ? advancedData.technology.diversification.normalized * 100 : 0}
                                        className="h-2"
                                      />
                                    </div>
                                    <Badge
                                      variant="outline"
                                      className={`mt-2 ${advancedData.technology.diversification.interpretation === "HIGH" ||
                                        advancedData.technology.diversification.interpretation === "STRONG"
                                        ? "bg-green-100 text-green-800 border-green-300"
                                        : advancedData.technology.diversification.interpretation === "LOW" ||
                                          advancedData.technology.diversification.interpretation === "WEAK"
                                          ? "bg-red-100 text-red-800 border-red-300"
                                          : "bg-gray-100 text-gray-700 border-gray-300"
                                        }`}
                                    >
                                      {formatLabel(advancedData.technology.diversification.interpretation)}
                                    </Badge>
                                  </div>
                                </TooltipProvider>
                              </div>
                            </div>
                          </CardContent>
                        </Card>

                        {/* Market Distribution */}
                        <Card>
                          <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                              <Users className="h-5 w-5 text-primary" />
                              Market Distribution
                            </CardTitle>
                            <CardDescription>Industry coverage and market diversification</CardDescription>
                          </CardHeader>
                          <CardContent>
                            <div className="grid md:grid-cols-2 gap-6">
                              <div>
                                <h4 className="font-semibold mb-4">Top 10 Industries</h4>
                                <ResponsiveContainer width="100%" height={350}>
                                  <PieChart>
                                    <Pie
                                      data={industryPieData}
                                      cx="50%"
                                      cy="50%"
                                      labelLine={false}
                                      label={({ name, percent }) => (percent > 0.05 ? `${name.substring(0, 15)}...` : "")}
                                      outerRadius={120}
                                      fill="#dc2626"
                                      dataKey="value"
                                    >
                                      {industryPieData.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                      ))}
                                    </Pie>
                                    <RechartsTooltip
                                      contentStyle={{
                                        backgroundColor: "white",
                                        border: "1px solid #e2e8f0",
                                        borderRadius: "6px",
                                      }}
                                      formatter={(value: any, name: any) => [`${Number(value).toFixed(1)}%`, name]}
                                    />
                                    <Legend wrapperStyle={{ fontSize: "11px" }} />
                                  </PieChart>
                                </ResponsiveContainer>
                              </div>
                              <div className="space-y-4">
                                <TooltipProvider>
                                  <h4 className="font-semibold mb-4">Market Diversification</h4>
                                  <div className="space-y-3">
                                    <div>
                                      <div className="flex items-center gap-2 mb-1">
                                        <span className="text-sm">Entropy</span>
                                        <Tooltip>
                                          <TooltipTrigger asChild>
                                            <Info className="h-3.5 w-3.5 text-muted-foreground cursor-help" />
                                          </TooltipTrigger>
                                          <TooltipContent className="max-w-xs">
                                            <p>
                                              Measures market breadth across industry sectors. Higher entropy indicates
                                              broader commercial applicability and diversified market opportunities.
                                            </p>
                                          </TooltipContent>
                                        </Tooltip>
                                        <span className="text-sm font-bold ml-auto">
                                          {advancedData.market.diversification.entropy?.toFixed(3) ?? "N/A"}
                                        </span>
                                      </div>
                                      <Progress
                                        value={advancedData.market.diversification.entropy ? (advancedData.market.diversification.entropy / 3.5) * 100 : 0}
                                        className="h-2"
                                      />
                                    </div>
                                    <div>
                                      <div className="flex items-center gap-2 mb-1">
                                        <span className="text-sm">Normalized Score</span>
                                        <Tooltip>
                                          <TooltipTrigger asChild>
                                            <Info className="h-3.5 w-3.5 text-muted-foreground cursor-help" />
                                          </TooltipTrigger>
                                          <TooltipContent className="max-w-xs">
                                            <p>
                                              Market entropy on 0-1 scale. Higher values suggest patent applicability across
                                              multiple industry verticals, increasing licensing opportunities.
                                            </p>
                                          </TooltipContent>
                                        </Tooltip>
                                        <span className="text-sm font-bold ml-auto">
                                          {advancedData.market.diversification.normalized?.toFixed(3) ?? "N/A"}
                                        </span>
                                      </div>
                                      <Progress
                                        value={advancedData.market.diversification.normalized ? advancedData.market.diversification.normalized * 100 : 0}
                                        className="h-2"
                                      />
                                    </div>
                                    <Badge
                                      variant="outline"
                                      className={`mt-2 ${advancedData.market.diversification.interpretation === "HIGH" ||
                                        advancedData.market.diversification.interpretation === "STRONG"
                                        ? "bg-green-100 text-green-800 border-green-300"
                                        : advancedData.market.diversification.interpretation === "LOW" ||
                                          advancedData.market.diversification.interpretation === "WEAK"
                                          ? "bg-red-100 text-red-800 border-red-300"
                                          : "bg-gray-100 text-gray-700 border-gray-300"
                                        }`}
                                    >
                                      {formatLabel(advancedData.market.diversification.interpretation)}
                                    </Badge>
                                  </div>
                                </TooltipProvider>
                              </div>
                            </div>
                          </CardContent>
                        </Card>

                        {/* Citations Analysis */}
                        <Card>
                          <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                              <Activity className="h-5 w-5 text-primary" />
                              Detailed EP Citation Analysis
                            </CardTitle>
                            <CardDescription>Complete breakdown of EP citation patterns and self-citations</CardDescription>
                          </CardHeader>
                          <CardContent>
                            <div className="grid md:grid-cols-3 gap-6">
                              <div>
                                <h4 className="font-semibold mb-4">Backward Citations</h4>
                                <div className="space-y-3">
                                  <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                                    <span className="text-sm">Total</span>
                                    <span className="text-lg font-bold">{advancedData.citations.backward.total}</span>
                                  </div>
                                  <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                                    <span className="text-sm">X Patents</span>
                                    <span className="text-lg font-bold">{advancedData.citations.backward.x_patent}</span>
                                  </div>
                                  <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                                    <span className="text-sm">Y Patents</span>
                                    <span className="text-lg font-bold">{advancedData.citations.backward.y_patent}</span>
                                  </div>
                                  <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                                    <span className="text-sm">X NPL</span>
                                    <span className="text-lg font-bold">{advancedData.citations.backward.x_npl}</span>
                                  </div>
                                  <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                                    <span className="text-sm">Y NPL</span>
                                    <span className="text-lg font-bold">{advancedData.citations.backward.y_npl}</span>
                                  </div>
                                </div>
                              </div>
                              <div>
                                <h4 className="font-semibold mb-4">Forward Citations</h4>
                                <div className="space-y-3">
                                  <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                                    <span className="text-sm">Total</span>
                                    <span className="text-lg font-bold">{advancedData.citations.forward.total}</span>
                                  </div>
                                  <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                                    <span className="text-sm">X Patents</span>
                                    <span className="text-lg font-bold">{advancedData.citations.forward.x_patent}</span>
                                  </div>
                                  <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                                    <span className="text-sm">Y Patents</span>
                                    <span className="text-lg font-bold">{advancedData.citations.forward.y_patent}</span>
                                  </div>
                                </div>
                              </div>
                              <div>
                                <h4 className="font-semibold mb-4">EP Self-Citations</h4>
                                <div className="space-y-3">
                                  <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                                    <span className="text-sm">Forward</span>
                                    <span className="text-lg font-bold">{advancedData.citations.self_citations.forward}</span>
                                  </div>
                                  <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                                    <span className="text-sm">Backward</span>
                                    <span className="text-lg font-bold">{advancedData.citations.self_citations.backward}</span>
                                  </div>
                                  <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                                    <span className="text-sm">Self Forward Rate</span>
                                    <span className="text-lg font-bold">
                                      {advancedData.citations.self_citations.self_forward_rate != null
                                        ? `${(advancedData.citations.self_citations.self_forward_rate * 100).toFixed(1)}%`
                                        : "N/A"}
                                    </span>
                                  </div>
                                  <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                                    <span className="text-sm">Self Blocking Rate</span>
                                    <span className="text-lg font-bold">
                                      {advancedData.citations.self_citations.self_blocking_rate != null
                                        ? `${(advancedData.citations.self_citations.self_blocking_rate * 100).toFixed(1)}%`
                                        : "N/A"}
                                    </span>
                                  </div>
                                </div>
                              </div>
                            </div>
                          </CardContent>
                        </Card>

                        {/* Detailed Citations - Removed to avoid redundancy with Overview Tab */}
                        {/* <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <Activity className="h-5 w-5 text-primary" />
                        Detailed Citation Analysis
                      </CardTitle>
                      <CardDescription>Complete breakdown of citation patterns and self-citations</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="grid md:grid-cols-2 gap-6">
                        <div>
                          <h4 className="font-semibold mb-4">Backward Citations</h4>
                          <div className="space-y-3">
                            <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                              <span className="text-sm">Total Backward</span>
                              <span className="text-lg font-bold">{advancedData.citation_details.backward_citations.count}</span>
                            </div>
                            <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                              <span className="text-sm">Normalized</span>
                              <span className="text-lg font-bold">{advancedData.citation_details.backward_citations.normalized.toFixed(1)}/100</span>
                            </div>
                            <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                              <span className="text-sm">Top Cited Patents</span>
                              <div className="flex gap-1 flex-wrap">
                                {advancedData.citation_details.backward_citations.top_cited_patents.map((patent) => (
                                  <Badge key={patent} variant="outline">{patent}</Badge>
                                ))}
                              </div>
                            </div>
                          </div>
                        </div>
                        <div>
                          <h4 className="font-semibold mb-4">Forward Citations & Self-Citations</h4>
                          <div className="space-y-3">
                            <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                              <span className="text-sm">Total Forward</span>
                              <span className="text-lg font-bold">{advancedData.citation_details.forward_citations.count}</span>
                            </div>
                            <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                              <span className="text-sm">Normalized</span>
                              <span className="text-lg font-bold">{advancedData.citation_details.forward_citations.normalized.toFixed(1)}/100</span>
                            </div>
                            <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                              <span className="text-sm">Self-Citations</span>
                              <span className="text-lg font-bold">{advancedData.citation_details.self_citations}</span>
                            </div>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card> */}

                        {/* Legal Analysis */}
                        <div className="space-y-6">
                          <h3 className="text-lg font-semibold flex items-center gap-2">
                            <TrendingUp className="h-5 w-5 text-primary" />
                            Global Citation Dynamics & Lifecycle
                          </h3>

                          <TrajectoryLifecycleCards metrics={lifecycleMetrics} />

                          <CitationEvolutionChart data={citationEvolutionData} />

                          {patentData?.patent?.appln_id ? (
                            <>
                              <ForecastCard applnId={patentData.patent.appln_id} />
                            </>
                          ) : null}
                        </div>

                        <Card>
                          <CardHeader>
                            <CardTitle>Legal Analysis</CardTitle>
                            <CardDescription>Legal events and status indicators</CardDescription>
                          </CardHeader>
                          <CardContent>
                            <div className="grid md:grid-cols-4 gap-4">
                              <div className="text-center p-4 bg-muted/50 rounded-lg">
                                <Scale className="h-8 w-8 text-primary mx-auto mb-2" />
                                <div className="text-2xl font-bold mb-1">{advancedData.legal.opposition_count}</div>
                                <div className="text-sm font-medium">Oppositions</div>
                              </div>
                              <div className="text-center p-4 bg-muted/50 rounded-lg">
                                <XCircle className="h-8 w-8 text-primary mx-auto mb-2" />
                                <div className="text-2xl font-bold mb-1">{advancedData.legal.lapse_count}</div>
                                <div className="text-sm font-medium">Lapses</div>
                              </div>
                              <div className="text-center p-4 bg-muted/50 rounded-lg">
                                <CheckCircle2 className="h-8 w-8 text-muted-foreground mx-auto mb-2" />
                                <div className="text-2xl font-bold mb-1">{advancedData.legal.renewal_payment_count}</div>
                                <div className="text-sm font-medium">Renewals</div>
                              </div>
                              <div className="text-center p-4 bg-muted/50 rounded-lg">
                                <FileWarning className="h-8 w-8 text-muted-foreground mx-auto mb-2" />
                                <div className="text-sm font-medium mb-2">Legal Uncertainty</div>
                                <Badge variant="outline" className={advancedData.legal.legal_uncertainty ? "border-primary text-primary" : "border-muted-foreground text-muted-foreground"}>
                                  {advancedData.legal.legal_uncertainty ? "YES" : "NO"}
                                </Badge>
                              </div>
                            </div>
                          </CardContent>
                        </Card>

                        {/* Innovation Analysis */}
                        <Card>
                          <CardHeader>
                            <CardTitle>Innovation Analysis</CardTitle>
                            <CardDescription>Technical innovation and impact indicators</CardDescription>
                          </CardHeader>
                          <CardContent>
                            <TooltipProvider>
                              <div className="grid md:grid-cols-3 gap-4">
                                <div>
                                  <div className="flex items-center gap-2 mb-2">
                                    <span className="text-sm text-muted-foreground">Innovation Score</span>
                                    <Tooltip>
                                      <TooltipTrigger asChild>
                                        <Info className="h-3.5 w-3.5 text-muted-foreground cursor-help" />
                                      </TooltipTrigger>
                                      <TooltipContent className="max-w-xs">
                                        <p>
                                          Composite innovation score measuring the patent's overall technological impact and
                                          novelty. Combines citation patterns, technological diversity, and field-normalized metrics.
                                        </p>
                                      </TooltipContent>
                                    </Tooltip>
                                  </div>
                                  <div className="text-3xl font-bold mb-2">
                                    {advancedData.innovation.innovation_score != null
                                      ? advancedData.innovation.innovation_score.toFixed(2)
                                      : "N/A"}
                                  </div>
                                  <Progress value={advancedData.innovation.innovation_score ?? 0} className="h-2" />
                                </div>
                                <div>
                                  <div className="flex items-center gap-2 mb-2">
                                    <span className="text-sm text-muted-foreground">Tech Field Influence</span>
                                    <Tooltip>
                                      <TooltipTrigger asChild>
                                        <Info className="h-3.5 w-3.5 text-muted-foreground cursor-help" />
                                      </TooltipTrigger>
                                      <TooltipContent className="max-w-xs">
                                        <p>
                                          Measures the patent's influence within its specific technology field. Higher values
                                          indicate greater recognition and impact among peers in the same technical domain.
                                        </p>
                                      </TooltipContent>
                                    </Tooltip>
                                  </div>
                                  <div className="text-3xl font-bold mb-2">
                                    {advancedData.innovation.tech_field_influence != null
                                      ? advancedData.innovation.tech_field_influence.toFixed(2)
                                      : "N/A"}
                                  </div>
                                  <Progress value={advancedData.innovation.tech_field_influence ?? 0} className="h-2" />
                                </div>
                                <div>
                                  <div className="flex items-center gap-2 mb-2">
                                    <span className="text-sm text-muted-foreground">Field Attention</span>
                                    <Tooltip>
                                      <TooltipTrigger asChild>
                                        <Info className="h-3.5 w-3.5 text-muted-foreground cursor-help" />
                                      </TooltipTrigger>
                                      <TooltipContent className="max-w-xs">
                                        <p>
                                          Indicates the level of attention and citation activity the patent receives within its
                                          field. Higher values suggest the patent addresses important problems or introduces
                                          significant advances that attract research interest.
                                        </p>
                                      </TooltipContent>
                                    </Tooltip>
                                  </div>
                                  <div className="text-3xl font-bold mb-2">
                                    {advancedData.innovation.field_attention != null
                                      ? advancedData.innovation.field_attention.toFixed(2)
                                      : "N/A"}
                                  </div>
                                  <Progress value={advancedData.innovation.field_attention != null ? Math.min(advancedData.innovation.field_attention, 100) : 0} className="h-2" />
                                </div>
                              </div>
                            </TooltipProvider>
                          </CardContent>
                        </Card>

                        {/* Global Rankings */}
                        <Card>
                          <CardHeader>
                            <CardTitle>Global Rankings</CardTitle>
                            <CardDescription>Comparative position against global patent database</CardDescription>
                          </CardHeader>
                          <CardContent>
                            <div className="space-y-4">
                              <div className="p-4 bg-muted/50 rounded-lg">
                                <div className="flex items-center justify-between mb-2">
                                  <span className="font-medium">Blocking Power Rank</span>
                                  <span className="text-lg font-bold">
                                    {advancedData.rankings.blocking_power.rank_global != null
                                      ? `#${advancedData.rankings.blocking_power.rank_global.toLocaleString()}`
                                      : "N/A"}
                                  </span>
                                </div>
                                <div className="flex items-center justify-between mb-1">
                                  <span className="text-sm text-muted-foreground">Percentile</span>
                                  <span className="text-sm font-medium">
                                    {advancedData.rankings.blocking_power.percentile_global != null
                                      ? `${advancedData.rankings.blocking_power.percentile_global.toFixed(1)}%ile`
                                      : "N/A"}
                                  </span>
                                </div>
                                <Progress value={advancedData.rankings.blocking_power.percentile_global ?? 0} className="h-2" />
                              </div>

                              <div className="p-4 bg-muted/50 rounded-lg">
                                <div className="flex items-center justify-between mb-2">
                                  <span className="font-medium">Technology Axis Rank</span>
                                  <span className="text-lg font-bold">
                                    {advancedData.rankings.technology_axis.rank_global != null
                                      ? `#${advancedData.rankings.technology_axis.rank_global.toLocaleString()}`
                                      : "N/A"}
                                  </span>
                                </div>
                                <div className="flex items-center justify-between mb-1">
                                  <span className="text-sm text-muted-foreground">Percentile</span>
                                  <span className="text-sm font-medium">
                                    {advancedData.rankings.technology_axis.percentile_global != null
                                      ? `${advancedData.rankings.technology_axis.percentile_global.toFixed(1)}%ile`
                                      : "N/A"}
                                  </span>
                                </div>
                                <Progress
                                  value={advancedData.rankings.technology_axis.percentile_global ?? 0}
                                  className="h-2"
                                />
                              </div>

                              <div className="p-4 bg-muted/50 rounded-lg">
                                <div className="flex items-center justify-between mb-2">
                                  <span className="font-medium">Market Axis Rank</span>
                                  <span className="text-lg font-bold">
                                    {advancedData.rankings.market_axis.rank_global != null
                                      ? `#${advancedData.rankings.market_axis.rank_global.toLocaleString()}`
                                      : "N/A"}
                                  </span>
                                </div>
                                <div className="flex items-center justify-between mb-1">
                                  <span className="text-sm text-muted-foreground">Percentile</span>
                                  <span className="text-sm font-medium">
                                    {advancedData.rankings.market_axis.percentile_global != null
                                      ? `${advancedData.rankings.market_axis.percentile_global.toFixed(1)}%ile`
                                      : "N/A"}
                                  </span>
                                </div>
                                <Progress
                                  value={advancedData.rankings.market_axis.percentile_global ?? 0}
                                  className="h-2"
                                />
                              </div>
                            </div>
                          </CardContent>
                        </Card>
                      </>
                    )}

                    <div className="grid md:grid-cols-2 gap-4">
                      <AiInsightCard
                        insight={advisoryData?.technology_insight}
                        loading={advisoryLoading}
                        title="AI Technology Insight"
                      />
                      <AiInsightCard
                        insight={advisoryData?.market_insight}
                        loading={advisoryLoading}
                        title="AI Market Insight"
                      />
                      <AiInsightCard
                        insight={advisoryData?.legal_health_note}
                        loading={advisoryLoading}
                        title="AI Legal Health"
                      />
                      <AiInsightCard
                        insight={advisoryData?.innovation_insight}
                        loading={advisoryLoading}
                        title="AI Innovation Insight"
                      />
                    </div>
                  </TabsContent>

                </Tabs>
              </CardContent>
            </Card>
          </div>
        )}
      </main>
    </div>
  )
}
