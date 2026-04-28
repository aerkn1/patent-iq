"use client";

import { DeferredClientComponent } from "@/components/ui/deferred-client-component";

const loadFamilyCompareWorkspace = () =>
  import("@/components/compare/family-compare-workspace").then((module) => module.FamilyCompareWorkspace);

export function FamilyCompareWorkspaceLazy() {
  return (
    <DeferredClientComponent
      loader={loadFamilyCompareWorkspace}
      componentProps={{}}
      fallback={<p>Loading compare workspace…</p>}
    />
  );
}
