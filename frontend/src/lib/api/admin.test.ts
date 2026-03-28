import { beforeEach, describe, expect, it, vi } from 'vitest';

const mocks = vi.hoisted(() => ({
  post: vi.fn(),
  get: vi.fn(),
  put: vi.fn(),
  buildAuthFingerprintHeaders: vi.fn(),
}));

vi.mock('./client', () => ({
  api: {
    post: mocks.post,
    get: mocks.get,
    put: mocks.put,
  },
}));

vi.mock('./fingerprint-auth', () => ({
  buildAuthFingerprintHeaders: mocks.buildAuthFingerprintHeaders,
}));

import { AdminAPI } from './admin';

describe('AdminAPI fingerprint headers', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.buildAuthFingerprintHeaders.mockReturnValue({
      'X-Device-Fingerprint': 'fingerprint-payload',
    });
    mocks.post.mockResolvedValue({ data: {} });
  });

  it('attaches fingerprint headers to impersonation entry', async () => {
    await AdminAPI.impersonateUser('student-1');

    expect(mocks.post).toHaveBeenCalledWith(
      '/admin/impersonate/student-1',
      undefined,
      {
        headers: {
          'X-Device-Fingerprint': 'fingerprint-payload',
        },
      },
    );
  });

  it('attaches fingerprint headers to impersonation exit', async () => {
    await AdminAPI.exitImpersonation();

    expect(mocks.post).toHaveBeenCalledWith(
      '/admin/impersonate/exit',
      undefined,
      {
        headers: {
          'X-Device-Fingerprint': 'fingerprint-payload',
        },
      },
    );
  });
});
