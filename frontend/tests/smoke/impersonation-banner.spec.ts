import { expect, test } from '@playwright/test';
import { installCommonApiMocks, mockDashboardData, mockDashboardProfile } from './support';

const smokePort = process.env.PLAYWRIGHT_TEST_PORT ?? '3100';
const baseURL = process.env.PLAYWRIGHT_TEST_BASE_URL ?? `http://127.0.0.1:${smokePort}`;

test('shows the impersonation banner for impersonated dashboard sessions', async ({ page }) => {
  await installCommonApiMocks(page);
  await mockDashboardProfile(page);
  await mockDashboardData(page);
  await page.context().addCookies([
    {
      name: 'impersonating',
      value: 'true',
      url: baseURL,
    },
  ]);

  await page.goto('/dashboard');

  await expect(page.getByText('Вы просматриваете систему от имени студента')).toBeVisible();
  await expect(page.getByRole('button', { name: 'Вернуться в админку' })).toBeVisible();
});
