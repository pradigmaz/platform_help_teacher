import { expect, test } from '@playwright/test';
import { installCommonApiMocks, mockUnauthorizedAuthCheck } from './support';

test('renders the login form when auth check fails', async ({ page }) => {
  await installCommonApiMocks(page);
  await mockUnauthorizedAuthCheck(page);

  await page.goto('/auth/login');

  await expect(page.getByRole('heading', { name: 'Авторизация' })).toBeVisible();
  await expect(page.getByPlaceholder('000000')).toBeVisible();
  await expect(page.getByRole('button', { name: 'Войти' })).toBeVisible();
  await expect(page.getByText('Введите код из Telegram-бота')).toBeVisible();
});
