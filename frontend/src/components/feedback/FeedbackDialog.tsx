'use client';

import { useCallback, useState } from 'react';
import { MessageSquarePlus } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { FormContent } from './FormContent';
import { SubmitActions } from './SubmitActions';
import { useAttachments } from './hooks/useAttachments';
import { useFeedbackForm } from './hooks/useFeedbackForm';
import type { FeedbackFormValues } from './schema';
import type { FeedbackDialogProps } from './types';

export function FeedbackDialog({ trigger }: FeedbackDialogProps) {
  const [open, setOpen] = useState(false);

  const attachments = useAttachments();
  const {
    form,
    submitting,
    feedbackCreated,
    uploadResult,
    uploadFailed,
    uploadInProgress,
    handleSubmit,
    retryFailedUploads,
    handleInvalidSubmit,
    resetForm,
  } = useFeedbackForm({
    attachments,
  });

  const handleClose = useCallback(() => {
    setOpen(false);
    resetForm();
  }, [resetForm]);

  const onSubmit = useCallback(
    async (values: FeedbackFormValues) => {
      const result = await handleSubmit(values);
      // Only close if all uploads succeeded or no uploads at all
      if (result.feedbackCreated && result.failedUploads === 0) {
        setTimeout(() => handleClose(), 2000);
      }
    },
    [handleClose, handleSubmit],
  );

  const handleDialogChange = useCallback(
    (value: boolean) => {
      // Always allow closing dialog - user can cancel at any time
      setOpen(value);
      if (!value) {
        handleClose();
      }
    },
    [handleClose],
  );

  const isSubmitDisabled = submitting || feedbackCreated || !form.formState.isValid;

  const handleReset = useCallback(() => {
    handleClose();
  }, [handleClose]);

  return (
    <Dialog open={open} onOpenChange={handleDialogChange}>
      <DialogTrigger asChild>
        {trigger || (
          <Button variant="ghost" size="icon" title="Обратная связь">
            <MessageSquarePlus className="h-5 w-5" />
          </Button>
        )}
      </DialogTrigger>
      <DialogContent className="sm:max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Обратная связь</DialogTitle>
          <DialogDescription>Сообщите об ошибке или предложите улучшение</DialogDescription>
        </DialogHeader>

        <form onSubmit={form.handleSubmit(onSubmit, handleInvalidSubmit)} className="space-y-4">
          <FormContent
            form={form}
            files={attachments.files}
            hasLimit={attachments.hasLimit}
            addFiles={attachments.addFiles}
            removeFile={attachments.removeFile}
          />

          <SubmitActions
            submitting={submitting}
            feedbackCreated={feedbackCreated}
            isSubmitDisabled={isSubmitDisabled}
            uploadResult={uploadResult}
            uploadFailed={uploadFailed}
            uploadInProgress={uploadInProgress}
            onCancel={handleClose}
            onRetry={feedbackCreated && (uploadResult?.failed ?? 0) > 0 ? retryFailedUploads : undefined}
            onReset={handleReset}
          />
        </form>
      </DialogContent>
    </Dialog>
  );
}
