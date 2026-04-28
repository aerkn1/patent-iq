import { expect, test, type Page } from "@playwright/test";

import { expectNoSeriousAxeViolations } from "./support/accessibility";
import {
  MOCK_FAMILY_ID,
  MOCK_PUBLICATION_ID,
  MOCK_PORTFOLIO_OWNER_ID,
  mockPatentIqApis,
} from "./support/mock-patentiq-api";

async function openHome(page: Page) {
  await page.goto("/");
  await expect(
    page.getByRole("heading", { level: 1, name: "Corporate IP intelligence workspaces" }),
  ).toBeVisible();
}

async function openPortfolioEntry(page: Page) {
  await page.goto("/portfolio");
  await expect(
    page.getByRole("heading", { level: 1, name: "Portfolio intelligence workspace" }),
  ).toBeVisible();
}

async function openMarket(page: Page) {
  await page.goto("/market");
  await expect(page.getByRole("heading", { level: 1, name: "Market command center" })).toBeVisible();
}

async function openPortfolioWorkspace(page: Page) {
  await page.goto(`/portfolio/${MOCK_PORTFOLIO_OWNER_ID}`);
  await expect(page.getByRole("heading", { level: 1, name: "Acme Holdings" })).toBeVisible();
}

async function openFamilyWorkspace(page: Page) {
  await page.goto(`/family/${MOCK_FAMILY_ID}`);
  await expect(
    page.getByRole("heading", { level: 1, name: "Acme signal routing family" }),
  ).toBeVisible();
}

async function openPublicationWorkspace(page: Page) {
  await page.goto(`/publication/${MOCK_PUBLICATION_ID}`);
  await expect(page.getByRole("heading", { level: 1, name: MOCK_PUBLICATION_ID })).toBeVisible();
}

function portfolioWorkspaceTabs(page: Page) {
  return page.getByRole("tablist", { name: "Portfolio workspace sections" });
}

test.beforeEach(async ({ page }) => {
  await mockPatentIqApis(page);
});

test.describe("frontend_v2 smoke coverage", () => {
  test("loads the enterprise home route with primary navigation", async ({ page }) => {
    await openHome(page);

    const primaryNav = page.getByRole("navigation", { name: "Primary" });

    await expect(primaryNav).toBeVisible();
    await expect(primaryNav.getByRole("link", { name: "Home" })).toBeVisible();
    await expect(primaryNav.getByRole("link", { name: "Portfolios" })).toBeVisible();
    await expect(primaryNav.getByRole("link", { name: "Markets" })).toBeVisible();
    await expect(page.getByText("Portfolio, family, market")).toBeVisible();
  });

  test("loads the portfolio entry search surface", async ({ page }) => {
    await openPortfolioEntry(page);

    await expect(page.getByRole("combobox", { name: "Search portfolio owner" })).toBeVisible();
    await expect(page.getByText("Portfolio Lookup")).toBeVisible();
  });

  test("loads the market workspace and supports segment switching", async ({ page }) => {
    await openMarket(page);

    await expect(page.getByRole("heading", { level: 3, name: "Segment league table" })).toBeVisible();
    await expect(page.getByRole("heading", { level: 3, name: "Computer technology drawer" })).toBeVisible();
    await expect(page.getByRole("heading", { level: 3, name: "Jurisdiction density" })).toBeVisible();

    await page.getByLabel("Selected segment").selectOption("Digital communication");

    await expect(page).toHaveURL(/segment=Digital(?:\+|%20)communication/);
    await expect(page.getByRole("heading", { level: 3, name: "Digital communication drawer" })).toBeVisible();
  });

  test("loads the portfolio workspace with mocked analytics data", async ({ page }) => {
    await openPortfolioWorkspace(page);

    await expect(portfolioWorkspaceTabs(page)).toBeVisible();
    await expect(page.getByRole("heading", { level: 2, name: "Portfolio summary" })).toBeVisible();
    await expect(page.getByText("Forecast-ready coverage")).toBeVisible();
    await expect(page.getByText("Acme Holdings", { exact: true })).toBeVisible();
  });

  test("loads the portfolio citations tab and its filter controls", async ({ page }) => {
    await openPortfolioWorkspace(page);

    await portfolioWorkspaceTabs(page).getByRole("tab", { name: /^Citations/i }).click();

    await expect(page).toHaveURL(/tab=citations/);
    await expect(page.getByRole("heading", { level: 3, name: "Citation summary" })).toBeVisible();
    await expect(page.getByRole("heading", { level: 3, name: "Forward citation chronology" })).toBeVisible();
    await expect(page.getByRole("heading", { level: 3, name: "Top attacking assignees" })).toBeVisible();

    await page.getByLabel("Attacker field").selectOption("Digital communications");

    await expect(page.getByText("Field: Digital communications").first()).toBeVisible();
  });

  test("loads the portfolio technology tab and supports field-cluster selection", async ({ page }) => {
    await openPortfolioWorkspace(page);

    await portfolioWorkspaceTabs(page).getByRole("tab", { name: /^Technology/i }).click();

    await expect(page).toHaveURL(/tab=fields/);
    await expect(page.getByRole("heading", { level: 3, name: "Current field exposure" })).toBeVisible();
    await expect(page.getByRole("heading", { level: 3, name: "Current market overlay" })).toBeVisible();
    await expect(page.getByRole("heading", { level: 3, name: "Field chronology" })).toBeVisible();
    await expect(page.getByRole("heading", { level: 3, name: "Normalized time-slice compare" })).toBeVisible();

    const clusterTabs = page.getByRole("tablist", { name: "Portfolio field clusters" });

    await clusterTabs.getByRole("tab", { name: "Signal routing" }).click();

    await expect(page).toHaveURL(/field=Signal(?:\+|%20)routing/);
    await expect(clusterTabs.getByRole("tab", { name: "Signal routing" })).toHaveAttribute("aria-selected", "true");
  });

  test("loads the portfolio forecast tab and reacts to horizon and scope changes", async ({ page }) => {
    await openPortfolioWorkspace(page);

    await portfolioWorkspaceTabs(page).getByRole("tab", { name: /^Forecast/i }).click();

    await expect(page).toHaveURL(/tab=forecast/);
    await expect(page.getByRole("heading", { level: 3, name: "Forecast outlook (interval-first)" })).toBeVisible();
    await expect(page.getByRole("heading", { level: 3, name: "Pending-grant pipeline" })).toBeVisible();
    await expect(page.getByRole("heading", { level: 3, name: "Forecast contributors" })).toBeVisible();

    const horizonTabs = page.getByRole("tablist", { name: "Forecast horizon" });

    await horizonTabs.getByRole("tab", { name: "5y" }).click();

    await expect(horizonTabs.getByRole("tab", { name: "5y" })).toHaveAttribute("aria-selected", "true");
    await expect(page.getByText("5y forecast")).toBeVisible();

    await page.getByLabel("Contributor scope").selectOption("phase04_lapse_risk");

    await expect(page.getByText("US · phase04_lapse_risk")).toBeVisible();
  });

  test("loads the family workspace with mocked family analytics data", async ({ page }) => {
    await openFamilyWorkspace(page);

    await expect(page.getByRole("tablist", { name: "Family workspace sections" })).toBeVisible();
    await expect(page.getByRole("heading", { level: 2, name: "Overview" })).toBeVisible();
    await expect(page.getByRole("heading", { level: 3, name: "Explainability metrics" })).toBeVisible();
    await expect(page.getByText("Modeled coverage only")).toBeVisible();
  });

  test("loads the publication workspace with mocked document evidence", async ({ page }) => {
    await openPublicationWorkspace(page);

    await expect(page.getByRole("tablist", { name: "Publication workspace sections" })).toBeVisible();
    await expect(page.getByText("Signal routing for adaptive network switching")).toBeVisible();
    await expect(page.getByRole("heading", { level: 3, name: "Bibliographic summary" })).toBeVisible();
    await expect(page.getByRole("heading", { level: 3, name: "Title" })).toBeVisible();
  });

  test("navigates from family member evidence into the publication workspace", async ({ page }) => {
    await openFamilyWorkspace(page);

    await page.getByRole("tablist", { name: "Family workspace sections" }).getByRole("tab", { name: /^Evidence/i }).click();
    await expect(page.getByRole("link", { name: MOCK_PUBLICATION_ID })).toBeVisible();
    await page.getByRole("link", { name: MOCK_PUBLICATION_ID }).click();

    await expect(page).toHaveURL(new RegExp(`/publication/${MOCK_PUBLICATION_ID}$`));
    await expect(page.getByRole("heading", { level: 1, name: MOCK_PUBLICATION_ID })).toBeVisible();
  });
});

test.describe("frontend_v2 accessibility coverage", () => {
  const routeChecks: Array<{
    name: string;
    open: (page: Page) => Promise<void>;
  }> = [
    { name: "home", open: openHome },
    { name: "portfolio entry", open: openPortfolioEntry },
    { name: "market workspace", open: openMarket },
    { name: "portfolio workspace", open: openPortfolioWorkspace },
    { name: "family workspace", open: openFamilyWorkspace },
    { name: "publication workspace", open: openPublicationWorkspace },
  ];

  for (const routeCheck of routeChecks) {
    test(`has no serious accessibility violations on ${routeCheck.name}`, async ({ page }) => {
      await routeCheck.open(page);
      await expectNoSeriousAxeViolations(page);
    });
  }

  test("has no serious accessibility violations across portfolio drilldown tabs", async ({ page }) => {
    await openPortfolioWorkspace(page);

    await portfolioWorkspaceTabs(page).getByRole("tab", { name: /^Citations/i }).click();
    await expect(page.getByRole("heading", { level: 3, name: "Citation summary" })).toBeVisible();
    await expectNoSeriousAxeViolations(page);

    await portfolioWorkspaceTabs(page).getByRole("tab", { name: /^Technology/i }).click();
    await expect(page.getByRole("heading", { level: 3, name: "Current field exposure" })).toBeVisible();
    await expectNoSeriousAxeViolations(page);

    await portfolioWorkspaceTabs(page).getByRole("tab", { name: /^Forecast/i }).click();
    await expect(page.getByRole("heading", { level: 3, name: "Forecast outlook (interval-first)" })).toBeVisible();
    await expectNoSeriousAxeViolations(page);
  });
});
