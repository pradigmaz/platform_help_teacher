import { expect, test } from '@playwright/test';
import {
  installCommonApiMocks,
  mockUnauthorizedAuthCheck,
  mockUnauthorizedDashboardProfile,
} from './support';

test('redirects unauthenticated dashboard access to the login page', async ({ page }) => {
  await installCommonApiMocks(page);
  await mockUnauthorizedDashboardProfile(page);
  await mockUnauthorizedAuthCheck(page);

  await page.goto('/dashboard');

  await expect(page).toHaveURL(/\/auth\/login\?returnUrl=%2Fdashboard/);
  await expect(page.getByRole('heading', { name: 'Авторизация' })).toBeVisible();
});
