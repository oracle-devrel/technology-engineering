const { chromium } = require("playwright");

(async () => {
  const browser = await chromium.launch({
    headless: false,
    slowMo: 150,
  });

  const page = await browser.newPage();

  // Correct port
  await page.goto("http://localhost:3004/");

  // Wait for the text field to appear and be visible
  await page.waitForSelector('textarea[placeholder="Type anything..."]', {
    timeout: 10000,
    state: "visible",
  });

  // First message
  const textbox = page.locator('textarea[placeholder="Type anything..."]');
  await textbox.click();
  await textbox.fill("I need parts for the production line");
  await textbox.press("Enter");

  // Wait for response and animations to complete
  await page.waitForTimeout(5000);

  // Second message
  await textbox.click();
  await textbox.fill(
    "I need a 15HP motor with 380V for standard shift operation"
  );
  await textbox.press("Enter");

  // Wait for the interactive choices to appear
  await page.waitForSelector(
    'button:has-text("Advise me, but I want to decide")',
    {
      timeout: 10000,
      state: "visible",
    }
  );

  // Click the correct button with full text
  await page
    .getByRole("button", { name: "Advise me, but I want to decide" })
    .click();

  // Wait for the HD-2024 option to appear
  await page.waitForSelector('button:has-text("HD-2024")', {
    timeout: 15000,
    state: "visible",
  });

  // Click HD-2024 option
  await page
    .getByRole("button", {
      name: "HD-2024 - Heavy-duty conveyor belt motor (15HP, 380V)",
    })
    .click();

  // Wait for "Ask all 3 suppliers" button
  await page.waitForSelector(
    'button:has-text("Ask all 3 suppliers for their prices")',
    {
      timeout: 15000,
      state: "visible",
    }
  );

  await page
    .getByRole("button", { name: "Ask all 3 suppliers for their prices" })
    .click();

  // Wait for "Analyze current offers" button
  await page.waitForSelector('button:has-text("Analyze current offers")', {
    timeout: 15000,
    state: "visible",
  });

  await page
    .getByRole("button", { name: "Analyze current offers (2 received)" })
    .click();

  // Wait for "Create order" button
  await page.waitForSelector(
    'button:has-text("Create order with TechParts Inc")',
    {
      timeout: 15000,
      state: "visible",
    }
  );

  await page
    .getByRole("button", { name: "Create order with TechParts Inc ($2,970)" })
    .click();

  // Wait for "Track order status" button
  await page.waitForSelector('button:has-text("Track order status")', {
    timeout: 15000,
    state: "visible",
  });

  await page.getByRole("button", { name: "Track order status" }).click();

  // Wait for final response
  await page.waitForTimeout(5000);

  // Keep browser open for a bit to see results
  await page.waitForTimeout(3000);

  await browser.close();
})();
