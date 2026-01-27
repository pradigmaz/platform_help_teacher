import { useCallback, useRef, useState } from 'react';
import { zodResolver } from '@hookform/resolvers/zod';
import { useForm } from 'react-hook-form';
import { toast } from 'sonner';
import api from '@/lib/api';
import { feedbackDefaults, feedbackSchema, type FeedbackFormValues } from '../schema';
import type { FeedbackSubmitResult, UploadResult } from '../types';

type UseFeedbackFormParams = {
  attachments: {
    uploadAll: (feedbackId: string) => Promise<UploadResult>;
    clearFiles: () => void;
  };
  onSuccess?: (result: FeedbackSubmitResult) => void;
  onError?: (message: string) => void;
};

export function useFeedbackForm({ attachments, onSuccess, onError }: UseFeedbackFormParams) {
  const [submitting, setSubmitting] = useState(false);
  const [feedbackCreated, setFeedbackCreated] = useState(false);
  const submittingRef = useRef(false);

  const form = useForm<FeedbackFormValues>({
    resolver: zodResolver(feedbackSchema),
    mode: 'onChange',
    defaultValues: feedbackDefaults,
  });

  const handleSubmit = useCallback(
    async (values: FeedbackFormValues): Promise<FeedbackSubmitResult> => {
      if (submittingRef.current) return { feedbackCreated, failedUploads: 0 };
      submittingRef.current = true;

      try {
        setSubmitting(true);
        const { data } = await api.post('/feedback', values);
        setFeedbackCreated(true);

        const uploadResult = await attachments.uploadAll(data.id);
        if (uploadResult.failed > 0) {
          toast.warning(`Отправлено, но ${uploadResult.failed} файл(ов) не загружено`);
        }

        const result: FeedbackSubmitResult = {
          feedbackCreated: true,
          failedUploads: uploadResult.failed,
        };
        onSuccess?.(result);
        return result;
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Не удалось отправить';
        toast.error(message);
        onError?.(message);
        return { feedbackCreated: false, failedUploads: 0 };
      } finally {
        setSubmitting(false);
        submittingRef.current = false;
      }
    },
    [attachments, feedbackCreated, onError, onSuccess],
  );

  const handleInvalidSubmit = useCallback(() => {
    toast.error('Проверьте поля формы');
  }, []);

  const resetForm = useCallback(() => {
    setFeedbackCreated(false);
    form.reset(feedbackDefaults);
    attachments.clearFiles();
  }, [attachments, form]);

  return {
    form,
    submitting,
    feedbackCreated,
    handleSubmit,
    handleInvalidSubmit,
    resetForm,
  };
}
