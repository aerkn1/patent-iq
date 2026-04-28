import { defineConfig } from "@playwright/test";

const chromeExecutablePath =
  process.platform === "darwin"
    ? "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    : undefined;

export default defineConfig({
  testDir: "./tests/e2e",
  fullyParallel: false,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 2 : 0,
  reporter: "list",
  workers: 1,
  use: {
    baseURL: "http://127.0.0.1:3000",
    trace: "on-first-retry",
    viewport: {
      width: 1440,
      height: 1024,
    },
    launchOptions: chromeExecutablePath
      ? {
          executablePath: chromeExecutablePath,
        }
      : undefined,
  },
  webServer: {
    command: "npm run start -- --hostname 127.0.0.1 --port 3000",
    url: "http://127.0.0.1:3000",
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
    env: {
      ...process.env,
      NEXT_PUBLIC_API_BASE_URL: "http://127.0.0.1:8000",
    },
  },
});
