"use client";

import { Info } from "lucide-react";
import { useCallback, useId, useLayoutEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";

type PortfolioMetricTooltipProps = {
  text: string;
};

export function PortfolioMetricTooltip({ text }: PortfolioMetricTooltipProps) {
  const triggerRef = useRef<HTMLSpanElement | null>(null);
  const [visible, setVisible] = useState(false);
  const [position, setPosition] = useState({ left: 0, top: 0 });
  const tooltipId = useId();

  const updatePosition = useCallback(() => {
    const trigger = triggerRef.current;
    if (!trigger || typeof window === "undefined") {
      return;
    }

    const rect = trigger.getBoundingClientRect();
    const tooltipWidth = Math.min(260, window.innerWidth - 24);
    const minLeft = tooltipWidth / 2 + 12;
    const maxLeft = window.innerWidth - tooltipWidth / 2 - 12;
    const centeredLeft = rect.left + rect.width / 2;

    setPosition({
      left: Math.min(Math.max(centeredLeft, minLeft), maxLeft),
      top: Math.max(rect.top - 10, 16),
    });
  }, []);

  useLayoutEffect(() => {
    if (!visible || typeof window === "undefined") {
      return;
    }

    updatePosition();
    window.addEventListener("resize", updatePosition);
    window.addEventListener("scroll", updatePosition, true);
    return () => {
      window.removeEventListener("resize", updatePosition);
      window.removeEventListener("scroll", updatePosition, true);
    };
  }, [updatePosition, visible]);

  return (
    <>
      <span
        ref={triggerRef}
        className="portfolio-metric-tooltip"
        tabIndex={0}
        aria-label={text}
        aria-describedby={visible ? tooltipId : undefined}
        onMouseEnter={() => setVisible(true)}
        onMouseLeave={() => setVisible(false)}
        onFocus={() => setVisible(true)}
        onBlur={() => setVisible(false)}
      >
        <Info size={12} aria-hidden="true" />
      </span>
      {visible && typeof document !== "undefined"
        ? createPortal(
            <span
              id={tooltipId}
              className="portfolio-metric-tooltip__bubble"
              role="tooltip"
              style={{ left: `${position.left}px`, top: `${position.top}px` }}
            >
              {text}
            </span>,
            document.body,
          )
        : null}
    </>
  );
}
