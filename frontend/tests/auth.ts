import { expect, type Page } from '@playwright/test';

export async function loginAsAdmin(page: Page) {
  await page.goto('/arena');
  await expect(page.getByRole('link', { name: 'Predict' })).toBeVisible();
}
