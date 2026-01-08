import axios, { AxiosError } from 'axios';
import axiosRetry from 'axios-retry';
import { getFingerprint } from '../fingerprint';

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

// --- Axios Configuration ---
const baseURL = process.env.NEXT_PUBLIC_API_URL || '/api/v1';

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
});

// Защита от SSRF
api.interceptors.request.use((config) => {
  if (!isValidRelativeUrl(config.url)) {
    return Promise.reject(new ApiError(400, 'Invalid URL: absolute URLs are not allowed'));
  }
  // Добавляем fingerprint в каждый запрос
  if (typeof window !== 'undefined') {
    config.headers['X-Device-Fingerprint'] = getFingerprint();
  }
  return config;
});

axiosRetry(api, {
  retries: 3,
  retryDelay: axiosRetry.exponentialDelay,
  retryCondition: (error) => {
    return (
      axiosRetry.isNetworkOrIdempotentRequestError(error) ||
      error.code === 'ERR_NETWORK' ||
      (error.response?.status ? error.response.status >= 500 : false)
    );
  },
});

// --- CSRF Token Management ---
let csrfToken: string | null = null;

export async function ensureCsrfToken(): Promise<string> {
  if (!csrfToken) {
    const { data } = await api.get<{ csrf_token: string }>('/auth/csrf-token');
    csrfToken = data.csrf_token;
  }
  return csrfToken;
}

export function resetCsrfToken(): void {
  csrfToken = null;
}

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<{ detail: string }>) => {
    if (error.code === 'ERR_NETWORK' || !error.response) {
      return Promise.reject(new ApiError(0, 'Network error. Please check your connection.', true));
    }

    if (error.response?.status === 403 && error.response?.data?.detail?.includes('CSRF')) {
      csrfToken = null;
    }

    const status = error.response?.status || 0;
    const message = error.response?.data?.detail || error.message || 'Something went wrong';
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

publicApi.interceptors.request.use((config) => {
  if (!isValidRelativeUrl(config.url)) {
    return Promise.reject(new ApiError(400, 'Invalid URL: absolute URLs are not allowed'));
  }
  // Добавляем fingerprint в каждый запрос
  if (typeof window !== 'undefined') {
    config.headers['X-Device-Fingerprint'] = getFingerprint();
  }
  return config;
});

publicApi.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ detail: string }>) => {
    if (error.code === 'ERR_NETWORK' || !error.response) {
      return Promise.reject(new ApiError(0, 'Network error. Please check your connection.', true));
    }
    const status = error.response?.status || 0;
    const message = error.response?.data?.detail || error.message || 'Something went wrong';
    const isRetryable = status >= 500 || status === 0;
    return Promise.reject(new ApiError(status, message, isRetryable));
  }
);

export default api;
