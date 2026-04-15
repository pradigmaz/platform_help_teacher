import process from 'node:process';
import { chromium } from '@playwright/test';

const baseUrl = (process.env.REPORTS_FLOW_BASE_URL ?? 'http://127.0.0.1').replace(/\/$/, '');
const groupId = process.env.REPORTS_FLOW_GROUP_ID ?? '4cc73ace-9296-45e6-9c69-efd9e3407bf9';
const reportCode = process.env.REPORTS_FLOW_REPORT_CODE ?? 'WPL89XDB';
const studentId = process.env.REPORTS_FLOW_STUDENT_ID ?? '6f43a717-1634-4de2-b591-ff1787a67aff';
const runs = Number.parseInt(process.env.REPORTS_FLOW_RUNS ?? '5', 10);

function median(values) {
  const sorted = values.slice().sort((left, right) => left - right);
  return sorted[Math.floor(sorted.length / 2)];
}

function summarizeApi(samples) {
  const grouped = new Map();

  for (const sample of samples) {
    const key = `${sample.method} ${sample.path}`;
    if (!grouped.has(key)) {
      grouped.set(key, []);
    }
    grouped.get(key).push(sample.durationMs);
  }

  return Object.fromEntries(Array.from(grouped.entries()).map(([key, durations]) => {
    const sorted = durations.slice().sort((left, right) => left - right);
    return [key, {
      count: durations.length,
      minMs: sorted[0],
      medianMs: sorted[Math.floor(sorted.length / 2)],
      maxMs: sorted[sorted.length - 1],
    }];
  }));
}

async function loginAsDevAdmin(page) {
  await page.goto(`${baseUrl}/auth/login?returnUrl=${encodeURIComponent(`/admin/groups/${groupId}/reports`)}`, {
    waitUntil: 'domcontentloaded',
  });
  await page.waitForLoadState('load');
  await page.getByRole('button', { name: 'Войти как dev admin', exact: true }).click();
}

async function measureRoute(page, path, ready) {
  const apiSamples = [];
  const readyMs = [];
  const settledMs = [];

  for (let run = 0; run < runs; run += 1) {
    const responses = [];
    const onRequestFinished = async (request) => {
      const url = new URL(request.url());
      if (!url.pathname.startsWith('/api/')) {
        return;
      }

      const timing = await request.timing();
      responses.push({
        method: request.method(),
        path: url.pathname,
        status: (await request.response())?.status() ?? null,
        durationMs: timing.responseEnd ? Math.round(timing.responseEnd) : null,
      });
    };

    page.on('requestfinished', onRequestFinished);
    const startedAt = Date.now();
    await page.goto(`${baseUrl}${path}`, { waitUntil: 'domcontentloaded' });
    await ready(page);
    readyMs.push(Date.now() - startedAt);
    await page.waitForLoadState('networkidle', { timeout: 30_000 });
    settledMs.push(Date.now() - startedAt);
    page.off('requestfinished', onRequestFinished);

    for (const response of responses) {
      if (response.durationMs !== null) {
        apiSamples.push(response);
      }
    }
  }

  return {
    readyMs,
    settledMs,
    readyMedianMs: median(readyMs),
    settledMedianMs: median(settledMs),
    apiSummary: summarizeApi(apiSamples),
  };
}

async function measurePublicAttestationSwitch(page) {
  await page.goto(`${baseUrl}/report/${reportCode}`, { waitUntil: 'domcontentloaded' });
  await page.getByRole('tab', { name: '1 аттестация' }).waitFor({ timeout: 30_000 });
  await page.waitForLoadState('networkidle', { timeout: 30_000 });

  const secondTab = page.getByRole('tab', { name: '2 аттестация' });
  const switchAvailable = await secondTab.isEnabled().catch(() => false);

  if (!switchAvailable) {
    return {
      switchAvailable,
      requestCount: 0,
      requests: [],
    };
  }

  const startedAt = Date.now();
  const switchedRequest = page.waitForResponse((response) => {
    const url = new URL(response.url());
    return url.pathname === `/api/v1/public/report/${reportCode}` && url.searchParams.get('attestation') === 'second';
  });
  await secondTab.click();
  const switchedResponse = await switchedRequest;
  await page.waitForLoadState('networkidle', { timeout: 30_000 });
  const settledMs = Date.now() - startedAt;
  const switchedResponseUrl = new URL(switchedResponse.url());
  const timing = await switchedResponse.request().timing();

  return {
    switchAvailable,
    settledMs,
    requestCount: 1,
    requests: [{
      method: switchedResponse.request().method(),
      path: switchedResponseUrl.pathname + switchedResponseUrl.search,
      status: switchedResponse.status(),
      durationMs: timing.responseEnd ? Math.round(timing.responseEnd) : null,
    }],
  };
}

async function measureStudentDetailFromReport(page) {
  const studentPath = `/report/${reportCode}/student/${studentId}`;
  const apiSamples = [];
  const readyMs = [];
  const settledMs = [];

  for (let run = 0; run < runs; run += 1) {
    const responses = [];
    const onRequestFinished = async (request) => {
      const url = new URL(request.url());
      if (!url.pathname.startsWith('/api/')) {
        return;
      }

      const timing = await request.timing();
      responses.push({
        method: request.method(),
        path: url.pathname + url.search,
        status: (await request.response())?.status() ?? null,
        durationMs: timing.responseEnd ? Math.round(timing.responseEnd) : null,
      });
    };

    await page.goto(`${baseUrl}/report/${reportCode}`, { waitUntil: 'domcontentloaded' });
    await page.getByRole('tab', { name: '1 аттестация' }).waitFor({ timeout: 30_000 });
    await page.waitForLoadState('networkidle', { timeout: 30_000 });

    page.on('requestfinished', onRequestFinished);
    const startedAt = Date.now();
    await page.locator(`a[href="${studentPath}"]`).last().click();
    await page.locator('h1').waitFor({ timeout: 30_000 });
    readyMs.push(Date.now() - startedAt);
    await page.waitForLoadState('networkidle', { timeout: 30_000 });
    settledMs.push(Date.now() - startedAt);
    page.off('requestfinished', onRequestFinished);

    for (const response of responses) {
      if (response.durationMs !== null) {
        apiSamples.push(response);
      }
    }
  }

  return {
    readyMs,
    settledMs,
    readyMedianMs: median(readyMs),
    settledMedianMs: median(settledMs),
    apiSummary: summarizeApi(apiSamples),
  };
}

async function main() {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    await loginAsDevAdmin(page);
    await page.waitForURL((url) => url.pathname === `/admin/groups/${groupId}/reports`, { timeout: 20_000 });

    const adminReports = await measureRoute(
      page,
      `/admin/groups/${groupId}/reports`,
      async (currentPage) => {
        await currentPage.getByRole('button', { name: 'Создать отчёт', exact: true }).waitFor({ timeout: 30_000 });
      },
    );

    const publicReport = await measureRoute(
      page,
      `/report/${reportCode}`,
      async (currentPage) => {
        await currentPage.getByRole('tab', { name: '1 аттестация' }).waitFor({ timeout: 30_000 });
      },
    );

    const studentReport = await measureRoute(
      page,
      `/report/${reportCode}/student/${studentId}`,
      async (currentPage) => {
        await currentPage.locator('h1').waitFor({ timeout: 30_000 });
      },
    );

    const studentDetailFromReport = await measureStudentDetailFromReport(page);
    const publicAttestationSwitch = await measurePublicAttestationSwitch(page);

    console.log(JSON.stringify({
      environment: {
        baseUrl,
        groupId,
        reportCode,
        studentId,
        runs,
        capturedAt: new Date().toISOString(),
      },
      adminReports,
      publicReport,
      studentReport,
      studentDetailFromReport,
      publicAttestationSwitch,
    }, null, 2));
  } finally {
    await context.close();
    await browser.close();
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
