/**
 * Hook для инициализации fingerprint при загрузке приложения.
 */
'use client';

import { useEffect, useState } from 'react';
import { initializeFingerprint, getFingerprintAsync } from '@/lib/fingerprint';

let isInitialized = false;

/**
 * Инициализирует fingerprint при монтировании компонента.
 * Гарантирует что fingerprint будет собран до первого API запроса.
 */
export function useInitializeFingerprint() {
  const [isReady, setIsReady] = useState(isInitialized);

  useEffect(() => {
    if (isInitialized) return;

    initializeFingerprint()
      .then(() => {
        isInitialized = true;
        setIsReady(true);
      })
      .catch((error) => {
        console.error('[Fingerprint] Initialization failed:', error);
        isInitialized = true;
        setIsReady(true);
      });
  }, []);

  return { isReady };
}

/**
 * Получает fingerprint (ждёт инициализации если нужно).
 */
export async function getInitializedFingerprint(): Promise<string> {
  return getFingerprintAsync();
}

/**
 * Проверяет готовность fingerprint (синхронно).
 */
export function isFingerprintReady(): boolean {
  return isInitialized;
}
