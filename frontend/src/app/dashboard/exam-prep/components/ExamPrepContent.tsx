'use client';

import type { SerializedEditorState } from 'lexical';
import LectureViewer from '@/components/lectures/LectureViewer';
import type { ExamPrepContentValue } from '@/lib/api';
import { cn } from '@/lib/utils';
import { getExamPrepText } from '@/lib/utils/exam-prep';

interface ExamPrepContentProps {
  value: string | ExamPrepContentValue | null | undefined;
  className?: string;
  placeholder?: string;
}

export function ExamPrepContent({ value, className, placeholder = 'Контент пока не заполнен.' }: ExamPrepContentProps) {
  const text = getExamPrepText(value);
  if (!text) {
    return <div className={cn('text-sm text-muted-foreground', className)}>{placeholder}</div>;
  }

  if (typeof value === 'string' || !value?.content) {
    return <div className={cn('whitespace-pre-wrap text-sm leading-6 text-foreground', className)}>{text}</div>;
  }

  return (
    <LectureViewer
      content={value.content as unknown as SerializedEditorState}
      className={cn(
        'rounded-xl bg-transparent text-foreground [&_.ContentEditable__root]:p-0 [&_.prose]:max-w-none',
        className,
      )}
    />
  );
}
