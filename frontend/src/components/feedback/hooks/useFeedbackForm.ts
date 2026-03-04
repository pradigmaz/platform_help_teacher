import { useCallback, useEffect, useRef, useState } from 'react';
import { zodResolver } from '@hookform/resolvers/zod';
import { useForm } from 'react-hook-form';
import { toast } from 'sonner';
import axios from 'axios';
import api from '@/lib/api';
import { feedbackDefaults, feedbackSchema, type FeedbackFormValues } from '../schema';
import type { FeedbackSubmitResult, UploadResult } from '../types';

type UseFeedbackFormParams = {
  attachments: {
    uploadAll: (feedbackId: string) => Promise<UploadResult>;
    retryUpload: (feedbackId: string, failedFiles: File[]) => Promise<UploadResult>;
    clearFiles: () => void;
    getFailedFiles?: () => File[];
    uploadInProgress?: boolean;
  };
  onSuccess?: (result: FeedbackSubmitResult) => void;
  onError?: (message: string) => void;
};

export function useFeedbackForm({ attachments, onSuccess, onError }: UseFeedbackFormParams) {
  const [submitting, setSubmitting] = useState(false);
  const [feedbackCreated, setFeedbackCreated] = useState(false);
  const [feedbackId, setFeedbackId] = useState<string | null>(null);
  const [uploadResult, setUploadResult] = useState<UploadResult | null>(null);
  const [uploadFailed, setUploadFailed] = useState(false);
  const submittingRef = useRef(false);
  const abortControllerRef = useRef<AbortController | null>(null);
  const mountedRef = useRef(true);

  const form = useForm<FeedbackFormValues>({
    resolver: zodResolver(feedbackSchema),
    mode: 'onChange',
    defaultValues: feedbackDefaults,
  });

  const handleSubmit = useCallback(
    async (values: FeedbackFormValues): Promise<FeedbackSubmitResult> => {
      if (submittingRef.current) return { feedbackCreated, failedUploads: 0 };
      submittingRef.current = true;
      abortControllerRef.current = new AbortController();

      try {
        setSubmitting(true);
        setUploadFailed(false);

        // Step 1: Create feedback record
        const { data } = await api.post('/feedback', values, {
          signal: abortControllerRef.current.signal,
        });
        setFeedbackCreated(true);
        setFeedbackId(data.id);

        // Step 2: Upload attachments
        let result: UploadResult | null = null;
        if (attachments.getFailedFiles && attachments.getFailedFiles().length > 0) {
          result = await attachments.uploadAll(data.id);
          setUploadResult(result);

          // Set uploadFailed flag if any uploads failed
          if (result.failed > 0) {
            setUploadFailed(true);
          }

          // Show detailed success/error toast
          if (result.failed === 0) {
            if (!mountedRef.current) {
              return { feedbackCreated: true, failedUploads: 0 };
            }
            toast.success('Фидбэк успешно отправлен', {
              description: result.total > 0
                ? `Загружено ${result.total} вложений`
                : 'Без вложений',
              duration: 5000,
            });
          } else {
            // Some files failed - show warning with details
            const failedFileNames = result.errors?.map(e => e.filename).join(', ');
            toast.warning('Фидбэк отправлен, но есть проблемы с вложениями', {
              description: `Не удалось загрузить ${result.failed} из ${result.total} файлов: ${failedFileNames}`,
              duration: 7000,
            });
          }
        } else {
          // No attachments
          result = { failed: 0, total: 0 };
          toast.success('Фидбэк успешно отправлен', {
            description: 'ID: ' + data.id,
            duration: 5000,
          });
        }

        const feedbackResult: FeedbackSubmitResult = {
          feedbackCreated: true,
          failedUploads: result.failed || 0,
          uploadErrors: result.errors,
        };
        onSuccess?.(feedbackResult);
        return feedbackResult;
      } catch (error) {
        if (axios.isCancel(error)) {
          toast.info('Отправка отменена');
          return { feedbackCreated, failedUploads: 0 };
        }
        const message = error instanceof Error ? error.message : 'Не удалось отправить';
        toast.error('Не удалось отправить фидбэк', {
          description: message,
          duration: 5000,
        });
        onError?.(message);
        return { feedbackCreated: false, failedUploads: 0 };
      } finally {
        setSubmitting(false);
        submittingRef.current = false;
        abortControllerRef.current = null;
      }
    },
    [attachments, feedbackCreated, onError, onSuccess],
  );

  const retryFailedUploads = useCallback(
    async (): Promise<boolean> => {
      if (!feedbackId || !uploadResult || uploadResult.failed === 0) {
        toast.error('Нет неудачных загрузок для повтора');
        return false;
      }

      try {
        setSubmitting(true);

        // Get failed files from attachments
        const failedFiles = attachments.getFailedFiles?.();
        if (!failedFiles || failedFiles.length === 0) {
          toast.warning('Не удалось найти файлы для повтора');
          return false;
        }

        const result = await attachments.retryUpload(feedbackId, failedFiles);
        setUploadResult(result);

        if (result.failed === 0) {
          toast.success('Повторная загрузка успешна', {
            description: `Загружено ${result.total} файлов`,
          });
          return true;
        } else {
          toast.warning('Повторная загрузка частично успешна', {
            description: `Успешно: ${result.total - result.failed}/${result.total}`,
          });
          return false;
        }
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Не удалось повторить';
        toast.error('Не удалось повторить загрузку', {
          description: message,
        });
        return false;
      } finally {
        setSubmitting(false);
      }
    },
    [feedbackId, uploadResult, attachments],
  );

  const handleInvalidSubmit = useCallback(() => {
    // Get all error messages
    const { errors } = form.formState;
    const errorFields = Object.keys(errors);

    if (errorFields.length === 0) {
      toast.error('Проверьте поля формы');
      return;
    }

    // Build detailed error message
    const errorMessages: string[] = [];
    errorFields.forEach(field => {
      const error = errors[field as keyof typeof errors];
      if (error?.message) {
        errorMessages.push(`${field}: ${error.message}`);
      }
    });

    toast.error('Исправьте ошибки в форме', {
      description: errorMessages.join('\n'),
      duration: 6000,
    });
  }, [form.formState]);

  const resetForm = useCallback(() => {
    // Cancel any ongoing requests only if not submitting
    if (!submittingRef.current) {
      abortControllerRef.current?.abort();
    }
    
    setFeedbackCreated(false);
    setFeedbackId(null);
    setUploadResult(null);
    setUploadFailed(false);
    form.reset(feedbackDefaults);
    attachments.clearFiles();
  }, [attachments, form]);

  // Cleanup on unmount
  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
      if (!submittingRef.current) {
        abortControllerRef.current?.abort();
      }
    };
  }, []);

  return {
    form,
    submitting,
    feedbackCreated,
    feedbackId,
    uploadResult,
    uploadFailed,
    uploadInProgress: attachments.uploadInProgress || false,
    handleSubmit,
    retryFailedUploads,
    handleInvalidSubmit,
    resetForm,
  };
}
