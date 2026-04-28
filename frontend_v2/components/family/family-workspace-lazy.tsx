"use client";

import dynamic from "next/dynamic";

type FamilyWorkspaceLazyProps = {
  familyId: string;
};

const FamilyWorkspace = dynamic(
  () => import("@/components/family/family-workspace").then((module) => module.FamilyWorkspace),
  {
    loading: () => <p className="portfolio-empty">Loading family workspace…</p>,
  },
);

export function FamilyWorkspaceLazy({ familyId }: FamilyWorkspaceLazyProps) {
  return <FamilyWorkspace familyId={familyId} />;
}
