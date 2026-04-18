import { beforeEach, describe, expect, it, vi } from 'vitest';

const mocks = vi.hoisted(() => ({
  post: vi.fn(),
  get: vi.fn(),
  buildAuthFingerprintHeaders: vi.fn(),
}));

vi.mock('./client', () => ({
  api: {
    post: mocks.post,
    get: mocks.get,
  },
}));

vi.mock('./fingerprint-auth', () => ({
  buildAuthFingerprintHeaders: mocks.buildAuthFingerprintHeaders,
}));

import { AuthAPI } from './auth';

describe('AuthAPI fingerprint headers', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.buildAuthFingerprintHeaders.mockReturnValue({
      'X-Device-Fingerprint': 'fingerprint-payload',
    });
    mocks.post.mockResolvedValue({ data: { ok: true } });
  });

  it('attaches fingerprint headers to otp login', async () => {
    await AuthAPI.login('123456', true, false);

    expect(mocks.post).toHaveBeenCalledWith(
      '/auth/otp',
      {
        otp: '123456',
        remember_device: true,
        force_session_cookie: false,
      },
      {
        headers: {
          'X-Device-Fingerprint': 'fingerprint-payload',
        },
      },
    );
  });

  it('attaches fingerprint headers to dev login', async () => {
    await AuthAPI.devLogin();

    expect(mocks.post).toHaveBeenCalledWith(
      '/auth/dev-login',
      { remember_device: true },
      {
        headers: {
          'X-Device-Fingerprint': 'fingerprint-payload',
        },
      },
    );
  });

  it('fetches auth status without fingerprint headers', async () => {
    mocks.get.mockResolvedValue({ data: { authenticated: false, user: null } });

    await AuthAPI.status();

    expect(mocks.get).toHaveBeenCalledWith('/auth/status');
    expect(mocks.buildAuthFingerprintHeaders).toHaveBeenCalledTimes(0);
  });
});
