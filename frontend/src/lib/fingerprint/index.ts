/**
 * Device fingerprint collector — модульная версия.
 */
export type { DeviceFingerprint } from './types';

import type { DeviceFingerprint } from './types';
import { getCanvasFingerprint, getCanvasGeometry } from './canvas';
import { getWebGLInfo, isWebGL2Available } from './webgl';
import { getAudioFingerprint } from './audio';
import { detectFonts } from './fonts';
import { getPlugins, getMimeTypes } from './plugins';
import { getConnectionInfo } from './network';
import { getMediaFeatures } from './media-features';
import { getMathFingerprint } from './math';
import { checkStorage, isIndexedDBAvailable } from './storage';
import { enrichWithAsyncData } from './async-collectors';

interface NavigatorExtended {
  oscpu?: string;
  deviceMemory?: number;
  vendorSub?: string;
  buildID?: string;
  pdfViewerEnabled?: boolean;
  globalPrivacyControl?: boolean;
}

type NavigatorWithExtensions = Navigator & NavigatorExtended;

let cachedFingerprint: string | null = null;

/**
 * Собирает fingerprint устройства (sync версия).
 */
export function collectFingerprint(): DeviceFingerprint {
  const nav = navigator as NavigatorWithExtensions;
  
  // Безопасно получаем данные с fallback
  const safeGet = <T>(fn: () => T, fallback: T): T => {
    try { return fn(); } catch { return fallback; }
  };
  
  const audioData = safeGet(() => getAudioFingerprint(), { hash: undefined, context: undefined });
  const mediaFeatures = safeGet(() => getMediaFeatures(), {});
  
  return {
    // Screen
    screen: safeGet(() => ({
      width: window.screen.width,
      height: window.screen.height,
      availWidth: window.screen.availWidth,
      availHeight: window.screen.availHeight,
      colorDepth: window.screen.colorDepth,
      pixelDepth: window.screen.pixelDepth,
      pixelRatio: window.devicePixelRatio || 1,
      orientation: screen.orientation?.type,
      orientationAngle: screen.orientation?.angle,
    }), { 
      width: 0, 
      height: 0, 
      availWidth: 0,
      availHeight: 0,
      colorDepth: 0, 
      pixelDepth: 0, 
      pixelRatio: 1,
      orientation: undefined,
      orientationAngle: undefined,
    }),
    
    // GPU
    webgl: safeGet(() => getWebGLInfo(), undefined),
    webgl2Available: safeGet(() => isWebGL2Available(), false),
    
    // Canvas
    canvas: safeGet(() => getCanvasFingerprint(), undefined),
    canvasGeometry: safeGet(() => getCanvasGeometry(), undefined),
    
    // Audio
    audio: audioData.hash,
    audioContext: audioData.context,
    
    // System
    platform: nav.platform || '',
    oscpu: nav.oscpu,
    hardwareConcurrency: nav.hardwareConcurrency || 0,
    deviceMemory: nav.deviceMemory,
    
    // Browser
    userAgent: nav.userAgent || '',
    vendor: nav.vendor || '',
    vendorSub: nav.vendorSub || '',
    product: nav.product || '',
    productSub: nav.productSub || '',
    buildID: nav.buildID,
    appName: nav.appName || '',
    appVersion: nav.appVersion || '',
    appCodeName: nav.appCodeName || '',
    
    // Locale
    language: nav.language || '',
    languages: safeGet(() => [...(nav.languages || [nav.language])], []),
    timezone: safeGet(() => Intl.DateTimeFormat().resolvedOptions().timeZone, ''),
    timezoneOffset: safeGet(() => new Date().getTimezoneOffset(), 0),
    
    // Network
    connection: safeGet(() => getConnectionInfo(), undefined),
    onLine: nav.onLine ?? true,
    
    // Input
    touchSupport: safeGet(() => 'ontouchstart' in window || nav.maxTouchPoints > 0, false),
    maxTouchPoints: nav.maxTouchPoints || 0,
    pointerEnabled: !!window.PointerEvent,
    
    // Storage
    cookieEnabled: nav.cookieEnabled ?? false,
    localStorageAvailable: safeGet(() => checkStorage('localStorage'), false),
    sessionStorageAvailable: safeGet(() => checkStorage('sessionStorage'), false),
    indexedDBAvailable: safeGet(() => isIndexedDBAvailable(), false),
    
    // Fonts
    fonts: safeGet(() => detectFonts(), []),
    
    // Plugins
    plugins: safeGet(() => getPlugins(), []),
    mimeTypes: safeGet(() => getMimeTypes(), []),
    
    // Flags
    pdfViewerEnabled: nav.pdfViewerEnabled ?? safeGet(() => nav.plugins?.namedItem('PDF Viewer') !== null, false),
    webdriver: nav.webdriver ?? false,
    doNotTrack: nav.doNotTrack,
    globalPrivacyControl: nav.globalPrivacyControl,
    
    // Media features
    ...mediaFeatures,
    
    // Math
    math: safeGet(() => getMathFingerprint(), undefined),
    
    // Date format
    dateFormat: safeGet(() => new Intl.DateTimeFormat().resolvedOptions().locale, ''),
  };
}

/**
 * Собирает расширенный fingerprint (async версия).
 */
export async function collectFingerprintAsync(): Promise<DeviceFingerprint> {
  return enrichWithAsyncData(collectFingerprint());
}

/**
 * Получает fingerprint как JSON строку (кэшируется).
 */
export function getFingerprint(): string {
  if (cachedFingerprint) return cachedFingerprint;
  try {
    const fp = collectFingerprint();
    // Проверяем что собрали хоть что-то
    if (!fp || Object.keys(fp).length === 0) {
      console.warn('[Fingerprint] Empty fingerprint collected');
      return '{}';
    }
    cachedFingerprint = JSON.stringify(fp);
    return cachedFingerprint;
  } catch (e) {
    console.error('[Fingerprint] Collection failed:', e);
    // Fallback — минимальный fingerprint
    try {
      const fallback = {
        screen: {
          width: window.screen?.width,
          height: window.screen?.height,
          colorDepth: window.screen?.colorDepth,
        },
        userAgent: navigator.userAgent,
        language: navigator.language,
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
        platform: navigator.platform,
      };
      return JSON.stringify(fallback);
    } catch {
      return '{}';
    }
  }
}

/**
 * Получает fingerprint как hash.
 */
export function getFingerprintHash(): string {
  const fp = getFingerprint();
  let hash = 0;
  for (let i = 0; i < fp.length; i++) {
    hash = ((hash << 5) - hash) + fp.charCodeAt(i);
    hash = hash & hash;
  }
  return Math.abs(hash).toString(36);
}
