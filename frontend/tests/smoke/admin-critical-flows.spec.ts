import { expect, test } from '@playwright/test';
import {
  installAdminShellMocks,
  mockAdminGroupsList,
  mockAdminAuditPage,
  mockAdminGroupDetail,
  mockAdminStudentPage,
  mockAdminJournalView,
  mockAdminSettingsPage,
} from './support';

test('renders the admin group detail screen', async ({ page }) => {
  await installAdminShellMocks(page);
  await mockAdminGroupDetail(page);

  await page.goto('/admin/groups/group-1');

  await expect(page.getByRole('heading', { name: 'Smoke Group' })).toBeVisible();
  await expect(page.getByRole('tab', { name: 'Студенты' })).toBeVisible();
  await expect(page.getByText('Smoke Student')).toBeVisible();
});

test('renders the admin journal screen with loaded journal data', async ({ page }) => {
  let notesBatchRequests = 0;
  await page.route('**/api/v1/admin/notes/batch**', async (route) => {
    notesBatchRequests += 1;
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({}),
    });
  });
  await installAdminShellMocks(page);
  await mockAdminJournalView(page);

  await page.goto('/admin/journal');

  await expect(page.getByRole('heading', { name: 'Журнал' })).toBeVisible();
  await expect(page.getByText('Smoke Student')).toBeVisible();
  await expect(page.getByText('03.04')).toBeVisible();
  expect(notesBatchRequests).toBe(0);
});

test('renders audit logs and security tabs for admin audit', async ({ page }) => {
  await installAdminShellMocks(page);
  await mockAdminAuditPage(page);

  await page.goto('/admin/audit');

  await expect(page.getByRole('heading', { name: 'Аудит действий' })).toBeVisible();
  await expect(page.getByText('Smoke Audit User')).toBeVisible();

  await page.getByRole('tab', { name: 'Безопасность' }).click();

  await expect(page.getByText('Активные баны за атаки')).toBeVisible();
  await expect(page.getByText('XSS: 3')).toBeVisible();
});

test('opens the mobile admin navigation sheet with accessible description', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await installAdminShellMocks(page);
  await mockAdminGroupsList(page);

  await page.goto('/admin/groups');

  await page.getByRole('button', { name: 'Открыть меню' }).click();

  await expect(page.getByText('Навигация администратора')).toBeVisible();
  await expect(page.getByText('Основные разделы и быстрые переходы по административным страницам.')).toHaveCount(1);
});

test('renders admin settings profile and backup tabs', async ({ page }) => {
  await installAdminShellMocks(page);
  await mockAdminSettingsPage(page);

  await page.goto('/admin/settings');

  await expect(page.getByRole('heading', { name: 'Настройки' })).toBeVisible();
  await expect(page.getByText('Контакты для связи')).toBeVisible();

  await page.getByRole('tab', { name: 'Бэкапы' }).click();

  await expect(page.getByText('Автоматическое резервное копирование')).toBeVisible();
  await expect(page.getByText('Резервные копии')).toBeVisible();
});

test('navigates groups to student without repeated admin shell bootstrap', async ({ page }) => {
  let usersMeRequests = 0;
  let feedbackCountRequests = 0;

  page.on('request', (request) => {
    const url = request.url();
    if (url.includes('/api/v1/users/me')) {
      usersMeRequests += 1;
    }
    if (url.includes('/api/v1/feedback/count/new')) {
      feedbackCountRequests += 1;
    }
  });

  await installAdminShellMocks(page);
  await mockAdminGroupsList(page);
  await mockAdminGroupDetail(page);
  await mockAdminStudentPage(page);

  await page.goto('/admin/groups');

  await expect(page.getByRole('heading', { name: 'Учебные группы' })).toBeVisible();
  await page.getByRole('link', { name: /Управление группой/i }).click({ force: true });

  await expect(page).toHaveURL('/admin/groups/group-1');
  await expect(page.getByRole('heading', { name: 'Smoke Group' })).toBeVisible();

  await page.getByRole('link', { name: 'Smoke Student' }).click();

  await expect(page).toHaveURL('/admin/students/student-1');
  await expect(page.getByRole('heading', { name: 'Профиль студента' })).toBeVisible();
  await expect(page.getByText('Smoke activity')).toBeVisible();
  await expect(page.getByText('Smoke Lab')).toBeVisible();

  expect(usersMeRequests).toBe(1);
  expect(feedbackCountRequests).toBe(1);
});
