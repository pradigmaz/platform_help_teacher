import { expect, test } from '@playwright/test';
import {
  installCommonApiMocks,
  mockUnauthorizedDashboardProfile,
} from './support';

test('redirects unauthenticated dashboard access to the login page', async ({ page }) => {
  await installCommonApiMocks(page);
  await mockUnauthorizedDashboardProfile(page);
  await page.route('**/api/v1/auth/status', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ authenticated: false, user: null }),
    });
  });

  await page.goto('/dashboard');

  await expect(page).toHaveURL(/\/auth\/login\?returnUrl=%2Fdashboard/);
  await expect(page.getByRole('heading', { name: 'Авторизация' })).toBeVisible();
});
