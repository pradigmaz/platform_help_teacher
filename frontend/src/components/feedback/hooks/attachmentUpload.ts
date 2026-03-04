import { type FileRejection } from 'react-dropzone';
import axios from 'axios';
import api from '@/lib/api';
import { FEEDBACK_ALLOWED_TYPES, FEEDBACK_MAX_SIZE } from '../types';

type UploadOrRetryParams = {
  feedbackId: string;
  file: File;
  abortSignal?: AbortSignal;
  existingAttachmentId?: string;
};

export type UploadAttemptResult = {
  success: boolean;
  error?: string;
  attachmentId?: string;
};

export function getRejectionReason(rejection: FileRejection): string {
  const { errors } = rejection;

  if (errors?.[0]?.code === 'file-too-large') {
    return `превышает лимит ${FEEDBACK_MAX_SIZE / 1024 / 1024}MB`;
  }

  if (errors?.[0]?.code === 'file-invalid-type') {
    return 'неподдерживаемый тип файла';
  }

  if (errors?.[0]?.message) {
    return errors[0].message;
  }

  return 'неизвестная ошибка';
}

export function validateFile(file: File): string | null {
  if (file.size > FEEDBACK_MAX_SIZE) {
    return `размер ${formatFileSize(file.size)} превышает лимит ${FEEDBACK_MAX_SIZE / 1024 / 1024}MB`;
  }

  if (!FEEDBACK_ALLOWED_TYPES.includes(file.type)) {
    return `тип "${file.type}" не поддерживается`;
  }

  const ext = file.name.split('.').pop()?.toLowerCase();
  if (!ext || !['png', 'jpg', 'jpeg', 'gif', 'webp'].includes(ext)) {
    return `расширение ".${ext || 'unknown'}" не поддерживается`;
  }

  return null;
}

export async function uploadOrRetryAttachment({
  feedbackId,
  file,
  abortSignal,
  existingAttachmentId,
}: UploadOrRetryParams): Promise<UploadAttemptResult> {
  try {
    let uploadUrl: string;
    let attachmentId: string;

    if (existingAttachmentId) {
      const { data } = await api.post(`/feedback/${feedbackId}/attachments/${existingAttachmentId}/presign`);
      uploadUrl = data.upload_url;
      attachmentId = existingAttachmentId;
    } else {
      const params = new URLSearchParams({
        filename: file.name,
        content_type: file.type,
        size: file.size.toString(),
      });
      const { data } = await api.post(`/feedback/${feedbackId}/attachments?${params.toString()}`);
      uploadUrl = data.upload_url;
      attachmentId = data.attachment_id;
    }

    const uploadResponse = await fetch(uploadUrl, {
      method: 'PUT',
      body: file,
      headers: { 'Content-Type': file.type },
      signal: abortSignal,
    });

    if (!uploadResponse.ok) {
      return {
        success: false,
        error: `Ошибка загрузки: HTTP ${uploadResponse.status} - ${uploadResponse.statusText}`,
      };
    }

    try {
      await api.put(`/feedback/${feedbackId}/attachments/${attachmentId}/mark-uploaded`);
    } catch {
      // File has been uploaded; DB flag can be retried separately if needed
    }

    return { success: true, attachmentId };
  } catch (error) {
    if (axios.isCancel(error) || (error instanceof Error && error.name === 'AbortError')) {
      throw error;
    }
    const errorMessage = error instanceof Error ? error.message : 'Неизвестная ошибка';
    return { success: false, error: errorMessage };
  }
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}
