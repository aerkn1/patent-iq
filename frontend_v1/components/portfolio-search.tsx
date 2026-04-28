"use client"

import * as React from "react"
import { Check, Loader2 } from "lucide-react"
import { cn } from "@/lib/utils"
import {
    Command,
    CommandEmpty,
    CommandGroup,
    CommandInput,
    CommandItem,
    CommandList,
} from "@/components/ui/command"
import { searchPortfolios } from "@/lib/api"

interface PortfolioSearchProps {
    onSelect: (ownerId: string) => void
    className?: string
    placeholder?: string
}

interface PortfolioResult {
    owner_id: number
    owner_name: string
    country?: string
    n_patents?: number
    portfolio_power_pct?: number
    portfolio_tier?: string
}

export function PortfolioSearch({ onSelect, className, placeholder = "Search portfolios..." }: PortfolioSearchProps) {
    const [open, setOpen] = React.useState(false)
    const [value, setValue] = React.useState("")
    const [query, setQuery] = React.useState("")
    const [results, setResults] = React.useState<PortfolioResult[]>([])
    const [loading, setLoading] = React.useState(false)

    // Debounce search
    React.useEffect(() => {
        if (!query || query.length < 2) {
            setResults([])
            return
        }

        const timer = setTimeout(async () => {
            setLoading(true)
            try {
                const data = await searchPortfolios(query)
                // Ensure data.results is an array
                setResults((data as any).results || [])
            } catch (error) {
                console.error("Search failed:", error)
                setResults([])
            } finally {
                setLoading(false)
            }
        }, 300)

        return () => clearTimeout(timer)
    }, [query])

    const [isOpen, setIsOpen] = React.useState(false)
    const commandRef = React.useRef<HTMLDivElement>(null)

    React.useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (commandRef.current && !commandRef.current.contains(event.target as Node)) {
                setIsOpen(false)
            }
        }
        document.addEventListener("mousedown", handleClickOutside)
        return () => document.removeEventListener("mousedown", handleClickOutside)
    }, [])

    return (
        <div className={cn("relative w-full", className)} ref={commandRef}>
            <Command
                shouldFilter={false}
                className="rounded-lg border shadow-sm overflow-visible bg-background"
            >
                <CommandInput
                    placeholder={placeholder}
                    value={query}
                    onValueChange={(val) => {
                        setQuery(val)
                        setIsOpen(true)
                    }}
                    onFocus={() => setIsOpen(true)}
                />

                {isOpen && (
                    <div className="absolute top-full left-0 w-full z-50 mt-1">
                        <CommandList className="rounded-lg border shadow-md bg-popover text-popover-foreground animate-in fade-in-0 zoom-in-95">
                            {loading && (
                                <div className="py-6 text-center text-sm text-muted-foreground flex justify-center items-center gap-2">
                                    <Loader2 className="h-4 w-4 animate-spin" />
                                    Searching...
                                </div>
                            )}
                            {!loading && query.length >= 2 && results.length === 0 && (
                                <CommandEmpty>No portfolios found.</CommandEmpty>
                            )}
                            {!loading && query.length < 2 && (
                                <div className="py-2 px-4 text-xs text-muted-foreground text-center">
                                    Type at least 2 characters...
                                </div>
                            )}

                            <CommandGroup>
                                {!loading && results.map((portfolio) => (
                                    <CommandItem
                                        key={portfolio.owner_id}
                                        value={portfolio.owner_id.toString()}
                                        onSelect={() => {
                                            onSelect(portfolio.owner_id.toString())
                                            setQuery(portfolio.owner_name) // Update input to selected name?
                                            setIsOpen(false)
                                        }}
                                        className="cursor-pointer"
                                    >
                                        <Check
                                            className={cn(
                                                "mr-2 h-4 w-4",
                                                // Check logic is a bit weird here if we don't have 'value' prop passed in correctly or managed state
                                                // Assuming we don't need persistent checkmarks for this search-and-go style
                                                "opacity-0"
                                            )}
                                        />
                                        <div className="flex flex-col">
                                            <span className="font-medium">{portfolio.owner_name}</span>
                                            <div className="flex gap-2 text-xs text-muted-foreground">
                                                {portfolio.country && <span>{portfolio.country}</span>}
                                                {portfolio.n_patents && <span>• {portfolio.n_patents} patents</span>}
                                                {portfolio.portfolio_tier && <span>• {portfolio.portfolio_tier}</span>}
                                            </div>
                                        </div>
                                    </CommandItem>
                                ))}
                            </CommandGroup>
                        </CommandList>
                    </div>
                )}
            </Command>
        </div>
    )
}
