"use client"

import * as React from "react"
import { Check, Loader2, Search } from "lucide-react"
import { cn } from "@/lib/utils"
import {
    Command,
    CommandEmpty,
    CommandGroup,
    CommandInput,
    CommandItem,
    CommandList,
} from "@/components/ui/command"
import { searchPatents } from "@/lib/api"

interface PatentSearchProps {
    onSelect: (applnId: string) => void
    className?: string
    placeholder?: string
}

interface PatentResult {
    appln_id: number
    appln_title: string
    ep_publn_id_full: string
}

export function PatentSearch({ onSelect, className, placeholder = "Search by publication ID (e.g. EP...)" }: PatentSearchProps) {
    const [open, setOpen] = React.useState(false)
    const [query, setQuery] = React.useState("")
    const [results, setResults] = React.useState<PatentResult[]>([])
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
                const data = await searchPatents(query)
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
            <div className="relative rounded-lg border shadow-sm bg-background">
                <div className="flex items-center px-3" cmdk-input-wrapper="">
                    <Search className="mr-2 h-4 w-4 shrink-0 opacity-50" />
                    <input
                        className="flex h-11 w-full rounded-md bg-transparent py-3 text-sm outline-none placeholder:text-muted-foreground disabled:cursor-not-allowed disabled:opacity-50"
                        placeholder={placeholder}
                        value={query}
                        onChange={(e) => {
                            setQuery(e.target.value)
                            setIsOpen(true)
                        }}
                        onFocus={() => setIsOpen(true)}
                    />
                </div>

                {isOpen && (
                    <div className="absolute top-full left-0 w-full z-50 mt-1 rounded-md border bg-popover text-popover-foreground shadow-md outline-none animate-in fade-in-0 zoom-in-95">
                        <div className="max-h-[300px] overflow-y-auto overflow-x-hidden p-1">
                            {loading && (
                                <div className="py-6 text-center text-sm text-muted-foreground flex justify-center items-center gap-2">
                                    <Loader2 className="h-4 w-4 animate-spin" />
                                    Searching...
                                </div>
                            )}
                            {!loading && query.length >= 2 && results.length === 0 && (
                                <div className="py-6 text-center text-sm text-muted-foreground">No patents found.</div>
                            )}
                            {!loading && query.length < 2 && (
                                <div className="py-2 px-4 text-xs text-muted-foreground text-center">
                                    Type at least 2 characters...
                                </div>
                            )}

                            {!loading && results.length > 0 && (
                                <div className="overflow-hidden p-1 text-foreground">
                                    {results.map((patent) => (
                                        <div
                                            key={patent.appln_id}
                                            className="relative flex cursor-default select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none aria-selected:bg-accent aria-selected:text-accent-foreground hover:bg-accent hover:text-accent-foreground data-[disabled]:pointer-events-none data-[disabled]:opacity-50"
                                            onClick={() => {
                                                onSelect(patent.appln_id.toString())
                                                setQuery(patent.ep_publn_id_full)
                                                setIsOpen(false)
                                            }}
                                        >
                                            <div className="flex flex-col w-full">
                                                <span className="font-medium">{patent.ep_publn_id_full}</span>
                                                <span className="text-xs text-muted-foreground truncate">
                                                    {patent.appln_title}
                                                </span>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                )}
            </div>
        </div>
    )
}
