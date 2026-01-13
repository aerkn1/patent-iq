import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Shield, TrendingUp, Gem, Brain, ArrowRight, Search } from "lucide-react"

export default function HomePage() {
  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Shield className="h-8 w-8 text-primary" />
            <h1 className="text-2xl font-bold">Patent Intelligence</h1>
          </div>
          <nav className="flex items-center gap-6">
            <Link href="/lookup" className="text-sm text-muted-foreground hover:text-foreground">
              Patent Lookup
            </Link>
            <Link href="/explore" className="text-sm text-muted-foreground hover:text-foreground">
              Portfolio Explorer
            </Link>
            <Link href="/portfolio" className="text-sm text-muted-foreground hover:text-foreground">
              Portfolio Analysis
            </Link>
            <Link href="/hidden-gems" className="text-sm text-muted-foreground hover:text-foreground">
              Hidden Gems
            </Link>
            <Button size="sm">Sign in</Button>
          </nav>
        </div>
      </header>

      {/* Hero Section */}
      <section className="container mx-auto px-4 py-16">
        <div className="max-w-4xl">
          <div className="inline-block px-3 py-1 mb-6 text-xs font-medium bg-primary/10 text-primary rounded-full">
            Powered by AI • EPO CodeFest 2026
          </div>
          <h2 className="text-5xl font-bold mb-6 text-balance">
            The first AI-powered platform to <span className="text-primary">predict patent blocking power</span>
          </h2>
          <p className="text-xl text-muted-foreground mb-8 text-pretty">
            Quantify blocking power using EPO examination evidence. Discover undervalued patents with high strategic
            value through automated AI-driven analysis.
          </p>

          {/* Quick Search */}
          <Card className="mb-12">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Search className="h-5 w-5" />
                Quick Patent Lookup
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex gap-2">
                <Input placeholder="Enter patent ID (e.g., EP3123456B1, US10123456B2)" className="flex-1" />
                <Button asChild>
                  <Link href="/lookup">Analyze</Link>
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Stats Grid */}
          <div className="grid grid-cols-4 gap-4 mb-12">
            <Card>
              <CardHeader className="pb-2">
                <CardDescription>Patents Analyzed</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold">8.7M</div>
                <p className="text-xs text-muted-foreground">2015-2024 dataset</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardDescription>Blocking Events</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold">500K+</div>
                <p className="text-xs text-muted-foreground">X/Y citations tracked</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardDescription>ML Models</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold">3</div>
                <p className="text-xs text-muted-foreground">Production deployed</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardDescription>Model Accuracy</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold">94.2%</div>
                <p className="text-xs text-muted-foreground">AUC-ROC score</p>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="container mx-auto px-4 py-16 border-t border-border">
        <h3 className="text-3xl font-bold mb-12">Key Features</h3>
        <div className="grid md:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <div className="flex items-center gap-3 mb-2">
                <div className="p-2 bg-primary/10 rounded-lg">
                  <Shield className="h-6 w-6 text-primary" />
                </div>
                <CardTitle>Blocking Power Index (BPI)</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <CardDescription className="text-base">
                Quantify a patent's ability to block competitors based on historical X/Y citations in EPO examination
                proceedings. Novel 0-100 scale metric combining block count, recency, severity, and ML predictions.
              </CardDescription>
              <Button variant="outline" size="sm" className="mt-4 bg-transparent" asChild>
                <Link href="/lookup">
                  Try BPI Analysis <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <div className="flex items-center gap-3 mb-2">
                <div className="p-2 bg-primary/10 rounded-lg">
                  <TrendingUp className="h-6 w-6 text-primary" />
                </div>
                <CardTitle>Automated IPscore (A-B-C-D)</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <CardDescription className="text-base">
                4-dimensional patent valuation: Legal Strength (A), Technology Strength (B), Market Strength (C), and
                Numeric Indicators (D). AI-powered scoring replaces weeks of manual due diligence.
              </CardDescription>
              <Button variant="outline" size="sm" className="mt-4 bg-transparent" asChild>
                <Link href="/portfolio">
                  Analyze Portfolio <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <div className="flex items-center gap-3 mb-2">
                <div className="p-2 bg-primary/10 rounded-lg">
                  <Gem className="h-6 w-6 text-primary" />
                </div>
                <CardTitle>Hidden Gems Discovery</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <CardDescription className="text-base">
                AI discovers patents with high blocking power but low conventional visibility. Find undervalued
                acquisition targets before competitors.
              </CardDescription>
              <Button variant="outline" size="sm" className="mt-4 bg-transparent" asChild>
                <Link href="/hidden-gems">
                  Discover Gems <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <div className="flex items-center gap-3 mb-2">
                <div className="p-2 bg-primary/10 rounded-lg">
                  <Brain className="h-6 w-6 text-primary" />
                </div>
                <CardTitle>AI Explanations</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <CardDescription className="text-base">
                LLM-generated insights and recommendations for every patent. Understand complex patent landscapes in
                plain English.
              </CardDescription>
              <Button variant="outline" size="sm" className="mt-4 bg-transparent" asChild>
                <Link href="/lookup">
                  See Example <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* CTA Section */}
      <section className="container mx-auto px-4 py-16 border-t border-border">
        <div className="max-w-3xl mx-auto text-center">
          <h3 className="text-3xl font-bold mb-4">Ready to get started?</h3>
          <p className="text-lg text-muted-foreground mb-8">
            Analyze your first patent or discover hidden gems in your portfolio.
          </p>
          <div className="flex gap-4 justify-center">
            <Button size="lg" asChild>
              <Link href="/lookup">Start Analysis</Link>
            </Button>
            <Button size="lg" variant="outline" asChild>
              <Link href="/hidden-gems">Find Hidden Gems</Link>
            </Button>
          </div>
        </div>
      </section>
    </div>
  )
}
