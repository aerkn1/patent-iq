import type { ReactNode } from "react";

import { AppFrame } from "@/components/ui/app-frame";

export default function WorkspaceLayout({ children }: { children: ReactNode }) {
  return <AppFrame>{children}</AppFrame>;
}
