"use client";

import { TrendingUp } from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { formatDecimal, formatPercent } from "@/components/portfolio/portfolio-format";
import { Surface } from "@/components/ui/surface";
import { getRiskBandColor } from "@/lib/design/chart-tokens";
import type { ForecastHorizon, PortfolioForecastPayload } from "@/lib/types/portfolio-v2";
import styles from "@/components/portfolio/forecast-panels.module.css";

type PortfolioForecastPanelProps = {
  forecast: PortfolioForecastPayload;
  horizon: ForecastHorizon;
  onHorizonChange?: (horizon: ForecastHorizon) => void;
  errorMessage?: string;
};

export function PortfolioForecastPanel({
  forecast,
  horizon,
  onHorizonChange,
  errorMessage,
}: PortfolioForecastPanelProps) {
  const interval = horizon === "3y" ? forecast.interval3y : forecast.interval5y;
  const riskRows = horizon === "3y" ? forecast.risk12m : forecast.risk24m;
  const leadingRiskBand = [...riskRows].sort((left, right) => right.share - left.share)[0];
  const riskChartRows = riskRows.map((row) => ({
    ...row,
    sharePercent: row.share * 100,
  }));

  return (
    <Surface
      className="portfolio-forecast-panel"
      title="Forecast outlook"
      icon={<TrendingUp size={16} />}
      actions={
        <div className="portfolio-horizon-switcher" role="tablist" aria-label="Forecast horizon">
          <button
            type="button"
            role="tab"
            aria-selected={horizon === "3y"}
            className={horizon === "3y" ? "selected" : ""}
            onClick={() => onHorizonChange?.("3y")}
          >
            3y
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={horizon === "5y"}
            className={horizon === "5y" ? "selected" : ""}
            onClick={() => onHorizonChange?.("5y")}
          >
            5y
          </button>
        </div>
      }
    >
      {errorMessage ? <p className="portfolio-error">{errorMessage}</p> : null}

      <div className="portfolio-section-summary">
        <article className="portfolio-section-summary__card">
          <span className="portfolio-section-summary__label">Expected midpoint</span>
          <strong>{formatDecimal(interval.total, 1)}</strong>
          <span>Directional forecast midpoint for the selected horizon.</span>
        </article>
        <article className="portfolio-section-summary__card">
          <span className="portfolio-section-summary__label">Forecast range</span>
          <strong>
            {formatDecimal(interval.low, 1)} to {formatDecimal(interval.high, 1)}
          </strong>
          <span>Read the interval as the planning output, not a point estimate.</span>
        </article>
        <article className="portfolio-section-summary__card">
          <span className="portfolio-section-summary__label">Dominant risk band</span>
          <strong>{leadingRiskBand ? leadingRiskBand.label.toUpperCase() : "—"}</strong>
          <span>{leadingRiskBand ? `${formatPercent(leadingRiskBand.share)} of current risk mix` : "No risk rows loaded."}</span>
        </article>
      </div>

      <div className={styles.chartSurface}>
        <h4 className={styles.chartTitle}>Risk-band distribution</h4>
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={riskChartRows} layout="vertical" margin={{ top: 20, right: 16, left: 16, bottom: 4 }}>
            <CartesianGrid strokeDasharray="3 3" horizontal={false} />
            <XAxis type="number" tickFormatter={(value: number) => `${value}%`} />
            <YAxis type="category" dataKey="label" width={80} tickLine={false} axisLine={false} />
            <Tooltip
              formatter={(value: number, name: string) => {
                if (name === "sharePercent") {
                  return [`${value.toFixed(1)}%`, "Risk share"];
                }
                return [`${value}`, "Families"];
              }}
              labelFormatter={(label) => `Risk band: ${String(label).toUpperCase()}`}
            />
            <Bar dataKey="sharePercent" radius={[0, 10, 10, 0]}>
              {riskChartRows.map((row) => (
                <Cell key={row.label} fill={getRiskBandColor(row.label)} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      <p className={`portfolio-small-note ${styles.footnote}`}>
        Forecast values are portfolio-level planning signals. Use the interval and risk mix as directional output rather than exact realized outcomes.
      </p>
    </Surface>
  );
}
