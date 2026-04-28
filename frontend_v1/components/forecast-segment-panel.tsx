"use client"

import { Card, CardContent } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from "@/components/ui/tooltip"
import { HelpCircle } from "lucide-react"
import type { PortfolioForecastSegments, SegmentItem } from "@/lib/types/forecast"

function clamp01(n: number) {
    if (Number.isNaN(n)) return 0
    if (n < 0) return 0
    if (n > 1) return 1
    return n
}

function SegmentTable({
    items,
    keyLabel,
    keyMonospace,
}: {
    items: SegmentItem[]
    keyLabel: string
    keyMonospace?: boolean
}) {
    if (!items?.length) {
        return <div className="text-sm text-muted-foreground py-4">No segment data available.</div>
    }

    return (
        <div className="border rounded-md overflow-hidden">
            <table className="w-full text-sm">
                <thead>
                    <tr className="bg-muted/50 text-xs">
                        <th className="text-left p-2.5 font-medium">{keyLabel}</th>
                        <th className="text-right p-2.5 font-medium">Expected</th>
                        <th className="text-right p-2.5 font-medium">Interval</th>
                        <th className="text-right p-2.5 font-medium">Share</th>
                    </tr>
                </thead>
                <tbody>
                    {items.map((s) => {
                        const pct = clamp01(s.share) * 100
                        return (
                            <tr key={s.key} className="border-t">
                                <td className={`p-2.5 ${keyMonospace ? "font-mono text-xs" : "text-sm"}`}>
                                    {s.key}
                                </td>
                                <td className="p-2.5 text-right font-semibold">
                                    {s.expected.toFixed(1)}
                                </td>
                                <td className="p-2.5 text-right text-xs text-muted-foreground">
                                    {s.interval_80.low.toFixed(1)}–{s.interval_80.high.toFixed(1)}
                                </td>
                                <td className="p-2.5">
                                    <div className="flex flex-col items-end gap-1">
                                        <div className="text-xs tabular-nums">{pct.toFixed(1)}%</div>
                                        <div className="h-2 w-24 rounded-full overflow-hidden bg-muted">
                                            <div
                                                className="h-full bg-primary"
                                                style={{ width: `${pct}%` }}
                                            />
                                        </div>
                                    </div>
                                </td>
                            </tr>
                        )
                    })}
                </tbody>
            </table>
        </div>
    )
}

export function ForecastSegmentPanel({
    segments,
}: {
    segments?: PortfolioForecastSegments | null
}) {
    const otherLabel = segments?.meta?.other_bucket_label ?? "OTHER"

    return (
        <Card>
            <CardContent className="p-5 space-y-4">
                <div className="flex items-center justify-between gap-4">
                    <div className="flex items-center gap-2">
                        <span className="text-sm font-semibold text-muted-foreground">
                            Where your forecast comes from
                        </span>
                        <TooltipProvider>
                            <Tooltip>
                                <TooltipTrigger className="cursor-help">
                                    <HelpCircle className="h-4 w-4 text-muted-foreground" />
                                </TooltipTrigger>
                                <TooltipContent className="max-w-sm">
                                    Segment totals are computed from owner-share weighted forecast contributions.
                                    CPC segments are allocated proportionally by CPC frequency, with tail folded into
                                    {" "}
                                    <span className="font-semibold">{otherLabel}</span>.
                                </TooltipContent>
                            </Tooltip>
                        </TooltipProvider>
                    </div>

                    {segments?.meta ? (
                        <span className="text-xs text-muted-foreground">
                            top {segments.meta.top_k} + {segments.meta.other_bucket_label}
                        </span>
                    ) : null}
                </div>

                {!segments ? (
                    <div className="text-sm text-muted-foreground">
                        Segment distributions are not available for this portfolio.
                    </div>
                ) : (
                    <Tabs defaultValue="cpc">
                        <TabsList className="h-7">
                            <TabsTrigger value="cpc" className="text-xs px-3 h-6">
                                CPC subclass
                            </TabsTrigger>
                            <TabsTrigger value="jurisdiction" className="text-xs px-3 h-6">
                                Jurisdiction coverage
                            </TabsTrigger>
                            <TabsTrigger value="grants" className="text-xs px-3 h-6">
                                Grant coverage
                            </TabsTrigger>
                            <TabsTrigger value="age" className="text-xs px-3 h-6">
                                Age cohort
                            </TabsTrigger>
                        </TabsList>

                        <TabsContent value="cpc" className="pt-2">
                            <SegmentTable
                                items={segments.by_cpc_subclass}
                                keyLabel="CPC"
                                keyMonospace
                            />
                        </TabsContent>

                        <TabsContent value="jurisdiction" className="pt-2">
                            <SegmentTable
                                items={segments.by_jurisdiction_coverage_bucket}
                                keyLabel="Coverage"
                            />
                        </TabsContent>

                        <TabsContent value="grants" className="pt-2">
                            <SegmentTable
                                items={segments.by_major_office_grant_bucket}
                                keyLabel="Major offices"
                            />
                        </TabsContent>

                        <TabsContent value="age" className="pt-2">
                            <SegmentTable
                                items={segments.by_as_of_year_bucket}
                                keyLabel="As-of year"
                            />
                        </TabsContent>
                    </Tabs>
                )}

                {segments?.meta ? (
                    <div className="text-xs text-muted-foreground">
                        Allocation: {segments.meta.allocation}. CPC limited to top {segments.meta.cpc_top_n_per_patent} per patent; remainder folded into {segments.meta.other_bucket_label}.
                    </div>
                ) : null}
            </CardContent>
        </Card>
    )
}
