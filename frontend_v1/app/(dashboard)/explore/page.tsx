"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import {

} from "lucide-react"
import { formatLabel } from "@/lib/utils"
import { fetchJson, getPortfolioDiscoverUrl } from "@/lib/api"
import type { PortfolioDiscoverResponse } from "@/lib/types/patent"
import { COUNTRIES, CPC_CODES, INDUSTRIES } from "@/lib/constants"



export default function PortfolioExplorerPage() {
  const [dimension, setDimension] = useState<"COUNTRY" | "CPC" | "INDUSTRY">("COUNTRY")
  const [selectedCountry, setSelectedCountry] = useState<string>("")
  const [selectedCPC, setSelectedCPC] = useState<string>("")
  const [selectedIndustry, setSelectedIndustry] = useState<string>("")
  const [discoverData, setDiscoverData] = useState<PortfolioDiscoverResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)



  // Fetch discover data based on dimension and value
  const fetchDiscoverData = async (dim: "COUNTRY" | "CPC" | "INDUSTRY", value: string) => {
    if (!value.trim()) {
      setDiscoverData(null)
      return
    }

    setLoading(true)
    setError(null)
    try {
      const data = await fetchJson<PortfolioDiscoverResponse>(getPortfolioDiscoverUrl(dim, value, 20))
      setDiscoverData(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch data")
      setDiscoverData(null)
    } finally {
      setLoading(false)
    }
  }

  // Fetch when dimension or value changes
  useEffect(() => {
    if (dimension === "COUNTRY" && selectedCountry) {
      fetchDiscoverData("COUNTRY", selectedCountry)
    } else if (dimension === "CPC" && selectedCPC) {
      fetchDiscoverData("CPC", selectedCPC)
    } else if (dimension === "INDUSTRY" && selectedIndustry) {
      fetchDiscoverData("INDUSTRY", selectedIndustry)
    } else {
      setDiscoverData(null)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dimension, selectedCountry, selectedCPC, selectedIndustry])

  // Reset selections when dimension changes
  useEffect(() => {
    setSelectedCountry("")
    setSelectedCPC("")
    setSelectedIndustry("")
    setDiscoverData(null)
  }, [dimension])

  return (
    <>


      {/* Portfolio Discovery */}
      <Card>
        <CardHeader>
          <CardTitle>Portfolio Discovery</CardTitle>
          <CardDescription>Explore top owners by classification metric</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-4 mb-6">
            {/* Dimension Selector */}
            <Select value={dimension} onValueChange={(v) => setDimension(v as "COUNTRY" | "CPC" | "INDUSTRY")}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Classification" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="COUNTRY">Country</SelectItem>
                <SelectItem value="CPC">CPC Code</SelectItem>
                <SelectItem value="INDUSTRY">Industry</SelectItem>
              </SelectContent>
            </Select>

            {/* Country Selector */}
            {dimension === "COUNTRY" && (
              <Select value={selectedCountry} onValueChange={setSelectedCountry}>
                <SelectTrigger className="w-[200px]">
                  <SelectValue placeholder="Select Country" />
                </SelectTrigger>
                <SelectContent>
                  {COUNTRIES.map((country) => (
                    <SelectItem key={country} value={country}>
                      {country}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}

            {/* CPC Selector */}
            {dimension === "CPC" && (
              <Select value={selectedCPC} onValueChange={setSelectedCPC}>
                <SelectTrigger className="w-[400px]">
                  <SelectValue placeholder="Select CPC Code" />
                </SelectTrigger>
                <SelectContent>
                  {CPC_CODES.map((cpc) => (
                    <SelectItem key={cpc.code} value={cpc.code}>
                      {cpc.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}

            {/* Industry Selector */}
            {dimension === "INDUSTRY" && (
              <Select value={selectedIndustry} onValueChange={setSelectedIndustry}>
                <SelectTrigger className="w-[400px]">
                  <SelectValue placeholder="Select Industry" />
                </SelectTrigger>
                <SelectContent>
                  {INDUSTRIES.map((industry) => (
                    <SelectItem key={industry.code} value={industry.code}>
                      {industry.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          </div>

          {loading && (
            <div className="text-center text-muted-foreground py-12">
              Loading rankings...
            </div>
          )}

          {error && (
            <div className="text-center text-red-600 py-12">
              Error: {error}
            </div>
          )}

          {!loading && !error && discoverData && discoverData.results.length > 0 && (
            <div className="border rounded-lg overflow-hidden">
              <table className="w-full">
                <thead className="bg-muted/50">
                  <tr>
                    <th className="text-left p-3 text-sm font-medium">Rank</th>
                    <th className="text-left p-3 text-sm font-medium">Owner Name</th>
                    <th className="text-right p-3 text-sm font-medium">Patents</th>
                    <th className="text-right p-3 text-sm font-medium">Power %</th>
                    <th className="text-center p-3 text-sm font-medium">Tier</th>
                    <th className="text-center p-3 text-sm font-medium">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {discoverData.results.map((owner) => (
                    <tr key={owner.owner_id} className="border-t border-border hover:bg-muted/30">
                      <td className="p-3 text-sm font-medium">{owner.rank}</td>
                      <td className="p-3 text-sm">{owner.owner_name}</td>
                      <td className="p-3 text-sm text-right">{owner.n_patents.toLocaleString()}</td>
                      <td className="p-3 text-sm text-right font-medium">
                        {owner.portfolio_power_pct.toFixed(1)}%
                      </td>
                      <td className="p-3 text-center">
                        <Badge variant="outline">{formatLabel(owner.portfolio_tier)}</Badge>
                      </td>
                      <td className="p-3 text-center">
                        <Button
                          size="sm"
                          asChild
                          className="bg-red-600 hover:bg-red-700 text-white"
                        >
                          <Link
                            href={`/portfolio?ownerId=${owner.owner_id}`}
                            target="_blank"
                            rel="noopener noreferrer"
                          >
                            View Portfolio
                          </Link>
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {!loading && !error && !discoverData && (
            <div className="text-center text-muted-foreground py-12">
              {dimension === "COUNTRY" && "Please select a country to view rankings"}
              {dimension === "CPC" && "Please select a CPC code to view rankings"}
              {dimension === "INDUSTRY" && "Please select an industry to view rankings"}
            </div>
          )}

          {!loading && !error && discoverData && discoverData.results.length === 0 && (
            <div className="text-center text-muted-foreground py-12">
              No results found for the selected {dimension === "COUNTRY" ? "country" : dimension === "CPC" ? "CPC code" : "industry"}
            </div>
          )}
        </CardContent>
      </Card>

    </>
  )
}

