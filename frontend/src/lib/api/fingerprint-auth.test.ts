import { beforeEach, describe, expect, it, vi } from 'vitest';

const mocks = vi.hoisted(() => ({
  readCachedAuthFingerprintEnvelope: vi.fn(),
}));

vi.mock('@/lib/fingerprint/adapter', () => ({
  readCachedAuthFingerprintEnvelope: mocks.readCachedAuthFingerprintEnvelope,
}));

import { buildAuthFingerprintHeaders } from './fingerprint-auth';

describe('buildAuthFingerprintHeaders', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('adds fingerprint header when cached envelope is available', () => {
    mocks.readCachedAuthFingerprintEnvelope.mockReturnValue('fingerprint-payload');

    expect(buildAuthFingerprintHeaders({ Accept: 'application/json' })).toEqual({
      Accept: 'application/json',
      'X-Device-Fingerprint': 'fingerprint-payload',
    });
  });

  it('leaves headers unchanged when cache is empty', () => {
    mocks.readCachedAuthFingerprintEnvelope.mockReturnValue(null);

    expect(buildAuthFingerprintHeaders({ Accept: 'application/json' })).toEqual({
      Accept: 'application/json',
    });
  });
});
