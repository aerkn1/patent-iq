"use client";

import type { ReactNode } from "react";

import { InfoPill } from "@/components/ui/data-pill";
import { Surface } from "@/components/ui/surface";

type MethodologyDisclosureItem = {
  code: string;
  detail: string;
  title: string;
};

type MethodologyDisclosureProps = {
  className?: string;
  description: string;
  items: MethodologyDisclosureItem[];
  links?: ReactNode;
  previewCount?: number;
  title: string;
};

export function MethodologyDisclosure({
  className,
  description,
  items,
  links,
  previewCount = 2,
  title,
}: MethodologyDisclosureProps) {
  const previewItems = items.slice(0, previewCount);

  return (
    <Surface
      className={className}
      title={title}
      description={description}
      badge={<InfoPill tone="neutral">{items.length} notes</InfoPill>}
    >
      <div className="flex flex-wrap items-center gap-2">{links}</div>
      {previewItems.length > 0 ? (
        <div className="mt-4 grid gap-3 md:grid-cols-2">
          {previewItems.map((item) => (
            <article
              key={item.code}
              className="grid gap-2 rounded-3xl border border-slate-200 bg-slate-50/80 p-4"
            >
              <span className="text-[11px] font-extrabold uppercase tracking-[0.14em] text-slate-500">{item.code}</span>
              <strong className="text-[15px] text-slate-900">{item.title}</strong>
              <p className="m-0 text-sm leading-6 text-slate-600">{item.detail}</p>
            </article>
          ))}
        </div>
      ) : null}
      <details className="mt-4 rounded-3xl border border-slate-200 bg-slate-50/80 p-4">
        <summary className="cursor-pointer list-none text-[15px] font-semibold text-slate-900">
          Expand full methodology and caveats
        </summary>
        <div className="mt-4 grid gap-3">
          {items.map((item) => (
            <article
              key={item.code}
              className="grid gap-2 rounded-2xl border border-slate-200 bg-white/90 p-4"
            >
              <span className="text-[11px] font-extrabold uppercase tracking-[0.14em] text-slate-500">{item.code}</span>
              <strong className="text-[15px] text-slate-900">{item.title}</strong>
              <p className="m-0 text-sm leading-6 text-slate-600">{item.detail}</p>
            </article>
          ))}
        </div>
      </details>
    </Surface>
  );
}
