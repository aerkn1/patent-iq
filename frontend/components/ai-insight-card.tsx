"use client"

import * as React from "react"
import { cn } from "@/lib/utils"
import { Sparkles, ChevronDown, ChevronUp, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"

interface AiInsightCardProps {
    insight: string | null | undefined
    loading?: boolean
    title?: string
    className?: string
    onGenerate?: () => void
}

export function AiInsightCard({
    insight,
    loading = false,
    title = "AI Insight",
    className,
    onGenerate,
}: AiInsightCardProps) {
    const [expanded, setExpanded] = React.useState(false)

    // If no insight, no loading, and no generation handler, don't render anything (legacy behavior)
    if (!loading && !insight && !onGenerate) return null

    const lines = (insight || "").split(/(?<=[.!?])\s+/)
    const previewText = lines.slice(0, 2).join(" ")
    const hasMore = (insight || "").length > previewText.length

    return (
        <div
            className={cn(
                "relative overflow-hidden rounded-lg border border-purple-500/20",
                "bg-gradient-to-br from-purple-950/40 via-slate-900/60 to-indigo-950/40",
                "backdrop-blur-sm shadow-lg shadow-purple-500/5",
                className
            )}
        >
            <div className="absolute inset-0 bg-gradient-to-r from-purple-500/5 via-transparent to-indigo-500/5 pointer-events-none" />

            <div className="relative p-4">
                <div className="flex items-center gap-2 mb-2">
                    <Sparkles className="h-4 w-4 text-purple-400 shrink-0" />
                    <span className="text-xs font-semibold uppercase tracking-wider text-purple-300/80">
                        {title}
                    </span>
                </div>

                {loading ? (
                    <div className="flex items-center gap-2 py-2">
                        <Loader2 className="h-4 w-4 animate-spin text-purple-400" />
                        <span className="text-sm text-muted-foreground">Generating insight...</span>
                    </div>
                ) : !insight && onGenerate ? (
                    <div className="flex flex-col items-start gap-3 py-2">
                        <p className="text-xs text-muted-foreground">
                            Generate specific insights for this section using AI.
                        </p>
                        <Button
                            size="sm"
                            variant="outline"
                            className="h-7 text-xs bg-purple-500/10 border-purple-500/20 hover:bg-purple-500/20 text-purple-300"
                            onClick={onGenerate}
                        >
                            Generate
                        </Button>
                    </div>
                ) : (
                    <>
                        <p className="text-sm leading-relaxed text-slate-200/90 whitespace-pre-wrap">
                            {expanded ? insight : previewText}
                            {!expanded && hasMore && "..."}
                        </p>

                        {hasMore && (
                            <button
                                onClick={() => setExpanded(!expanded)}
                                className="mt-2 flex items-center gap-1 text-xs text-purple-400 hover:text-purple-300 transition-colors"
                            >
                                {expanded ? (
                                    <>
                                        <ChevronUp className="h-3 w-3" />
                                        Show less
                                    </>
                                ) : (
                                    <>
                                        <ChevronDown className="h-3 w-3" />
                                        Read more
                                    </>
                                )}
                            </button>
                        )}
                    </>
                )}
            </div>
        </div>
    )
}
