import type { ComponentType } from "react";

import {
  BookOpenText,
  BriefcaseBusiness,
  GitCompareArrows,
  Home,
  Newspaper,
  Radar,
} from "lucide-react";

export type WorkspaceNavItem = {
  href: string;
  label: string;
  description: string;
  icon: ComponentType<{ className?: string }>;
  match: (pathname: string) => boolean;
};

export const workspaceNavigationItems: WorkspaceNavItem[] = [
  {
    href: "/",
    label: "Home",
    description: "Operator entry console",
    icon: Home,
    match: (pathname) => pathname === "/",
  },
  {
    href: "/portfolio",
    label: "Portfolio",
    description: "Owner intelligence workspaces",
    icon: BriefcaseBusiness,
    match: (pathname) => pathname.startsWith("/portfolio"),
  },
  {
    href: "/family",
    label: "Family",
    description: "Evidence and legal drillthrough",
    icon: BookOpenText,
    match: (pathname) => pathname.startsWith("/family"),
  },
  {
    href: "/publication",
    label: "Publication",
    description: "Document-level evidence",
    icon: Newspaper,
    match: (pathname) => pathname.startsWith("/publication"),
  },
  {
    href: "/market",
    label: "Market",
    description: "Field and jurisdiction command",
    icon: Radar,
    match: (pathname) => pathname.startsWith("/market"),
  },
  {
    href: "/compare",
    label: "Compare",
    description: "Peer-aware analytical lenses",
    icon: GitCompareArrows,
    match: (pathname) => pathname.startsWith("/compare"),
  },
];
