'use client';

type CacheEntry<T> = {
  data: T | null;
  expiresAt: number;
  inFlight: Promise<T> | null;
};

const entries = new Map<string, CacheEntry<unknown>>();

function getEntry<T>(key: string): CacheEntry<T> {
  const existing = entries.get(key) as CacheEntry<T> | undefined;
  if (existing) {
    return existing;
  }

  const created: CacheEntry<T> = {
    data: null,
    expiresAt: 0,
    inFlight: null,
  };
  entries.set(key, created as CacheEntry<unknown>);
  return created;
}

export async function loadCached<T>(
  key: string,
  loader: () => Promise<T>,
  options?: {
    forceRefresh?: boolean;
    ttlMs?: number;
  },
): Promise<T> {
  const ttlMs = options?.ttlMs ?? 15_000;
  const entry = getEntry<T>(key);
  const now = Date.now();

  if (!options?.forceRefresh && entry.data !== null && entry.expiresAt > now) {
    return entry.data;
  }

  if (!options?.forceRefresh && entry.inFlight) {
    return entry.inFlight;
  }

  entry.inFlight = loader()
    .then((data) => {
      entry.data = data;
      entry.expiresAt = Date.now() + ttlMs;
      return data;
    })
    .finally(() => {
      entry.inFlight = null;
    });

  return entry.inFlight;
}

export function invalidateCached(key: string) {
  entries.delete(key);
}

export function invalidateCachedByPrefix(prefix: string) {
  for (const key of entries.keys()) {
    if (key.startsWith(prefix)) {
      entries.delete(key);
    }
  }
}

export function resetReadCacheForTests() {
  entries.clear();
}
