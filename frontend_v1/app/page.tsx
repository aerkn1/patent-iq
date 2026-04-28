"use client"

import Link from "next/link"
import Image from "next/image"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Search, Database } from "lucide-react"
import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { getGlobalStats } from "@/lib/api"
import type { GlobalStats } from "@/lib/types/stats"
import { PatentSearch } from "@/components/patent-search"

export default function HomePage() {
  const [stats, setStats] = useState<GlobalStats | null>(null)
  const router = useRouter()

  useEffect(() => {
    getGlobalStats().then(setStats).catch(console.error)
  }, [])

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Image src="/logo.png" width={40} height={40} alt="Patent-IQ" className="rounded-full" />
            <h1 className="text-2xl font-bold">Patent-IQ</h1>
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
          <h1 className="text-6xl font-extrabold mb-4 tracking-tight text-foreground">
            Patent-IQ
          </h1>
          <h2 className="text-5xl font-bold mb-6 text-balance">
            <span className="text-primary">AI-Powered</span> IP Portfolio Intelligence Platform
          </h2>
          <p className="text-xl text-muted-foreground mb-8 text-pretty font-serif">
            Unlock actionable insights across patent portfolios using advanced machine learning and data-driven
            analytics. Identify strengths, benchmark performance, anticipate trends, and support strategic IP decisions
            with precision and confidence.
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
                <PatentSearch
                  className="flex-1"
                  placeholder="Enter patent ID (e.g., EP3123456B1)..."
                  onSelect={(id) => router.push(`/lookup?patentId=${id}`)}
                />
                <Button asChild>
                  <Link href="/lookup">Analyze</Link>
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Stats Grid */}
          <div className="grid grid-cols-3 gap-4 mb-12">
            <Card>
              <CardHeader className="pb-2">
                <CardDescription>Patents Analyzed</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold">
                  {stats ? stats.total_patents.toLocaleString() : "..."}
                </div>
                <p className="text-xs text-muted-foreground">EP & Global dataset</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardDescription>Portfolios</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold">
                  {stats ? stats.total_portfolios.toLocaleString() : "..."}
                </div>
                <p className="text-xs text-muted-foreground">Active owners tracked</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardDescription>ML Models Active</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex flex-col gap-2">
                  <div className="flex items-center gap-2">
                    <div className={`h-2.5 w-2.5 rounded-full ${stats?.models_status?.["3y"] ? "bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]" : "bg-red-500"}`} />
                    <span className="text-sm font-medium">3-Year Horizon</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className={`h-2.5 w-2.5 rounded-full ${stats?.models_status?.["5y"] ? "bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]" : "bg-red-500"}`} />
                    <span className="text-sm font-medium">5-Year Horizon</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Methodology / Trust Section */}
          <div className="mb-12 p-6 bg-muted/30 rounded-xl border border-border">
            <div className="flex items-start gap-4">
              <div className="p-3 bg-primary/10 rounded-lg shrink-0">
                <Database className="h-6 w-6 text-primary" />
              </div>
              <div>
                <h3 className="text-xl font-bold mb-2">ML & Data</h3>
                <p className="text-muted-foreground leading-relaxed">
                  Our insights are generated using advanced Machine Learning models trained on valid citations and examination data.
                  We utilize <strong>EPO PATSTAT</strong> and other online open source resources to provide comprehensive coverage across both <strong>EP and Global scope</strong>.
                  This ensures that our BPI and valuation metrics entail real-world examination evidence rather than just theoretical indicators.
                </p>
              </div>
            </div>
          </div>

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
