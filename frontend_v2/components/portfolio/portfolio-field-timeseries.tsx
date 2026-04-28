"use client";

import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { useMemo, useState } from "react";

import { formatNumber, formatPercent } from "@/components/portfolio/portfolio-format";
import { PortfolioTooltipLabel } from "@/components/portfolio/portfolio-tooltip-label";
import { Surface } from "@/components/ui/surface";
import { chartTokens } from "@/lib/design/chart-tokens";
import { workspaceTooltipCopy } from "@/lib/content/workspace-tooltips";
import type { PortfolioFieldTimeseries, PortfolioFieldTimeseriesPoint } from "@/lib/types/portfolio-v2";
import styles from "@/components/portfolio/technology-panels.module.css";

type PortfolioFieldTimeseriesPanelProps = {
  timeseries: PortfolioFieldTimeseries[];
  isLoading?: boolean;
  selectedField?: string;
  onSelectField?: (field: string) => void;
  note?: string;
  errorMessage?: string;
};

export function PortfolioFieldTimeseriesPanel({
  timeseries,
  isLoading = false,
  selectedField,
  onSelectField,
  note,
  errorMessage,
}: PortfolioFieldTimeseriesPanelProps) {
  const [fieldIndex, setFieldIndex] = useState(-1);
  const aggregateSeries = useMemo<PortfolioFieldTimeseries | undefined>(() => {
    if (timeseries.length === 0) {
      return undefined;
    }

    const totals = new Map<number, PortfolioFieldTimeseriesPoint>();
    timeseries.forEach((series) => {
      series.points.forEach((point) => {
        const current = totals.get(point.year) ?? { year: point.year, share: 0, portfolio: 0 };
        current.share += point.share;
        current.portfolio += point.portfolio;
        totals.set(point.year, current);
      });
    });

    return {
      field: "All fields",
      points: Array.from(totals.values())
        .map((point) => ({
          ...point,
          share: point.portfolio,
        }))
        .sort((left, right) => left.year - right.year),
    };
  }, [timeseries]);
  const controlledSeries =
    selectedField && selectedField.length > 0 ? timeseries.find((series) => series.field === selectedField) : undefined;
  const localSelected = fieldIndex >= 0 ? (timeseries[fieldIndex] ?? timeseries[0]) : aggregateSeries;
  const selected = controlledSeries ?? (selectedField && selectedField.length === 0 ? aggregateSeries : localSelected) ?? timeseries[0];
  const selectValue =
    selectedField !== undefined
      ? selectedField || "__all__"
      : fieldIndex >= 0
        ? (timeseries[fieldIndex]?.field ?? timeseries[0]?.field ?? "__all__")
        : "__all__";
  const latestPoint = selected?.points[selected.points.length - 1];
  const isAggregateView = (selectedField !== undefined ? selectedField.length === 0 : fieldIndex < 0) && Boolean(aggregateSeries);
  const chartTitle = isAggregateView ? "All field activity" : "Selected field history";

  return (
    <Surface
      className="portfolio-panel--timeline"
      title={<PortfolioTooltipLabel label="Field chronology" tooltip={workspaceTooltipCopy.fields.fieldChronology} />}
      actions={
        <select
          aria-label="Field chronology selector"
          className={styles.timeseriesControl}
          value={selectValue}
          disabled={timeseries.length === 0}
          onChange={(event) => {
            const nextField = event.target.value;
            if (onSelectField) {
              onSelectField(nextField === "__all__" ? "" : nextField);
              return;
            }
            if (nextField === "__all__") {
              setFieldIndex(-1);
              return;
            }
            const nextIndex = timeseries.findIndex((series) => series.field === nextField);
            setFieldIndex(nextIndex >= 0 ? nextIndex : 0);
          }}
        >
          <option value="__all__">All fields</option>
          {timeseries.map((series) => (
            <option key={series.field} value={series.field}>
              {series.field}
            </option>
          ))}
        </select>
      }
    >
      <div className={styles.chartShell}>
        <h4 className={styles.chartShellTitle}>
          <PortfolioTooltipLabel
            label={chartTitle}
            tooltip={
              isAggregateView ? workspaceTooltipCopy.fields.allFieldActivity : workspaceTooltipCopy.fields.selectedFieldHistory
            }
          />
        </h4>
        {errorMessage ? <p className="portfolio-error">{errorMessage}</p> : null}
        {isLoading && selected ? <p className="portfolio-small-note">Refreshing field chronology…</p> : null}
        {!selected ? (
          isLoading ? (
            <p className="portfolio-empty">Loading field chronology…</p>
          ) : (
            <p className="portfolio-empty">No chronology loaded for the selected field.</p>
          )
        ) : (
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={selected.points}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="year" />
              <YAxis tickFormatter={(value: number) => (isAggregateView ? formatNumber(value) : `${(value * 100).toFixed(0)}%`)} />
              <Tooltip
                formatter={(value: number) => (isAggregateView ? formatNumber(value) : formatPercent(value))}
                labelFormatter={(label) => `Year: ${label}`}
              />
              <Area
                type="monotone"
                dataKey={isAggregateView ? "portfolio" : "share"}
                stroke={chartTokens.series.accent}
                fill={chartTokens.reference.areaAccent}
                fillOpacity={1}
                isAnimationActive={false}
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>
      {selected && selected.points.length <= 1 ? (
        <p className={`portfolio-small-note ${styles.timeseriesNote}`}>
          Only one PIT snapshot is currently available for this selection, so the chart does not yet show a real trend line.
        </p>
      ) : null}
      {selected && selected.points.length > 1 && latestPoint ? (
        <p className={`portfolio-small-note ${styles.timeseriesNote}`}>
          {isAggregateView
            ? `Latest loaded active families: ${formatNumber(latestPoint.portfolio)} as of ${latestPoint.year}.`
            : `Latest loaded share: ${formatPercent(latestPoint.share)} as of ${latestPoint.year}.`}
        </p>
      ) : null}
      {note ? <p className={`portfolio-small-note ${styles.timeseriesNote}`}>{note}</p> : null}
    </Surface>
  );
}
