"use client"

import Image from "next/image"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { Search, Compass, BarChart3, Gem, Moon, Sun } from "lucide-react"
import { useTheme } from "next-themes"
import {
    Sidebar,
    SidebarContent,
    SidebarFooter,
    SidebarHeader,
    SidebarMenu,
    SidebarMenuButton,
    SidebarMenuItem,
    SidebarSeparator,
    useSidebar,
} from "@/components/ui/sidebar"
import { Button } from "@/components/ui/button"
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip"
import { cn } from "@/lib/utils"

const NAV_ITEMS = [
    { href: "/lookup", label: "Patent Lookup", icon: Search },
    { href: "/explore", label: "Portfolio Explorer", icon: Compass },
    { href: "/portfolio", label: "Portfolio Analysis", icon: BarChart3 },
    { href: "/hidden-gems", label: "Hidden Gems", icon: Gem },
]

export function AppSidebar() {
    const pathname = usePathname()
    const { theme, setTheme } = useTheme()
    const { state } = useSidebar()
    const isCollapsed = state === "collapsed"

    return (
        <Sidebar collapsible="icon">
            {/* Header: Logo + wordmark */}
            <SidebarHeader className="px-3 py-4">
                <Link href="/" className="flex items-center gap-2 min-w-0">
                    <Image
                        src="/logo.png"
                        width={32}
                        height={32}
                        alt="Patent-IQ"
                        className="rounded-full shrink-0"
                    />
                    {!isCollapsed && (
                        <span className="font-bold text-lg leading-none truncate">Patent-IQ</span>
                    )}
                </Link>
            </SidebarHeader>

            <SidebarContent>
                <SidebarMenu>
                    {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
                        const isActive = pathname?.startsWith(href)

                        const button = (
                            <SidebarMenuButton
                                asChild
                                isActive={isActive}
                                className={cn(
                                    "relative",
                                    isActive && "border-l-2 border-primary rounded-l-none pl-[calc(0.75rem-2px)]"
                                )}
                            >
                                <Link href={href}>
                                    <Icon className="h-4 w-4 shrink-0" />
                                    <span>{label}</span>
                                </Link>
                            </SidebarMenuButton>
                        )

                        return (
                            <SidebarMenuItem key={href}>
                                {isCollapsed ? (
                                    <Tooltip>
                                        <TooltipTrigger asChild>{button}</TooltipTrigger>
                                        <TooltipContent side="right">{label}</TooltipContent>
                                    </Tooltip>
                                ) : (
                                    button
                                )}
                            </SidebarMenuItem>
                        )
                    })}
                </SidebarMenu>
            </SidebarContent>

            <SidebarSeparator />

            <SidebarFooter className="px-3 py-3">
                <Tooltip>
                    <TooltipTrigger asChild>
                        <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
                            className="h-8 w-8"
                        >
                            <Sun className="h-4 w-4 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
                            <Moon className="absolute h-4 w-4 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
                            <span className="sr-only">Toggle theme</span>
                        </Button>
                    </TooltipTrigger>
                    {isCollapsed && <TooltipContent side="right">Toggle theme</TooltipContent>}
                </Tooltip>
            </SidebarFooter>
        </Sidebar>
    )
}
