const { test, expect } = require('@playwright/test');
const fs = require('fs');
const path = require('path');

const repo = 'Bayes-correlations-of-Russia';
const screenshotDir = path.join(process.cwd(), 'qa-screenshots', repo);

async function openDashboard(page) {
  const errors = [];
  page.on('console', (message) => {
    if (message.type() === 'error') errors.push(message.text());
  });
  page.on('pageerror', (error) => errors.push(error.message));
  await page.goto('/', { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => window.AppI18n && window.AppI18n.ready);
  await expect(page.locator('[data-testid="language-toggle"]')).toHaveCount(1);
  await expect(page.locator('[data-testid="language-toggle"]')).toBeVisible();
  await expect(page.locator('#status')).toContainText(/Готово|Done/i, { timeout: 60000 });
  await expect(page.locator('#heatmap')).not.toBeEmpty({ timeout: 60000 });
  await expect(page.locator('#scatter3d')).not.toBeEmpty({ timeout: 60000 });
  return errors;
}

async function expectEnglish(page) {
  await expect(page.locator('html')).toHaveAttribute('lang', 'en');
  await expect(page.getByRole('heading', { name: /Digital Demographic Observatory/i })).toBeVisible();
  await expect(page.locator('label[for="region"]')).toHaveText('Russian region');
  await expect(page.getByRole('heading', { name: 'Correlation Matrix Heatmap' })).toBeVisible();
  await expect(page.getByTestId('language-toggle')).toHaveText('RU');
}

async function expectRussian(page) {
  await expect(page.locator('html')).toHaveAttribute('lang', 'ru');
  await expect(page.getByRole('heading', { name: /Цифровая демографическая обсерватория/i })).toBeVisible();
  await expect(page.locator('label[for="region"]')).toHaveText('Субъект РФ');
  await expect(page.getByRole('heading', { name: 'Тепловая карта матрицы корреляций' })).toBeVisible();
  await expect(page.getByTestId('language-toggle')).toHaveText('EN');
}

test.describe('EN/RU dashboard interface', () => {
  test.beforeAll(() => fs.mkdirSync(screenshotDir, { recursive: true }));

  test('defaults to English for non-Russian devices and persists toggles', async ({ page }, testInfo) => {
    test.skip(testInfo.project.name !== 'desktop', 'Desktop-only EN default check.');
    const errors = await openDashboard(page);
    await expectEnglish(page);
    await page.screenshot({ path: path.join(screenshotDir, 'desktop-en.png'), fullPage: true });

    await page.getByTestId('language-toggle').click();
    await expectRussian(page);
    await expect(page.evaluate(() => localStorage.getItem('lang'))).resolves.toBe('ru');
    await page.reload({ waitUntil: 'domcontentloaded' });
    await expect(page.locator('#status')).toContainText(/Готово|Done/i, { timeout: 60000 });
    await expectRussian(page);
    await page.screenshot({ path: path.join(screenshotDir, 'desktop-ru.png'), fullPage: true });

    await page.getByTestId('language-toggle').click();
    await expectEnglish(page);
    await expect(page.evaluate(() => localStorage.getItem('lang'))).resolves.toBe('en');
    expect(errors).toEqual([]);
  });

  test('defaults to Russian for Russian devices and mobile screenshots stay clean', async ({ page }, testInfo) => {
    test.skip(testInfo.project.name !== 'mobile', 'Mobile-only RU default check.');
    const errors = await openDashboard(page);
    await expectRussian(page);
    await page.screenshot({ path: path.join(screenshotDir, 'mobile-ru.png'), fullPage: true });

    await page.getByTestId('language-toggle').click();
    await expectEnglish(page);
    await page.screenshot({ path: path.join(screenshotDir, 'mobile-en.png'), fullPage: true });
    expect(errors).toEqual([]);
  });
});
