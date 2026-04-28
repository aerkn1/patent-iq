import { FamilyWorkspaceLazy } from "@/components/family/family-workspace-lazy";

export default async function FamilyPage({
  params,
}: {
  params: Promise<{ familyId: string }>;
}) {
  const { familyId } = await params;

  return <FamilyWorkspaceLazy familyId={familyId} />;
}
