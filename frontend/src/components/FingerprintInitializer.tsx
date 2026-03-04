/**
 * Client-компонент для инициализации fingerprint при загрузке приложения.
 */
'use client';

import { useInitializeFingerprint } from '@/hooks/useFingerprint';

export function FingerprintInitializer() {
  useInitializeFingerprint();
  return null;
}
