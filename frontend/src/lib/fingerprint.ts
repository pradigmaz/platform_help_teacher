/**
 * Device fingerprint collector.
 * Собирает уникальные характеристики устройства для идентификации.
 */

interface DeviceFingerprint {
  canvas?: string;
  webgl?: {
    vendor: string;
    renderer: string;
  };
  screen: {
    width: number;
    height: number;
    colorDepth: number;
    pixelRatio: number;
  };
  timezone: string;
  language: string;
  platform: string;
  hardwareConcurrency: number;
  touchSupport: boolean;
  cookieEnabled: boolean;
}

let cachedFingerprint: string | null = null;

/**
 * Генерирует canvas fingerprint.
 */
function getCanvasFingerprint(): string | undefined {
  try {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    if (!ctx) return undefined;

    canvas.width = 200;
    canvas.height = 50;

    ctx.textBaseline = 'top';
    ctx.font = '14px Arial';
    ctx.fillStyle = '#f60';
    ctx.fillRect(125, 1, 62, 20);
    ctx.fillStyle = '#069';
    ctx.fillText('Fingerprint', 2, 15);
    ctx.fillStyle = 'rgba(102, 204, 0, 0.7)';
    ctx.fillText('Canvas', 4, 17);

    return canvas.toDataURL().slice(-50);
  } catch {
    return undefined;
  }
}

/**
 * Получает WebGL информацию.
 */
function getWebGLInfo(): { vendor: string; renderer: string } | undefined {
  try {
    const canvas = document.createElement('canvas');
    const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
    if (!gl) return undefined;

    const debugInfo = (gl as WebGLRenderingContext).getExtension('WEBGL_debug_renderer_info');
    if (!debugInfo) return undefined;

    return {
      vendor: (gl as WebGLRenderingContext).getParameter(debugInfo.UNMASKED_VENDOR_WEBGL) || 'unknown',
      renderer: (gl as WebGLRenderingContext).getParameter(debugInfo.UNMASKED_RENDERER_WEBGL) || 'unknown',
    };
  } catch {
    return undefined;
  }
}

/**
 * Собирает fingerprint устройства.
 */
export function collectFingerprint(): DeviceFingerprint {
  return {
    canvas: getCanvasFingerprint(),
    webgl: getWebGLInfo(),
    screen: {
      width: window.screen.width,
      height: window.screen.height,
      colorDepth: window.screen.colorDepth,
      pixelRatio: window.devicePixelRatio || 1,
    },
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    language: navigator.language,
    platform: navigator.platform,
    hardwareConcurrency: navigator.hardwareConcurrency || 0,
    touchSupport: 'ontouchstart' in window,
    cookieEnabled: navigator.cookieEnabled,
  };
}

/**
 * Получает fingerprint как JSON строку (кэшируется).
 */
export function getFingerprint(): string {
  if (cachedFingerprint) return cachedFingerprint;
  
  try {
    const fp = collectFingerprint();
    cachedFingerprint = JSON.stringify(fp);
    return cachedFingerprint;
  } catch {
    return '{}';
  }
}

/**
 * Получает fingerprint как hash (короткая версия).
 */
export function getFingerprintHash(): string {
  const fp = getFingerprint();
  let hash = 0;
  for (let i = 0; i < fp.length; i++) {
    const char = fp.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash;
  }
  return Math.abs(hash).toString(36);
}
