import type { Page } from '@playwright/test';

const emptyAnnouncements: [] = [];
const defaultAdminUser = {
  id: 'admin-1',
  full_name: 'Smoke Admin',
  username: 'smoke_admin',
  role: 'admin',
  onboarding_completed: true,
};

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

export async function installAdminShellMocks(page: Page): Promise<void> {
  await installCommonApiMocks(page);

  await page.route('**/api/v1/users/me', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(defaultAdminUser),
    });
  });

  await page.route('**/api/v1/feedback/count/new', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ count: 0 }),
    });
  });

  await page.route('**/api/v1/admin/notes**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([]),
    });
  });
}

export async function mockAdminGroupDetail(page: Page): Promise<void> {
  await page.route('**/api/v1/groups/group-1', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        id: 'group-1',
        name: 'Smoke Group',
        code: 'SMOKE-01',
        invite_code: 'INVITE-001',
        created_at: '2026-04-03T10:00:00Z',
        has_subgroups: true,
        students: [
          {
            id: 'student-1',
            full_name: 'Smoke Student',
            username: 'smoke_student',
            subgroup: 1,
            is_active: true,
          },
        ],
      }),
    });
  });
}

export async function mockAdminJournalView(page: Page): Promise<void> {
  await page.route('**/api/v1/admin/journal/view**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        resolved: {
          group_id: 'group-1',
          subject_id: 'subject-1',
          week_start: '2026-04-01',
          week_end: '2026-04-07',
        },
        groups: [
          {
            id: 'group-1',
            name: 'Smoke Group',
            code: 'SMOKE-01',
            students_count: 1,
            has_subgroups: false,
          },
        ],
        subjects: [{ id: 'subject-1', name: 'Математика' }],
        lessons: [
          {
            id: 'lesson-1',
            date: '2026-04-03',
            lesson_number: 1,
            lesson_type: 'PRACTICE',
            topic: 'Smoke Topic',
            work_number: 1,
            lecture_work_type: null,
            subgroup: null,
            is_cancelled: false,
            subject_id: 'subject-1',
            subject_name: 'Математика',
            group_id: 'group-1',
            group_name: 'Smoke Group',
          },
        ],
        students: [
          {
            id: 'student-1',
            full_name: 'Smoke Student',
            subgroup: null,
            is_active: true,
          },
        ],
        attendance: {
          'lesson-1': {
            'student-1': 'PRESENT',
          },
        },
        grades: {
          'lesson-1': {
            'student-1': {
              grade: 5,
              work_number: 1,
            },
          },
        },
        attestation_scores: {},
        stats: {
          total_lessons: 1,
          lectures: 0,
          labs: 0,
          practices: 1,
          attendance_rate: 100,
          average_grade: 5,
          by_status: {
            present: 1,
            late: 0,
            excused: 0,
            absent: 0,
          },
        },
      }),
    });
  });
}

export async function mockAdminAuditPage(page: Page): Promise<void> {
  await page.route('**/api/v1/admin/audit?**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        items: [
          {
            id: 'audit-1',
            user_id: 'student-1',
            user_name: 'Smoke Audit User',
            actor_role: 'student',
            action_type: 'login',
            entity_type: null,
            entity_id: null,
            method: 'POST',
            path: '/auth/login',
            response_status: 200,
            duration_ms: 12,
            ip_address: '127.0.0.1',
            ip_forwarded: null,
            user_agent: 'Playwright',
            created_at: '2026-04-03T10:00:00Z',
          },
        ],
        total: 1,
        skip: 0,
        limit: 50,
      }),
    });
  });

  await page.route('**/api/v1/admin/audit/stats/summary?days=7', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        total_logs: 1,
        unique_users: 1,
        unique_ips: 1,
        by_action_type: { login: 1 },
        period_days: 7,
      }),
    });
  });

  await page.route('**/api/v1/admin/security/bans?**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([
        {
          identifier: 'ip:127.0.0.1',
          strike_count: 3,
          is_banned: true,
          ban_ttl: 3600,
          strikes: [
            {
              timestamp: '2026-04-03T10:00:00Z',
              url: '/admin/audit',
              attack_type: 'xss',
              description: 'Smoke XSS attempt',
              severity: 5,
            },
          ],
        },
      ]),
    });
  });

  await page.route('**/api/v1/admin/security/stats', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        total_bans: 1,
        active_bans: 1,
        strikes_today: 3,
        top_attack_types: { xss: 3 },
      }),
    });
  });
}

export async function mockAdminSettingsPage(page: Page): Promise<void> {
  await page.route('**/api/v1/users/profile/contacts', async (route) => {
    if (route.request().method() === 'PUT') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          contacts: { telegram: '@smoke_admin', vk: '', max: '' },
          visibility: { telegram: 'student', vk: 'none', max: 'none' },
        }),
      });
      return;
    }

    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        contacts: { telegram: '@smoke_admin', vk: '', max: '' },
        visibility: { telegram: 'student', vk: 'none', max: 'none' },
      }),
    });
  });

  await page.route('**/api/v1/admin/backups/settings', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        enabled: true,
        schedule_hour: 17,
        schedule_minute: 0,
        retention_days: 30,
        max_backups: 10,
        notify_on_success: false,
        notify_on_failure: true,
      }),
    });
  });

  await page.route('**/api/v1/admin/backups/', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        backups: [
          {
            name: 'smoke-backup',
            key: 'backup-1',
            size: 1024,
            created_at: '2026-04-03T10:00:00Z',
            portable: true,
            created_with_current_key: true,
            offsite_present: true,
          },
        ],
        total: 1,
      }),
    });
  });

  await page.route('**/api/v1/admin/backups/health', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        status: 'healthy',
        freshness_status: 'fresh',
        expected_max_age_hours: 24,
        offsite_configured: true,
        checks: {
          backups: {
            status: 'ok',
            latest: 'backup-1',
            age_hours: 1,
          },
        },
      }),
    });
  });
}
