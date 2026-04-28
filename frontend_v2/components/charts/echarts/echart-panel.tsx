"use client";

import dynamic from "next/dynamic";
import type { EChartsOption } from "echarts";
import type { CSSProperties } from "react";

const ReactECharts = dynamic(() => import("echarts-for-react"), { ssr: false });

type EChartPanelProps = {
  className?: string;
  option: EChartsOption;
  style?: CSSProperties;
};

export function EChartPanel({ className, option, style }: EChartPanelProps) {
  return (
    <div className={className}>
      <ReactECharts
        option={option}
        style={style ?? { height: 320, width: "100%" }}
        opts={{ renderer: "canvas" }}
        notMerge
        lazyUpdate
      />
    </div>
  );
}
