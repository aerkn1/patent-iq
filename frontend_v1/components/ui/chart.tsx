'use client'

import * as React from 'react'
import { cn } from '@/lib/utils'

// Stub — recharts dependency removed; this file is retained for type compatibility only.
// No components from this file are in use; all charts have been migrated to @nivo.

export type ChartConfig = {
  [k in string]: {
    label?: React.ReactNode
    icon?: React.ComponentType
    color?: string
  }
}

function ChartContainer({
  className,
  children,
  ...props
}: React.ComponentProps<'div'> & { config?: ChartConfig; children?: React.ReactNode }) {
  return (
    <div data-slot="chart" className={cn('flex aspect-video justify-center text-xs', className)} {...props}>
      {children}
    </div>
  )
}

function ChartTooltipContent({ className }: React.ComponentProps<'div'>) {
  return <div className={cn('border bg-background p-2 rounded text-xs shadow', className)} />
}

function ChartLegendContent({ className }: React.ComponentProps<'div'>) {
  return <div className={cn('flex items-center gap-4', className)} />
}

const ChartTooltip = ChartTooltipContent
const ChartLegend = ChartLegendContent

function ChartStyle(_: { id: string; config: ChartConfig }) {
  return null
}

export {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  ChartLegend,
  ChartLegendContent,
  ChartStyle,
}
