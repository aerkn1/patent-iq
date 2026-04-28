"use client";

import { CircleAlert } from "lucide-react";
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

import { formatNumber, formatPercent } from "@/components/portfolio/portfolio-format";
import { PortfolioTooltipLabel } from "@/components/portfolio/portfolio-tooltip-label";
import { Surface } from "@/components/ui/surface";
import { chartTokens } from "@/lib/design/chart-tokens";
import { workspaceTooltipCopy } from "@/lib/content/workspace-tooltips";
import type { PortfolioFieldSegmentRow } from "@/lib/types/portfolio-v2";
import styles from "@/components/portfolio/technology-panels.module.css";

type PortfolioFieldExposureProps = {
  rows: PortfolioFieldSegmentRow[];
  isLoading?: boolean;
  errorMessage?: string;
};

export function PortfolioFieldExposure({ rows, isLoading = false, errorMessage }: PortfolioFieldExposureProps) {
  const chartData = [...rows]
    .sort((left, right) => right.activeShare - left.activeShare)
    .map((row) => ({
      ...row,
      fieldLabel: row.field,
      sharePercent: row.activeShare * 100,
      delta: row.change12m,
      direction: row.hotspotDirection,
    }));
  const palette = [
    chartTokens.series.accent,
    chartTokens.series.info,
    chartTokens.series.success,
    chartTokens.series.warning,
    chartTokens.rank.secondary,
    chartTokens.rank.tertiary,
    chartTokens.series.critical,
    chartTokens.series.neutral,
  ];
  const rankedRows = chartData.slice(0, 7);
  const remainingRows = chartData.slice(7);
  const remainingShare = remainingRows.reduce((total, row) => total + row.activeShare, 0);
  const remainingFamilies = remainingRows.reduce((total, row) => total + row.activeFamilies, 0);
  const pieRows =
    remainingShare > 0
      ? [
          ...rankedRows,
          {
            field: "Other fields",
            fieldLabel: "Other fields",
            sharePercent: remainingShare * 100,
            activeShare: remainingShare,
            activeFamilies: remainingFamilies,
            delta: 0,
            direction: "stable" as const,
          },
        ]
      : rankedRows;
  const topThreeShare = chartData.slice(0, 3).reduce((total, row) => total + row.activeShare, 0);
  const leadingField = chartData[0];

  return (
    <Surface
      className="portfolio-field-exposure portfolio-panel--field"
      title={<PortfolioTooltipLabel label="Field footprint" tooltip={workspaceTooltipCopy.fields.fieldFootprint} />}
    >
      {errorMessage ? <p className="portfolio-error">{errorMessage}</p> : null}
      {isLoading && chartData.length > 0 ? <p className="portfolio-small-note">Refreshing field footprint…</p> : null}
      {chartData.length === 0 ? (
        isLoading ? (
          <p className="portfolio-empty">Loading field footprint…</p>
        ) : (
          <p className="portfolio-empty">No field exposure available for this slice.</p>
        )
      ) : (
        <div className={styles.footprintBody}>
          <div className={styles.footprintChart}>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={pieRows}
                  dataKey="sharePercent"
                  nameKey="fieldLabel"
                  innerRadius={68}
                  outerRadius={112}
                  stroke="rgba(255,255,255,0.92)"
                  strokeWidth={2}
                  paddingAngle={pieRows.length > 1 ? 2 : 0}
                  isAnimationActive={false}
                >
                  {pieRows.map((row, index) => (
                    <Cell key={`${row.fieldLabel}-${index}`} fill={palette[index % palette.length]} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(value: number, _name: string, item) => {
                    const payload = item?.payload as { activeFamilies?: number } | undefined;
                    return [`${value.toFixed(1)}%`, `${formatNumber(payload?.activeFamilies ?? 0)} active families`];
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className={styles.footprintLegend}>
            {pieRows.map((row, index) => (
              <div
                key={`${row.fieldLabel}-legend`}
                className={styles.footprintLegendItem}
                style={{ ["--footprint-color" as string]: palette[index % palette.length] }}
              >
                <span className={styles.footprintLegendIdentity}>
                  <span
                    className={styles.footprintLegendSwatch}
                    style={{ backgroundColor: palette[index % palette.length] }}
                  />
                  <span>{row.fieldLabel}</span>
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
      {chartData.length > 0 ? (
        <div className="portfolio-field-warning">
          <CircleAlert size={14} />
          {leadingField ? (
            <>
              <PortfolioTooltipLabel label="Leading field" tooltip={workspaceTooltipCopy.fields.leadingField} />{" "}
              {leadingField.field} at {formatPercent(leadingField.activeShare)}.{" "}
              <PortfolioTooltipLabel label="Top 3 fields" tooltip={workspaceTooltipCopy.fields.topThreeFields} />{" "}
              account for {formatPercent(topThreeShare)}. Historical change belongs in chronology and compare.
            </>
          ) : (
            "Current field mix only. Historical change belongs in chronology and compare."
          )}
        </div>
      ) : null}
    </Surface>
  );
}
