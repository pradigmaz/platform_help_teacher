import { useCallback, useEffect, useState } from 'react';
import { toast } from 'sonner';
import api from '@/lib/api';
import { FEEDBACK_ACCEPT, FEEDBACK_ALLOWED_TYPES, FEEDBACK_FILE_LIMIT, FEEDBACK_MAX_SIZE, type PendingFile, type UploadResult } from '../types';

export function useAttachments(limit = FEEDBACK_FILE_LIMIT) {
  const [files, setFiles] = useState<PendingFile[]>([]);

  const addFiles = useCallback(
    (acceptedFiles: File[]) => {
      if (acceptedFiles.length === 0) return;
      const remaining = Math.max(0, limit - files.length);
      const toAdd = acceptedFiles.slice(0, remaining);

      const valid: PendingFile[] = [];
      const rejected: string[] = [];

      toAdd.forEach((file) => {
        if (file.size > FEEDBACK_MAX_SIZE) {
          rejected.push(`${file.name} > 5MB`);
          return;
        }
        if (!FEEDBACK_ALLOWED_TYPES.includes(file.type)) {
          rejected.push(`${file.name} — неподдерживаемый тип`);
          return;
        }
        valid.push({ file, preview: URL.createObjectURL(file) });
      });

      if (rejected.length) {
        toast.warning(`Файлы не добавлены: ${rejected.join(', ')}`);
      }
      if (valid.length) {
        setFiles((prev) => [...prev, ...valid]);
      }
    },
    [files.length, limit],
  );

  const removeFile = useCallback((index: number) => {
    setFiles((prev) => {
      if (!prev[index]) return prev;
      URL.revokeObjectURL(prev[index].preview);
      return prev.filter((_, i) => i !== index);
    });
  }, []);

  const clearFiles = useCallback(() => {
    setFiles((prev) => {
      prev.forEach((f) => URL.revokeObjectURL(f.preview));
      return [];
    });
  }, []);

  useEffect(() => () => clearFiles(), [clearFiles]);

  const uploadAll = useCallback(
    async (feedbackId: string): Promise<UploadResult> => {
      let failed = 0;

      for (const { file } of files) {
        const ok = await uploadAttachment(feedbackId, file);
        if (!ok) failed += 1;
      }

      return { failed, total: files.length };
    },
    [files],
  );

  return {
    files,
    addFiles,
    removeFile,
    clearFiles,
    uploadAll,
    hasLimit: files.length >= limit,
    dropzoneAccept: FEEDBACK_ACCEPT,
  };
}

async function uploadAttachment(feedbackId: string, file: File): Promise<boolean> {
  try {
    const params = new URLSearchParams({
      filename: file.name,
      content_type: file.type,
      size: file.size.toString(),
    });
    const { data } = await api.post(`/feedback/${feedbackId}/attachments?${params.toString()}`);

    const response = await fetch(data.upload_url, {
      method: 'PUT',
      body: file,
      headers: { 'Content-Type': file.type },
    });

    if (!response.ok) {
      console.error('MinIO upload failed:', response.status, response.statusText);
      return false;
    }
    return true;
  } catch (error) {
    console.error('Upload failed:', error);
    return false;
  }
}
