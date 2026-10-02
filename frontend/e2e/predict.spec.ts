import { test, expect } from '@playwright/test';

test.describe('Predict Flow', () => {
  test('User can login and run a prediction', async ({ page }) => {
    // Navigate to local dev server (assuming 5173 for vite)
    // For CI/CD we might use the dockerized port 80
    await page.goto('http://localhost:5173');

    // Should see login page
    await expect(page.locator('text=HR Insights Login')).toBeVisible();

    // Fill login
    await page.fill('input[type="email"]', 'admin@hr.local');
    await page.fill('input[type="password"]', 'admin123');
    await page.click('button[type="submit"]');

    // Should arrive at Dashboard
    await expect(page.locator('text=Welcome to HR Insights')).toBeVisible();

    // Navigate to Predict
    await page.click('text=Predict Performance');
    await expect(page.locator('h1', { hasText: 'Predict Performance' })).toBeVisible();

    // Run prediction with default data
    await page.click('button[type="submit"]');

    // Wait for result
    await expect(page.locator('text=Analysis Result')).toBeVisible();
    await expect(page.locator('text=Confidence')).toBeVisible();
  });
});
