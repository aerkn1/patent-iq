"use client";

import type { PortfolioPagination } from "@/lib/types/portfolio-v2";

type PortfolioPaginationProps = {
  pagination?: PortfolioPagination;
  onPageChange?: (offset: number) => void;
};

export function PortfolioPaginationControls({ pagination, onPageChange }: PortfolioPaginationProps) {
  if (!pagination || !onPageChange) {
    return null;
  }

  const { limit, offset, returnedCount, totalCount } = pagination;
  const previousOffset = Math.max(0, offset - limit);
  const nextOffset = offset + limit;
  const hasPrevious = offset > 0;
  const hasNext = totalCount == null ? returnedCount >= limit : nextOffset < totalCount;
  const start = totalCount === 0 ? 0 : offset + 1;
  const end = offset + returnedCount;

  return (
    <div className="portfolio-pagination">
      <span className="portfolio-pagination__status">
        {totalCount != null ? `${start}-${end} of ${totalCount}` : `${returnedCount} rows`}
      </span>
      <div className="portfolio-pagination__actions">
        <button type="button" disabled={!hasPrevious} onClick={() => onPageChange(previousOffset)}>
          Prev
        </button>
        <button type="button" disabled={!hasNext} onClick={() => onPageChange(nextOffset)}>
          Next
        </button>
      </div>
    </div>
  );
}
