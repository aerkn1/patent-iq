"use client";

import { DeferredClientComponent } from "@/components/ui/deferred-client-component";

const loadPortfolioCompareWorkspace = () =>
  import("@/components/compare/portfolio-compare-workspace").then((module) => module.PortfolioCompareWorkspace);

export function PortfolioCompareWorkspaceLazy() {
  return (
    <DeferredClientComponent
      loader={loadPortfolioCompareWorkspace}
      componentProps={{}}
      fallback={<p>Loading compare workspace…</p>}
    />
  );
}
