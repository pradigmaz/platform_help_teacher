import { describe, expect, it } from 'vitest';
import { buildGlobalAttestationSettingsPayload } from './buildSavePayload';
import { DEFAULT_FORM_STATE } from './types';

describe('buildGlobalAttestationSettingsPayload', () => {
  it('omits legacy lab thresholds from the global attestation save payload', () => {
    const payload = buildGlobalAttestationSettingsPayload('first', DEFAULT_FORM_STATE);

    expect(payload.labs_count_first).toBeUndefined();
    expect(payload.labs_count_second).toBeUndefined();
    expect(payload.labs_weight).toBe(DEFAULT_FORM_STATE.labs_weight);
  });
});

