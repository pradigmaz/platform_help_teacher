import { readCachedAuthFingerprintEnvelope } from '@/lib/fingerprint/adapter';

export function buildAuthFingerprintHeaders(
  headers: Record<string, string> = {},
): Record<string, string> {
  const envelope = readCachedAuthFingerprintEnvelope();
  if (!envelope) {
    return headers;
  }

  return {
    ...headers,
    'X-Device-Fingerprint': envelope,
  };
}
