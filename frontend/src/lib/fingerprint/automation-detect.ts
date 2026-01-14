/**
 * Детекция автоматизации браузера (Selenium, Puppeteer, Playwright).
 * 
 * Сигналы:
 * 1. navigator.webdriver = true
 * 2. HeadlessChrome в User-Agent
 * 3. Глобальные переменные Selenium (cdc_*, $cdc_*)
 * 4. Отсутствие window.chrome в Chrome UA
 * 5. Пустой navigator.plugins в Chrome
 * 6. CDP serialization side effect
 */

export interface AutomationSignals {
  isWebdriver: boolean;
  isHeadless: boolean;
  hasSeleniumVars: boolean;
  hasChromeObject: boolean;
  pluginsCount: number;
  hasPhantom: boolean;
  hasNightmare: boolean;
  hasCypressVars: boolean;
  suspiciousUA: boolean;
  chromeVersionMismatch: boolean;
  automationScore: number; // 0-100, выше = больше вероятность автоматизации
}

// Selenium глобальные переменные
const SELENIUM_VARS = [
  'cdc_adoQpoasnfa76pfcZLmcfl_Array',
  'cdc_adoQpoasnfa76pfcZLmcfl_Object', 
  'cdc_adoQpoasnfa76pfcZLmcfl_Promise',
  'cdc_adoQpoasnfa76pfcZLmcfl_Proxy',
  'cdc_adoQpoasnfa76pfcZLmcfl_Symbol',
  'cdc_adoQpoasnfa76pfcZLmcfl_JSON',
  'cdc_adoQpoasnfa76pfcZLmcfl_Window',
  '$cdc_asdjflasutopfhvcZLmcfl_',
  '__webdriver_evaluate',
  '__selenium_evaluate',
  '__webdriver_script_function',
  '__webdriver_script_func',
  '__webdriver_script_fn',
  '__fxdriver_evaluate',
  '__driver_unwrapped',
  '__webdriver_unwrapped',
  '__driver_evaluate',
  '__selenium_unwrapped',
  '__fxdriver_unwrapped',
  '_Selenium_IDE_Recorder',
  '_selenium',
  'calledSelenium',
  '$chrome_asyncScriptInfo',
  '$cdc_asdjflasutopfhvcZLmcfl_',
  'ret_nodes', // Selenium executeScript artifact
];

// Cypress переменные
const CYPRESS_VARS = ['__cypress', 'Cypress', '__cy'];

// Максимальные известные версии браузеров (обновлять периодически)
const MAX_KNOWN_VERSIONS = {
  chrome: 135,
  firefox: 130,
  safari: 18,
  edge: 135,
};

/**
 * Проверяет наличие глобальных переменных.
 */
function checkGlobalVars(vars: string[]): boolean {
  return vars.some(v => {
    try {
      return v in window || (window as unknown as Record<string, unknown>)[v] !== undefined;
    } catch {
      return false;
    }
  });
}

/**
 * Проверяет версию браузера в UA на реалистичность.
 */
function checkSuspiciousUA(): { suspicious: boolean; versionMismatch: boolean } {
  const ua = navigator.userAgent;
  
  // Проверка HeadlessChrome
  if (ua.includes('HeadlessChrome')) {
    return { suspicious: true, versionMismatch: false };
  }
  
  // Проверка нереалистичных версий Chrome
  const chromeMatch = ua.match(/Chrome\/(\d+)/);
  if (chromeMatch) {
    const version = parseInt(chromeMatch[1], 10);
    if (version > MAX_KNOWN_VERSIONS.chrome) {
      return { suspicious: true, versionMismatch: true };
    }
  }
  
  // Проверка нереалистичных версий Firefox
  const firefoxMatch = ua.match(/Firefox\/(\d+)/);
  if (firefoxMatch) {
    const version = parseInt(firefoxMatch[1], 10);
    if (version > MAX_KNOWN_VERSIONS.firefox) {
      return { suspicious: true, versionMismatch: true };
    }
  }
  
  return { suspicious: false, versionMismatch: false };
}

/**
 * Проверяет наличие window.chrome в Chrome браузере.
 */
function checkChromeObject(): boolean {
  const ua = navigator.userAgent;
  const isChrome = ua.includes('Chrome') && !ua.includes('Edg') && !ua.includes('OPR');
  
  if (isChrome) {
    // В реальном Chrome должен быть window.chrome
    return 'chrome' in window && (window as Record<string, unknown>).chrome !== undefined;
  }
  
  return true; // Не Chrome — не проверяем
}

/**
 * Собирает сигналы автоматизации.
 */
export function detectAutomation(): AutomationSignals {
  const nav = navigator as Navigator & { webdriver?: boolean };
  const uaCheck = checkSuspiciousUA();
  
  const signals: AutomationSignals = {
    isWebdriver: nav.webdriver === true,
    isHeadless: navigator.userAgent.includes('HeadlessChrome') || 
                navigator.userAgent.includes('HeadlessFirefox'),
    hasSeleniumVars: checkGlobalVars(SELENIUM_VARS),
    hasChromeObject: checkChromeObject(),
    pluginsCount: navigator.plugins?.length ?? 0,
    hasPhantom: 'callPhantom' in window || '_phantom' in window || 'phantom' in window,
    hasNightmare: '__nightmare' in window,
    hasCypressVars: checkGlobalVars(CYPRESS_VARS),
    suspiciousUA: uaCheck.suspicious,
    chromeVersionMismatch: uaCheck.versionMismatch,
    automationScore: 0,
  };
  
  // Расчёт score
  let score = 0;
  
  if (signals.isWebdriver) score += 40;
  if (signals.isHeadless) score += 50;
  if (signals.hasSeleniumVars) score += 50;
  if (!signals.hasChromeObject && navigator.userAgent.includes('Chrome')) score += 30;
  if (signals.pluginsCount === 0 && navigator.userAgent.includes('Chrome')) score += 20;
  if (signals.hasPhantom) score += 50;
  if (signals.hasNightmare) score += 50;
  if (signals.hasCypressVars) score += 30;
  if (signals.suspiciousUA) score += 25;
  if (signals.chromeVersionMismatch) score += 35;
  
  signals.automationScore = Math.min(100, score);
  
  return signals;
}

/**
 * Быстрая проверка — вероятно бот?
 */
export function isProbablyBot(): boolean {
  const signals = detectAutomation();
  return signals.automationScore >= 40;
}
