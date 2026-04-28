"use client";

import { createElement, useEffect, useState, type ComponentType, type ReactNode } from "react";

type DeferredClientComponentProps<TProps extends object> = {
  loader: () => Promise<ComponentType<TProps>>;
  componentProps: TProps;
  fallback: ReactNode;
};

export function DeferredClientComponent<TProps extends object>({
  loader,
  componentProps,
  fallback,
}: DeferredClientComponentProps<TProps>) {
  const [LoadedComponent, setLoadedComponent] = useState<ComponentType<TProps> | null>(null);

  useEffect(() => {
    let active = true;

    void loader().then((component) => {
      if (active) {
        setLoadedComponent(() => component);
      }
    });

    return () => {
      active = false;
    };
  }, [loader]);

  if (!LoadedComponent) {
    return <>{fallback}</>;
  }

  return createElement(LoadedComponent, componentProps);
}
