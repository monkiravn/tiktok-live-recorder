import { test, expect } from "@playwright/test";

test.describe("Recording Flow", () => {
  test("should create a recording and navigate to job detail", async ({
    page,
  }) => {
    await page.goto("/record");

    await expect(
      page.getByRole("heading", { name: /record now/i })
    ).toBeVisible();

    // Fill in the form
    await page.fill('input[id="room_id"]', "123456789");
    await page.fill('input[id="duration"]', "1800");

    // Mock the API call
    await page.route("/api/recordings", (route) => {
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          task_id: "test-recording-task-id",
          status: "PENDING",
        }),
      });
    });

    // Mock the job status API
    await page.route("/api/jobs/test-recording-task-id", (route) => {
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          task_id: "test-recording-task-id",
          status: "STARTED",
          result: {
            returncode: 0,
            files: [],
            s3: [],
            started_at: new Date().toISOString(),
            ended_at: null,
          },
        }),
      });
    });

    // Submit the form
    await page.click('button:has-text("Start Recording")');

    // Should navigate to job detail page
    await page.waitForURL(/\/jobs\/test-recording-task-id/);
    await expect(
      page.getByRole("heading", { name: /job detail/i })
    ).toBeVisible();
    await expect(page.locator("text=test-recording-task-id")).toBeVisible();
  });

  test("should validate recording form", async ({ page }) => {
    await page.goto("/record");

    // Try to submit without filling required fields
    await page.click('button:has-text("Start Recording")');

    // Should show validation error
    await expect(page.locator("text=Cần nhập room_id hoặc url")).toBeVisible();
  });

  test("should show configuration options", async ({ page }) => {
    await page.goto("/record");

    await expect(page.getByText("Room ID")).toBeVisible();
    await expect(page.getByText("URL (Alternative to Room ID)")).toBeVisible();
    await expect(page.getByText("Duration (seconds)")).toBeVisible();
    await expect(page.getByText("Proxy (optional)")).toBeVisible();
    await expect(page.getByText("Cookies Path (optional)")).toBeVisible();
  });
});
