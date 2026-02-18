"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectSeparator,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {

} from "lucide-react"
import { formatLabel } from "@/lib/utils"
import { fetchJson, getPortfolioDiscoverUrl } from "@/lib/api"
import type { PortfolioDiscoverResponse } from "@/lib/types/patent"



export default function PortfolioExplorerPage() {
  const [dimension, setDimension] = useState<"COUNTRY" | "CPC" | "INDUSTRY">("COUNTRY")
  const [selectedCountry, setSelectedCountry] = useState<string>("")
  const [selectedCPC, setSelectedCPC] = useState<string>("")
  const [selectedIndustry, setSelectedIndustry] = useState<string>("")
  const [discoverData, setDiscoverData] = useState<PortfolioDiscoverResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)



  const countries = [
    "AD", "AE", "AG", "AL", "AM", "AO", "AR", "AT", "AU", "AW", "AZ", "BA", "BB", "BD", "BE", "BF", "BG", "BH", "BM", "BN", "BO", "BR", "BS", "BW", "BY", "BZ", "CA", "CH", "CL", "CM", "CN", "CO", "CR", "CU", "CW", "CY", "CZ", "DE", "DK", "DM", "DO", "DZ", "EC", "EE", "EG", "ES", "FI", "FJ", "FR", "GB", "GD", "GE", "GH", "GI", "GR", "GT", "HK", "HN", "HR", "HU", "ID", "IE", "IL", "IN", "IR", "IS", "IT", "JM", "JO", "JP", "KE", "KG", "KH", "KN", "KP", "KR", "KW", "KY", "KZ", "LB", "LC", "LI", "LK", "LT", "LU", "LV", "LY", "MA", "MC", "MD", "ME", "MG", "MK", "MN", "MO", "MT", "MU", "MW", "MX", "MY", "NA", "NG", "NI", "NL", "NO", "NZ", "OM", "PA", "PE", "PG", "PH", "PK", "PL", "PR", "PT", "QA", "RO", "RS", "RU", "SA", "SC", "SD", "SE", "SG", "SI", "SK", "SM", "SV", "SY", "TC", "TH", "TJ", "TM", "TN", "TR", "TT", "TW", "TZ", "UA", "UG", "US", "UY", "UZ", "VC", "VE", "VG", "VN", "WS", "ZA", "ZM", "ZW"
  ]

  // Common CPC codes for dropdown (Top 50 from parquet)
  const cpcCodes = [
    { code: "G06F", label: "G06F - Electric Digital Data Processing" },
    { code: "H04L", label: "H04L - Transmission of Digital Information" },
    { code: "H01L", label: "H01L - Semiconductor Devices" },
    { code: "A61K", label: "A61K - Preparations for Medical, Dental, or Toilet Purposes" },
    { code: "H04W", label: "H04W - Wireless Communication Networks" },
    { code: "G06Q", label: "G06Q - Data Processing Systems or Methods" },
    { code: "H04N", label: "H04N - Pictorial Communication" },
    { code: "A61B", label: "A61B - Diagnosis; Surgery; Identification" },
    { code: "Y02E", label: "Y02E - Reduction of Greenhouse Gas Emissions, Related to Energy" },
    { code: "G06T", label: "G06T - Image Data Processing or Generation" },
    { code: "Y02T", label: "Y02T - Climate Change Mitigation Technologies Related to Transportation" },
    { code: "H01M", label: "H01M - Processes or Means, e.g. Batteries, for the Direct Conversion of Chemical Energy into Electrical Energy" },
    { code: "C07D", label: "C07D - Heterocyclic Compounds" },
    { code: "C12N", label: "C12N - Microorganisms or Enzymes; Compositions Thereof" },
    { code: "B60R", label: "B60R - Vehicles, Vehicle Fittings, or Vehicle Parts, Not Otherwise Provided For" },
    { code: "Y02B", label: "Y02B - Indexing Scheme Relating to Climate Change Mitigation Technologies Related to Buildings" },
    { code: "B60W", label: "B60W - Conjoint Control of Vehicle Sub-Units" },
    { code: "G06N", label: "G06N - Computer Systems Based on Specific Computational Models" },
    { code: "H05K", label: "H05K - Printed Circuits; Casings or Constructional Details of Electric Apparatus" },
    { code: "H04B", label: "H04B - Transmission" },
    { code: "G01N", label: "G01N - Investigating or Analysing Materials by Determining Their Chemical or Physical Properties" },
    { code: "H02J", label: "H02J - Circuit Arrangements or Systems for Spuplying or Distributing Electric Power" },
    { code: "C07C", label: "C07C - Acyclic or Carbocyclic Compounds" },
    { code: "C08L", label: "C08L - Compositions of Macromolecular Compounds" },
    { code: "A61P", label: "A61P - Specific Therapeutic Activity of Chemical Compounds or Medicinal Preparations" },
    { code: "C09K", label: "C09K - Materials for Applications not Otherwise Provided For" },
    { code: "H04M", label: "H04M - Telephonic Communication" },
    { code: "G01S", label: "G01S - Radio Direction-Finding; Radio Navigation; Determining Distance or Velocity by Use of Radio Waves" },
    { code: "F16H", label: "F16H - Gearing" },
    { code: "F02D", label: "F02D - Controlling Combustion Engines" },
    { code: "B60K", label: "B60K - Arrangement or Mounting of Propulsion Units or of Transmissions in Vehicles" },
    { code: "B01D", label: "B01D - Separation" },
    { code: "H02K", label: "H02K - Dynamo-Electric Machines" },
    { code: "A61F", label: "A61F - Filters Implantable into Blood Vessels; Prostheses; Devices Providing Patency to, or Preventing Collapsing of, Tubular Structures of the Body" },
    { code: "G05B", label: "G05B - Monitoring or Testing Arrangements" },
    { code: "C08G", label: "C08G - Macromolecular Compounds Obtained by Reactions Otherwise Than By Carbon-to-Carbon Unsaturated Bonds" },
    { code: "H01R", label: "H01R - Electrically-Conductive Connections" },
    { code: "F21S", label: "F21S - Non-Portable Lighting Devices" },
    { code: "G01R", label: "G01R - Measuring Electric Variables; Measuring Magnetic Variables" },
    { code: "G02B", label: "G02B - Optical Elements, Systems, or Apparatus" },
    { code: "B01J", label: "B01J - Chemical or Physical Processes, e.g. Catalysis or Colloid Chemistry; Their Relevant Apparatus" },
    { code: "G02F", label: "G02F - Devices or Arrangements, the Optical Operation of Which is Modified by Changing the Optical Properties of the Medium of the Devices or Arrangements" },
    { code: "G01C", label: "G01C - Measuring Distances, Levels or Bearings; Surveying; Navigation; Gyroscopic Instruments; Photogrammetry or Videogrammetry" },
    { code: "A61M", label: "A61M - Devices for Introducing Media into or Drawing Media from the Body" },
    { code: "C08F", label: "C08F - Macromolecular Compounds Obtained by Reactions Only Involving Carbon-to-Carbon Unsaturated Bonds" },
    { code: "Y02P", label: "Y02P - Climate Change Mitigation Technologies Related to Production or Processing of Goods" },
    { code: "G09G", label: "G09G - Arrangements or Circuits for Control of Indicating Devices Using Static Means to Present Variable Information" },
    { code: "A63F", label: "A63F - Card, Board, or Roulette Games; Indoor Games Using Small Moving Playing Bodies; Video Games; Games not Otherwise Provided For" },
    { code: "G06K", label: "G06K - Recognition of Data; Presentation of Data; Record Carriers; Handling Record Carriers" },
    { code: "F01N", label: "F01N - Gas-Flow Silencers or Exhaust Apparatus for Machines or Engines in General" }
  ]

  // Industry codes for dropdown
  const industries = [
    { code: "ANALYSIS_OF_BIOLOGICAL_MATERIALS", label: "Analysis Of Biological Materials" },
    { code: "AUDIO_VISUAL_TECHNOLOGY", label: "Audio Visual Technology" },
    { code: "BASIC_COMMUNICATION_PROCESSES", label: "Basic Communication Processes" },
    { code: "BASIC_MATERIALS_CHEMISTRY", label: "Basic Materials Chemistry" },
    { code: "BIOTECHNOLOGY", label: "Biotechnology" },
    { code: "CHEMICAL_ENGINEERING", label: "Chemical Engineering" },
    { code: "CIVIL_ENGINEERING", label: "Civil Engineering" },
    { code: "COMPUTER_TECHNOLOGY", label: "Computer Technology" },
    { code: "CONTROL", label: "Control" },
    { code: "DIGITAL_COMMUNICATION", label: "Digital Communication" },
    { code: "ELECTRICAL_MACHINERY_APPARATUS_ENERGY", label: "Electrical Machinery Apparatus Energy" },
    { code: "ENGINES_PUMPS_TURBINES", label: "Engines Pumps Turbines" },
    { code: "ENVIRONMENTAL_TECHNOLOGY", label: "Environmental Technology" },
    { code: "FOOD_CHEMISTRY", label: "Food Chemistry" },
    { code: "FURNITURE_GAMES", label: "Furniture Games" },
    { code: "HANDLING", label: "Handling" },
    { code: "IT_METHODS_FOR_MANAGEMENT", label: "It Methods For Management" },
    { code: "MACHINE_TOOLS", label: "Machine Tools" },
    { code: "MACROMOLECULAR_CHEMISTRY_POLYMERS", label: "Macromolecular Chemistry Polymers" },
    { code: "MATERIALS_METALLURGY", label: "Materials Metallurgy" },
    { code: "MEASUREMENT", label: "Measurement" },
    { code: "MECHANICAL_ELEMENTS", label: "Mechanical Elements" },
    { code: "MEDICAL_TECHNOLOGY", label: "Medical Technology" },
    { code: "MICRO_STRUCTURAL_AND_NANO_TECHNOLOGY", label: "Micro Structural And Nano Technology" },
    { code: "OPTICS", label: "Optics" },
    { code: "ORGANIC_FINE_CHEMISTRY", label: "Organic Fine Chemistry" },
    { code: "OTHER_CONSUMER_GOODS", label: "Other Consumer Goods" },
    { code: "OTHER_SPECIAL_MACHINES", label: "Other Special Machines" },
    { code: "PHARMACEUTICALS", label: "Pharmaceuticals" },
    { code: "SEMICONDUCTORS", label: "Semiconductors" },
    { code: "SURFACE_TECHNOLOGY_COATING", label: "Surface Technology Coating" },
    { code: "TELECOMMUNICATIONS", label: "Telecommunications" },
    { code: "TEXTILE_AND_PAPER_MACHINES", label: "Textile And Paper Machines" },
    { code: "THERMAL_PROCESSES_AND_APPARATUS", label: "Thermal Processes And Apparatus" },
    { code: "TRANSPORT", label: "Transport" },
  ]

  const topCountries = ["US", "CN", "JP", "DE", "KR", "GB", "FR", "IN", "CA", "IT"]
  const restCountries = countries
    .filter((country) => !topCountries.includes(country))
    .slice()
    .sort()

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
                  <SelectGroup>
                    <SelectLabel>Top Countries</SelectLabel>
                    {topCountries.map((country) => (
                      <SelectItem key={country} value={country}>
                        {country}
                      </SelectItem>
                    ))}
                  </SelectGroup>
                  <SelectSeparator />
                  <SelectGroup>
                    <SelectLabel>All Countries</SelectLabel>
                    {restCountries.map((country) => (
                      <SelectItem key={country} value={country}>
                        {country}
                      </SelectItem>
                    ))}
                  </SelectGroup>
                </SelectContent>
              </Select>
            )}

            {/* CPC Selector */}
            {dimension === "CPC" && (
              <Select value={selectedCPC} onValueChange={setSelectedCPC}>
                <SelectTrigger className="w-[200px]">
                  <SelectValue placeholder="Select CPC Code" />
                </SelectTrigger>
                <SelectContent>
                  {cpcCodes.map((cpc) => (
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
                <SelectTrigger className="w-[240px]">
                  <SelectValue placeholder="Select Industry" />
                </SelectTrigger>
                <SelectContent>
                  {industries.map((industry) => (
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
                    <th className="text-right p-3 text-sm font-medium">Avg Power</th>
                    <th className="text-right p-3 text-sm font-medium">Total Power</th>
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
                      <td className="p-3 text-sm text-right font-medium">
                        {owner.adjusted_power_score?.toFixed(1) ?? "-"}
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

