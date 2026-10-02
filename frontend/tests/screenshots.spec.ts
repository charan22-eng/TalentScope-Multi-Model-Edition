import { test } from '@playwright/test';
import fs from 'fs';
import path from 'path';

const __dirname = import.meta.dirname || __dirname;

test('Capture Screenshots', async ({ page }) => {
  const routes = [
    { name: 'home', url: '/' },
    { name: 'predict', url: '/predict' },
    { name: 'batch', url: '/batch' },
    { name: 'dashboard', url: '/dashboard' },
    { name: 'model-lab', url: '/model-lab' },
    { name: 'methodology', url: '/methodology' },
    { name: 'data-explorer', url: '/data-explorer' },
  ];
  
  const dateStr = new Date().toISOString().split('T')[0];
  const sha = 'v0.7'; // mock sha
  
  const outDir = path.join(__dirname, '../../reports/evidence/phase-8/screenshots');
  if (!fs.existsSync(outDir)) {
    fs.mkdirSync(outDir, { recursive: true });
  }

  for (const route of routes) {
    await page.goto(`http://localhost:5173${route.url}`);
    await page.waitForTimeout(500); // Wait for render
    
    // Desktop
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.screenshot({ path: path.join(outDir, `${route.name}-desktop-${dateStr}-${sha}.png`), fullPage: true });
    
    // Mobile
    await page.setViewportSize({ width: 360, height: 640 });
    await page.screenshot({ path: path.join(outDir, `${route.name}-mobile-${dateStr}-${sha}.png`), fullPage: true });
  }
});
