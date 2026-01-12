'use client';

import { SerializedEditorState } from 'lexical';
import { LectureEditor } from '@/components/lectures';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
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

const VARIANT_OPTIONS = Array.from({ length: 30 }, (_, i) => i + 1);

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
              <Select 
                value={String(variants.length)} 
                onValueChange={(v) => onSetVariantsCount(Number(v))}
              >
                <SelectTrigger className="w-[80px] h-8">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {VARIANT_OPTIONS.map((n) => (
                    <SelectItem key={n} value={String(n)}>{n}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
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
