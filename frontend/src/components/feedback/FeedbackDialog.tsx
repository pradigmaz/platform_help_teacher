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
  const { form, submitting, feedbackCreated, handleSubmit, handleInvalidSubmit, resetForm } = useFeedbackForm({
    attachments,
  });

  const handleClose = useCallback(() => {
    setOpen(false);
    resetForm();
  }, [resetForm]);

  const onSubmit = useCallback(
    async (values: FeedbackFormValues) => {
      const result = await handleSubmit(values);
      if (result.feedbackCreated) {
        setTimeout(() => handleClose(), 1500);
      }
    },
    [handleClose, handleSubmit],
  );

  const handleDialogChange = useCallback(
    (value: boolean) => {
      if (feedbackCreated) return;
      setOpen(value);
      if (!value) {
        handleClose();
      }
    },
    [feedbackCreated, handleClose],
  );

  const isSubmitDisabled = submitting || feedbackCreated || !form.formState.isValid;

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
            onCancel={handleClose}
          />
        </form>
      </DialogContent>
    </Dialog>
  );
}
