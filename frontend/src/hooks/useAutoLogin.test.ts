import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, renderHook, waitFor } from '@testing-library/react';

const mocks = vi.hoisted(() => ({
  authApi: {
    login: vi.fn(),
    devLogin: vi.fn(),
    status: vi.fn(),
  },
  router: {
    push: vi.fn(),
    replace: vi.fn(),
    refresh: vi.fn(),
  },
  setUser: vi.fn(),
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
  primeAuthFingerprint: vi.fn(),
}));

vi.mock('next/navigation', () => ({
  useRouter: () => mocks.router,
}));

vi.mock('sonner', () => ({
  toast: mocks.toast,
}));

vi.mock('@/stores', () => ({
  useAuthStore: {
    getState: () => ({
      setUser: mocks.setUser,
    }),
  },
}));

vi.mock('@/lib/api', () => ({
  AuthAPI: mocks.authApi,
  ApiError: class ApiError extends Error {},
}));

vi.mock('@/lib/fingerprint/adapter', () => ({
  primeAuthFingerprint: mocks.primeAuthFingerprint,
}));

import { useAutoLogin } from './useAutoLogin';

describe('useAutoLogin', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.primeAuthFingerprint.mockResolvedValue(undefined);
    mocks.authApi.status.mockResolvedValue({ authenticated: false, user: null });
    mocks.authApi.login.mockResolvedValue({
      user: {
        full_name: 'Test User',
        role: 'student',
      },
    });
    window.history.replaceState({}, '', '/auth/login#code=123456');
  });

  afterEach(() => {
    vi.unstubAllEnvs();
    window.history.replaceState({}, '', '/');
  });

  it('uses remember_device=false for auto-login codes and preserves returnUrl', async () => {
    window.history.replaceState({}, '', '/auth/login?returnUrl=%2Freports#code=123456');

    const { result } = renderHook(() => useAutoLogin());

    await waitFor(() => expect(result.current.checkingAuth).toBe(false));
    expect(result.current.rememberDevice).toBe(false);

    await waitFor(() => {
      expect(mocks.authApi.login).toHaveBeenCalledWith('123456', false, true);
    });

    expect(mocks.authApi.login).toHaveBeenCalledTimes(1);
    expect(result.current.rememberDevice).toBe(false);
    expect(mocks.router.push).toHaveBeenCalledWith('/reports');
    expect(window.location.search).toBe('?returnUrl=%2Freports');
  });

  it('redirects already authenticated users via AuthAPI.status', async () => {
    mocks.authApi.status.mockResolvedValue({
      authenticated: true,
      user: {
        full_name: 'Admin User',
        role: 'admin',
      },
    });

    renderHook(() => useAutoLogin());

    await waitFor(() => {
      expect(mocks.authApi.status).toHaveBeenCalledTimes(1);
      expect(mocks.setUser).toHaveBeenCalledWith({
        full_name: 'Admin User',
        role: 'admin',
      });
      expect(mocks.router.replace).toHaveBeenCalledWith('/admin');
    });

    expect(mocks.authApi.login).not.toHaveBeenCalled();
  });

  it('prewarms auth fingerprint on mount without blocking auth check', async () => {
    const { result } = renderHook(() => useAutoLogin());

    await waitFor(() => expect(result.current.checkingAuth).toBe(false));

    expect(mocks.primeAuthFingerprint).toHaveBeenCalledTimes(1);
    expect(mocks.authApi.status).toHaveBeenCalledTimes(1);
  });

  it('does not wait for fingerprint prewarm before auto-login submit', async () => {
    mocks.primeAuthFingerprint.mockReturnValue(new Promise(() => {}));

    const { result } = renderHook(() => useAutoLogin());

    await waitFor(() => expect(result.current.checkingAuth).toBe(false));
    await waitFor(() => {
      expect(mocks.authApi.login).toHaveBeenCalledWith('123456', false, true);
    });

    expect(mocks.primeAuthFingerprint).toHaveBeenCalledTimes(1);
  });

  it('ignores non-numeric legacy query codes', async () => {
    window.history.replaceState({}, '', '/auth/login?code=ABC123');

    const { result } = renderHook(() => useAutoLogin());

    await waitFor(() => expect(result.current.checkingAuth).toBe(false));

    expect(mocks.authApi.login).not.toHaveBeenCalled();
    expect(mocks.router.push).not.toHaveBeenCalled();
  });

  it('enables dev login in development and redirects admins', async () => {
    vi.stubEnv('NODE_ENV', 'development');
    mocks.authApi.devLogin.mockResolvedValue({
      user: {
        full_name: 'Dev Admin',
        role: 'admin',
      },
    });

    const { result } = renderHook(() => useAutoLogin());

    await waitFor(() => expect(result.current.checkingAuth).toBe(false));
    expect(result.current.canUseDevLogin).toBe(true);

    await act(async () => {
      await result.current.devLogin();
    });

    expect(mocks.authApi.devLogin).toHaveBeenCalledWith(true);
    expect(mocks.setUser).toHaveBeenCalledWith({
      full_name: 'Dev Admin',
      role: 'admin',
    });
    expect(mocks.router.push).toHaveBeenCalledWith('/admin');
  });
});
