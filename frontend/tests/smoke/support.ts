import type { Page } from '@playwright/test';

const emptyAnnouncements: [] = [];

export async function installCommonApiMocks(page: Page): Promise<void> {
  await page.route('**/api/v1/auth/fingerprint-mode', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ mode: 'off' }),
    });
  });

  await page.route('**/api/v1/auth/csrf-token', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ csrf_token: 'smoke-csrf-token' }),
    });
  });

  await page.route('**/api/v1/student/announcements**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(emptyAnnouncements),
    });
  });

  await page.route('**/api/v1/public/semester-info', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        current_semester: null,
        semester_start: null,
        semester_end: null,
      }),
    });
  });
}

export async function mockUnauthorizedAuthCheck(page: Page): Promise<void> {
  await page.route('**/api/v1/users/me', async (route) => {
    await route.fulfill({
      status: 401,
      contentType: 'application/json',
      body: JSON.stringify({ detail: 'Unauthorized' }),
    });
  });
}

export async function mockUnauthorizedDashboardProfile(page: Page): Promise<void> {
  await page.route('**/api/v1/student/profile', async (route) => {
    await route.fulfill({
      status: 401,
      contentType: 'application/json',
      body: JSON.stringify({ detail: 'Session expired' }),
    });
  });
}

export async function mockDashboardProfile(page: Page): Promise<void> {
  await page.route('**/api/v1/student/profile', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        full_name: 'Smoke Student',
        username: 'smoke_student',
        group: { code: 'SMOKE-01' },
      }),
    });
  });
}

export async function mockDashboardData(page: Page): Promise<void> {
  await page.route('**/api/v1/student/attendance', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        stats: {
          total_classes: 10,
          present: 9,
          late: 0,
          excused: 0,
          absent: 1,
          attendance_rate: 90,
        },
        records: [],
      }),
    });
  });

  await page.route('**/api/v1/student/labs', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([
        {
          id: 'lab-1',
          number: 1,
          title: 'ЛР 1',
          subject_id: 'subject-1',
          max_grade: 5,
          is_available: true,
        },
      ]),
    });
  });

  await page.route('**/api/v1/student/attestation/subjects/**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([{ id: 'subject-1', name: 'Математика' }]),
    });
  });

  await page.route('**/api/v1/student/attestation/first**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        attestation_type: 'first',
        subject_id: 'subject-1',
        total_score: 10,
        grade: '5',
        is_passing: true,
      }),
    });
  });

  await page.route('**/api/v1/student/attestation/second**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        attestation_type: 'second',
        subject_id: 'subject-1',
        total_score: 12,
        grade: '5',
        is_passing: true,
      }),
    });
  });
}
