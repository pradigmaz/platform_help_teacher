export async function createContext(browser, storageState) {
  const context = await browser.newContext(
    storageState ? { storageState } : undefined,
  );
  await context.addInitScript(() => {
    window.__phase7LongTasks = [];
    try {
      const observer = new PerformanceObserver((list) => {
        window.__phase7LongTasks.push(
          ...list.getEntries().map((entry) => ({
            name: entry.name,
            startTime: Math.round(entry.startTime),
            duration: Math.round(entry.duration),
          })),
        );
      });
      observer.observe({ type: 'longtask', buffered: true });
    } catch {}
  });
  return context;
}

export function attachResponseTrace(page) {
  const responses = [];
  page.on('response', async (response) => {
    const request = response.request();
    const url = request.url();
    const path = new URL(url).pathname;
    const headers = await request.allHeaders();
    responses.push({
      url,
      path,
      method: request.method(),
      status: response.status(),
      resourceType: request.resourceType(),
      hasFingerprintHeader: typeof headers['x-device-fingerprint'] === 'string',
      fingerprintHeaderLength: headers['x-device-fingerprint']?.length ?? 0,
      isApi: path.includes('/api/v1/'),
      isAuthRoute: path.includes('/api/v1/auth/') || path.includes('/api/v1/admin/impersonate'),
    });
  });
  return responses;
}

function summarizeResponses(responses) {
  const api = responses.filter((entry) => entry.isApi);
  const auth = api.filter((entry) => entry.isAuthRoute);
  const nonAuth = api.filter((entry) => !entry.isAuthRoute);
  return {
    total: responses.length,
    apiTotal: api.length,
    authTotal: auth.length,
    nonAuthTotal: nonAuth.length,
    authWithFingerprint: auth.filter((entry) => entry.hasFingerprintHeader).length,
    nonAuthWithFingerprint: nonAuth.filter((entry) => entry.hasFingerprintHeader).length,
    apiRequests: api.map(({ url, path, method, status, hasFingerprintHeader, fingerprintHeaderLength }) => ({
      url,
      path,
      method,
      status,
      hasFingerprintHeader,
      fingerprintHeaderLength,
    })),
  };
}

export async function collectPageEvidence(context, baseUrl, path, settleMs) {
  const page = await context.newPage();
  const responses = attachResponseTrace(page);
  const startedAt = Date.now();
  await page.goto(`${baseUrl}${path}`, { waitUntil: 'domcontentloaded' });
  await page.waitForLoadState('load').catch(() => {});
  await page.waitForTimeout(settleMs);
  const performanceSummary = await page.evaluate(() => {
    const nav = performance.getEntriesByType('navigation')[0];
    const paints = performance.getEntriesByType('paint');
    const fcp = paints.find((entry) => entry.name === 'first-contentful-paint');
    return {
      domContentLoadedMs: nav ? Math.round(nav.domContentLoadedEventEnd) : null,
      loadMs: nav ? Math.round(nav.loadEventEnd) : null,
      responseEndMs: nav ? Math.round(nav.responseEnd) : null,
      firstContentfulPaintMs: fcp ? Math.round(fcp.startTime) : null,
      longTasks: Array.isArray(window.__phase7LongTasks) ? window.__phase7LongTasks : [],
    };
  });
  const result = {
    path,
    finalUrl: page.url(),
    settledMs: Date.now() - startedAt,
    performance: performanceSummary,
    network: summarizeResponses(responses),
  };
  await page.close();
  return result;
}

export async function fetchJson(page, path, method = 'GET', body = null) {
  return page.evaluate(async ({ path: requestPath, method: requestMethod, body: requestBody }) => {
    let csrfToken = null;
    if (requestMethod !== 'GET') {
      const csrfResponse = await fetch('/api/v1/auth/csrf-token', {
        credentials: 'include',
        cache: 'no-store',
      });
      const csrfPayload = await csrfResponse.json();
      csrfToken = csrfPayload.csrf_token;
    }

    const response = await fetch(`/api/v1${requestPath}`, {
      method: requestMethod,
      credentials: 'include',
      headers: {
        ...(requestMethod !== 'GET' ? { 'Content-Type': 'application/json', 'X-CSRF-Token': csrfToken } : {}),
      },
      body: requestBody ? JSON.stringify(requestBody) : undefined,
    });

    const rawText = await response.text();
    let payload = null;
    try {
      payload = rawText ? JSON.parse(rawText) : null;
    } catch {
      payload = rawText;
    }

    return {
      status: response.status,
      ok: response.ok,
      payload,
    };
  }, { path, method, body });
}
