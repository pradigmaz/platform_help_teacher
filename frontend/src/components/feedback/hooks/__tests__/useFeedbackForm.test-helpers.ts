import { vi } from 'vitest';
import type { UploadResult } from '../../types';

export interface AttachmentsMock {
  uploadAll: (feedbackId: string) => Promise<UploadResult>;
  retryUpload: (feedbackId: string, failedFiles: File[]) => Promise<UploadResult>;
  clearFiles: () => void;
  getFailedFiles: () => File[];
  uploadInProgress: boolean;
}

export function makeAttachments(overrides?: Partial<AttachmentsMock>): AttachmentsMock {
  return {
    uploadAll: vi.fn().mockResolvedValue({ failed: 0, total: 0 }) as unknown as AttachmentsMock['uploadAll'],
    retryUpload: vi.fn().mockResolvedValue({ failed: 0, total: 0 }) as unknown as AttachmentsMock['retryUpload'],
    clearFiles: vi.fn(),
    getFailedFiles: vi.fn().mockReturnValue([]) as unknown as AttachmentsMock['getFailedFiles'],
    uploadInProgress: false,
    ...overrides,
  };
}

export const validFormValues = {
  title: 'Test feedback',
  description: 'Test description',
  category: 'bug',
};
