"use client";

import { useState } from "react";
import { Search } from "lucide-react";

import type { PortfolioOwnerSuggestion } from "@/lib/types/portfolio-v2";

type PortfolioWorkspaceControlsProps = {
  ownerInputValue: string;
  onOwnerInputChange: (value: string) => void;
  onOwnerSubmit?: (ownerId: string) => void;
  onOwnerSelect?: (owner: PortfolioOwnerSuggestion) => void;
  suggestions?: PortfolioOwnerSuggestion[];
  searching?: boolean;
  variant?: "panel" | "banner";
};

function normalizeSearchToken(value: string) {
  return value.trim().toUpperCase().replace(/[^A-Z0-9]+/g, "_").replace(/^_+|_+$/g, "");
}

export function PortfolioWorkspaceControls({
  ownerInputValue,
  onOwnerInputChange,
  onOwnerSubmit,
  onOwnerSelect,
  suggestions = [],
  searching = false,
  variant = "panel",
}: PortfolioWorkspaceControlsProps) {
  const [activeIndex, setActiveIndex] = useState(-1);
  const hasSuggestions = suggestions.length > 0;
  const activeOwner = activeIndex >= 0 ? suggestions[activeIndex] : undefined;
  const exactMatch = suggestions.find((owner) => {
    const normalizedQuery = normalizeSearchToken(ownerInputValue);
    return (
      normalizeSearchToken(owner.ownerId) === normalizedQuery ||
      normalizeSearchToken(owner.label) === normalizedQuery
    );
  });

  const submitOwner = () => {
    if (activeOwner && onOwnerSelect) {
      onOwnerSelect(activeOwner);
      return;
    }
    if (exactMatch && onOwnerSelect) {
      onOwnerSelect(exactMatch);
      return;
    }
    if (suggestions[0] && onOwnerSelect) {
      onOwnerSelect(suggestions[0]);
      return;
    }
    if (onOwnerSubmit) {
      onOwnerSubmit(ownerInputValue.trim());
    }
  };

  const isBanner = variant === "banner";

  return (
    <section
      className={`portfolio-workspace-controls${isBanner ? " portfolio-workspace-controls--banner" : " panel-shell"}`}
      role="search"
    >
      {!isBanner ? (
        <div className="portfolio-workspace-controls__head">
          <span className="portfolio-workspace-controls__eyebrow">Switch Portfolio</span>
          <p className="portfolio-workspace-controls__copy">
            Search another harmonized owner without changing the current workspace layout.
          </p>
        </div>
      ) : null}
      <div className="portfolio-hero__search portfolio-workspace-controls__search">
        <div className="portfolio-owner-search">
          <div className="portfolio-search__control">
            <Search className="portfolio-search__icon" />
            <input
              value={ownerInputValue}
              onChange={(event) => {
                setActiveIndex(-1);
                onOwnerInputChange(event.target.value);
              }}
              onKeyDown={(event) => {
                if (event.key === "ArrowDown") {
                  event.preventDefault();
                  setActiveIndex((current) => {
                    if (!hasSuggestions) {
                      return -1;
                    }
                    return current < suggestions.length - 1 ? current + 1 : 0;
                  });
                  return;
                }

                if (event.key === "ArrowUp") {
                  event.preventDefault();
                  setActiveIndex((current) => {
                    if (!hasSuggestions) {
                      return -1;
                    }
                    return current > 0 ? current - 1 : suggestions.length - 1;
                  });
                  return;
                }

                if (event.key === "Escape") {
                  setActiveIndex(-1);
                  return;
                }

                if (event.key !== "Enter") {
                  return;
                }
                event.preventDefault();
                submitOwner();
              }}
              placeholder="Search owner name or harmonized id"
              role="combobox"
              aria-label="Portfolio owner search"
              aria-activedescendant={activeOwner ? `portfolio-workspace-owner-option-${activeOwner.ownerId}` : undefined}
              aria-autocomplete="list"
              aria-controls="portfolio-workspace-owner-results"
              aria-expanded={hasSuggestions}
              autoComplete="off"
            />
          </div>
          {searching ? <div className="portfolio-owner-search__status">Searching owners...</div> : null}
          {!searching && hasSuggestions ? (
            <div
              id="portfolio-workspace-owner-results"
              className="portfolio-owner-search__menu"
              role="listbox"
              aria-label="Owner suggestions"
            >
              {suggestions.map((owner, index) => (
                <button
                  key={owner.ownerId}
                  type="button"
                  role="option"
                  id={`portfolio-workspace-owner-option-${owner.ownerId}`}
                  className="portfolio-owner-search__item"
                  aria-selected={activeIndex === index}
                  data-active={activeIndex === index ? "true" : "false"}
                  onClick={() => onOwnerSelect?.(owner)}
                  onMouseEnter={() => setActiveIndex(index)}
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
        <button type="button" onClick={submitOwner}>
          Open
        </button>
      </div>
    </section>
  );
}
