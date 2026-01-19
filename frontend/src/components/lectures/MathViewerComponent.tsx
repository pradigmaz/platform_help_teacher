'use client';

import { useEffect, useRef, useState } from 'react';
import katex from 'katex';
import 'katex/dist/katex.min.css';
import { cn } from '@/lib/utils';

interface MathViewerComponentProps {
  latex: string;
  displayMode: boolean;
}

export function MathViewerComponent({ latex, displayMode }: MathViewerComponentProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;
    
    try {
      katex.render(latex, containerRef.current, {
        displayMode,
        throwOnError: false,
        errorColor: '#ef4444',
        trust: false,
        strict: 'warn',
      });
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка рендеринга формулы');
    }
  }, [latex, displayMode]);

  return (
    <span
      ref={containerRef}
      className={cn(
        displayMode ? "block my-4 py-2 text-center" : "inline",
        error && "text-destructive"
      )}
      title={error || undefined}
    />
  );
}

export default MathViewerComponent;
