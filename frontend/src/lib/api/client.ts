import axios, { AxiosError } from 'axios';
import axiosRetry from 'axios-retry';
import qs from 'qs';
import logger from '@/lib/logger';

// --- Custom Error Class ---
export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public isRetryable: boolean = false
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

function formatApiDetail(detail: unknown): string {
  if (typeof detail === 'string') {
    return detail;
  }

  if (Array.isArray(detail)) {
    const messages = detail.map((item) => {
      if (typeof item === 'string') {
        return item;
      }

      if (item && typeof item === 'object') {
        const record = item as Record<string, unknown>;
        const location = Array.isArray(record.loc) ? record.loc.join('.') : null;
        const message = typeof record.msg === 'string' ? record.msg : JSON.stringify(record);
        return location ? `${location}: ${message}` : message;
      }

      return String(item);
    });

    return messages.join('; ');
  }

  if (detail && typeof detail === 'object') {
    if ('detail' in detail) {
      return formatApiDetail((detail as Record<string, unknown>).detail);
    }
    return JSON.stringify(detail);
  }

  return '';
}

// --- Axios Configuration ---
const baseURL = process.env.NEXT_PUBLIC_API_URL || '/api/v1';
const perfDebugEnabled = process.env.NEXT_PUBLIC_PERF_DEBUG === '1';

type RequestMetadata = {
  startTime: number;
};

// Валидация URL для защиты от SSRF (CVE-2025-27152)
function isValidRelativeUrl(url: string | undefined): boolean {
  if (!url) return true;
  if (url.startsWith('http://') || url.startsWith('https://') || 
      url.startsWith('data:') || url.startsWith('//')) {
    return false;
  }
  return true;
}

export const api = axios.create({
  baseURL,
  timeout: 30000,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
  paramsSerializer: (params) => qs.stringify(params, { arrayFormat: 'repeat' }),
});

// Защита от SSRF + автоматическое добавление CSRF токена
api.interceptors.request.use(async (config) => {
  const requestConfig = config as typeof config & { metadata?: RequestMetadata };
  if (perfDebugEnabled) {
    requestConfig.metadata = { startTime: performance.now() };
  }
  if (!isValidRelativeUrl(config.url)) {
    return Promise.reject(new ApiError(400, 'Invalid URL: absolute URLs are not allowed'));
  }
  // Автоматически добавляем CSRF токен для мутирующих запросов
  const method = config.method?.toUpperCase();
  if (method && ['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) {
    try {
      const token = await ensureCsrfTokenInternal();
      if (token) {
        config.headers['X-CSRF-Token'] = token;
      }
    } catch {
      // Игнорируем ошибку получения токена для /auth/csrf-token
    }
  }
  return config;
});

axiosRetry(api, {
  retries: 3,
  retryDelay: axiosRetry.exponentialDelay,
  retryCondition: (error) => {
    // НЕ повторяем POST/PUT/PATCH/DELETE — они не идемпотентны
    const method = error.config?.method?.toUpperCase();
    if (method && ['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) {
      return false;
    }
    return (
      axiosRetry.isNetworkOrIdempotentRequestError(error) ||
      error.code === 'ERR_NETWORK' ||
      (error.response?.status ? error.response.status >= 500 : false)
    );
  },
});

// --- CSRF Token Management ---
let csrfToken: string | null = null;
let csrfTokenPromise: Promise<string | null> | null = null;

// Внутренняя функция для interceptor (избегает бесконечной рекурсии)
async function ensureCsrfTokenInternal(): Promise<string | null> {
  // Если уже есть токен — возвращаем
  if (csrfToken) return csrfToken;
  
  // Если уже идёт запрос — ждём его
  if (csrfTokenPromise) return csrfTokenPromise;
  
  // Запрашиваем новый токен
  csrfTokenPromise = axios.get<{ csrf_token: string }>(`${baseURL}/auth/csrf-token`, {
    withCredentials: true,
  }).then(({ data }) => {
    csrfToken = data.csrf_token;
    csrfTokenPromise = null;
    return csrfToken;
  }).catch(() => {
    csrfTokenPromise = null;
    return null;
  });
  
  return csrfTokenPromise;
}

export async function ensureCsrfToken(): Promise<string> {
  const token = await ensureCsrfTokenInternal();
  if (!token) {
    throw new ApiError(0, 'Failed to obtain CSRF token');
  }
  return token;
}

export function resetCsrfToken(): void {
  csrfToken = null;
}

// Response interceptor
api.interceptors.response.use(
  (response) => {
    if (perfDebugEnabled) {
      const requestConfig = response.config as typeof response.config & { metadata?: RequestMetadata };
      const startTime = requestConfig.metadata?.startTime;
      if (startTime !== undefined) {
        logger.debug('api_request_complete', {
          component: 'api',
          action: response.config.method?.toUpperCase() ?? 'GET',
          url: response.config.url,
          status: response.status,
          durationMs: Math.round(performance.now() - startTime),
        });
      }
    }
    return response;
  },
  async (error: AxiosError<{ detail: unknown }>) => {
    if (perfDebugEnabled && error.config) {
      const requestConfig = error.config as typeof error.config & { metadata?: RequestMetadata };
      const startTime = requestConfig.metadata?.startTime;
      if (startTime !== undefined) {
        logger.debug('api_request_failed', {
          component: 'api',
          action: error.config.method?.toUpperCase() ?? 'GET',
          url: error.config.url,
          status: error.response?.status ?? 0,
          durationMs: Math.round(performance.now() - startTime),
        });
      }
    }
    if (axios.isCancel(error)) {
      return Promise.reject(error);
    }
    if (error.code === 'ERR_NETWORK' || !error.response) {
      return Promise.reject(new ApiError(0, 'Network error. Please check your connection.', true));
    }

    const status = error.response?.status || 0;
    const detail = error.response?.data?.detail;
    const detailText = formatApiDetail(detail);
    
    // 401 Unauthorized — редирект на логин
    if (status === 401 && typeof window !== 'undefined') {
      // Очищаем auth store
      const { useAuthStore } = await import('@/stores');
      useAuthStore.getState().logout();
      
      // Не редиректим если уже на странице авторизации
      const isAuthPage = window.location.pathname.startsWith('/auth');
      if (!isAuthPage) {
        // Сохраняем текущий URL для возврата после логина
        const returnUrl = window.location.pathname + window.location.search;
        window.location.href = `/auth/login?returnUrl=${encodeURIComponent(returnUrl)}`;
        // Возвращаем rejected promise чтобы прервать цепочку
        return Promise.reject(new ApiError(401, 'Session expired', false));
      }
    }
    
    // CSRF ошибка (400 или 403) — сбрасываем токен и повторяем запрос один раз
    if ((status === 400 || status === 403) && detailText.includes('CSRF')) {
      csrfToken = null;
      
      // Повторяем запрос только если это первая попытка
      const config = error.config;
      if (config && !config.headers['X-CSRF-Retry']) {
        config.headers['X-CSRF-Retry'] = 'true';
        // Получаем новый токен
        const newToken = await ensureCsrfTokenInternal();
        if (newToken) {
          config.headers['X-CSRF-Token'] = newToken;
          return api.request(config);
        }
      }
    }

    const message = detailText || error.message || 'Something went wrong';
    const isRetryable = status >= 500 || status === 0;
    return Promise.reject(new ApiError(status, message, isRetryable));
  }
);

// --- Public API (без авторизации) ---
export const publicApi = axios.create({
  baseURL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

publicApi.interceptors.request.use(async (config) => {
  if (!isValidRelativeUrl(config.url)) {
    return Promise.reject(new ApiError(400, 'Invalid URL: absolute URLs are not allowed'));
  }
  return config;
});

publicApi.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ detail: unknown }>) => {
    if (error.code === 'ERR_NETWORK' || !error.response) {
      return Promise.reject(new ApiError(0, 'Network error. Please check your connection.', true));
    }
    const status = error.response?.status || 0;
    const message = formatApiDetail(error.response?.data?.detail) || error.message || 'Something went wrong';
    const isRetryable = status >= 500 || status === 0;
    return Promise.reject(new ApiError(status, message, isRetryable));
  }
);

export default api;
