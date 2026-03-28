import { render, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const mocks = vi.hoisted(() => ({
  router: {
    push: vi.fn(),
  },
  toast: {
    success: vi.fn(),
    error: vi.fn(),
    info: vi.fn(),
  },
  primeAuthFingerprint: vi.fn(),
}));

vi.mock('next/navigation', () => ({
  useRouter: () => mocks.router,
}));

vi.mock('sonner', () => ({
  toast: mocks.toast,
}));

vi.mock('@/lib/api', () => ({
  AdminAPI: {
    exitImpersonation: vi.fn(),
  },
}));

vi.mock('@/lib/fingerprint/adapter', () => ({
  primeAuthFingerprint: mocks.primeAuthFingerprint,
}));

vi.mock('@/components/ui/button', () => ({
  Button: ({ children, ...props }: React.ButtonHTMLAttributes<HTMLButtonElement>) => (
    <button type="button" {...props}>
      {children}
    </button>
  ),
}));

import { ImpersonationBanner } from './ImpersonationBanner';

describe('ImpersonationBanner fingerprint prewarm', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    document.cookie = 'impersonating=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/';
  });

  afterEach(() => {
    document.cookie = 'impersonating=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/';
  });

  it('prewarms fingerprint when impersonation banner is active', async () => {
    document.cookie = 'impersonating=true; path=/';

    render(<ImpersonationBanner />);

    await waitFor(() => {
      expect(mocks.primeAuthFingerprint).toHaveBeenCalledTimes(1);
    });
  });

  it('does not prewarm fingerprint when impersonation is inactive', async () => {
    render(<ImpersonationBanner />);

    await waitFor(() => {
      expect(mocks.primeAuthFingerprint).not.toHaveBeenCalled();
    });
  });
});
