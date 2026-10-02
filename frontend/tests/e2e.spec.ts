import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test('App Shell Axe Check', async ({ page }) => {
  await page.goto('http://localhost:5173/');
  const accessibilityScanResults = await new AxeBuilder({ page }).analyze();
  expect(accessibilityScanResults.violations).toEqual([]);
});

test('Theme Persistence', async ({ page }) => {
  await page.goto('http://localhost:5173/');
  const root = page.locator('html');
  await expect(root).toHaveAttribute('data-theme', 'dark');

  // Click theme toggle
  await page.getByLabel('Toggle theme').click();
  await expect(root).toHaveAttribute('data-theme', 'light');

  // Reload and check
  await page.reload();
  await expect(root).toHaveAttribute('data-theme', 'light');
});

test.describe('3D Fallbacks', () => {
  test.use({ reducedMotion: 'reduce' });

  test('Reduced motion triggers fallback', async ({ page }) => {
    await page.goto('http://localhost:5173/3d');
    const fallback = page.getByTestId('scene-fallback');
    await expect(fallback).toBeVisible();
    await expect(fallback).toHaveText(/disabled or unavailable/);
  });
});
