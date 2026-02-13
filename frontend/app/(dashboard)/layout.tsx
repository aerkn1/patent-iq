import type React from "react"
import { ThemeProvider } from "@/components/theme-provider"
import { TooltipProvider } from "@/components/ui/tooltip"
import { AppHeader } from "@/components/app-header"

export default function DashboardLayout({
    children,
}: Readonly<{
    children: React.ReactNode
}>) {
    return (
        <ThemeProvider attribute="class" defaultTheme="light" enableSystem disableTransitionOnChange>
            <TooltipProvider delayDuration={200}>
                <div className="min-h-screen bg-background">
                    <AppHeader />
                    <main className="container mx-auto px-4 py-8 animate-in fade-in slide-in-from-bottom-4 duration-500 ease-in-out">
                        {children}
                    </main>
                </div>
            </TooltipProvider>
        </ThemeProvider>
    )
}
