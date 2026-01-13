'use client';

import { SerializedEditorState } from 'lexical';
import { LectureEditor } from '@/components/lectures';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { IconCode } from '@tabler/icons-react';
import { VariantCard, VariantData } from '../VariantCard';
import { LabVariant } from './types';

interface PracticeTabProps {
  practiceContent?: SerializedEditorState;
  variants: LabVariant[];
  onPracticeChange: (content: SerializedEditorState) => void;
  onSetVariantsCount: (count: number) => void;
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
  onSetVariantsCount,
  onUpdateVariant,
  onRemoveVariant,
  onMoveVariant,
  externalFontSize,
  externalLineHeight,
}: PracticeTabProps) {
  const handleCountChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseInt(e.target.value, 10);
    if (!isNaN(value) && value >= 1 && value <= 100) {
      onSetVariantsCount(value);
    }
  };

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
            stickyToolbar={true}
            externalFontSize={externalFontSize}
            externalLineHeight={externalLineHeight}
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>Варианты заданий</span>
            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground">Количество:</span>
              <Input
                type="number"
                min={1}
                max={100}
                value={variants.length}
                onChange={handleCountChange}
                className="w-[70px] h-8 text-center"
              />
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {variants.map((variant, index) => (
            <VariantCard
              key={variant.id}
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
