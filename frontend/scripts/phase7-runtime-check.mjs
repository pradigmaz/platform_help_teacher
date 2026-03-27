import fs from 'node:fs/promises';
import process from 'node:process';
import { chromium } from '@playwright/test';
import {
  collectPageEvidence,
  createContext,
  fetchJson,
} from './phase7-runtime-helpers.mjs';

const baseUrl = (process.env.PHASE7_BASE_URL ?? 'http://localhost').replace(/\/$/, '');
const outputPath = process.env.PHASE7_OUTPUT ?? '/tmp/fingerprint-phase7-runtime.json';
const studentId = process.env.PHASE7_STUDENT_ID ?? '';
const studentOtp = process.env.PHASE7_STUDENT_OTP ?? '';
const settleMs = Number.parseInt(process.env.PHASE7_SETTLE_MS ?? '2500', 10);
const allowDeviceMutations = process.env.PHASE7_ALLOW_DEVICE_MUTATIONS === '1';

function requireEnv(name, value) {
  if (!value) {
    throw new Error(`Missing required env: ${name}`);
  }
}

async function openSecurityTab(page) {
  await page.goto(`${baseUrl}/dashboard/settings`, { waitUntil: 'domcontentloaded' });
  await page.waitForLoadState('load');
  await page.getByRole('tab', { name: 'Безопасность', exact: true }).click();
  await page.getByText('Активные сессии', { exact: true }).waitFor({ timeout: 10000 });
  await page.getByText('Привязанные устройства', { exact: true }).waitFor({ timeout: 10000 });
  await page.waitForTimeout(1000);
}

function collectExpectedFragments(sessionsPayload, devicesPayload) {
  const fragments = ['Активные сессии', 'Привязанные устройства'];
  const currentSession = sessionsPayload?.sessions?.[0];
  const currentDevice = devicesPayload?.devices?.[0];

  if (currentSession?.device?.platform && currentSession?.device?.browser) {
    fragments.push(`${currentSession.device.platform} • ${currentSession.device.browser}`);
  }
  if (currentSession?.ip_address) {
    fragments.push(currentSession.ip_address);
  }
  if (currentSession?.device?.screen) {
    fragments.push(currentSession.device.screen);
  }
  if (currentSession?.is_current) {
    fragments.push('Текущая');
  }
  if (currentDevice?.device_info?.platform && currentDevice?.device_info?.browser) {
    fragments.push(`${currentDevice.device_info.platform} • ${currentDevice.device_info.browser}`);
  }
  if (currentDevice?.device_info?.screen) {
    fragments.push(currentDevice.device_info.screen);
  }
  if (currentDevice && !currentDevice.is_trusted) {
    fragments.push('Подтвердить');
  }

  return Array.from(new Set(fragments));
}

async function collectSecurityUiEvidence(page, expectedFragments) {
  const bodyText = await page.locator('body').innerText();
  const missing = expectedFragments.filter((fragment) => !bodyText.includes(fragment));
  if (missing.length > 0) {
    throw new Error(`Security UI is missing expected fragments: ${missing.join(', ')}`);
  }

  return {
    matchedFragments: expectedFragments,
  };
}

function selectMutableDevice(devicesPayload) {
  const devices = Array.isArray(devicesPayload?.devices) ? devicesPayload.devices : [];
  const untrusted = devices.filter((device) => !device.is_trusted);
  if (untrusted.length !== 1) {
    return null;
  }
  return untrusted[0];
}

async function loginWithDevAdmin(browser) {
  const context = await createContext(browser);
  const page = await context.newPage();
  await page.goto(`${baseUrl}/auth/login`, { waitUntil: 'domcontentloaded' });
  await page.waitForLoadState('load');
  const responsePromise = page.waitForResponse((response) => response.url().includes('/api/v1/auth/dev-login'));
  await page.getByRole('button', { name: 'Войти как dev admin', exact: true }).click();
  const response = await responsePromise;
  await page.waitForURL((url) => !url.pathname.startsWith('/auth/login'), { timeout: 15000 });
  const mode = await page.evaluate(() => ({
    dom: document.documentElement.dataset.fingerprintMode ?? null,
    cached: sessionStorage.getItem('auth_fingerprint_v1'),
  }));
  const headers = await response.request().allHeaders();
  return {
    context,
    page,
    request: {
      status: response.status(),
      hasFingerprintHeader: typeof headers['x-device-fingerprint'] === 'string',
      fingerprintHeaderLength: headers['x-device-fingerprint']?.length ?? 0,
    },
    mode,
  };
}

async function loginWithOtp(browser) {
  requireEnv('PHASE7_STUDENT_OTP', studentOtp);
  const context = await createContext(browser);
  const page = await context.newPage();
  await page.goto(`${baseUrl}/auth/login`, { waitUntil: 'domcontentloaded' });
  await page.waitForLoadState('load');
  await page.getByPlaceholder('000000').fill(studentOtp);
  await page.getByLabel('Запомнить устройство').check();
  const responsePromise = page.waitForResponse((response) => response.url().includes('/api/v1/auth/otp'));
  await page.getByRole('button', { name: 'Войти', exact: true }).click();
  const response = await responsePromise;
  await page.waitForURL((url) => url.pathname.startsWith('/dashboard'), { timeout: 15000 });
  const headers = await response.request().allHeaders();
  const mode = await page.evaluate(() => ({
    dom: document.documentElement.dataset.fingerprintMode ?? null,
    cached: sessionStorage.getItem('auth_fingerprint_v1'),
  }));
  return {
    context,
    page,
    request: {
      status: response.status(),
      hasFingerprintHeader: typeof headers['x-device-fingerprint'] === 'string',
      fingerprintHeaderLength: headers['x-device-fingerprint']?.length ?? 0,
    },
    mode,
  };
}

async function impersonateStudent(page) {
  requireEnv('PHASE7_STUDENT_ID', studentId);
  await page.goto(`${baseUrl}/admin/students/${studentId}`, { waitUntil: 'domcontentloaded' });
  await page.waitForLoadState('load');
  await page.getByRole('button', { name: 'Войти как', exact: true }).hover();
  const responsePromise = page.waitForResponse((response) => response.url().includes(`/api/v1/admin/impersonate/${studentId}`));
  await page.getByRole('button', { name: 'Войти как', exact: true }).click();
  const response = await responsePromise;
  await page.waitForURL((url) => url.pathname.startsWith('/dashboard'), { timeout: 15000 });
  const headers = await response.request().allHeaders();
  const mode = await page.evaluate(() => ({
    dom: document.documentElement.dataset.fingerprintMode ?? null,
    cached: sessionStorage.getItem('auth_fingerprint_v1'),
  }));
  return {
    request: {
      status: response.status(),
      hasFingerprintHeader: typeof headers['x-device-fingerprint'] === 'string',
      fingerprintHeaderLength: headers['x-device-fingerprint']?.length ?? 0,
    },
    mode,
  };
}

async function exitImpersonation(page) {
  const responsePromise = page.waitForResponse((response) => response.url().includes('/api/v1/admin/impersonate/exit'));
  await page.getByRole('button', { name: 'Вернуться в админку' }).click();
  const response = await responsePromise;
  await page.waitForURL((url) => url.pathname.startsWith('/admin'), { timeout: 15000 });
  const headers = await response.request().allHeaders();
  return {
    status: response.status(),
    hasFingerprintHeader: typeof headers['x-device-fingerprint'] === 'string',
    fingerprintHeaderLength: headers['x-device-fingerprint']?.length ?? 0,
  };
}

async function main() {
  const browser = await chromium.launch({ headless: true });
  try {
    const result = {
      baseUrl,
      generatedAt: new Date().toISOString(),
      mode: process.env.FRONTEND_FINGERPRINT_MODE ?? null,
    };

    const admin = await loginWithDevAdmin(browser);
    result.devAdminLogin = admin.request;
    result.devAdminMode = admin.mode;

    const impersonation = await impersonateStudent(admin.page);
    result.impersonation = impersonation;
    result.exitImpersonation = await exitImpersonation(admin.page);
    await admin.context.close();

    if (studentOtp) {
      const student = await loginWithOtp(browser);
      result.studentOtpLogin = student.request;
      result.studentMode = student.mode;

      const labsResponse = await fetchJson(student.page, '/student/labs');
      const firstLab = Array.isArray(labsResponse.payload) ? labsResponse.payload[0] : null;
      result.studentLabs = {
        status: labsResponse.status,
        firstLabId: firstLab?.id ?? null,
        total: Array.isArray(labsResponse.payload) ? labsResponse.payload.length : null,
      };

      await openSecurityTab(student.page);
      result.sessions = await fetchJson(student.page, '/users/me/sessions');
      result.devicesBefore = await fetchJson(student.page, '/users/me/devices');
      result.securityUi = await collectSecurityUiEvidence(
        student.page,
        collectExpectedFragments(result.sessions.payload, result.devicesBefore.payload),
      );
      const studentState = await student.context.storageState();

      const mutableDevice = selectMutableDevice(result.devicesBefore.payload);
      if (allowDeviceMutations && mutableDevice) {
        const deviceId = mutableDevice.id;
        result.confirmDevice = await fetchJson(student.page, `/users/me/devices/${deviceId}/confirm`, 'POST');
        result.devicesAfterConfirm = await fetchJson(student.page, '/users/me/devices');
        result.deleteDevice = await fetchJson(student.page, `/users/me/devices/${deviceId}`, 'DELETE');
        result.devicesAfterDelete = await fetchJson(student.page, '/users/me/devices');
      } else {
        result.deviceMutationSkipped = allowDeviceMutations
          ? 'No unique untrusted device candidate was found for safe mutation'
          : 'Device confirm/delete skipped without PHASE7_ALLOW_DEVICE_MUTATIONS=1';
      }

      await student.context.close();
      const dashboardContext = await createContext(browser, studentState);
      result.dashboard = await collectPageEvidence(dashboardContext, baseUrl, '/dashboard', settleMs);
      await dashboardContext.close();

      if (result.studentLabs.firstLabId) {
        const labContext = await createContext(browser, studentState);
        result.labDetail = await collectPageEvidence(
          labContext,
          baseUrl,
          `/dashboard/labs/${result.studentLabs.firstLabId}`,
          settleMs,
        );
        await labContext.close();
      }
    }

    await fs.writeFile(outputPath, `${JSON.stringify(result, null, 2)}\n`, 'utf8');
    console.log(outputPath);
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
