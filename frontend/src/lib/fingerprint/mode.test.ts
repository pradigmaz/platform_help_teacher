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

  it('prefers the runtime mode endpoint for the current page lifecycle', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ mode: 'auth_only' }),
    });
    vi.stubGlobal('fetch', fetchMock);

    await expect(primeFingerprintMode()).resolves.toBe('auth_only');
    expect(getFingerprintMode()).toBe('auth_only');
    await expect(primeFingerprintMode()).resolves.toBe('auth_only');
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it('falls back to bootstrap mode when the runtime endpoint fails', async () => {
    document.documentElement.dataset.fingerprintMode = 'auth_only';
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('boom')));

    await expect(primeFingerprintMode()).resolves.toBe('auth_only');
    expect(getFingerprintMode()).toBe('auth_only');
  });

  it('does not freeze bootstrap fallback after a transient endpoint failure', async () => {
    document.documentElement.dataset.fingerprintMode = 'off';
    const fetchMock = vi
      .fn()
      .mockRejectedValueOnce(new Error('boom'))
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ mode: 'auth_only' }),
      });
    vi.stubGlobal('fetch', fetchMock);

    await expect(primeFingerprintMode()).resolves.toBe('off');
    expect(getFingerprintMode()).toBe('off');

    await expect(primeFingerprintMode()).resolves.toBe('auth_only');
    expect(getFingerprintMode()).toBe('auth_only');
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it('drops the resolved runtime mode when cache is cleared', async () => {
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
