'use client';

import { ErrorBoundary, FallbackProps } from 'react-error-boundary';
import { Button } from '@/components/ui/button';
import { ApiError } from '@/lib/api';
import { AlertCircle, RefreshCw } from 'lucide-react';

function ErrorFallback({ error, resetErrorBoundary }: FallbackProps) {
  // Determine if it's an API error and if it's retryable
  const isApiError = error instanceof ApiError;
  const isRetryable = isApiError ? error.isRetryable : true; // Default to true for unknown errors
  const message = error.message || 'Произошла непредвиденная ошибка';

  return (
    <div className="flex flex-col items-center justify-center min-h-[400px] p-6 text-center space-y-4 rounded-lg border bg-card text-card-foreground shadow-sm">
      <div className="p-3 bg-red-100 dark:bg-red-900/20 rounded-full">
        <AlertCircle className="w-10 h-10 text-red-600 dark:text-red-400" />
      </div>
      <div className="space-y-2">
        <h3 className="text-xl font-semibold tracking-tight">Что-то пошло не так</h3>
        <p className="text-sm text-muted-foreground max-w-[300px] mx-auto">
          {message}
        </p>
      </div>
      <div className="pt-4">
        {isRetryable ? (
          <Button onClick={resetErrorBoundary} variant="outline" className="gap-2">
            <RefreshCw className="w-4 h-4" />
            Попробовать снова
          </Button>
        ) : (
          <Button 
            onClick={() => window.location.reload()} 
            variant="secondary"
            className="gap-2"
          >
            <RefreshCw className="w-4 h-4" />
            Перезагрузить страницу
          </Button>
        )}
      </div>
    </div>
  );
}

interface ApiErrorBoundaryProps {
  children: React.ReactNode;
}

export function ApiErrorBoundary({ children }: ApiErrorBoundaryProps) {
  return (
    <ErrorBoundary
      FallbackComponent={ErrorFallback}
      onReset={() => {
        // Reset the state of your app so the error doesn't happen again
        // For example, invalidate queries if using React Query
      }}
    >
      {children}
    </ErrorBoundary>
  );
}

