"use client"

import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"

/** Format tier strings like "ABOVE_AVERAGE" → "Above Average" */
function formatTierLabel(tier: string): string {
    return tier
        .replace(/_/g, " ")
        .toLowerCase()
        .replace(/\b\w/g, (c) => c.toUpperCase())
}

const POSITIVE_KEYWORDS = [
    "HIGH", "STRONG", "ABOVE_AVERAGE", "RISING", "GROWING",
    "STRONGLY_MAINTAINED", "HIGHLY_DIVERSIFIED", "EARLY", "FAST",
]

const NEGATIVE_KEYWORDS = [
    "LOW", "WEAK", "BELOW_AVERAGE", "DECLINING", "SHRINKING",
    "POORLY_MAINTAINED", "NOT_MAINTAINED", "CONCENTRATED", "LATE", "SLOW",
]

const MODERATE_KEYWORDS = [
    "MODERATE", "AVERAGE", "MODERATELY_MAINTAINED", "MODERATELY_DIVERSIFIED",
    "STEADY", "STABLE", "MID",
]

function getTierVariant(tier: string): "positive" | "negative" | "moderate" | "neutral" {
    const upper = tier.toUpperCase()
    if (POSITIVE_KEYWORDS.some((kw) => upper.includes(kw))) return "positive"
    if (NEGATIVE_KEYWORDS.some((kw) => upper.includes(kw))) return "negative"
    if (MODERATE_KEYWORDS.some((kw) => upper.includes(kw))) return "moderate"
    return "neutral"
}

const variantStyles: Record<string, string> = {
    positive: "bg-emerald-100 text-emerald-800 border-emerald-300 dark:bg-emerald-900/30 dark:text-emerald-300 dark:border-emerald-700",
    negative: "bg-red-100 text-red-800 border-red-300 dark:bg-red-900/30 dark:text-red-300 dark:border-red-700",
    moderate: "bg-amber-100 text-amber-800 border-amber-300 dark:bg-amber-900/30 dark:text-amber-300 dark:border-amber-700",
    neutral: "bg-gray-100 text-gray-700 border-gray-300 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-600",
}

interface TierBadgeProps {
    tier: string
    className?: string
    size?: "sm" | "md" | "lg"
}

export function TierBadge({ tier, className, size = "sm" }: TierBadgeProps) {
    const variant = getTierVariant(tier)
    const sizeStyles = {
        sm: "",
        md: "text-sm px-3 py-1",
        lg: "text-base px-4 py-2",
    }

    return (
        <Badge
            variant="outline"
            className={cn(variantStyles[variant], sizeStyles[size], className)}
        >
            {formatTierLabel(tier)}
        </Badge>
    )
}
