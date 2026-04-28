import { FamilyIdJump } from "@/components/family/family-id-jump";
import { PageShell } from "@/components/ui/page-shell";

export default function FamilyIndexPage() {
  return (
    <PageShell
      eyebrow="Family"
      title="Family evidence workspace"
      description="Open a DOCDB family directly to review legal posture, classification spread, citation chronology, and forecast support."
      overflowVisible
    >
      <FamilyIdJump />
    </PageShell>
  );
}
