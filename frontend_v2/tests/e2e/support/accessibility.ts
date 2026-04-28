import { expect, type Page } from "@playwright/test";
import axe from "axe-core";

type AxeViolation = {
  description: string;
  help: string;
  id: string;
  impact: string | null;
  nodes: Array<{
    failureSummary?: string;
    target: string[];
  }>;
};

function formatViolations(violations: AxeViolation[]): string {
  return violations
    .map((violation) => {
      const nodes = violation.nodes
        .map((node) => `${node.target.join(" ")} ${node.failureSummary ?? ""}`.trim())
        .join(" | ");

      return `${violation.id} [${violation.impact ?? "unknown"}] ${violation.help}: ${nodes}`;
    })
    .join("\n");
}

export async function expectNoSeriousAxeViolations(page: Page) {
  const result = await page.evaluate(async (source) => {
    const existing = document.querySelector("script[data-axe='true']");
    if (!existing) {
      const script = document.createElement("script");
      script.type = "text/javascript";
      script.dataset.axe = "true";
      script.textContent = source;
      document.head.appendChild(script);
    }

    const axeGlobal = (window as typeof window & {
      axe: {
        run: (context?: Element | Document, options?: unknown) => Promise<{
          violations: AxeViolation[];
        }>;
      };
    }).axe;

    return axeGlobal.run(document, {
      runOnly: {
        type: "tag",
        values: ["wcag2a", "wcag2aa"],
      },
    });
  }, axe.source);

  const seriousViolations = result.violations.filter(
    (violation) => violation.impact === "serious" || violation.impact === "critical",
  );

  expect(
    seriousViolations,
    seriousViolations.length > 0 ? formatViolations(seriousViolations) : undefined,
  ).toEqual([]);
}
