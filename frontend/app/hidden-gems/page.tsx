"use client"

import { useState } from "react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { Shield, ArrowLeft, Gem, Search, TrendingUp } from "lucide-react"
import { Progress } from "@/components/ui/progress"

export default function HiddenGemsPage() {
  const [searched, setSearched] = useState(false)
  const [techArea, setTechArea] = useState("G06N")
  const [minBpi, setMinBpi] = useState("70")

  // Mock hidden gems data
  const mockGems = [
    {
      id: "EP3123456B1",
      title: "Neural network pruning method for edge devices",
      applicant: "SmallTech GmbH",
      filingDate: "2018-03-15",
      cpc: "G06N3/08",
      bpi: 87,
      visibility: 22,
      valueGap: 65,
      opportunityScore: 78.5,
      rationale: {
        highBlocking: "This patent has blocked 34 competitors but has only 8 forward citations",
        lowVisibility: [
          "Only 8 forward citations (low academic visibility)",
          "Small family size (2 members)",
          "Small applicant portfolio (12 patents total)",
        ],
      },
      blockingStats: {
        totalBlocks: 34,
        recentBlocks: 9,
        blockedCompanies: ["CompetitorA Corp", "TechStartup GmbH", "InnovateLabs"],
      },
    },
    {
      id: "EP3234567B1",
      title: "Quantum error correction circuit for fault-tolerant computing",
      applicant: "UniversityX",
      filingDate: "2019-07-22",
      cpc: "G06N10/70",
      bpi: 82,
      visibility: 28,
      valueGap: 54,
      opportunityScore: 75.2,
      rationale: {
        highBlocking: "Blocked 28 applications in last 3 years",
        lowVisibility: [
          "Only 2-member family",
          "University applicant (31 patents total)",
          "Limited geographic coverage (EP only)",
        ],
      },
      blockingStats: {
        totalBlocks: 28,
        recentBlocks: 12,
        blockedCompanies: ["QuantumTech Inc", "IBMResearch", "GoogleAI"],
      },
    },
    {
      id: "EP3345678B1",
      title: "Federated learning privacy preservation method",
      applicant: "PrivacyFirst Ltd",
      filingDate: "2020-02-14",
      cpc: "G06N20/00",
      bpi: 79,
      visibility: 31,
      valueGap: 48,
      opportunityScore: 72.8,
      rationale: {
        highBlocking: "High blocking power in emerging privacy-preserving ML space",
        lowVisibility: [
          "Only 6 forward citations",
          "Single jurisdiction filing",
          "Small startup applicant (5 patents)",
        ],
      },
      blockingStats: {
        totalBlocks: 22,
        recentBlocks: 8,
        blockedCompanies: ["DataSafe Corp", "SecureML", "PrivateAI"],
      },
    },
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
              <Gem className="h-6 w-6 text-primary" />
              <h1 className="text-xl font-bold">Hidden Gems Discovery</h1>
            </div>
          </div>
          <nav className="flex items-center gap-6">
            <Link href="/lookup" className="text-sm text-muted-foreground hover:text-foreground">
              Patent Lookup
            </Link>
            <Link href="/portfolio" className="text-sm text-muted-foreground hover:text-foreground">
              Portfolio Analysis
            </Link>
          </nav>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8">
        {/* Intro */}
        <div className="max-w-3xl mb-8">
          <p className="text-lg text-muted-foreground">
            Find patents with <span className="font-semibold text-foreground">high blocking power</span> but{" "}
            <span className="font-semibold text-foreground">low conventional visibility</span>—undervalued acquisition
            opportunities that competitors haven't discovered yet.
          </p>
        </div>

        {/* Filters */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Search Filters</CardTitle>
            <CardDescription>Customize your hidden gems search criteria</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-4 gap-4">
              <div>
                <label className="text-sm font-medium mb-2 block">Technology Area</label>
                <Select value={techArea} onValueChange={setTechArea}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Any">Any</SelectItem>
                    <SelectItem value="G06N">G06N (AI/ML)</SelectItem>
                    <SelectItem value="H01L">H01L (Semiconductors)</SelectItem>
                    <SelectItem value="C12N">C12N (Biotech)</SelectItem>
                    <SelectItem value="A61K">A61K (Pharma)</SelectItem>
                    <SelectItem value="G06F">G06F (Computing)</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div>
                <label className="text-sm font-medium mb-2 block">Min BPI</label>
                <Select value={minBpi} onValueChange={setMinBpi}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="60">60</SelectItem>
                    <SelectItem value="65">65</SelectItem>
                    <SelectItem value="70">70</SelectItem>
                    <SelectItem value="75">75</SelectItem>
                    <SelectItem value="80">80</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div>
                <label className="text-sm font-medium mb-2 block">Max Visibility</label>
                <Select defaultValue="40">
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="30">30</SelectItem>
                    <SelectItem value="35">35</SelectItem>
                    <SelectItem value="40">40</SelectItem>
                    <SelectItem value="45">45</SelectItem>
                    <SelectItem value="50">50</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div>
                <label className="text-sm font-medium mb-2 block">Jurisdiction</label>
                <Select defaultValue="Any">
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Any">Any</SelectItem>
                    <SelectItem value="EP">EP</SelectItem>
                    <SelectItem value="US">US</SelectItem>
                    <SelectItem value="CN">CN</SelectItem>
                    <SelectItem value="JP">JP</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <Button className="w-full mt-4" onClick={() => setSearched(true)}>
              <Search className="mr-2 h-4 w-4" />
              Search Hidden Gems
            </Button>
          </CardContent>
        </Card>

        {!searched ? (
          <div className="text-center py-12">
            <Gem className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-xl font-semibold mb-2">Adjust filters and search for hidden gems</h3>
            <p className="text-muted-foreground">
              Our AI will identify undervalued patents with high strategic blocking power
            </p>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Results Header */}
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-xl font-bold">Found {mockGems.length} Hidden Gems</h3>
                <p className="text-sm text-muted-foreground">Sorted by value gap (BPI - Visibility)</p>
              </div>
              <Button variant="outline">Export Top 20 as CSV</Button>
            </div>

            {/* Results */}
            {mockGems.map((gem, index) => (
              <Card key={gem.id} className="border-2 border-primary/20">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <Badge className="bg-primary">{index + 1}</Badge>
                        <CardTitle className="text-xl">{gem.title}</CardTitle>
                      </div>
                      <CardDescription className="text-base">
                        <span className="font-mono font-semibold">{gem.id}</span> • {gem.applicant}
                      </CardDescription>
                    </div>
                    <Badge variant="outline" className="text-sm">
                      {gem.cpc}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="space-y-6">
                  {/* Scores */}
                  <div className="grid grid-cols-4 gap-4">
                    <div>
                      <div className="text-sm text-muted-foreground mb-1">BPI Score</div>
                      <div className="flex items-baseline gap-1">
                        <div className="text-3xl font-bold text-primary">{gem.bpi}</div>
                        <div className="text-sm text-muted-foreground">/100</div>
                      </div>
                      <Progress value={gem.bpi} className="h-2 mt-2" />
                    </div>

                    <div>
                      <div className="text-sm text-muted-foreground mb-1">Visibility</div>
                      <div className="flex items-baseline gap-1">
                        <div className="text-3xl font-bold">{gem.visibility}</div>
                        <div className="text-sm text-muted-foreground">/100</div>
                      </div>
                      <Progress value={gem.visibility} className="h-2 mt-2" />
                    </div>

                    <div>
                      <div className="text-sm text-muted-foreground mb-1">Value Gap</div>
                      <div className="flex items-baseline gap-1">
                        <div className="text-3xl font-bold text-emerald-600">{gem.valueGap}</div>
                        <div className="text-sm text-muted-foreground">points</div>
                      </div>
                      <Progress value={gem.valueGap} className="h-2 mt-2" />
                    </div>

                    <div>
                      <div className="text-sm text-muted-foreground mb-1">Opportunity</div>
                      <div className="flex items-baseline gap-1">
                        <div className="text-3xl font-bold">{gem.opportunityScore.toFixed(0)}</div>
                        <div className="text-sm text-muted-foreground">/100</div>
                      </div>
                      <Progress value={gem.opportunityScore} className="h-2 mt-2" />
                    </div>
                  </div>

                  {/* Rationale */}
                  <div className="bg-primary/5 border border-primary/20 rounded-lg p-4">
                    <div className="flex items-start gap-3">
                      <TrendingUp className="h-5 w-5 text-primary mt-0.5 flex-shrink-0" />
                      <div>
                        <p className="font-semibold mb-2">Why This is a Hidden Gem:</p>
                        <p className="text-sm text-muted-foreground mb-3">{gem.rationale.highBlocking}</p>
                        <div>
                          <p className="text-sm font-medium mb-2">Low Visibility Factors:</p>
                          <ul className="space-y-1">
                            {gem.rationale.lowVisibility.map((factor, i) => (
                              <li key={i} className="text-sm text-muted-foreground flex items-start gap-2">
                                <span className="text-primary mt-0.5">•</span>
                                <span>{factor}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Blocking Stats */}
                  <div>
                    <h4 className="font-semibold mb-3 flex items-center gap-2">
                      <Shield className="h-4 w-4" />
                      Blocking Activity
                    </h4>
                    <div className="grid grid-cols-3 gap-4">
                      <Card>
                        <CardHeader className="pb-2">
                          <CardDescription>Total Blocks</CardDescription>
                        </CardHeader>
                        <CardContent>
                          <div className="text-2xl font-bold">{gem.blockingStats.totalBlocks}</div>
                        </CardContent>
                      </Card>
                      <Card>
                        <CardHeader className="pb-2">
                          <CardDescription>Recent (24mo)</CardDescription>
                        </CardHeader>
                        <CardContent>
                          <div className="text-2xl font-bold">{gem.blockingStats.recentBlocks}</div>
                        </CardContent>
                      </Card>
                      <Card>
                        <CardHeader className="pb-2">
                          <CardDescription>Key Competitors</CardDescription>
                        </CardHeader>
                        <CardContent>
                          <div className="text-2xl font-bold">{gem.blockingStats.blockedCompanies.length}</div>
                        </CardContent>
                      </Card>
                    </div>
                    <div className="mt-3">
                      <p className="text-sm text-muted-foreground">
                        <span className="font-medium">Blocked companies:</span>{" "}
                        {gem.blockingStats.blockedCompanies.join(", ")}
                      </p>
                    </div>
                  </div>

                  {/* Metadata */}
                  <div className="flex items-center justify-between pt-4 border-t border-border">
                    <div className="flex items-center gap-4 text-sm text-muted-foreground">
                      <span>Filed: {gem.filingDate}</span>
                      <span>•</span>
                      <span>Applicant: {gem.applicant}</span>
                    </div>
                    <div className="flex gap-2">
                      <Button variant="outline" size="sm" asChild>
                        <Link href={`/lookup?id=${gem.id}`}>View Full Analysis</Link>
                      </Button>
                      <Button size="sm">Export Report</Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}

            {/* Load More */}
            <div className="text-center">
              <Button variant="outline">Load More Results</Button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
