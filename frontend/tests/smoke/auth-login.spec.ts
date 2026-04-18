import { expect, test } from '@playwright/test';
import { installCommonApiMocks } from './support';

test('renders the login form when auth check fails', async ({ page }) => {
  let authStatusHits = 0;
  let usersMeRequests = 0;

  page.on('request', (request) => {
    const url = request.url();
    if (url.includes('/api/v1/users/me')) {
      usersMeRequests += 1;
    }
  });

  await installCommonApiMocks(page);
  await page.route('**/api/v1/auth/status', async (route) => {
    authStatusHits += 1;
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ authenticated: false, user: null }),
    });
  });

  await page.goto('/auth/login');

  await expect(page.getByRole('heading', { name: 'Авторизация' })).toBeVisible();
  await expect(page.getByPlaceholder('000000')).toBeVisible();
  await expect(page.getByRole('button', { name: 'Войти' })).toBeVisible();
  await expect(page.getByText('Введите код из Telegram-бота')).toBeVisible();
  expect(authStatusHits).toBe(1);
  expect(usersMeRequests).toBe(0);
});
