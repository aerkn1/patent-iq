import type React from "react"
import { ThemeProvider } from "@/components/theme-provider"
import { TooltipProvider } from "@/components/ui/tooltip"
import { SidebarProvider, SidebarInset, SidebarTrigger } from "@/components/ui/sidebar"
import { AppSidebar } from "@/components/app-sidebar"

export default function DashboardLayout({
    children,
}: Readonly<{
    children: React.ReactNode
}>) {
    return (
        <ThemeProvider attribute="class" defaultTheme="light" enableSystem disableTransitionOnChange>
            <TooltipProvider delayDuration={200}>
                <SidebarProvider defaultOpen={true}>
                    <AppSidebar />
                    <SidebarInset>
                        <header className="flex h-10 items-center border-b border-border px-4 shrink-0">
                            <SidebarTrigger className="-ml-1" />
                        </header>
                        <main className="flex-1 overflow-auto p-6">
                            {children}
                        </main>
                    </SidebarInset>
                </SidebarProvider>
            </TooltipProvider>
        </ThemeProvider>
    )
}
