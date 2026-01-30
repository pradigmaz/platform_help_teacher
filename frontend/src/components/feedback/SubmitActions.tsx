import { Check, RefreshCw, AlertTriangle, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import type { UploadResult } from './types';

type SubmitActionsProps = {
  submitting: boolean;
  feedbackCreated: boolean;
  isSubmitDisabled: boolean;
  uploadResult: UploadResult | null;
  uploadFailed?: boolean;
  uploadInProgress?: boolean;
  onCancel: () => void;
  onRetry?: () => void;
  onReset?: () => void;
};

export function SubmitActions({
  submitting,
  feedbackCreated,
  isSubmitDisabled,
  uploadResult,
  uploadFailed = false,
  uploadInProgress = false,
  onCancel,
  onRetry,
  onReset,
}: SubmitActionsProps) {
  const hasFailedUploads = uploadResult && uploadResult.failed > 0;
  const showRetrySection = uploadFailed && hasFailedUploads && onRetry;

  return (
    <div className="flex flex-col gap-3 pt-2">
      {/* Retry section for failed uploads */}
      {showRetrySection && (
        <div className="flex items-start gap-3 p-3 bg-yellow-50 dark:bg-yellow-950/20 border border-yellow-200 dark:border-yellow-900/30 rounded-md">
          <AlertTriangle className="h-5 w-5 text-yellow-600 dark:text-yellow-500 flex-shrink-0 mt-0.5" />
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-yellow-800 dark:text-yellow-300">
              Проблемы с вложениями
            </p>
            <p className="text-xs text-yellow-700 dark:text-yellow-400 mt-1">
              {uploadResult.failed} из {uploadResult.total} файлов не удалось загрузить
            </p>
            {uploadResult.errors && uploadResult.errors.length > 0 && (
              <details className="mt-2">
                <summary className="text-xs text-yellow-600 dark:text-yellow-500 cursor-pointer hover:underline">
                  Показать ошибки
                </summary>
                <ul className="mt-1 space-y-1">
                  {uploadResult.errors.slice(0, 3).map((error, idx: number) => (
                    <li key={idx} className="text-xs text-yellow-700 dark:text-yellow-400 truncate">
                      {error.filename}: {error.error}
                    </li>
                  ))}
                  {uploadResult.errors.length > 3 && (
                    <li className="text-xs text-yellow-600 dark:text-yellow-500">
                      ... и еще {uploadResult.errors.length - 3}
                    </li>
                  )}
                </ul>
              </details>
            )}
          </div>
          <Button
            type="button"
            size="sm"
            variant="outline"
            onClick={onRetry}
            disabled={submitting || uploadInProgress}
            className="flex-shrink-0 h-8"
          >
            {uploadInProgress ? (
              <>
                <RefreshCw className="h-4 w-4 mr-1 animate-spin" />
                Повтор...
              </>
            ) : (
              <>
                <RefreshCw className="h-4 w-4 mr-1" />
                Повторить
              </>
            )}
          </Button>
        </div>
      )}

      {/* Action buttons */}
      <div className="flex justify-end gap-2">
        {feedbackCreated ? (
          <>
            {hasFailedUploads ? (
              <Button type="button" variant="outline" onClick={onReset} disabled={submitting || uploadInProgress}>
                <X className="h-4 w-4 mr-1" />
                Начать новый
              </Button>
            ) : (
              <Button type="button" variant="outline" onClick={onReset}>
                <X className="h-4 w-4 mr-1" />
                Закрыть
              </Button>
            )}
            <Button
              type="button"
              variant="default"
              onClick={onReset}
              className="bg-green-600 hover:bg-green-600 text-white"
              disabled={submitting || uploadInProgress}
            >
              <Check className="h-4 w-4 mr-1" />
              Отправлено!
            </Button>
          </>
        ) : (
          <>
            <Button type="button" variant="outline" onClick={onCancel} disabled={submitting}>
              <X className="h-4 w-4 mr-1" />
              Отмена
            </Button>
            <Button
              type="submit"
              disabled={isSubmitDisabled}
            >
              {submitting ? (
                <>
                  <RefreshCw className="h-4 w-4 mr-1 animate-spin" />
                  Отправка...
                </>
              ) : (
                'Отправить'
              )}
            </Button>
          </>
        )}
      </div>
    </div>
  );
}
