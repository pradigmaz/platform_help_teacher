const inFlightRequests = new Map<string, Promise<unknown>>();

export function runSingleFlight<T>(key: string, loader: () => Promise<T>): Promise<T> {
  const existing = inFlightRequests.get(key) as Promise<T> | undefined;
  if (existing) {
    return existing;
  }

  const request = loader().finally(() => {
    inFlightRequests.delete(key);
  });

  inFlightRequests.set(key, request);
  return request;
}

export function clearSingleFlight(key?: string): void {
  if (key) {
    inFlightRequests.delete(key);
    return;
  }

  inFlightRequests.clear();
}
