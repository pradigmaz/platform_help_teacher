'use client';

import { useRef, useMemo } from 'react';
import katex from 'katex';
import 'katex/dist/katex.min.css';
import { cn } from '@/lib/utils';

interface MathViewerComponentProps {
  latex: string;
  displayMode: boolean;
}

export function MathViewerComponent({ latex, displayMode }: MathViewerComponentProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  const { html, error } = useMemo(() => {
    try {
      const rendered = katex.renderToString(latex, {
        displayMode,
        throwOnError: false,
        errorColor: '#ef4444',
        trust: true,
        strict: false,
      });
      return { html: rendered, error: null };
    } catch (err) {
      return { html: '', error: err instanceof Error ? err.message : 'Ошибка рендеринга формулы' };
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
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}

export default MathViewerComponent;
