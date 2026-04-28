import { SemanticWorkspaceLazy } from "@/components/semantic/semantic-workspace-lazy";
import { PageShell } from "@/components/ui/page-shell";

export default function SemanticComparePage() {
  return (
    <PageShell>
      <SemanticWorkspaceLazy />
    </PageShell>
  );
}
