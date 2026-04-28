"use client";

import { DeferredClientComponent } from "@/components/ui/deferred-client-component";

type PublicationWorkspaceLazyProps = {
  publicationId: string;
};

const loadPublicationWorkspace = () =>
  import("@/components/publication/publication-workspace").then((module) => module.PublicationWorkspace);

export function PublicationWorkspaceLazy({ publicationId }: PublicationWorkspaceLazyProps) {
  return (
    <DeferredClientComponent
      loader={loadPublicationWorkspace}
      componentProps={{ publicationId }}
      fallback={<p className="portfolio-empty">Loading publication workspace…</p>}
    />
  );
}
