"use client";

import { useEffect, useState, type ComponentType } from "react";

type OperatorEntryConsoleLazyProps = {
  fallbackClassName: string;
};

export function OperatorEntryConsoleLazy({ fallbackClassName }: OperatorEntryConsoleLazyProps) {
  const [ConsoleComponent, setConsoleComponent] = useState<ComponentType | null>(null);

  useEffect(() => {
    let active = true;

    void import("./operator-entry-console").then((module) => {
      if (active) {
        setConsoleComponent(() => module.OperatorEntryConsole);
      }
    });

    return () => {
      active = false;
    };
  }, []);

  if (!ConsoleComponent) {
    return <div className={fallbackClassName}>Loading workspace entry...</div>;
  }

  return <ConsoleComponent />;
}
