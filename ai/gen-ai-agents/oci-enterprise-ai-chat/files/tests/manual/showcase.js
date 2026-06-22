/**
 * OCI Generative AI Agents Hub - Full App Showcase
 *
 * Automated demo that walks through every major feature of the app.
 * Works with the real OCI API - does NOT depend on specific mock responses.
 *
 * Run:   node tests/showcase.spec.js
 * Requires: npm run dev on localhost:3000
 */

const { chromium } = require("playwright");

// ─── Config ────────────────────────────────────────────────────
const BASE = "http://localhost:3000";
const SLOW_MO = 50;
const TYPE_DELAY = 40; // ms between keystrokes

const wait = (page, ms) => page.waitForTimeout(ms);

const humanType = async (locator, text, delay = TYPE_DELAY) => {
  await locator.click();
  await locator.pressSequentially(text, { delay });
};

/**
 * Wait until the loading indicator (DotMatrixLoader) disappears,
 * meaning the assistant finished responding.
 */
const waitForResponse = async (page, timeout = 60000) => {
  // First wait a bit for loading to start
  await wait(page, 1500);
  // Then wait for loading to finish (no more DotMatrixLoader visible)
  try {
    await page.waitForFunction(
      () => {
        // Check if there's any loading indicator on page
        const loaders = document.querySelectorAll('[class*="loader"], [class*="Loader"]');
        const dots = document.querySelectorAll('svg circle[r]');
        // Also check for the "Thinking" text
        const thinking = document.querySelector('span');
        const isLoading = Array.from(loaders).some(el => el.offsetParent !== null);
        return !isLoading;
      },
      { timeout }
    );
  } catch {
    // Timeout is OK - just means response is still streaming
  }
  // Extra buffer for animations to settle
  await wait(page, 2000);
};

(async () => {
  console.log("🎬 Starting OCI Agents Hub Showcase...\n");

  const browser = await chromium.launch({
    headless: false,
    slowMo: SLOW_MO,
    args: ["--window-size=1440,900"],
  });

  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
  });

  const page = await context.newPage();

  try {
    // ═══════════════════════════════════════════════════════════
    // SCENE 1: Intro Page — animated brand reveal
    // ═══════════════════════════════════════════════════════════
    console.log("📍 Scene 1: Intro page");
    await page.goto(`${BASE}/intro`);
    // Flask at 0.5s, typing 2.2s→4.5s, chip at 4.6s
    await wait(page, 7000);

    // ═══════════════════════════════════════════════════════════
    // SCENE 2: Splash Page — logo + click to continue
    // ═══════════════════════════════════════════════════════════
    console.log("📍 Scene 2: Splash page");
    await page.goto(`${BASE}/splash`);
    await wait(page, 3500);
    await page.click("body");
    await wait(page, 1200);

    // ═══════════════════════════════════════════════════════════
    // SCENE 3: Main App — welcome animations
    // ═══════════════════════════════════════════════════════════
    console.log("📍 Scene 3: Main app loads");
    await page.waitForSelector("textarea", { timeout: 10000, state: "visible" });
    await wait(page, 3500); // welcome typing animation

    // ═══════════════════════════════════════════════════════════
    // SCENE 4: Change model in Header
    // ═══════════════════════════════════════════════════════════
    console.log("📍 Scene 4: Model selector");
    try {
      // Model text shows without prefix (e.g. "gpt-4.1")
      const modelText = page.getByText("gpt-4.1").first();
      await modelText.click({ timeout: 5000 });
      await wait(page, 1000);

      // Pick a different model
      const menuItem = page.getByRole("menuitem").nth(4); // pick 5th model
      await menuItem.click({ timeout: 3000 });
      await wait(page, 800);
    } catch {
      console.log("  (model selector skipped)");
      await page.keyboard.press("Escape").catch(() => {});
    }

    // ═══════════════════════════════════════════════════════════
    // SCENE 5: Send first message
    // ═══════════════════════════════════════════════════════════
    console.log("📍 Scene 5: First message");
    const textbox = page.locator("textarea").first();

    await humanType(textbox, "I need parts for the production line");
    await wait(page, 400);
    await textbox.press("Enter");
    console.log("  → Waiting for response...");
    await waitForResponse(page);

    // ═══════════════════════════════════════════════════════════
    // SCENE 6: Send second message (motor specs)
    // ═══════════════════════════════════════════════════════════
    console.log("📍 Scene 6: Second message");
    await humanType(
      textbox,
      "I need a 15HP motor with 380V for standard shift operation"
    );
    await wait(page, 400);
    await textbox.press("Enter");
    console.log("  → Waiting for response...");
    await waitForResponse(page);

    // If interactive choices appeared, click the first one
    try {
      const choiceBtn = page.locator('button').filter({
        hasText: /Advise me|advisory|decide/i,
      }).first();
      if (await choiceBtn.isVisible({ timeout: 3000 })) {
        console.log("  → Found interactive choice, clicking...");
        await wait(page, 1500);
        await choiceBtn.click();
        await waitForResponse(page);
      }
    } catch {
      // No interactive choices - that's fine
    }

    // ═══════════════════════════════════════════════════════════
    // SCENE 7: Try expanding chips (if any exist)
    // ═══════════════════════════════════════════════════════════
    console.log("📍 Scene 7: Expand chips");
    try {
      // Look for expandable chip elements
      const chips = page.locator('[class*="MuiChip"], [role="status"]').filter({
        hasText: /Planning|API|Search|Tool|Call|Agent/i,
      });
      const count = await chips.count();
      if (count > 0) {
        console.log(`  → Found ${count} chips, expanding first...`);
        await chips.first().click({ timeout: 3000 });
        await wait(page, 2500);
        await chips.first().click();
        await wait(page, 500);
      }
    } catch {
      console.log("  (no chips to expand)");
    }

    // ═══════════════════════════════════════════════════════════
    // SCENE 8: Click any remaining interactive buttons
    // ═══════════════════════════════════════════════════════════
    console.log("📍 Scene 8: Click available interactions");
    // Try clicking interactive option buttons sequentially
    for (let i = 0; i < 5; i++) {
      try {
        // Look for choice/action buttons (not copy, not nav)
        const actionButtons = page.locator('button').filter({
          hasText: /HD-2024|supplier|order|track|analyze|create|select/i,
        });
        const first = actionButtons.first();
        if (await first.isVisible({ timeout: 2000 })) {
          const btnText = await first.textContent();
          console.log(`  → Clicking: "${btnText.trim().substring(0, 50)}..."`);
          await wait(page, 1000);
          await first.click();
          await waitForResponse(page);
        } else {
          break;
        }
      } catch {
        break;
      }
    }

    // ═══════════════════════════════════════════════════════════
    // SCENE 9: Scroll through conversation
    // ═══════════════════════════════════════════════════════════
    console.log("📍 Scene 9: Scroll conversation");

    // Find the scrollable chat container (right column)
    await page.evaluate(() => {
      const containers = document.querySelectorAll("div");
      for (const el of containers) {
        if (el.scrollHeight > el.clientHeight && el.clientHeight > 200) {
          const style = window.getComputedStyle(el);
          if (style.overflowY === "auto" || style.overflowY === "scroll") {
            el.scrollTo({ top: 0, behavior: "smooth" });
            el._isScrollContainer = true;
            break;
          }
        }
      }
    });
    await wait(page, 1500);

    // Slow scroll down
    for (let i = 0; i < 6; i++) {
      await page.evaluate(() => {
        const containers = document.querySelectorAll("div");
        for (const el of containers) {
          if (el._isScrollContainer) {
            el.scrollBy({ top: 400, behavior: "smooth" });
            break;
          }
        }
      });
      await wait(page, 900);
    }

    // ═══════════════════════════════════════════════════════════
    // SCENE 10: Resize sidebar
    // ═══════════════════════════════════════════════════════════
    console.log("📍 Scene 10: Resize sidebar");
    try {
      const dividerPos = await page.evaluate(() => {
        const allDivs = document.querySelectorAll("div");
        for (const div of allDivs) {
          const style = window.getComputedStyle(div);
          if (style.cursor === "col-resize" && div.offsetWidth <= 10) {
            const rect = div.getBoundingClientRect();
            return { x: rect.x + rect.width / 2, y: rect.y + rect.height / 2 };
          }
        }
        return null;
      });

      if (dividerPos) {
        await page.mouse.move(dividerPos.x, dividerPos.y);
        await wait(page, 200);
        await page.mouse.down();
        // Drag left (shrink sidebar)
        for (let x = dividerPos.x; x > dividerPos.x - 120; x -= 8) {
          await page.mouse.move(x, dividerPos.y);
          await wait(page, 20);
        }
        await wait(page, 400);
        // Drag right (expand sidebar)
        for (let x = dividerPos.x - 120; x < dividerPos.x + 80; x += 8) {
          await page.mouse.move(x, dividerPos.y);
          await wait(page, 20);
        }
        await page.mouse.up();
        await wait(page, 300);
        // Return to original
        await page.mouse.move(dividerPos.x + 80, dividerPos.y);
        await page.mouse.down();
        for (let x = dividerPos.x + 80; x >= dividerPos.x; x -= 8) {
          await page.mouse.move(x, dividerPos.y);
          await wait(page, 20);
        }
        await page.mouse.up();
        await wait(page, 500);
      }
    } catch {
      console.log("  (resize skipped)");
    }

    // ═══════════════════════════════════════════════════════════
    // SCENE 11: Settings — Appearance
    // ═══════════════════════════════════════════════════════════
    console.log("📍 Scene 11: Settings — Appearance");
    await page.goto(`${BASE}/settings/appearance`);
    await wait(page, 2000);

    // Show the fields (just look at them)
    const titleInput = page.locator('input[type="text"]').first();
    if (await titleInput.isVisible({ timeout: 2000 })) {
      await titleInput.click();
      await wait(page, 800);
    }

    // ═══════════════════════════════════════════════════════════
    // SCENE 12: Settings — Prompts
    // ═══════════════════════════════════════════════════════════
    console.log("📍 Scene 12: Settings — Prompts");
    await page.goto(`${BASE}/settings/prompts`);
    await wait(page, 1500);

    // Click through sub-tabs
    for (const tabName of ["System", "Instructions", "Widgets"]) {
      try {
        const tab = page.getByText(tabName, { exact: true }).first();
        if (await tab.isVisible({ timeout: 1500 })) {
          await tab.click();
          await wait(page, 1200);
        }
      } catch {
        // tab not found
      }
    }

    // ═══════════════════════════════════════════════════════════
    // SCENE 13: Settings — Tools / MCP
    // ═══════════════════════════════════════════════════════════
    console.log("📍 Scene 13: Settings — Tools");
    await page.goto(`${BASE}/settings/tools`);
    await wait(page, 2500);

    // ═══════════════════════════════════════════════════════════
    // SCENE 14: New Conversation
    // ═══════════════════════════════════════════════════════════
    console.log("📍 Scene 14: New conversation");
    await page.goto(BASE);
    await page.waitForSelector("textarea", { timeout: 10000, state: "visible" });
    await wait(page, 2000);

    // Show recent conversations in sidebar
    console.log("  → Sidebar with recent conversations");
    await wait(page, 1500);

    // Click new conversation
    try {
      const newConvBtn = page.getByRole("button", { name: "New conversation" });
      await newConvBtn.click({ timeout: 3000 });
      await wait(page, 2000);
    } catch {
      console.log("  (new conversation button not found)");
    }

    // ═══════════════════════════════════════════════════════════
    // SCENE 15: Quick follow-up message
    // ═══════════════════════════════════════════════════════════
    console.log("📍 Scene 15: Quick message");
    const textbox2 = page.locator("textarea").first();
    await humanType(textbox2, "What can you help me with today?");
    await wait(page, 400);
    await textbox2.press("Enter");
    await waitForResponse(page);

    // ═══════════════════════════════════════════════════════════
    // SCENE 16: Sample Widgets page
    // ═══════════════════════════════════════════════════════════
    console.log("📍 Scene 16: Sample widgets");
    await page.goto(`${BASE}/sample-widgets`);
    await wait(page, 2000);

    // Slow scroll through widgets
    for (let i = 0; i < 6; i++) {
      await page.evaluate(() => window.scrollBy({ top: 350, behavior: "smooth" }));
      await wait(page, 1200);
    }

    // ═══════════════════════════════════════════════════════════
    // SCENE 17: TextField demo page
    // ═══════════════════════════════════════════════════════════
    console.log("📍 Scene 17: TextField page");
    await page.goto(`${BASE}/textfield`);
    await wait(page, 4500); // typing animations

    const tfInput = page.locator("textarea").first();
    try {
      if (await tfInput.isVisible({ timeout: 3000 })) {
        await humanType(tfInput, "Show me the Q4 2025 inventory report", 50);
        await wait(page, 2000);
      }
    } catch {
      // textfield page might not have textarea
    }

    // ═══════════════════════════════════════════════════════════
    // FINALE: Back to intro
    // ═══════════════════════════════════════════════════════════
    console.log("📍 Finale: Back to intro");
    await page.goto(`${BASE}/intro`);
    await wait(page, 7000);

    console.log("\n✅ Showcase complete!");
  } catch (error) {
    console.error(`\n❌ Error at: ${error.message}`);
  } finally {
    console.log("Closing browser in 3s...");
    await wait(page, 3000);
    await browser.close();
  }
})();
