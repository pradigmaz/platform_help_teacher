import { describe, expect, it } from 'vitest';

import {
  buildSecurityUserInfoMap,
  extractSecurityUserIds,
  formatSecurityBanTimeLeft,
} from './securityTabModel';

describe('securityTabModel', () => {
  it('extracts user identifiers from bans only', () => {
    expect(
      extractSecurityUserIds([
        { identifier: 'user:42' } as never,
        { identifier: 'ip:127.0.0.1' } as never,
      ])
    ).toEqual(['42']);
  });

  it('builds user info map from resolved entries', () => {
    expect(
      buildSecurityUserInfoMap([
        { userId: '42', info: { id: '42', full_name: 'Иванов Иван' } as never },
        null,
      ])
    ).toEqual({
      '42': { id: '42', full_name: 'Иванов Иван' },
    });
  });

  it('formats ban ttl for expired and hour-long values', () => {
    expect(formatSecurityBanTimeLeft(null)).toBe('Истёк');
    expect(formatSecurityBanTimeLeft(3660)).toBe('1 ч 1 мин');
  });
});
