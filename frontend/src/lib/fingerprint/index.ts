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

interface NavigatorExtended extends Navigator {
  oscpu?: string;
  deviceMemory?: number;
  vendorSub?: string;
  buildID?: string;
  pdfViewerEnabled?: boolean;
  webdriver?: boolean;
  globalPrivacyControl?: boolean;
}

let cachedFingerprint: string | null = null;

/**
 * Собирает fingerprint устройства (sync версия).
 */
export function collectFingerprint(): DeviceFingerprint {
  const nav = navigator as NavigatorExtended;
  const audioData = getAudioFingerprint();
  const mediaFeatures = getMediaFeatures();
  
  return {
    // Screen
    screen: {
      width: window.screen.width,
      height: window.screen.height,
      availWidth: window.screen.availWidth,
      availHeight: window.screen.availHeight,
      colorDepth: window.screen.colorDepth,
      pixelDepth: window.screen.pixelDepth,
      pixelRatio: window.devicePixelRatio || 1,
      orientation: screen.orientation?.type,
      orientationAngle: screen.orientation?.angle,
    },
    
    // GPU
    webgl: getWebGLInfo(),
    webgl2Available: isWebGL2Available(),
    
    // Canvas
    canvas: getCanvasFingerprint(),
    canvasGeometry: getCanvasGeometry(),
    
    // Audio
    audio: audioData.hash,
    audioContext: audioData.context,
    
    // System
    platform: navigator.platform,
    oscpu: nav.oscpu,
    hardwareConcurrency: navigator.hardwareConcurrency || 0,
    deviceMemory: nav.deviceMemory,
    
    // Browser
    userAgent: navigator.userAgent,
    vendor: navigator.vendor,
    vendorSub: nav.vendorSub || '',
    product: navigator.product,
    productSub: navigator.productSub,
    buildID: nav.buildID,
    appName: navigator.appName,
    appVersion: navigator.appVersion,
    appCodeName: navigator.appCodeName,
    
    // Locale
    language: navigator.language,
    languages: [...(navigator.languages || [navigator.language])],
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    timezoneOffset: new Date().getTimezoneOffset(),
    
    // Network
    connection: getConnectionInfo(),
    onLine: navigator.onLine,
    
    // Input
    touchSupport: 'ontouchstart' in window || navigator.maxTouchPoints > 0,
    maxTouchPoints: navigator.maxTouchPoints || 0,
    pointerEnabled: !!window.PointerEvent,
    
    // Storage
    cookieEnabled: navigator.cookieEnabled,
    localStorageAvailable: checkStorage('localStorage'),
    sessionStorageAvailable: checkStorage('sessionStorage'),
    indexedDBAvailable: isIndexedDBAvailable(),
    
    // Fonts
    fonts: detectFonts(),
    
    // Plugins
    plugins: getPlugins(),
    mimeTypes: getMimeTypes(),
    
    // Flags
    pdfViewerEnabled: nav.pdfViewerEnabled ?? navigator.plugins.namedItem('PDF Viewer') !== null,
    webdriver: nav.webdriver ?? false,
    doNotTrack: navigator.doNotTrack,
    globalPrivacyControl: nav.globalPrivacyControl,
    
    // Media features
    ...mediaFeatures,
    
    // Math
    math: getMathFingerprint(),
    
    // Date format
    dateFormat: new Intl.DateTimeFormat().resolvedOptions().locale,
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
    cachedFingerprint = JSON.stringify(collectFingerprint());
    return cachedFingerprint;
  } catch {
    return '{}';
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
