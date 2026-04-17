import { describe, expect, it } from 'vitest';

import { formatScoreValue } from './score-format';

describe('formatScoreValue', () => {
  it('rounds noisy floating point score values to one decimal place', () => {
    expect(formatScoreValue(21.649484536082475)).toBe('21.6');
    expect(formatScoreValue(13.350515463917525)).toBe('13.4');
  });

  it('keeps integer-looking score values compact', () => {
    expect(formatScoreValue(40)).toBe('40');
    expect(formatScoreValue(20.000000000000004)).toBe('20');
  });
});
