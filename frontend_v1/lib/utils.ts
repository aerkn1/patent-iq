import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Formats technical strings into readable labels for UI display
 * Examples:
 * - "MODERATE" -> "Moderate"
 * - "ABOVE_AVERAGE" -> "Above Average"
 * - "TOP_25_PERCENT" -> "Top 25%"
 * - "HIGHLY_DIVERSIFIED" -> "Highly Diversified"
 * - "BOTTOM_50%" -> "Bottom 50%"
 */
export function formatLabel(str: string | null | undefined): string {
  if (!str) return ''

  // Handle special cases first
  const specialCases: Record<string, string> = {
    TOP_25_PERCENT: 'Top 25%',
    TOP_10_PERCENT: 'Top 10%',
    TOP_5_PERCENT: 'Top 5%',
    BOTTOM_50: 'Bottom 50%',
    BOTTOM_25: 'Bottom 25%',
    BOTTOM_10: 'Bottom 10%',
    ABOVE_AVERAGE: 'Above Average',
    BELOW_AVERAGE: 'Below Average',
    HIGHLY_DIVERSIFIED: 'Highly Diversified',
    MODERATELY_DIVERSIFIED: 'Moderately Diversified',
    LOW_DIVERSIFIED: 'Low Diversified',
    LOW_UPSIDE: 'Low Upside',
    HIGH_UPSIDE: 'High Upside',
    CRITICAL_ASSET: 'Critical Asset',
    DEFENSIVE_ADVANTAGE: 'Defensive Advantage',
    STABLE: 'Stable',
  }

  // Check if it's a special case
  if (specialCases[str]) {
    return specialCases[str]
  }

  // Handle strings ending with % (like "BOTTOM_50%")
  if (str.includes('%')) {
    const withoutPercent = str.replace('%', '')
    if (specialCases[withoutPercent]) {
      return specialCases[withoutPercent]
    }
  }

  // Convert underscores to spaces and capitalize words
  return str
    .split('_')
    .map((word) => {
      // Capitalize first letter, lowercase the rest
      return word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()
    })
    .join(' ')
}
