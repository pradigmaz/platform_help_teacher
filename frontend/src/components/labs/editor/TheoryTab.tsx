'use client';

import { SerializedEditorState } from 'lexical';
import { LectureEditor } from '@/components/lectures';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { IconBook } from '@tabler/icons-react';

interface TheoryTabProps {
  content?: SerializedEditorState;
  onChange: (content: SerializedEditorState) => void;
  onFontSizeChange?: (size: string) => void;
  onLineHeightChange?: (height: string) => void;
}

export function TheoryTab({ content, onChange, onFontSizeChange, onLineHeightChange }: TheoryTabProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <IconBook className="h-5 w-5" />
          Теоретическая часть
        </CardTitle>
      </CardHeader>
      <CardContent>
        <LectureEditor
          initialContent={content}
          onChange={onChange}
          className="min-h-[500px]"
          preset="full"
          onFontSizeChange={onFontSizeChange}
          onLineHeightChange={onLineHeightChange}
        />
      </CardContent>
    </Card>
  );
}
