"use client";

import { ArrowDown, ArrowUp, ArrowUpDown } from "lucide-react";
import { useEffect, useMemo, useState, type ReactNode } from "react";
import {
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  useReactTable,
  type ColumnDef,
  type SortingState,
} from "@tanstack/react-table";

import { cn } from "@/lib/utils";

export type DataTableColumn<TData> = ColumnDef<TData, unknown>;

type DataTableShellProps<TData> = {
  columns: DataTableColumn<TData>[];
  data: TData[];
  emptyMessage: string;
  getRowClassName?: (row: TData) => string | undefined;
  getRowKey?: (row: TData, index: number) => string;
  pageSize?: number;
  toolbar?: ReactNode;
  wrapperClassName?: string;
};

export function DataTableShell<TData>({
  columns,
  data,
  emptyMessage,
  getRowClassName,
  getRowKey,
  pageSize,
  toolbar,
  wrapperClassName,
}: DataTableShellProps<TData>) {
  const [sorting, setSorting] = useState<SortingState>([]);
  const [pageIndex, setPageIndex] = useState(0);

  const table = useReactTable({
    columns,
    data,
    getCoreRowModel: getCoreRowModel(),
    getRowId: getRowKey ? (row, index) => getRowKey(row, index) : undefined,
    getSortedRowModel: getSortedRowModel(),
    onSortingChange: setSorting,
    state: { sorting },
  });

  const rows = table.getRowModel().rows;
  const effectivePageSize = pageSize && pageSize > 0 ? pageSize : rows.length || 1;
  const totalPages = Math.max(1, Math.ceil(rows.length / effectivePageSize));
  const safePageIndex = Math.min(pageIndex, totalPages - 1);
  const pageStart = safePageIndex * effectivePageSize;
  const pageEnd = pageStart + effectivePageSize;
  const visibleRows = rows.slice(pageStart, pageEnd);
  const showPagination = pageSize != null && rows.length > effectivePageSize;
  const columnCount = useMemo(
    () =>
      table
        .getAllLeafColumns()
        .filter((column) => column.getIsVisible()).length || 1,
    [table],
  );

  useEffect(() => {
    if (pageIndex !== safePageIndex) {
      setPageIndex(safePageIndex);
    }
  }, [pageIndex, safePageIndex]);

  useEffect(() => {
    setPageIndex(0);
  }, [pageSize, data.length]);

  return (
    <div className={cn("grid gap-4", wrapperClassName)}>
      {toolbar ? <div className="flex flex-wrap items-center justify-between gap-3">{toolbar}</div> : null}
      <div className="overflow-auto rounded-3xl border border-slate-200/80 bg-white/85 shadow-sm">
        <table className="min-w-[720px] w-full border-separate border-spacing-0">
          <thead>
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map((header) => {
                  const canSort = header.column.getCanSort();
                  const sortState = header.column.getIsSorted();
                  return (
                    <th
                      key={header.id}
                      className="sticky top-0 z-[1] border-b border-slate-200 bg-slate-50/95 px-4 py-3 text-left text-[11px] font-extrabold uppercase tracking-[0.14em] text-slate-500"
                    >
                      {header.isPlaceholder ? null : canSort ? (
                        <button
                          type="button"
                          className="inline-flex items-center gap-2 text-left text-inherit"
                          onClick={header.column.getToggleSortingHandler()}
                        >
                          <span>{flexRender(header.column.columnDef.header, header.getContext())}</span>
                          {sortState === "asc" ? (
                            <ArrowUp size={13} />
                          ) : sortState === "desc" ? (
                            <ArrowDown size={13} />
                          ) : (
                            <ArrowUpDown size={13} className="opacity-60" />
                          )}
                        </button>
                      ) : (
                        flexRender(header.column.columnDef.header, header.getContext())
                      )}
                    </th>
                  );
                })}
              </tr>
            ))}
          </thead>
          <tbody>
            {visibleRows.length === 0 ? (
              <tr>
                <td
                  colSpan={columnCount}
                  className="px-4 py-10 text-sm text-slate-500"
                >
                  {emptyMessage}
                </td>
              </tr>
            ) : (
              visibleRows.map((row, index) => (
                <tr
                  key={row.id}
                  className={cn(
                    "transition-colors hover:bg-amber-50/50",
                    getRowClassName?.(row.original),
                  )}
                  data-row-index={pageStart + index}
                >
                  {row.getVisibleCells().map((cell) => (
                    <td
                      key={cell.id}
                      className="border-b border-slate-200 px-4 py-3 align-middle text-[13px] text-slate-700"
                    >
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
      {showPagination ? (
        <div className="flex flex-wrap items-center justify-between gap-3 text-sm text-slate-500">
          <span>
            {`${pageStart + 1}-${Math.min(rows.length, pageEnd)} of ${rows.length}`}
          </span>
          <div className="flex items-center gap-2">
            <button
              type="button"
              className="rounded-full border border-slate-200 bg-white px-3 py-1.5 text-slate-700 transition hover:border-slate-300 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-45"
              disabled={safePageIndex === 0}
              onClick={() => setPageIndex((current) => Math.max(0, current - 1))}
            >
              Prev
            </button>
            <span>{`Page ${safePageIndex + 1} / ${totalPages}`}</span>
            <button
              type="button"
              className="rounded-full border border-slate-200 bg-white px-3 py-1.5 text-slate-700 transition hover:border-slate-300 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-45"
              disabled={safePageIndex >= totalPages - 1}
              onClick={() => setPageIndex((current) => Math.min(totalPages - 1, current + 1))}
            >
              Next
            </button>
          </div>
        </div>
      ) : null}
    </div>
  );
}
