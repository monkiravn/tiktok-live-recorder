import { test, expect } from "@playwright/test";

test.describe("Dashboard", () => {
  test("should load dashboard page", async ({ page }) => {
    await page.goto("/");

    await expect(
      page.getByRole("heading", { name: /dashboard/i })
    ).toBeVisible();
    await expect(page.getByText("Active Watchers")).toBeVisible();
    await expect(page.getByText("Running Jobs")).toBeVisible();
  });

  test("should show health status", async ({ page }) => {
    await page.goto("/");

    // Wait for health checks to complete
    await expect(page.locator("text=API:")).toBeVisible({ timeout: 10000 });
    await expect(page.locator("text=Workers:")).toBeVisible({ timeout: 10000 });
  });

  test("should navigate to other pages", async ({ page }) => {
    await page.goto("/");

    // Test navigation to watchers
    await page.click("text=Watchers");
    await expect(
      page.getByRole("heading", { name: /watchers/i })
    ).toBeVisible();

    // Test navigation to jobs
    await page.click("text=Jobs");
    await expect(page.getByRole("heading", { name: /jobs/i })).toBeVisible();

    // Test navigation to files
    await page.click("text=Files");
    await expect(page.getByRole("heading", { name: /files/i })).toBeVisible();

    // Test navigation to record
    await page.click("text=Record Now");
    await expect(
      page.getByRole("heading", { name: /record now/i })
    ).toBeVisible();
  });
});
