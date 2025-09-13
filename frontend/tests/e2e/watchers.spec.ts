import { test, expect } from "@playwright/test";

test.describe("Watchers Management", () => {
  test("should create a watcher with room_id", async ({ page }) => {
    await page.goto("/watchers");

    await expect(
      page.getByRole("heading", { name: /watchers/i })
    ).toBeVisible();

    // Fill in the form
    await page.fill('input[id="room_id"]', "123456789");
    await page.fill('input[id="poll_interval"]', "30");

    // Mock the API call to prevent actual watcher creation
    await page.route("/api/watchers", (route) => {
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ task_id: "test-task-id", status: "PENDING" }),
      });
    });

    // Submit the form
    await page.click('button:has-text("Create Watcher")');

    // Should show success toast (might need to wait for it)
    await expect(page.locator("text=Watcher created successfully")).toBeVisible(
      { timeout: 5000 }
    );
  });

  test("should validate form input", async ({ page }) => {
    await page.goto("/watchers");

    // Try to submit without filling required fields
    await page.click('button:has-text("Create Watcher")');

    // Should show validation error
    await expect(page.locator("text=Cần nhập room_id hoặc url")).toBeVisible();
  });

  test("should show delete watcher section", async ({ page }) => {
    await page.goto("/watchers");

    await expect(
      page.getByRole("heading", { name: /delete watcher/i })
    ).toBeVisible();
    await expect(
      page.getByPlaceholder("Enter room_id or url to delete")
    ).toBeVisible();
  });
});
