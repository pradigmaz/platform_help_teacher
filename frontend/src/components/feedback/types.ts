import type { ReactNode } from 'react';

export type FeedbackDialogProps = {
  trigger?: ReactNode;
};

export type PendingFile = {
  file: File;
  preview: string;
};

export const FEEDBACK_FILE_LIMIT = 5;
export const FEEDBACK_MAX_SIZE = 5 * 1024 * 1024; // 5MB
export const FEEDBACK_ALLOWED_TYPES = ['image/png', 'image/jpeg', 'image/gif', 'image/webp'];
export const FEEDBACK_ACCEPT = { 'image/*': ['.png', '.jpg', '.jpeg', '.gif', '.webp'] };

export type UploadResult = {
  failed: number;
  total: number;
};

export type FeedbackSubmitResult = {
  feedbackCreated: boolean;
  failedUploads: number;
};
