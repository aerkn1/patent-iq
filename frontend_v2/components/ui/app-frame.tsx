import { Suspense, type ReactNode } from "react";

import { WorkspaceContext, WorkspaceContextProvider } from "@/components/ui/workspace-context";
import { WorkspaceNav } from "@/components/ui/workspace-nav";

import styles from "./app-frame.module.css";

type AppFrameProps = {
  children: ReactNode;
};

export function AppFrame({ children }: AppFrameProps) {
  return (
    <div className={styles.frame}>
      <Suspense fallback={<div className={styles.navFallback} aria-hidden="true" />}>
        <WorkspaceNav />
      </Suspense>
      <div className={styles.main}>
        <WorkspaceContextProvider>
          <Suspense fallback={null}>
            <WorkspaceContext />
          </Suspense>
          <div className={styles.canvas}>{children}</div>
        </WorkspaceContextProvider>
      </div>
    </div>
  );
}
