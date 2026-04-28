"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { fetchFamilySuggestions } from "@/lib/api/family-v2";
import type { FamilySuggestion } from "@/lib/types/family-v2";

import styles from "./family-id-jump.module.css";

const MIN_QUERY_LENGTH = 2;

function formatStatus(status?: string | null): string {
  return status ? status.replace(/_/g, " ") : "";
}

function looksLikeFamilyId(value: string): boolean {
  return /^\d{6,}$/.test(value.trim());
}

export function FamilyIdJump() {
  const router = useRouter();
  const [value, setValue] = useState("");
  const [suggestions, setSuggestions] = useState<FamilySuggestion[]>([]);
  const [searching, setSearching] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);

  const openFamily = (familyId: string) => {
    const next = familyId.trim();
    if (!next) {
      return;
    }
    router.push(`/family/${encodeURIComponent(next)}`);
  };

  useEffect(() => {
    const candidate = value.trim();
    setActiveIndex(-1);
    if (candidate.length < MIN_QUERY_LENGTH || looksLikeFamilyId(candidate)) {
      setSuggestions([]);
      setSearching(false);
      return;
    }

    const controller = new AbortController();
    const timeout = window.setTimeout(() => {
      setSearching(true);
      void fetchFamilySuggestions(candidate, 8, controller.signal)
        .then(setSuggestions)
        .catch((error: unknown) => {
          if (error instanceof DOMException && error.name === "AbortError") {
            return;
          }
          setSuggestions([]);
        })
        .finally(() => {
          if (!controller.signal.aborted) {
            setSearching(false);
          }
        });
    }, 180);

    return () => {
      window.clearTimeout(timeout);
      controller.abort();
    };
  }, [value]);

  const activeFamily = activeIndex >= 0 ? suggestions[activeIndex] : undefined;

  return (
    <section className={styles.panel}>
      <div className={styles.eyebrow}>Direct jump</div>
      <h2 className={styles.title}>Jump to a family</h2>
      <p className={styles.description}>Enter a DOCDB family id directly, or search serving DuckDB families by owner or primary field.</p>
      <form
        className={styles.form}
        onSubmit={(event) => {
          event.preventDefault();
          openFamily(activeFamily?.familyId ?? value);
        }}
      >
        <div className={styles.inputWrap}>
          <input
            value={value}
            onChange={(event) => setValue(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "ArrowDown") {
                event.preventDefault();
                setActiveIndex((current) => (suggestions.length === 0 ? -1 : current < suggestions.length - 1 ? current + 1 : 0));
                return;
              }
              if (event.key === "ArrowUp") {
                event.preventDefault();
                setActiveIndex((current) => (suggestions.length === 0 ? -1 : current > 0 ? current - 1 : suggestions.length - 1));
                return;
              }
              if (event.key === "Enter" && activeFamily) {
                event.preventDefault();
                openFamily(activeFamily.familyId);
              }
            }}
            placeholder="Family id, owner, or field"
            aria-label="Jump to family workspace"
            autoComplete="off"
          />
          {searching ? <span className={styles.searching}>Searching serving families...</span> : null}
          {suggestions.length > 0 ? (
            <div className={styles.lookupMenu}>
              {suggestions.map((family, index) => (
                <button
                  key={family.familyId}
                  type="button"
                  className={styles.lookupItem}
                  data-active={activeIndex === index ? "true" : "false"}
                  onClick={() => openFamily(family.familyId)}
                  onMouseEnter={() => setActiveIndex(index)}
                >
                  <span className={styles.lookupLabel}>Family {family.label}</span>
                  <span className={styles.lookupMeta}>
                    {family.ownerLabel ?? "Unknown owner"}
                    {family.primaryField ? ` | ${family.primaryField}` : ""}
                    {family.status ? ` | ${formatStatus(family.status)}` : ""}
                  </span>
                </button>
              ))}
            </div>
          ) : null}
        </div>
        <button type="submit">Open family</button>
      </form>
    </section>
  );
}
