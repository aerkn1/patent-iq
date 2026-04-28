"use client"

import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import type { TopContributor, DifficultyBucket } from "@/lib/types/forecast"

const BUCKET_STYLES: Record<DifficultyBucket, string> = {
    LOW: "bg-emerald-100 text-emerald-700 border-emerald-200",
    MID: "bg-amber-100 text-amber-700 border-amber-200",
    HIGH: "bg-rose-100 text-rose-700 border-rose-200",
}

interface TopContributorsTableProps {
    contributors: TopContributor[]
}

export function TopContributorsTable({ contributors }: TopContributorsTableProps) {
    if (!contributors.length) return null

    return (
        <Card>
            <CardContent className="p-5 space-y-3">
                <div className="flex items-center justify-between">
                    <span className="text-sm font-semibold text-muted-foreground">
                        Top Contributors
                    </span>
                    <span className="text-xs text-muted-foreground">
                        Top {contributors.length} patents by expected contribution
                    </span>
                </div>

                <div className="border rounded-md overflow-hidden">
                    <table className="w-full text-sm">
                        <thead>
                            <tr className="bg-muted/50 text-xs">
                                <th className="text-left p-2.5 font-medium">#</th>
                                <th className="text-left p-2.5 font-medium">Patent ID</th>
                                <th className="text-right p-2.5 font-medium">Contribution</th>
                                <th className="text-right p-2.5 font-medium">Expected</th>
                                <th className="text-right p-2.5 font-medium">Interval</th>
                                <th className="text-right p-2.5 font-medium">Share</th>
                                <th className="text-center p-2.5 font-medium">Difficulty</th>
                            </tr>
                        </thead>
                        <tbody>
                            {contributors.map((c, idx) => (
                                <tr
                                    key={c.appln_id}
                                    className="border-t hover:bg-muted/30 transition-colors cursor-pointer"
                                    onClick={() => {
                                        window.location.href = `/lookup?patentId=${c.appln_id}`
                                    }}
                                >
                                    <td className="p-2.5 text-muted-foreground text-xs">{idx + 1}</td>
                                    <td className="p-2.5 font-mono text-xs">{c.appln_id}</td>
                                    <td className="p-2.5 text-right font-semibold">
                                        {c.contribution.toFixed(2)}
                                    </td>
                                    <td className="p-2.5 text-right">{c.expected.toFixed(2)}</td>
                                    <td className="p-2.5 text-right text-xs text-muted-foreground">
                                        {c.interval_80.low.toFixed(1)}–{c.interval_80.high.toFixed(1)}
                                    </td>
                                    <td className="p-2.5 text-right text-xs">
                                        {(c.owner_share * 100).toFixed(0)}%
                                    </td>
                                    <td className="p-2.5 text-center">
                                        <Badge
                                            variant="outline"
                                            className={`text-[10px] ${BUCKET_STYLES[c.difficulty_bucket]}`}
                                        >
                                            {c.difficulty_bucket}
                                        </Badge>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </CardContent>
        </Card>
    )
}
