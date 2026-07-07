import path from "node:path"
import { defineConfig, devices } from "@playwright/test"

const port = Number(process.env.PLAYWRIGHT_PORT ?? 3012)
const baseURL = process.env.PLAYWRIGHT_BASE_URL ?? `http://127.0.0.1:${port}`
const repoRoot = path.resolve(__dirname, "..")
const trustedInternalHosts = "logan-forge-lb.logan-forge.svc,logan-forge-lb.logan-forge.svc.cluster.local"

export default defineConfig({
  testDir: "./tests/e2e",
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1,
  reporter: [["list"], ["html", { outputFolder: "playwright-report", open: "never" }]],
  use: {
    baseURL,
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
    actionTimeout: 10_000,
    navigationTimeout: 30_000,
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: process.env.PLAYWRIGHT_BASE_URL
    ? undefined
    : {
        command: `pnpm exec next dev --hostname 127.0.0.1 --port ${port}`,
        url: baseURL,
        reuseExistingServer: !process.env.CI,
        timeout: 120_000,
        env: {
          LOGAN_DETECTIONS_REPO: repoRoot,
          FORGE_TRUSTED_INTERNAL_HOSTS: trustedInternalHosts,
          // Exercise the production-like "one trusted reverse proxy" mode so the
          // rate-limit test verifies the right-anchored X-Forwarded-For keying.
          FORGE_TRUSTED_PROXY_HOPS: "1",
          FORGE_ALLOWED_ORIGINS: [
            `http://127.0.0.1:${port}`,
            `http://localhost:${port}`,
            "https://convert.octodemo.cloud",
            "https://forge.octodemo.cloud",
            "http://logan-forge-lb.logan-forge.svc",
            "http://logan-forge-lb.logan-forge.svc.cluster.local",
          ].join(","),
        },
      },
})
