"use client";

import { PortfolioWorkspaceSkeleton } from "@/components/portfolio/portfolio-workspace-skeleton";
import { DeferredClientComponent } from "@/components/ui/deferred-client-component";

type PortfolioWorkspaceLazyProps = {
  ownerId: string;
};

const loadPortfolioWorkspace = () =>
  import("@/components/portfolio/portfolio-workspace").then((module) => module.PortfolioWorkspace);

export function PortfolioWorkspaceLazy({ ownerId }: PortfolioWorkspaceLazyProps) {
  return (
    <DeferredClientComponent
      loader={loadPortfolioWorkspace}
      componentProps={{ ownerId }}
      fallback={<PortfolioWorkspaceSkeleton />}
    />
  );
}
