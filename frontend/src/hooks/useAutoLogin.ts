'use client';

import { useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { toast } from 'sonner';
import { AuthAPI, ApiError } from '@/lib/api';
import { ZodError } from 'zod';
import { AxiosError } from 'axios';
import { useAuthStore } from '@/stores';

interface UseAutoLoginOptions {
  /** Redirect path after successful login (overrides role-based redirect) */
  redirectTo?: string;
  /** Callback when login succeeds */
  onSuccess?: (user: { full_name: string; role: string }) => void;
  /** Callback when login fails */
  onError?: (error: string) => void;
}

interface UseAutoLoginResult {
  /** Current OTP value */
  otp: string;
  /** Set OTP value */
  setOtp: (value: string) => void;
  /** Whether to remember device (persistent session) */
  rememberDevice: boolean;
  /** Set remember device */
  setRememberDevice: (value: boolean) => void;
  /** Whether login is in progress */
  loading: boolean;
  /** Whether initial auth check is in progress */
  checkingAuth: boolean;
  /** Trigger login manually */
  login: (code?: string, rememberDeviceOverride?: boolean, forceSessionCookieOverride?: boolean) => Promise<void>;
  /** Trigger development-only test login */
  devLogin: () => Promise<void>;
  /** Whether dev login shortcut should be shown */
  canUseDevLogin: boolean;
}

/**
 * Hook for handling OTP-based authentication.
 * Supports auto-login from URL fragment (#code=123456).
 */
export function useAutoLogin(options: UseAutoLoginOptions = {}): UseAutoLoginResult {
  const { redirectTo, onSuccess, onError } = options;
  const [otp, setOtp] = useState('');
  const [rememberDevice, setRememberDevice] = useState(false);
  const [loading, setLoading] = useState(false);
  const [checkingAuth, setCheckingAuth] = useState(true);
  const router = useRouter();
  const loginAttemptedRef = useRef(false);
  const canUseDevLogin = process.env.NODE_ENV === 'development';

  // Check if already authenticated
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const user = await AuthAPI.me();
        if (user.role === 'admin' || user.role === 'teacher') {
          router.replace('/admin');
          return;
        } else if (user.role === 'student') {
          router.replace('/dashboard');
          return;
        }
      } catch {
        // Not logged in - show form
      }
      setCheckingAuth(false);
    };
    checkAuth();
  }, [router]);

  // Auto-login from URL fragment (#code=123456)
  useEffect(() => {
    if (checkingAuth || loginAttemptedRef.current) return;
    
    // Check fragment first (more secure), then query params (legacy)
    const hash = typeof window !== 'undefined' ? window.location.hash : '';
    const hashMatch = hash.match(/code=(\d{6})/);
    const codeFromFragment = hashMatch ? hashMatch[1] : null;
    
    // Fallback to query params for backwards compatibility
    const params = typeof window !== 'undefined' ? new URLSearchParams(window.location.search) : null;
    const queryCode = params?.get('code');
    const codeFromQuery = queryCode && /^\d{6}$/.test(queryCode) ? queryCode : null;
    
    const code = codeFromFragment || codeFromQuery;
    
    if (code && code.length === 6) {
      const autoLoginRememberDevice = false;
      setOtp(code);
      setRememberDevice(autoLoginRememberDevice);
      loginAttemptedRef.current = true;
      console.log('[Hook:useAutoLogin] Auto-login detected, forcing session-only cookies');
      // Clear fragment/query from URL for security
      if (typeof window !== 'undefined') {
        const nextParams = new URLSearchParams(window.location.search);
        nextParams.delete('code');
        const nextSearch = nextParams.toString();
        const nextUrl = nextSearch ? `${window.location.pathname}?${nextSearch}` : window.location.pathname;
        window.history.replaceState({}, '', nextUrl);
      }
      const timer = setTimeout(() => login(code, autoLoginRememberDevice, true), 100);
      return () => clearTimeout(timer);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [checkingAuth]);

  const handleSuccessfulLogin = async (data: Awaited<ReturnType<typeof AuthAPI.login>>) => {
    console.log('[Hook:useAutoLogin] Login successful, updating store', { user: data.user });
    useAuthStore.getState().setUser(data.user);

    const params = typeof window !== 'undefined' ? new URLSearchParams(window.location.search) : null;
    const returnUrl = params?.get('returnUrl');

    let targetPath = '/';
    if (redirectTo) {
      targetPath = redirectTo;
    } else if (returnUrl && returnUrl.startsWith('/') && !returnUrl.startsWith('//')) {
      targetPath = returnUrl;
    } else if (data.user?.role === 'admin' || data.user?.role === 'teacher') {
      targetPath = '/admin';
    } else if (data.user?.role === 'student') {
      targetPath = '/dashboard';
    }

    toast.success('Вход выполнен успешно');
    onSuccess?.(data.user);

    router.push(targetPath);
    router.refresh();
  };

  const login = async (code?: string, rememberDeviceOverride?: boolean, forceSessionCookieOverride?: boolean) => {
    const otpCode = code || otp;
    const effectiveRememberDevice = rememberDeviceOverride ?? rememberDevice;
    const effectiveForceSessionCookie = forceSessionCookieOverride ?? false;
    if (otpCode.length !== 6) return;

    setLoading(true);

    try {
      const data = await AuthAPI.login(otpCode, effectiveRememberDevice, effectiveForceSessionCookie);
      await handleSuccessfulLogin(data);
    } catch (err: unknown) {
      let message = 'Ошибка входа';

      if (err instanceof ApiError) {
        message = err.message;
      } else if (err instanceof ZodError) {
        message = 'Ошибка валидации данных';
      } else if (err instanceof AxiosError) {
        message = err.response?.data?.detail || err.message;
      } else if (err instanceof Error) {
        message = err.message;
      }

      if (message === 'Invalid or expired code') {
        message = 'Код неверный или устарел. Запросите новый код у бота!';
        toast.error(message, {
          duration: 8000,
          description: 'Код действует 5 минут. Получите новый командой /code в Telegram боте.',
        });
      } else {
        toast.error(message);
      }
      
      onError?.(message);
      setLoading(false);
    }
  };

  const devLogin = async () => {
    if (!canUseDevLogin) return;

    setLoading(true);

    try {
      const data = await AuthAPI.devLogin(true);
      await handleSuccessfulLogin(data);
    } catch (err: unknown) {
      let message = 'Ошибка dev-входа';

      if (err instanceof ApiError) {
        message = err.message;
      } else if (err instanceof ZodError) {
        message = 'Ошибка валидации данных';
      } else if (err instanceof AxiosError) {
        message = err.response?.data?.detail || err.message;
      } else if (err instanceof Error) {
        message = err.message;
      }

      toast.error(message);
      onError?.(message);
      setLoading(false);
    }
  };

  return {
    otp,
    setOtp: (value: string) => setOtp(value.replace(/\D/g, '')),
    rememberDevice,
    setRememberDevice,
    loading,
    checkingAuth,
    login,
    devLogin,
    canUseDevLogin,
  };
}
