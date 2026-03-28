import { beforeEach, describe, expect, it, vi } from 'vitest';

import {
  clearFingerprintModeCache,
  getFingerprintMode,
  primeFingerprintMode,
} from './mode';

describe('fingerprint mode', () => {
  beforeEach(() => {
    clearFingerprintModeCache();
    document.documentElement.dataset.fingerprintMode = 'off';
    vi.unstubAllGlobals();
  });

  it('uses the server bootstrap mode without extra network requests', async () => {
    document.documentElement.dataset.fingerprintMode = 'auth_only';
    const fetchMock = vi.fn();
    vi.stubGlobal('fetch', fetchMock);

    await expect(primeFingerprintMode()).resolves.toBe('auth_only');
    expect(getFingerprintMode()).toBe('auth_only');
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('falls back to the runtime endpoint when bootstrap mode is unavailable', async () => {
    delete document.documentElement.dataset.fingerprintMode;
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ mode: 'auth_only' }),
    });
    vi.stubGlobal('fetch', fetchMock);

    await expect(primeFingerprintMode()).resolves.toBe('auth_only');
    expect(getFingerprintMode()).toBe('auth_only');
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it('falls back to off when bootstrap is unavailable and the runtime endpoint fails', async () => {
    delete document.documentElement.dataset.fingerprintMode;
    const fetchMock = vi.fn().mockRejectedValue(new Error('boom'));
    vi.stubGlobal('fetch', fetchMock);

    await expect(primeFingerprintMode()).resolves.toBe('off');
    expect(getFingerprintMode()).toBe('off');
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it('drops the resolved runtime mode when cache is cleared', async () => {
    delete document.documentElement.dataset.fingerprintMode;
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ mode: 'auth_only' }),
    }));

    await expect(primeFingerprintMode()).resolves.toBe('auth_only');
    clearFingerprintModeCache();
    document.documentElement.dataset.fingerprintMode = 'off';

    expect(getFingerprintMode()).toBe('off');
  });
});
