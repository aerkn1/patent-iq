"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { fetchPublicationSuggestions } from "@/lib/api/publication-v2";
import type { PublicationSuggestion } from "@/lib/types/publication-v2";

import styles from "./publication-id-jump.module.css";

const MIN_QUERY_LENGTH = 2;

export function PublicationIdJump() {
  const router = useRouter();
  const [value, setValue] = useState("");
  const [suggestions, setSuggestions] = useState<PublicationSuggestion[]>([]);
  const [searching, setSearching] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);

  const openPublication = (publicationId: string) => {
    const next = publicationId.trim().toUpperCase();
    if (!next) {
      return;
    }
    router.push(`/publication/${encodeURIComponent(next)}`);
  };

  useEffect(() => {
    const candidate = value.trim();
    setActiveIndex(-1);
    if (candidate.length < MIN_QUERY_LENGTH) {
      setSuggestions([]);
      setSearching(false);
      return;
    }

    const controller = new AbortController();
    const timeout = window.setTimeout(() => {
      setSearching(true);
      void fetchPublicationSuggestions(candidate, 8, controller.signal)
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

  const activePublication = activeIndex >= 0 ? suggestions[activeIndex] : undefined;

  return (
    <section className={styles.panel}>
      <div className={styles.eyebrow}>Direct jump</div>
      <h2 className={styles.title}>Jump to a publication</h2>
      <p className={styles.description}>Search the publication serving snapshot by publication id, then open the document-level workspace.</p>
      <form
        className={styles.form}
        onSubmit={(event) => {
          event.preventDefault();
          openPublication(activePublication?.publicationId ?? value);
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
              if (event.key === "Enter" && activePublication) {
                event.preventDefault();
                openPublication(activePublication.publicationId);
              }
            }}
            placeholder="Publication id, e.g. EP2606406"
            aria-label="Jump to publication workspace"
            autoComplete="off"
          />
          {searching ? <span className={styles.searching}>Searching publication ids...</span> : null}
          {suggestions.length > 0 ? (
            <div className={styles.lookupMenu}>
              {suggestions.map((publication, index) => (
                <button
                  key={publication.publicationId}
                  type="button"
                  className={styles.lookupItem}
                  data-active={activeIndex === index ? "true" : "false"}
                  onClick={() => openPublication(publication.publicationId)}
                  onMouseEnter={() => setActiveIndex(index)}
                >
                  <span className={styles.lookupLabel}>{publication.label}</span>
                  <span className={styles.lookupMeta}>
                    {publication.authority ?? "Unknown office"}
                    {publication.kindCode ? ` | ${publication.kindCode}` : ""}
                    {publication.publicationDate ? ` | ${publication.publicationDate}` : ""}
                    {publication.familyId ? ` | Family ${publication.familyId}` : ""}
                  </span>
                </button>
              ))}
            </div>
          ) : null}
        </div>
        <button type="submit">Open publication</button>
      </form>
    </section>
  );
}
