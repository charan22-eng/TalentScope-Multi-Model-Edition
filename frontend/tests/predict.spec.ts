import { test, expect } from '@playwright/test';
import { loginAsAdmin } from './auth';

test.describe('Predict Flow', () => {
  test('User can run a prediction and advisor locks non-actionable features', async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto('http://localhost:5173/predict');
    
    await expect(page.getByRole('heading', { name: 'TalentScope Prediction Suite' })).toBeVisible({ timeout: 5000 });
    
    // Default mode, Experience is enabled
    const expInput = page.locator('#experience_years');
    await expect(expInput).toBeEnabled();
    
    // Check advisor mode
    const advisorToggle = page.getByRole('button', { name: /What-If Advisor: OFF/ });
    await advisorToggle.click();
    
    // Experience should now be disabled (non-actionable)
    await expect(expInput).toBeDisabled();
    
    // Attendance should still be actionable
    const attInput = page.locator('#attendance');
    await expect(attInput).toBeEnabled();
    
    // Submit
    await page.getByRole('button', { name: 'Run All 7 Models' }).click();
    
    // Verify result
    await expect(page.getByRole('heading', { name: '7-Model Consensus Arena' })).toBeVisible({ timeout: 15000 });
    await expect(page.getByText('Model Agreement Meter')).toBeVisible();
  });
});
