'use client';

import { useRef, useCallback, useEffect } from 'react';

interface UseAutoSaveOptions {
  delay?: number;
  onSave: () => Promise<void>;
}

export function useAutoSave({ delay = 500, onSave }: UseAutoSaveOptions) {
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  const isSavingRef = useRef(false);

  const triggerSave = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    timeoutRef.current = setTimeout(async () => {
      if (isSavingRef.current) return;
      
      isSavingRef.current = true;
      try {
        await onSave();
      } catch (err) {
        console.error('Autosave failed:', err);
      } finally {
        isSavingRef.current = false;
      }
    }, delay);
  }, [delay, onSave]);

  const cancelSave = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  return { triggerSave, cancelSave, isSaving: isSavingRef.current };
}
