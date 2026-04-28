"use client";

import { DeferredClientComponent } from "@/components/ui/deferred-client-component";

const loadMarketWorkspace = () =>
  import("@/components/market/market-workspace").then((module) => module.MarketWorkspace);

export function MarketWorkspaceLazy() {
  return (
    <DeferredClientComponent
      loader={loadMarketWorkspace}
      componentProps={{}}
      fallback={<p className="portfolio-empty">Loading market intelligence workspace…</p>}
    />
  );
}
