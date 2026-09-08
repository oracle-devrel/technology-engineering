import { expect } from '@playwright/test';

// Type a message and submit, retrying until the user bubble actually renders.
// The textarea becomes visible BEFORE useChat's genaiService finishes its async
// init (IndexedDB session sync); an Enter pressed inside that window is dropped
// with only a toast. Under parallel dev-server load that window stretches long
// enough to eat the first submit, so a single Enter makes chat-flow specs flaky.
export async function sendChatMessage(page, text) {
  const input = page.locator('textarea').first();
  await expect(input).toBeVisible({ timeout: 30_000 });
  await expect(async () => {
    await input.fill(text);
    await input.press('Enter');
    await expect(page.getByText(text).first()).toBeVisible({ timeout: 1_500 });
  }).toPass({ timeout: 20_000 });
}
