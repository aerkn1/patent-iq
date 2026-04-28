import { PublicationIdJump } from "@/components/publication/publication-id-jump";
import { PageShell } from "@/components/ui/page-shell";

export default function PublicationIndexPage() {
  return (
    <PageShell
      eyebrow="Publication"
      title="Publication evidence workspace"
      description="Open a publication directly to inspect register facts, text evidence, and family-member navigation."
      overflowVisible
    >
      <PublicationIdJump />
    </PageShell>
  );
}
