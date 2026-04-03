/**
 * Preservation tests — Property 2: Non-cancelled requests behave identically
 *
 * These tests verify baseline behaviour for all scenarios where the POST request
 * is NOT cancelled via abort(). They MUST PASS on unfixed code.
 *
 * Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';

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

vi.mock('@hookform/resolvers/zod', () => ({
  zodResolver: () => async (values: unknown) => ({ values, errors: {} }),
}));

import { toast } from 'sonner';
import api from '@/lib/api';
import { ApiError } from '@/lib/api/client';
import { useFeedbackForm } from '../useFeedbackForm';
import { makeAttachments, validFormValues } from './useFeedbackForm.test-helpers';

// --- Tests ---

describe('Preservation: non-cancelled requests behave as before', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  /**
   * TC1: Successful submission without attachments
   * → toast.success('Фидбэк успешно отправлен') + feedbackCreated: true
   */
  it('TC1: successful submit without attachments → toast.success + feedbackCreated', async () => {
    (api.post as ReturnType<typeof vi.fn>).mockResolvedValue({ data: { id: 'fb-001' } });

    const attachments = makeAttachments();
    const { result } = renderHook(() => useFeedbackForm({ attachments }));

    let submitResult: Awaited<ReturnType<typeof result.current.handleSubmit>>;
    await act(async () => {
      submitResult = await result.current.handleSubmit(validFormValues as never);
    });

    expect(toast.success).toHaveBeenCalledWith(
      'Фидбэк успешно отправлен',
      expect.objectContaining({ duration: 5000 }),
    );
    expect(toast.error).not.toHaveBeenCalled();
    expect(submitResult!.feedbackCreated).toBe(true);
    expect(submitResult!.failedUploads).toBe(0);
  });

  /**
   * TC2: Successful submission with attachments (all uploaded OK)
   * → toast.success with attachment description
   */
  it('TC2: successful submit with attachments (all ok) → toast.success', async () => {
    (api.post as ReturnType<typeof vi.fn>).mockResolvedValue({ data: { id: 'fb-002' } });

    const mockFile = new File(['content'], 'screenshot.png', { type: 'image/png' });
    const attachments = makeAttachments({
      getFailedFiles: vi.fn().mockReturnValue([mockFile]),
      uploadAll: vi.fn().mockResolvedValue({ failed: 0, total: 1, errors: [] }),
    });

    const { result } = renderHook(() => useFeedbackForm({ attachments }));

    let submitResult: Awaited<ReturnType<typeof result.current.handleSubmit>>;
    await act(async () => {
      submitResult = await result.current.handleSubmit(validFormValues as never);
    });

    expect(toast.success).toHaveBeenCalledWith(
      'Фидбэк успешно отправлен',
      expect.objectContaining({ description: expect.stringContaining('1') }),
    );
    expect(toast.error).not.toHaveBeenCalled();
    expect(submitResult!.feedbackCreated).toBe(true);
  });

  it.each([
    ['TC3', new ApiError(500, 'Internal Server Error')],
    ['TC4', new ApiError(429, 'Too many requests. Please try again later.')],
  ])('%s: failed submit keeps toast.error behavior', async (_caseId, error) => {
    (api.post as ReturnType<typeof vi.fn>).mockRejectedValue(error);

    const attachments = makeAttachments();
    const { result } = renderHook(() => useFeedbackForm({ attachments }));

    let submitResult: Awaited<ReturnType<typeof result.current.handleSubmit>>;
    await act(async () => {
      submitResult = await result.current.handleSubmit(validFormValues as never);
    });

    expect(toast.error).toHaveBeenCalledWith(
      'Не удалось отправить фидбэк',
      expect.objectContaining({ description: error.message }),
    );
    expect(toast.success).not.toHaveBeenCalled();
    expect(submitResult!.feedbackCreated).toBe(false);
  });

  /**
   * TC5: Partial attachment upload failure → toast.warning with details
   */
  it('TC5: partial attachment upload failure → toast.warning with details', async () => {
    (api.post as ReturnType<typeof vi.fn>).mockResolvedValue({ data: { id: 'fb-005' } });

    const mockFile1 = new File(['a'], 'ok.png', { type: 'image/png' });
    const mockFile2 = new File(['b'], 'fail.png', { type: 'image/png' });

    const attachments = makeAttachments({
      getFailedFiles: vi.fn().mockReturnValue([mockFile1, mockFile2]),
      uploadAll: vi.fn().mockResolvedValue({
        failed: 1,
        total: 2,
        errors: [{ filename: 'fail.png', error: 'Upload failed' }],
      }),
    });

    const { result } = renderHook(() => useFeedbackForm({ attachments }));

    let submitResult: Awaited<ReturnType<typeof result.current.handleSubmit>>;
    await act(async () => {
      submitResult = await result.current.handleSubmit(validFormValues as never);
    });

    expect(toast.warning).toHaveBeenCalledWith(
      'Фидбэк отправлен, но есть проблемы с вложениями',
      expect.objectContaining({
        description: expect.stringContaining('fail.png'),
      }),
    );
    expect(toast.error).not.toHaveBeenCalled();
    expect(submitResult!.feedbackCreated).toBe(true);
    expect(submitResult!.failedUploads).toBe(1);
  });

  /**
   * TC6: resetForm() without POST in-flight → clean reset, no toast
   */
  it('TC6: resetForm() without active POST → clean reset, no toast', async () => {
    const attachments = makeAttachments();
    const { result } = renderHook(() => useFeedbackForm({ attachments }));

    act(() => {
      result.current.resetForm();
    });

    // No toast should be shown
    expect(toast.success).not.toHaveBeenCalled();
    expect(toast.error).not.toHaveBeenCalled();
    expect(toast.info).not.toHaveBeenCalled();
    expect(toast.warning).not.toHaveBeenCalled();

    // clearFiles should be called
    expect(attachments.clearFiles).toHaveBeenCalled();

    // feedbackCreated should be reset
    expect(result.current.feedbackCreated).toBe(false);
  });
});
