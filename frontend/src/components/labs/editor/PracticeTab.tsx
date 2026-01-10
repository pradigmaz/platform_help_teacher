'use client';

import { SerializedEditorState } from 'lexical';
import { LectureEditor } from '@/components/lectures';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { IconCode, IconPlus } from '@tabler/icons-react';
import { VariantCard, VariantData } from '../VariantCard';
import { LabVariant } from './types';

interface PracticeTabProps {
  practiceContent?: SerializedEditorState;
  variants: LabVariant[];
  onPracticeChange: (content: SerializedEditorState) => void;
  onAddVariant: () => void;
  onUpdateVariant: (index: number, field: keyof LabVariant, value: unknown) => void;
  onRemoveVariant: (index: number) => void;
  onMoveVariant: (index: number, direction: 'up' | 'down') => void;
  externalFontSize?: string;
  externalLineHeight?: string;
}

export function PracticeTab({
  practiceContent,
  variants,
  onPracticeChange,
  onAddVariant,
  onUpdateVariant,
  onRemoveVariant,
  onMoveVariant,
  externalFontSize,
  externalLineHeight,
}: PracticeTabProps) {
  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <IconCode className="h-5 w-5" />
            Общее задание
          </CardTitle>
        </CardHeader>
        <CardContent>
          <LectureEditor
            initialContent={practiceContent}
            onChange={onPracticeChange}
            className="min-h-[300px]"
            preset="practice"
            externalFontSize={externalFontSize}
            externalLineHeight={externalLineHeight}
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>Варианты заданий</span>
            <Button size="sm" onClick={onAddVariant}>
              <IconPlus className="h-4 w-4 mr-1" />
              Добавить вариант
            </Button>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {variants.map((variant, index) => (
            <VariantCard
              key={index}
              variant={variant as VariantData}
              index={index}
              totalVariants={variants.length}
              onUpdate={onUpdateVariant}
              onRemove={onRemoveVariant}
              onMove={onMoveVariant}
              externalFontSize={externalFontSize}
              externalLineHeight={externalLineHeight}
            />
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
