import type { ReactNode } from 'react';

export type FeedbackDialogProps = {
  trigger?: ReactNode;
};

export type PendingFile = {
  file: File;
  preview: string;
  attachmentId?: string; // Attachment ID from backend (used for retry)
};

export type UploadError = {
  filename: string;
  error: string;
};

export type UploadResult = {
  failed: number;
  total: number;
  errors?: UploadError[];
};

export type FeedbackSubmitResult = {
  feedbackCreated: boolean;
  failedUploads: number;
  uploadErrors?: UploadError[];
};

/**
 * Feedback Attachment Validation Rules
 *
 * File Limits:
 * - Maximum attachments per feedback: 5 files
 * - Maximum file size: 5MB per file
 *
 * Allowed File Types:
 * - MIME types: image/png, image/jpeg, image/gif, image/webp
 * - Extensions: .png, .jpg, .jpeg, .gif, .webp
 *
 * Validation Flow:
 * 1. Client-side validation (dropzone + custom checks)
 *    - File size check
 *    - MIME type check
 *    - Extension check
 * 2. Backend validation (api/v1/feedback endpoints)
 *    - Same checks + magic bytes verification
 *    - Storage path validation
 *
 * Error Handling:
 * - Dropzone provides detailed rejection reasons
 * - Backend returns specific error messages
 * - Upload failures can be retried
 *
 * Backend Notes:
 * - MINIO_ENDPOINT must be accessible from browser for presigned URLs
 * - Ensure CSP allows connections to MinIO endpoint
 * - Storage paths include '/' (e.g., feedback/{id}/{id}.ext)
 * - Attachments are marked as uploaded after successful PUT
 */
export const FEEDBACK_FILE_LIMIT = 5;
export const FEEDBACK_MAX_SIZE = 5 * 1024 * 1024; // 5MB
export const FEEDBACK_ALLOWED_TYPES = ['image/png', 'image/jpeg', 'image/gif', 'image/webp'];
export const FEEDBACK_ACCEPT = { 'image/*': ['.png', '.jpg', '.jpeg', '.gif', '.webp'] };

/**
 * Feedback Form Validation Rules
 *
 * Title:
 * - Minimum length: 5 characters
 * - Maximum length: 200 characters
 * - Required field
 *
 * Description:
 * - Minimum length: 20 characters
 * - Maximum length: 10,000 characters
 * - Required field
 *
 * Type:
 * - Must be either 'bug' or 'suggestion'
 * - Required field
 */
export const FEEDBACK_VALIDATION = {
  title: {
    minLength: 5,
    maxLength: 200,
  },
  description: {
    minLength: 20,
    maxLength: 10000,
  },
} as const;
