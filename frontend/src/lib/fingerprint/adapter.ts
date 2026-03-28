import { isAuthFingerprintCollectionEnabled, primeFingerprintMode } from './mode';

const AUTH_FINGERPRINT_CACHE_KEY = 'auth_fingerprint_v1';
const AUTH_FINGERPRINT_TTL_MS = 30 * 60 * 1000;

type JsonRecord = Record<string, unknown>;

type CachedFingerprintRecord = {
  envelope: string;
  expiresAt: number;
};

type FingerprintEnvelope = {
  schema: 'fingerprint-migration-v1';
  kind: 'normalized_replacement';
  summary: {
    platform: string;
    browser: string;
    screen: {
      width: number;
      height: number;
    };
  };
  matching: {
    platform: string;
    hardwareConcurrency: number;
    screen: {
      width: number;
      height: number;
      colorDepth: number;
    };
    webgl: {
      vendor: string;
      renderer: string;
    };
    canvas: string;
    userAgent: string;
  };
  client: {
    userAgent: string;
    language?: string;
    timezone?: string;
  };
  raw: {
    adapter: 'thumbmarkjs';
    adapter_version: 1;
    library_version: string;
    thumbmark?: string;
    components: {
      system: JsonRecord;
      hardware: JsonRecord;
      canvas: JsonRecord;
      locales: JsonRecord;
    };
    errors: string[];
  };
};

let inFlightFingerprintCollection: Promise<string | null> | null = null;

function asRecord(value: unknown): JsonRecord | null {
  return value && typeof value === 'object' && !Array.isArray(value) ? (value as JsonRecord) : null;
}

function nonEmptyString(value: unknown): string | null {
  return typeof value === 'string' && value.trim() ? value.trim() : null;
}

function positiveInteger(value: unknown): number | null {
  return typeof value === 'number' && Number.isInteger(value) && value > 0 ? value : null;
}

function readCacheRecord(): CachedFingerprintRecord | null {
  if (typeof sessionStorage === 'undefined') {
    return null;
  }

  const rawValue = sessionStorage.getItem(AUTH_FINGERPRINT_CACHE_KEY);
  if (!rawValue) {
    return null;
  }

  try {
    const parsed = JSON.parse(rawValue) as Partial<CachedFingerprintRecord>;
    if (typeof parsed.envelope !== 'string' || typeof parsed.expiresAt !== 'number') {
      sessionStorage.removeItem(AUTH_FINGERPRINT_CACHE_KEY);
      return null;
    }
    if (parsed.expiresAt <= Date.now()) {
      sessionStorage.removeItem(AUTH_FINGERPRINT_CACHE_KEY);
      return null;
    }
    return {
      envelope: parsed.envelope,
      expiresAt: parsed.expiresAt,
    };
  } catch {
    sessionStorage.removeItem(AUTH_FINGERPRINT_CACHE_KEY);
    return null;
  }
}

function writeCacheRecord(envelope: string): void {
  if (typeof sessionStorage === 'undefined') {
    return;
  }

  const payload: CachedFingerprintRecord = {
    envelope,
    expiresAt: Date.now() + AUTH_FINGERPRINT_TTL_MS,
  };
  sessionStorage.setItem(AUTH_FINGERPRINT_CACHE_KEY, JSON.stringify(payload));
}

function normalizePlatformFamily(platform: string): string {
  if (platform.includes('Win')) return 'Windows';
  if (platform.includes('Mac')) return 'macOS';
  if (platform.includes('Linux')) return 'Linux';
  if (platform.includes('Android')) return 'Android';
  if (platform.includes('iPhone') || platform.includes('iPad')) return 'iOS';
  return platform;
}

function getScreenSnapshot(): { width: number; height: number; colorDepth: number } | null {
  if (typeof window === 'undefined' || typeof window.screen === 'undefined') {
    return null;
  }

  const width = positiveInteger(window.screen.width);
  const height = positiveInteger(window.screen.height);
  const colorDepth = positiveInteger(window.screen.colorDepth);
  if (width === null || height === null || colorDepth === null) {
    return null;
  }

  return { width, height, colorDepth };
}

function buildVendorErrors(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }

  return value.flatMap((entry) => {
    const record = asRecord(entry);
    const message = nonEmptyString(record?.message);
    return message ? [message] : [];
  });
}

function buildEnvelope(result: { thumbmark?: string; components?: unknown; error?: unknown; version?: string }): FingerprintEnvelope | null {
  const components = asRecord(result.components);
  const system = asRecord(components?.system);
  const hardware = asRecord(components?.hardware);
  const canvas = asRecord(components?.canvas);
  const locales = asRecord(components?.locales) ?? {};
  const browser = asRecord(system?.browser);
  const videocard = asRecord(hardware?.videocard);
  const screen = getScreenSnapshot();

  const platform = nonEmptyString(system?.platform);
  const browserName = nonEmptyString(browser?.name);
  const userAgent = nonEmptyString(system?.useragent);
  const hardwareConcurrency = positiveInteger(system?.hardwareConcurrency);
  const canvasHash = nonEmptyString(canvas?.commonPixelsHash);
  const webglVendor = nonEmptyString(videocard?.vendorUnmasked) ?? nonEmptyString(videocard?.vendor);
  const webglRenderer = nonEmptyString(videocard?.rendererUnmasked) ?? nonEmptyString(videocard?.renderer);

  if (
    !platform ||
    !browserName ||
    !userAgent ||
    hardwareConcurrency === null ||
    !canvasHash ||
    !webglVendor ||
    !webglRenderer ||
    !screen
  ) {
    return null;
  }

  const language = nonEmptyString(locales.languages);
  const timezone = nonEmptyString(locales.timezone);

  return {
    schema: 'fingerprint-migration-v1',
    kind: 'normalized_replacement',
    summary: {
      platform: normalizePlatformFamily(platform),
      browser: browserName,
      screen: {
        width: screen.width,
        height: screen.height,
      },
    },
    matching: {
      platform,
      hardwareConcurrency,
      screen,
      webgl: {
        vendor: webglVendor,
        renderer: webglRenderer,
      },
      canvas: canvasHash,
      userAgent,
    },
    client: {
      userAgent,
      ...(language ? { language } : {}),
      ...(timezone ? { timezone } : {}),
    },
    raw: {
      adapter: 'thumbmarkjs',
      adapter_version: 1,
      library_version: nonEmptyString(result.version) ?? 'unknown',
      ...(nonEmptyString(result.thumbmark) ? { thumbmark: result.thumbmark } : {}),
      components: {
        system: system ?? {},
        hardware: hardware ?? {},
        canvas: canvas ?? {},
        locales,
      },
      errors: buildVendorErrors(result.error),
    },
  };
}

async function collectAuthFingerprintEnvelope(): Promise<string | null> {
  try {
    const { Thumbmark } = await import('@thumbmarkjs/thumbmarkjs');
    const thumbmark = new Thumbmark({
      include: ['canvas', 'hardware', 'locales', 'system'],
      logging: false,
      performance: false,
      experimental: false,
      cache_lifetime_in_ms: 0,
      stabilize: ['private', 'iframe'],
      timeout: 5000,
    });
    const envelope = buildEnvelope(await thumbmark.get());
    if (!envelope) {
      return null;
    }

    const serialized = JSON.stringify(envelope);
    writeCacheRecord(serialized);
    return serialized;
  } catch {
    return null;
  }
}

export function readCachedAuthFingerprintEnvelope(): string | null {
  if (!isAuthFingerprintCollectionEnabled()) {
    return null;
  }

  return readCacheRecord()?.envelope ?? null;
}

export async function primeAuthFingerprint(): Promise<void> {
  const mode = await primeFingerprintMode();
  if (mode !== 'auth_only' || readCachedAuthFingerprintEnvelope()) {
    return;
  }

  if (!inFlightFingerprintCollection) {
    inFlightFingerprintCollection = collectAuthFingerprintEnvelope().finally(() => {
      inFlightFingerprintCollection = null;
    });
  }

  await inFlightFingerprintCollection;
}

export function clearAuthFingerprintCache(): void {
  if (typeof sessionStorage !== 'undefined') {
    sessionStorage.removeItem(AUTH_FINGERPRINT_CACHE_KEY);
  }
  inFlightFingerprintCollection = null;
}
