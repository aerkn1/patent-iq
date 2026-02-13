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

    if (!loading && !insight && !onGenerate) return null

    const lines = (insight || "").split(/(?<=[.!?])\s+/)
    const previewText = lines.slice(0, 2).join(" ")
    const hasMore = (insight || "").length > previewText.length

    return (
        <div
            className={cn(
                "relative overflow-hidden rounded-lg border",
                "border-primary/20 bg-primary/5",
                "shadow-sm",
                className
            )}
        >
            <div className="absolute inset-0 bg-gradient-to-r from-primary/5 via-transparent to-primary/5 pointer-events-none" />

            <div className="relative p-4">
                <div className="flex items-center gap-2 mb-2">
                    <Sparkles className="h-4 w-4 text-primary shrink-0" />
                    <span className="text-xs font-semibold uppercase tracking-wider text-primary/70">
                        {title}
                    </span>
                </div>

                {loading ? (
                    <div className="flex items-center gap-2 py-2">
                        <Loader2 className="h-4 w-4 animate-spin text-primary" />
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
                            className="h-7 text-xs bg-primary/10 border-primary/20 hover:bg-primary/20 text-primary"
                            onClick={onGenerate}
                        >
                            Generate
                        </Button>
                    </div>
                ) : (
                    <>
                        <p className="text-sm leading-relaxed text-foreground/80 whitespace-pre-wrap">
                            {expanded ? insight : previewText}
                            {!expanded && hasMore && "..."}
                        </p>

                        {hasMore && (
                            <button
                                onClick={() => setExpanded(!expanded)}
                                className="mt-2 flex items-center gap-1 text-xs text-primary hover:text-primary/80 transition-colors"
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
