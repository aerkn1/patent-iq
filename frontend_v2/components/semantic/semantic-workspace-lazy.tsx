"use client";

import { DeferredClientComponent } from "@/components/ui/deferred-client-component";

const loadSemanticWorkspace = () =>
  import("@/components/semantic/semantic-workspace").then((module) => module.SemanticWorkspace);

export function SemanticWorkspaceLazy() {
  return (
    <DeferredClientComponent
      loader={loadSemanticWorkspace}
      componentProps={{}}
      fallback={<p>Loading semantic workspace…</p>}
    />
  );
}
