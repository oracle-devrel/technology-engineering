// UI smoke tests: the app boots, the chat surface renders, the settings pages
// mount. Anything deeper (real chats, tool runs) needs OCI credentials and
// stays out of the automated suite.
import { test, expect } from '@playwright/test';

test('home renders the chat input', async ({ page }) => {
  await page.goto('/');
  await expect(page.locator('textarea').first()).toBeVisible({ timeout: 30000 });
});

test('settings → tools renders the native tool list', async ({ page }) => {
  await page.goto('/settings/tools');
  await expect(page.getByText('Text to SQL').first()).toBeVisible({ timeout: 30000 });
});

test('health endpoint responds', async ({ request }) => {
  const res = await request.get('/ready');
  expect(res.ok()).toBeTruthy();
});
