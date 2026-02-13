"use client"

import {
    Accordion,
    AccordionContent,
    AccordionItem,
    AccordionTrigger,
} from "@/components/ui/accordion"
import { Badge } from "@/components/ui/badge"
import type { ForecastMeta } from "@/lib/types/forecast"

interface ModelTransparencyAccordionProps {
    featuresUsed: Record<string, number | boolean>
    meta: ForecastMeta
}

const FEATURE_LABELS: Record<string, string> = {
    cites_pre_asof: "Citations before as-of",
    family_members_count: "Family members",
    family_jurisdiction_count: "Jurisdictions",
    major_office_grant_auth_count: "Major office grants",
    family_cpc_subclass_count: "CPC subclasses",
    has_us_grant: "US grant",
    has_cn_grant: "CN grant",
    has_jp_grant: "JP grant",
    has_kr_grant: "KR grant",
    as_of_year: "As-of year",
}

export function ModelTransparencyAccordion({
    featuresUsed,
    meta,
}: ModelTransparencyAccordionProps) {
    return (
        <Accordion type="single" collapsible className="w-full">
            <AccordionItem value="model-info" className="border-none">
                <AccordionTrigger className="text-xs text-muted-foreground py-2 hover:no-underline">
                    Model details
                </AccordionTrigger>
                <AccordionContent>
                    <div className="space-y-3 pb-2">
                        {/* Model version + calibration */}
                        <div className="flex flex-wrap gap-2">
                            <Badge variant="secondary" className="text-[10px]">
                                v{meta.model_version}
                            </Badge>
                            <Badge variant="secondary" className="text-[10px]">
                                {meta.calibration}
                            </Badge>
                            <Badge variant="secondary" className="text-[10px]">
                                {meta.as_of_definition}
                            </Badge>
                        </div>

                        {/* Feature table */}
                        <div className="border rounded-md overflow-hidden">
                            <table className="w-full text-xs">
                                <thead>
                                    <tr className="bg-muted/50">
                                        <th className="text-left p-2 font-medium">Feature</th>
                                        <th className="text-right p-2 font-medium">Value</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {Object.entries(featuresUsed).map(([key, value]) => (
                                        <tr key={key} className="border-t">
                                            <td className="p-2 text-muted-foreground">
                                                {FEATURE_LABELS[key] || key}
                                            </td>
                                            <td className="p-2 text-right font-mono">
                                                {typeof value === "boolean"
                                                    ? value ? "✓" : "✗"
                                                    : typeof value === "number"
                                                        ? Number.isInteger(value) ? value : value.toFixed(2)
                                                        : String(value)}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </AccordionContent>
            </AccordionItem>
        </Accordion>
    )
}
