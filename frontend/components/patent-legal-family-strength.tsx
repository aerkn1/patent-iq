"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"
import type { FamilyData } from "@/lib/types/patent"

interface PatentLegalFamilyStrengthProps {
    familyData?: FamilyData
    legalStrengthScore?: number
    className?: string
}

export function PatentLegalFamilyStrength({ familyData, legalStrengthScore, className }: PatentLegalFamilyStrengthProps) {
    if (!familyData) return null

    const majorOffices = ["EP", "US", "CN", "JP", "KR"]
    const grantedOffices = familyData.major_office_grant_auths || []

    return (
        <Card className={cn("w-full", className)}>
            <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium uppercase tracking-wide text-muted-foreground">
                    Family & Legal Strength
                </CardTitle>
            </CardHeader>
            <CardContent>
                <div className="flex flex-wrap items-center gap-6 text-sm">
                    {/* Legal Strength Pill */}
                    {legalStrengthScore !== undefined && (
                        <div className="flex items-center gap-2 bg-secondary/20 px-3 py-1.5 rounded-full border border-secondary/20">
                            <span className="font-medium text-muted-foreground">Legal Strength:</span>
                            <span className="font-bold text-foreground">{legalStrengthScore.toFixed(0)}/100</span>
                        </div>
                    )}

                    {/* Family Size */}
                    <div className="flex flex-col">
                        <span className="text-xs text-muted-foreground">Family Size</span>
                        <span className="font-semibold text-lg">{familyData.family_members_count}</span>
                    </div>

                    {/* Jurisdictions */}
                    <div className="flex flex-col">
                        <span className="text-xs text-muted-foreground">Jurisdictions</span>
                        <span className="font-semibold text-lg">{familyData.family_jurisdiction_count}</span>
                    </div>

                    {/* Technical Breadth */}
                    <div className="flex flex-col">
                        <span className="text-xs text-muted-foreground">Tech Breadth</span>
                        <span className="font-semibold text-lg">{familyData.family_cpc_subclass_count} <span className="text-xs font-normal text-muted-foreground">CPC Subs</span></span>
                    </div>

                    {/* Major Office Grants */}
                    <div className="flex flex-col">
                        <span className="text-xs text-muted-foreground mb-1">Major Grants</span>
                        <div className="flex items-center gap-1">
                            {majorOffices.map((office) => {
                                const isGranted = grantedOffices.includes(office)
                                return (
                                    <Badge
                                        key={office}
                                        variant={isGranted ? "default" : "outline"}
                                        className={cn(
                                            "w-7 h-5 flex items-center justify-center p-0 text-[10px]",
                                            !isGranted && "text-muted-foreground/40 border-dashed"
                                        )}
                                    >
                                        {office}
                                    </Badge>
                                )
                            })}
                        </div>
                    </div>
                </div>
            </CardContent>
        </Card>
    )
}
