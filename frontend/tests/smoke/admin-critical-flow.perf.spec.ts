import { expect, test } from '@playwright/test';
import {
  installAdminShellMocks,
  mockAdminAuditPage,
  mockAdminGroupDetail,
  mockAdminGroupsList,
  mockAdminStudentPage,
} from './support';

test('measures admin critical flow timings with smoke mocks', async ({ page }) => {
  const requestCounts = new Map<string, number>();

  page.on('request', (request) => {
    const url = request.url();
    if (!url.includes('/api/v1/')) {
      return;
    }

    const path = new URL(url).pathname;
    requestCounts.set(path, (requestCounts.get(path) ?? 0) + 1);
  });

  await installAdminShellMocks(page);
  await mockAdminGroupsList(page);
  await mockAdminGroupDetail(page);
  await mockAdminStudentPage(page);
  await mockAdminAuditPage(page);

  const groupsStartedAt = Date.now();
  await page.goto('/admin/groups');
  await expect(page.getByRole('heading', { name: 'Учебные группы' })).toBeVisible();
  const groupsShellMs = Date.now() - groupsStartedAt;

  const groupStartedAt = Date.now();
  await page.getByRole('link', { name: /Управление группой/i }).click({ force: true });
  await expect(page).toHaveURL('/admin/groups/group-1');
  await expect(page.getByRole('heading', { name: 'Smoke Group' })).toBeVisible();
  const groupRouteMs = Date.now() - groupStartedAt;

  const studentStartedAt = Date.now();
  await page.getByRole('link', { name: 'Smoke Student' }).click();
  await expect(page).toHaveURL('/admin/students/student-1');
  await expect(page.getByRole('heading', { name: 'Профиль студента' })).toBeVisible();
  const studentShellMs = Date.now() - studentStartedAt;

  await expect(page.getByText('Smoke activity')).toBeVisible();
  await expect(page.getByText('Smoke Lab')).toBeVisible();
  const studentFullMs = Date.now() - studentStartedAt;

  console.info(
    `ADMIN_FLOW_PERF ${JSON.stringify({
      groupsShellMs,
      groupRouteMs,
      studentShellMs,
      studentFullMs,
      requestCounts: Object.fromEntries(requestCounts),
    })}`,
  );
});
