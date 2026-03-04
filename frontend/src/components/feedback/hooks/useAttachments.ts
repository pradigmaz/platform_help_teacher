import { useCallback, useEffect, useRef, useState } from 'react';
import { toast } from 'sonner';
import axios from 'axios';
import { type FileRejection } from 'react-dropzone';
import { FEEDBACK_ACCEPT, FEEDBACK_FILE_LIMIT, type PendingFile, type UploadResult, type UploadError } from '../types';
import { getRejectionReason, uploadOrRetryAttachment, validateFile } from './attachmentUpload';

export function useAttachments(limit = FEEDBACK_FILE_LIMIT) {
  const [files, setFiles] = useState<PendingFile[]>([]);
  const [uploadInProgress, setUploadInProgress] = useState(false);
  const abortControllerRef = useRef<AbortController | null>(null);

  const addFiles = useCallback(
    (acceptedFiles: File[], rejectedFiles: FileRejection[]) => {
      if (acceptedFiles.length === 0 && rejectedFiles.length === 0) return;

      const remaining = Math.max(0, limit - files.length);
      const toAdd = acceptedFiles.slice(0, remaining);

      const valid: PendingFile[] = [];
      const rejectionReasons: string[] = [];

      // Handle rejected files from dropzone
      if (rejectedFiles.length > 0) {
        rejectedFiles.forEach((rejection: FileRejection) => {
          const file = rejection.file;
          const reason = getRejectionReason(rejection);
          rejectionReasons.push(`${file.name}: ${reason}`);
        });
      }

      // Handle accepted files
      toAdd.forEach((file) => {
        const validationError = validateFile(file);
        if (validationError) {
          rejectionReasons.push(`${file.name}: ${validationError}`);
          return;
        }
        valid.push({ file, preview: URL.createObjectURL(file) });
      });

      // Show detailed rejection errors
      if (rejectionReasons.length > 0) {
        toast.error('Некоторые файлы не были добавлены', {
          description: rejectionReasons.slice(0, 3).join('\n'),
          duration: 5000,
        });
      }

      if (valid.length) {
        setFiles((prev) => [...prev, ...valid]);
        toast.success(`Добавлено ${valid.length} файл(ов)`);
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

  useEffect(() => {
    return () => {
      clearFiles();
      abortControllerRef.current?.abort();
    };
  }, [clearFiles]);

  const uploadAll = useCallback(
    async (feedbackId: string): Promise<UploadResult> => {
      setUploadInProgress(true);
      abortControllerRef.current = new AbortController();
      
      let failed = 0;
      const errors: UploadError[] = [];

      try {
        for (const { file, preview } of files) {
          const result = await uploadOrRetryAttachment({
            feedbackId,
            file,
            abortSignal: abortControllerRef.current.signal,
          });
          if (!result.success) {
            failed += 1;
            errors.push({ filename: file.name, error: result.error || 'Unknown error' });
          } else {
            setFiles((prev) =>
              prev.map((pf) =>
                pf.preview === preview ? { ...pf, attachmentId: result.attachmentId } : pf
              )
            );
          }
        }
      } catch (error) {
        if (axios.isCancel(error) || (error instanceof Error && error.name === 'AbortError')) {
          toast.info('Загрузка отменена');
          return { failed, total: files.length, errors };
        }
        throw error;
      } finally {
        setUploadInProgress(false);
        abortControllerRef.current = null;
      }

      return { failed, total: files.length, errors };
    },
    [files],
  );

  const retryUpload = useCallback(
    async (feedbackId: string, failedFiles: File[]): Promise<UploadResult> => {
      setUploadInProgress(true);
      abortControllerRef.current = new AbortController();
      
      let failed = 0;
      const errors: UploadError[] = [];

      try {
        // Find files in our state and retry with existing attachment IDs
        for (const file of failedFiles) {
          const pendingFile = files.find((pf) => pf.file === file);
          if (!pendingFile) {
            failed += 1;
            errors.push({ filename: file.name, error: 'File not found in state' });
            continue;
          }

          const result = await uploadOrRetryAttachment({
            feedbackId,
            file,
            existingAttachmentId: pendingFile.attachmentId,
            abortSignal: abortControllerRef.current.signal,
          });
          if (!result.success) {
            failed += 1;
            errors.push({ filename: file.name, error: result.error || 'Unknown error' });
          } else {
            setFiles((prev) =>
              prev.map((pf) =>
                pf.file === file ? { ...pf, attachmentId: result.attachmentId } : pf
              )
            );
          }
        }
      } catch (error) {
        if (axios.isCancel(error) || (error instanceof Error && error.name === 'AbortError')) {
          toast.info('Загрузка отменена');
          return { failed, total: failedFiles.length, errors };
        }
        throw error;
      } finally {
        setUploadInProgress(false);
        abortControllerRef.current = null;
      }

      return { failed, total: failedFiles.length, errors };
    },
    [files],
  );

  const getFailedFiles = useCallback((): File[] => {
    // Return files that don't have attachmentId (failed to create DB record)
    return files.filter((f) => !f.attachmentId).map((f) => f.file);
  }, [files]);

  return {
    files,
    addFiles,
    removeFile,
    clearFiles,
    uploadAll,
    retryUpload,
    getFailedFiles,
    uploadInProgress,
    hasLimit: files.length >= limit,
    dropzoneAccept: FEEDBACK_ACCEPT,
  };
}
