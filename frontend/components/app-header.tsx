"use client"

import Image from "next/image"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { Moon, Sun } from "lucide-react"
import { useTheme } from "next-themes"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

const NAV_LINKS = [
    { href: "/lookup", label: "Patent Lookup" },
    { href: "/explore", label: "Portfolio Explorer" },
    { href: "/portfolio", label: "Portfolio Analysis" },
]

export function AppHeader() {
    const pathname = usePathname()
    const { theme, setTheme } = useTheme()

    return (
        <header className="sticky top-0 z-50 border-b border-border bg-card/80 backdrop-blur-md">
            <div className="container mx-auto px-4 py-4">
                <div className="flex items-center justify-between">
                    {/* Logo */}
                    <Link href="/" className="flex items-center gap-2 font-bold text-2xl">
                        <Image src="/logo.png" width={40} height={40} alt="Patent-IQ" className="rounded-full" />
                        Patent-IQ
                    </Link>

                    {/* Right Side: Nav & Actions */}
                    <div className="flex items-center gap-6">
                        {/* Nav Links */}
                        <nav className="hidden md:flex items-center gap-6">
                            {NAV_LINKS.map((link) => {
                                const isActive = pathname?.startsWith(link.href)
                                return (
                                    <Link
                                        key={link.href}
                                        href={link.href}
                                        className={cn(
                                            "text-sm font-medium transition-colors",
                                            isActive
                                                ? "text-foreground"
                                                : "text-muted-foreground hover:text-foreground"
                                        )}
                                    >
                                        {link.label}
                                    </Link>
                                )
                            })}
                        </nav>

                        {/* Theme Toggle */}
                        <div className="flex items-center gap-2">
                            <Button
                                variant="ghost"
                                size="icon"
                                onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
                                className="h-9 w-9"
                            >
                                <Sun className="h-4 w-4 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
                                <Moon className="absolute h-4 w-4 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
                                <span className="sr-only">Toggle theme</span>
                            </Button>
                        </div>
                    </div>
                </div>
            </div>
        </header>
    )
}
