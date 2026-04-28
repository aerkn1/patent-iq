"use client";

import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip } from "recharts";

import { formatNumber, formatPercent } from "@/components/portfolio/portfolio-format";
import { PortfolioTooltipLabel } from "@/components/portfolio/portfolio-tooltip-label";
import { Surface } from "@/components/ui/surface";
import { workspaceTooltipCopy } from "@/lib/content/workspace-tooltips";
import type { PortfolioStatusSlice } from "@/lib/types/portfolio-v2";

import styles from "./portfolio-status-distribution-panel.module.css";

type PortfolioStatusDistributionPanelProps = {
  slices: PortfolioStatusSlice[];
  unclassifiedFamilyCount: number;
};

const STATUS_COLORS: Record<string, string> = {
  pending_emerging: "#1d4ed8",
  fully_active: "#2f9e44",
  partially_lapsed: "#e03131",
  dead: "#5c677d",
};

export function PortfolioStatusDistributionPanel({
  slices,
  unclassifiedFamilyCount,
}: PortfolioStatusDistributionPanelProps) {
  const hiddenUnderFireCount = slices
    .filter((slice) => slice.key === "under_fire")
    .reduce((sum, slice) => sum + slice.count, 0);
  const visibleSlices = slices.filter((slice) => slice.key !== "under_fire");
  const total = visibleSlices.reduce((sum, slice) => sum + slice.count, 0);
  const chartSlices = visibleSlices.map((slice) => ({
    ...slice,
    share: total > 0 ? slice.count / total : 0,
  }));
  const outsideChartCount = unclassifiedFamilyCount + hiddenUnderFireCount;
  const outsideChartLabel =
    outsideChartCount > 0
      ? `${formatNumber(outsideChartCount)} in-scope families sit outside this chart due to missing status mapping or suppressed under-fire status.`
      : "All in-scope families are classified in this chart.";

  return (
    <Surface
      title={
        <PortfolioTooltipLabel
          label="Family status distribution"
          tooltip={workspaceTooltipCopy.overview.familyStatusDistribution}
        />
      }
      description="This view shows current family status across the in-scope portfolio denominator."
    >
      {total > 0 ? (
        <div className={styles.layout}>
          <div className={styles.chartWrap}>
            <ResponsiveContainer width="100%" height={240}>
              <PieChart>
                <Pie
                  data={chartSlices}
                  dataKey="count"
                  nameKey="label"
                  innerRadius={56}
                  outerRadius={86}
                  stroke="rgba(255,255,255,0.92)"
                  strokeWidth={2}
                  paddingAngle={chartSlices.length > 1 ? 2 : 0}
                >
                  {chartSlices.map((slice) => (
                    <Cell key={slice.key} fill={STATUS_COLORS[slice.key] ?? "#94a3b8"} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(value: number, _name: string, item) => {
                    const payload = item?.payload as PortfolioStatusSlice | undefined;
                    return [formatNumber(value), `${payload?.label ?? "Status"} · ${formatPercent(payload?.share ?? 0)}`];
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className={styles.summary}>
            <div className={styles.headline}>
              <PortfolioTooltipLabel
                label="In-scope families in chart"
                tooltip={workspaceTooltipCopy.overview.inScopeFamiliesInChart}
              />
              <strong>{formatNumber(total)}</strong>
              <span>{outsideChartLabel}</span>
            </div>
            <div className={styles.list}>
              {chartSlices.map((slice) => (
                <div key={slice.key} className={styles.row}>
                  <div className={styles.label}>
                    <span className={styles.swatch} style={{ backgroundColor: STATUS_COLORS[slice.key] ?? "#94a3b8" }} />
                    <PortfolioTooltipLabel
                      label={slice.label}
                      tooltip={
                        slice.key === "fully_active"
                          ? workspaceTooltipCopy.overview.fullyActive
                          : slice.key === "partially_lapsed"
                            ? workspaceTooltipCopy.overview.partiallyLapsed
                            : workspaceTooltipCopy.overview.dead
                      }
                      textClassName={styles.labelText}
                    />
                  </div>
                  <span className={styles.count}>{formatNumber(slice.count)} families</span>
                  <span className={styles.share}>{formatPercent(slice.share)}</span>
                </div>
              ))}
            </div>
            <div className={styles.note}>Shares are calculated across the visible in-scope portfolio family set represented in this chart.</div>
          </div>
        </div>
      ) : (
        <p className="portfolio-empty-state">No in-scope family status mix is available for this portfolio.</p>
      )}
    </Surface>
  );
}
