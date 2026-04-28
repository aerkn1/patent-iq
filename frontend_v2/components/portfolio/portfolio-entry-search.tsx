"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Search } from "lucide-react";

import { fetchPortfolioOwnerSuggestions } from "@/lib/api/portfolio-v2";
import type { PortfolioOwnerSuggestion } from "@/lib/types/portfolio-v2";

function normalizeSearchToken(value: string) {
  return value.trim().toUpperCase().replace(/[^A-Z0-9]+/g, "_").replace(/^_+|_+$/g, "");
}

export function PortfolioEntrySearch() {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [rows, setRows] = useState<PortfolioOwnerSuggestion[]>([]);
  const [searching, setSearching] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);

  useEffect(() => {
    const trimmed = query.trim();
    if (trimmed.length < 2) {
      return;
    }

    let cancelled = false;

    const timeoutId = window.setTimeout(() => {
      void fetchPortfolioOwnerSuggestions(trimmed, 10)
        .then((result) => {
          if (!cancelled) {
            setRows(result.rows);
            setActiveIndex(-1);
          }
        })
        .catch(() => {
          if (!cancelled) {
            setRows([]);
            setActiveIndex(-1);
          }
        })
        .finally(() => {
          if (!cancelled) {
            setSearching(false);
          }
        });
    }, 180);

    return () => {
      cancelled = true;
      window.clearTimeout(timeoutId);
    };
  }, [query]);

  const openOwner = (ownerId: string) => {
    const trimmed = ownerId.trim();
    if (!trimmed) {
      return;
    }
    router.push(`/portfolio/${encodeURIComponent(trimmed)}`);
  };

  const exactMatch = rows.find((owner) => {
    const normalizedQuery = normalizeSearchToken(query);
    return (
      normalizeSearchToken(owner.ownerId) === normalizedQuery ||
      normalizeSearchToken(owner.label) === normalizedQuery
    );
  });

  const activeOwner = activeIndex >= 0 ? rows[activeIndex] : undefined;

  return (
    <section className="panel-shell portfolio-entry-search">
      <div className="portfolio-entry-search__eyebrow">Portfolio Lookup</div>
      <h2>Search a real owner slice</h2>
      <p className="portfolio-entry-search__copy">
        Type an owner display name or harmonized owner id. Navigation uses the harmonized owner id returned by the backend search.
      </p>
      <div className="portfolio-owner-search">
        <div className="portfolio-search__control">
          <Search className="portfolio-search__icon" />
          <input
            value={query}
            onChange={(event) => {
              const nextValue = event.target.value;
              const trimmed = nextValue.trim();
              setActiveIndex(-1);
              if (trimmed.length < 2) {
                setRows([]);
              }
              setSearching(trimmed.length >= 2);
              setQuery(nextValue);
            }}
            onKeyDown={(event) => {
              if (event.key === "ArrowDown") {
                event.preventDefault();
                setActiveIndex((current) => {
                  if (rows.length === 0) {
                    return -1;
                  }
                  return current < rows.length - 1 ? current + 1 : 0;
                });
                return;
              }

              if (event.key === "ArrowUp") {
                event.preventDefault();
                setActiveIndex((current) => {
                  if (rows.length === 0) {
                    return -1;
                  }
                  return current > 0 ? current - 1 : rows.length - 1;
                });
                return;
              }

              if (event.key === "Escape") {
                setActiveIndex(-1);
                return;
              }

              if (event.key === "Enter") {
                if (activeOwner) {
                  event.preventDefault();
                  openOwner(activeOwner.ownerId);
                  return;
                }
                if (exactMatch) {
                  event.preventDefault();
                  openOwner(exactMatch.ownerId);
                  return;
                }
                if (rows[0]) {
                  event.preventDefault();
                  openOwner(rows[0].ownerId);
                }
              }
            }}
            placeholder="Search owner name or harmonized id"
            role="combobox"
            aria-label="Search portfolio owner"
            aria-activedescendant={activeOwner ? `portfolio-owner-option-${activeOwner.ownerId}` : undefined}
            aria-autocomplete="list"
            aria-controls="portfolio-owner-search-results"
            aria-expanded={rows.length > 0}
            autoComplete="off"
          />
        </div>
        {searching ? <div className="portfolio-owner-search__status">Searching owners...</div> : null}
        {rows.length > 0 ? (
          <div
            id="portfolio-owner-search-results"
            className="portfolio-owner-search__menu"
            role="listbox"
            aria-label="Owner search results"
          >
            {rows.map((owner, index) => (
              <button
                key={owner.ownerId}
                type="button"
                role="option"
                id={`portfolio-owner-option-${owner.ownerId}`}
                className="portfolio-owner-search__item"
                onClick={() => openOwner(owner.ownerId)}
                onMouseEnter={() => setActiveIndex(index)}
                aria-selected={activeIndex === index}
                data-active={activeIndex === index ? "true" : "false"}
              >
                <span className="portfolio-owner-search__label">{owner.label}</span>
                <span className="portfolio-owner-search__meta">
                  {owner.ownerId}
                  {owner.familyCount != null ? ` • ${owner.familyCount} families` : ""}
                </span>
              </button>
            ))}
          </div>
        ) : null}
      </div>
    </section>
  );
}
