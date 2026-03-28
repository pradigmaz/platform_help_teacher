export type FingerprintMode = 'off' | 'auth_only';

let inFlightFingerprintMode: Promise<FingerprintMode> | null = null;
let resolvedFingerprintMode: FingerprintMode | null = null;

function normalizeFingerprintMode(value: string | null | undefined): FingerprintMode {
  return value === 'auth_only' ? 'auth_only' : 'off';
}

function readFingerprintModeFromDom(): string | null {
  if (typeof document === 'undefined') {
    return null;
  }

  return document.documentElement.dataset.fingerprintMode ?? null;
}

function readFingerprintModeFromEnv(): string | null {
  if (typeof process === 'undefined') {
    return null;
  }

  return process.env.NEXT_PUBLIC_FINGERPRINT_MODE ?? null;
}

function getBootstrapFingerprintMode(): FingerprintMode {
  return normalizeFingerprintMode(readFingerprintModeFromDom() ?? readFingerprintModeFromEnv());
}

export function getFingerprintMode(): FingerprintMode {
  return resolvedFingerprintMode ?? getBootstrapFingerprintMode();
}

export function isAuthFingerprintCollectionEnabled(): boolean {
  return getFingerprintMode() === 'auth_only';
}

export async function primeFingerprintMode(): Promise<FingerprintMode> {
  if (resolvedFingerprintMode) {
    return resolvedFingerprintMode;
  }

  if (!inFlightFingerprintMode) {
    inFlightFingerprintMode = (async () => {
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || '/api/v1';

      try {
        const response = await fetch(`${baseUrl}/auth/fingerprint-mode`, {
          credentials: 'include',
          cache: 'no-store',
        });
        if (!response.ok) {
          throw new Error(`Failed to load fingerprint mode: ${response.status}`);
        }

        const payload = await response.json() as { mode?: string };
        resolvedFingerprintMode = normalizeFingerprintMode(payload.mode);
        return resolvedFingerprintMode;
      } catch {
        return getBootstrapFingerprintMode();
      } finally {
        inFlightFingerprintMode = null;
      }
    })();
  }

  return inFlightFingerprintMode;
}

export function clearFingerprintModeCache(): void {
  resolvedFingerprintMode = null;
  inFlightFingerprintMode = null;
}
