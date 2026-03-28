/**
 * Exploration test — Bug Condition: CanceledError treated as submission error
 *
 * Bug Condition:
 *   input.postRequestInFlight = true
 *   AND input.abortControllerAbortCalled = true
 *   AND input.axiosThrows = 'CanceledError'
 *
 * Expected (after fix): toast.error NOT called, toastType ∈ {'info', 'none'}
 * Actual (before fix):  toast.error IS called — bug confirmed
 *
 * Validates: Requirements 1.1, 1.2, 1.3, 2.1, 2.2, 2.3
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import axios, { CanceledError } from 'axios';

// --- Mocks ---

vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
    info: vi.fn(),
    warning: vi.fn(),
  },
}));

vi.mock('@/lib/api', () => ({
  default: {
    post: vi.fn(),
  },
}));

// Mock zodResolver
vi.mock('@hookform/resolvers/zod', () => ({
  zodResolver: () => async (values: unknown) => ({ values, errors: {} }),
}));

import { toast } from 'sonner';
import api from '@/lib/api';
import { useFeedbackForm } from '../useFeedbackForm';

// --- Helpers ---

function makeAttachments() {
  return {
    uploadAll: vi.fn().mockResolvedValue({ failed: 0, total: 0 }),
    retryUpload: vi.fn().mockResolvedValue({ failed: 0, total: 0 }),
    clearFiles: vi.fn(),
    getFailedFiles: vi.fn().mockReturnValue([]),
    uploadInProgress: false,
  };
}

const validFormValues = {
  title: 'Test feedback',
  description: 'Test description',
  category: 'bug',
};

// --- Tests ---

describe('Bug Condition: CanceledError treated as submission error', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  /**
   * Test Case 1: handleSubmit → abort() before server response
   *
   * Scenario: User submits form, then closes dialog (abort() called) before server responds.
   * api.post throws CanceledError (as axios does when AbortController.abort() is called).
   *
   * Expected (after fix): toast.error NOT called
   * Actual (before fix):  toast.error IS called with 'Не удалось отправить фидбэк'
   */
  it('TC1: abort() before server response — toast.error should NOT be called', async () => {
    // Arrange: api.post throws CanceledError (simulates abort())
    const canceledError = new CanceledError('Request aborted');
    (api.post as ReturnType<typeof vi.fn>).mockRejectedValue(canceledError);

    const attachments = makeAttachments();
    const { result } = renderHook(() =>
      useFeedbackForm({ attachments })
    );

    // Act: submit form (api.post will throw CanceledError)
    await act(async () => {
      await result.current.handleSubmit(validFormValues as never);
    });

    // Assert: toast.error should NOT be called (bug: it IS called)
    expect(toast.error).not.toHaveBeenCalled();
  });

  /**
   * Test Case 2: handleSubmit → resetForm() before server response
   *
   * Scenario: User submits form, then closes dialog (resetForm called).
   * resetForm calls abort(), api.post throws CanceledError.
   *
   * Expected (after fix): toast.error NOT called
   * Actual (before fix):  toast.error IS called
   */
  it('TC2: resetForm() while POST in-flight — toast.error should NOT be called', async () => {
    // Arrange: api.post is a promise that we control
    let rejectPost!: (err: unknown) => void;
    const postPromise = new Promise<never>((_, reject) => {
      rejectPost = reject;
    });
    (api.post as ReturnType<typeof vi.fn>).mockReturnValue(postPromise);

    const attachments = makeAttachments();
    const { result } = renderHook(() =>
      useFeedbackForm({ attachments })
    );

    // Start submit (don't await — it's in-flight)
    let submitPromise: Promise<unknown>;
    act(() => {
      submitPromise = result.current.handleSubmit(validFormValues as never);
    });

    // Simulate abort via resetForm (closes dialog)
    act(() => {
      result.current.resetForm();
    });

    // Now reject the post with CanceledError (as abort() would cause)
    const canceledError = new CanceledError('Request aborted');
    act(() => {
      rejectPost(canceledError);
    });

    // Wait for submit to complete
    await act(async () => {
      await submitPromise!;
    });

    // Assert: toast.error should NOT be called (bug: it IS called)
    expect(toast.error).not.toHaveBeenCalled();
  });

  /**
   * Test Case 3: Response interceptor wraps CanceledError in ApiError
   *
   * Scenario: Verify that the response interceptor in client.ts wraps CanceledError
   * into ApiError, losing cancellation information.
   *
   * This is the root cause: interceptor sees !error.response → wraps in ApiError(0, 'Network error...')
   * Then in catch block: error.name === 'ApiError', not 'AbortError' → toast.error shown
   *
   * Expected (after fix): CanceledError passes through interceptor unchanged
   * Actual (before fix):  CanceledError is wrapped in ApiError — error.name !== 'AbortError'
   */
  it('TC3: response interceptor should NOT wrap CanceledError in ApiError', async () => {
    // Import the actual api client to test the interceptor
    const { api: realApi } = await import('@/lib/api/client');

    // Create a CanceledError as axios would
    const canceledError = new CanceledError('canceled');

    // Simulate what the interceptor does with a CanceledError
    // The interceptor checks: if (error.code === 'ERR_NETWORK' || !error.response)
    // CanceledError has: error.code = 'ERR_CANCELED', error.response = undefined
    // So !error.response is TRUE → interceptor wraps it in ApiError

    // We verify by checking the error that comes out of the interceptor
    // by mocking the underlying adapter to throw CanceledError
    const mockAdapter = vi.fn().mockRejectedValue(canceledError);
    const originalAdapter = realApi.defaults.adapter;
    realApi.defaults.adapter = mockAdapter;

    let caughtError: unknown;
    try {
      await realApi.get('/test-cancel-interceptor');
    } catch (err) {
      caughtError = err;
    } finally {
      realApi.defaults.adapter = originalAdapter;
    }

    // After fix: caughtError should be CanceledError (axios.isCancel returns true)
    // Before fix: caughtError is ApiError(0, 'Network error...') — cancellation info lost
    expect(axios.isCancel(caughtError)).toBe(true);
  });
});
