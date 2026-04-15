import process from 'node:process';
import { chromium } from '@playwright/test';

const baseUrl = (process.env.LECTURES_FLOW_BASE_URL ?? 'http://127.0.0.1').replace(/\/$/, '');
const runs = Number.parseInt(process.env.LECTURES_FLOW_RUNS ?? '3', 10);

function now() {
  return Date.now();
}

function summarize(values) {
  const sorted = [...values].sort((a, b) => a - b);
  const avg = values.reduce((sum, value) => sum + value, 0) / values.length;

  return {
    min: Math.min(...values),
    median: sorted[Math.floor(sorted.length / 2)],
    avg: Math.round(avg * 10) / 10,
    max: Math.max(...values),
  };
}

function countRequests(entries) {
  return Object.fromEntries(
    entries.reduce((map, entry) => {
      const key = `${entry.method} ${entry.path}`;
      map.set(key, (map.get(key) ?? 0) + 1);
      return map;
    }, new Map()),
  );
}

async function measureRun(browser, runNumber) {
  const context = await browser.newContext({ baseURL: baseUrl });
  const page = await context.newPage();
  const events = [];
  const title = `Codex Perf Lecture ${Date.now()}-${runNumber}`;

  page.on('response', async (response) => {
    const url = response.url();
    if (!url.includes('/api/v1/') && !url.includes('/admin/lectures')) {
      return;
    }

    const request = response.request();
    const timing = await request.timing();
    events.push({
      method: request.method(),
      path: new URL(url).pathname,
      status: response.status(),
      durationMs: timing.responseEnd > 0 ? Math.round(timing.responseEnd) : null,
    });
  });

  try {
    await page.goto(
      `${baseUrl}/auth/login?returnUrl=${encodeURIComponent('/admin/lectures')}`,
      { waitUntil: 'domcontentloaded' },
    );
    await page.getByRole('button', { name: 'Войти как dev admin', exact: true }).click();
    await page.waitForURL((url) => url.pathname === '/admin/lectures', { timeout: 20_000 });

    const listStartedAt = now();
    await page.getByRole('heading', { name: 'Лекции' }).waitFor({ timeout: 20_000 });
    const lecturesHeadingMs = now() - listStartedAt;
    await page.waitForLoadState('networkidle', { timeout: 20_000 });
    const lecturesIdleMs = now() - listStartedAt;
    const listEvents = [...events];

    await page.getByRole('button', { name: 'Создать лекцию' }).first().click();
    await page.getByRole('textbox', { name: 'Название' }).fill(title);
    const createStartedAt = now();
    await page.getByRole('button', { name: 'Создать' }).last().click();
    await page.waitForURL((url) => /^\/admin\/lectures\/[^/]+$/.test(url.pathname), { timeout: 20_000 });
    const createUrlMs = now() - createStartedAt;
    const createdPath = new URL(page.url()).pathname;
    const lectureId = createdPath.split('/').at(-1);

    await page.getByPlaceholder('Название лекции').waitFor({ timeout: 20_000 });
    const createHeaderMs = now() - createStartedAt;
    await page.locator('[contenteditable="true"]').first().waitFor({ timeout: 20_000 });
    const createEditorReadyMs = now() - createStartedAt;
    const createEvents = events.slice(listEvents.length);

    const deleteStartedAt = now();
    await page.locator('button.text-destructive').click();
    await page.getByRole('alertdialog').waitFor({ timeout: 20_000 });
    await page.getByRole('button', { name: 'Удалить' }).last().click();
    await page.waitForURL((url) => url.pathname === '/admin/lectures', { timeout: 20_000 });
    const deleteUrlMs = now() - deleteStartedAt;
    await page.getByRole('heading', { name: 'Лекции' }).waitFor({ timeout: 20_000 });
    const deleteHeadingMs = now() - deleteStartedAt;
    await page.waitForLoadState('networkidle', { timeout: 20_000 });
    const deleteIdleMs = now() - deleteStartedAt;
    const deleteEvents = events.slice(listEvents.length + createEvents.length);

    return {
      run: runNumber,
      createdLectureId: lectureId,
      lectures: {
        headingMs: lecturesHeadingMs,
        idleMs: lecturesIdleMs,
        requestCounts: countRequests(listEvents),
      },
      create: {
        urlMs: createUrlMs,
        headerMs: createHeaderMs,
        editorReadyMs: createEditorReadyMs,
        requestCounts: countRequests(createEvents),
      },
      delete: {
        urlMs: deleteUrlMs,
        headingMs: deleteHeadingMs,
        idleMs: deleteIdleMs,
        requestCounts: countRequests(deleteEvents),
        routeRequests: deleteEvents.map((entry) => `${entry.method} ${entry.path}`),
      },
    };
  } finally {
    await context.close();
  }
}

async function main() {
  const browser = await chromium.launch({ headless: true });

  try {
    const results = [];

    for (let index = 1; index <= runs; index += 1) {
      results.push(await measureRun(browser, index));
    }

    console.log(JSON.stringify({
      baseUrl,
      runs,
      summary: {
        lecturesHeadingMs: summarize(results.map((result) => result.lectures.headingMs)),
        lecturesIdleMs: summarize(results.map((result) => result.lectures.idleMs)),
        createUrlMs: summarize(results.map((result) => result.create.urlMs)),
        createHeaderMs: summarize(results.map((result) => result.create.headerMs)),
        createEditorReadyMs: summarize(results.map((result) => result.create.editorReadyMs)),
        deleteUrlMs: summarize(results.map((result) => result.delete.urlMs)),
        deleteHeadingMs: summarize(results.map((result) => result.delete.headingMs)),
        deleteIdleMs: summarize(results.map((result) => result.delete.idleMs)),
      },
      runsDetail: results,
    }, null, 2));
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
