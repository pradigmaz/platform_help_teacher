import { defineConfig } from '@playwright/test';

const port = process.env.PLAYWRIGHT_TEST_PORT ?? '3100';
const baseURL = process.env.PLAYWRIGHT_TEST_BASE_URL ?? `http://127.0.0.1:${port}`;

export default defineConfig({
  testDir: './tests/smoke',
  testMatch: '**/*.spec.ts',
  fullyParallel: true,
  use: {
    baseURL,
    trace: 'on-first-retry',
  },
  webServer: {
    command: 'npm run start:smoke',
    url: baseURL,
    reuseExistingServer: !process.env.CI,
    timeout: 240_000,
    env: {
      HOSTNAME: '127.0.0.1',
      NEXT_TELEMETRY_DISABLED: '1',
      NEXT_PUBLIC_FINGERPRINT_MODE: 'off',
      PLAYWRIGHT_TEST_PORT: port,
      PORT: port,
    },
  },
});
