/**
 * Storage availability checks.
 */

export function checkStorage(type: 'localStorage' | 'sessionStorage'): boolean {
  try {
    const storage = window[type];
    const key = '__fp_test__';
    storage.setItem(key, '1');
    storage.removeItem(key);
    return true;
  } catch {
    return false;
  }
}

export function isIndexedDBAvailable(): boolean {
  return !!window.indexedDB;
}
