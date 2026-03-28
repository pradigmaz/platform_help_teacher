import { beforeEach, describe, expect, it, vi } from 'vitest';

const mocks = vi.hoisted(() => ({
  get: vi.fn(),
  primeFingerprintMode: vi.fn(),
}));

vi.mock('@thumbmarkjs/thumbmarkjs', () => ({
  Thumbmark: class Thumbmark {
    async get() {
      return mocks.get();
    }
  },
}));

vi.mock('./mode', () => ({
  isAuthFingerprintCollectionEnabled: () => true,
  primeFingerprintMode: mocks.primeFingerprintMode,
}));

import {
  clearAuthFingerprintCache,
  primeAuthFingerprint,
  readCachedAuthFingerprintEnvelope,
} from './adapter';

describe('auth fingerprint adapter', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.primeFingerprintMode.mockResolvedValue('auth_only');
    clearAuthFingerprintCache();
    sessionStorage.clear();
    document.documentElement.dataset.fingerprintMode = 'auth_only';

    Object.defineProperty(window, 'screen', {
      configurable: true,
      value: {
        width: 1920,
        height: 1080,
        colorDepth: 24,
      },
    });

    mocks.get.mockResolvedValue({
      thumbmark: 'thumbmark-hash',
      version: '1.7.6',
      components: {
        system: {
          platform: 'Win32',
          useragent: 'Mozilla/5.0 Chrome/122.0',
          hardwareConcurrency: 8,
          browser: { name: 'Chrome', version: '122.0.0.0' },
        },
        hardware: {
          videocard: {
            vendor: 'Intel',
            renderer: 'Iris Xe',
          },
        },
        canvas: {
          commonPixelsHash: 'canvas-hash',
        },
        locales: {
          languages: 'ru-RU',
          timezone: 'Europe/Moscow',
        },
      },
      error: [{ message: 'sample warning' }],
    });
  });

  it('collects and caches a canonical auth fingerprint envelope', async () => {
    await primeAuthFingerprint();

    const envelope = readCachedAuthFingerprintEnvelope();
    expect(envelope).toBeTruthy();

    const parsed = JSON.parse(envelope!);
    expect(parsed).toMatchObject({
      schema: 'fingerprint-migration-v1',
      kind: 'normalized_replacement',
      summary: {
        platform: 'Windows',
        browser: 'Chrome',
        screen: { width: 1920, height: 1080 },
      },
      matching: {
        platform: 'Win32',
        hardwareConcurrency: 8,
        screen: { width: 1920, height: 1080, colorDepth: 24 },
        webgl: { vendor: 'Intel', renderer: 'Iris Xe' },
        canvas: 'canvas-hash',
        userAgent: 'Mozilla/5.0 Chrome/122.0',
      },
      client: {
        userAgent: 'Mozilla/5.0 Chrome/122.0',
        language: 'ru-RU',
        timezone: 'Europe/Moscow',
      },
    });
    expect(parsed.raw).toMatchObject({
      adapter: 'thumbmarkjs',
      adapter_version: 1,
      library_version: '1.7.6',
      thumbmark: 'thumbmark-hash',
      errors: ['sample warning'],
    });
  });

  it('deduplicates concurrent collection and reuses cached payload', async () => {
    await Promise.all([primeAuthFingerprint(), primeAuthFingerprint()]);

    expect(mocks.get).toHaveBeenCalledTimes(1);
    expect(readCachedAuthFingerprintEnvelope()).toBeTruthy();
  });

  it('returns null when the cached payload has expired', () => {
    sessionStorage.setItem(
      'auth_fingerprint_v1',
      JSON.stringify({
        envelope: '{"schema":"fingerprint-migration-v1"}',
        expiresAt: Date.now() - 1,
      }),
    );

    expect(readCachedAuthFingerprintEnvelope()).toBeNull();
  });
});
