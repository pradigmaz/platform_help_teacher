'use client';

import { useState, useCallback, useMemo } from 'react';
import { SerializedEditorState } from 'lexical';
import { LectureEditor } from '@/components/lectures';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { IconChevronDown, IconChevronRight, IconTrash, IconArrowUp, IconArrowDown } from '@tabler/icons-react';
import { cn } from '@/lib/utils';
import { extractTextFromLexical, truncateText } from '@/lib/utils/lexical-utils';

export interface VariantData {
  id: string;
  number: number;
  content?: SerializedEditorState;
  description: string;
  test_data?: string;
}

interface VariantCardProps {
  variant: VariantData;
  index: number;
  totalVariants: number;
  onUpdate: (index: number, field: keyof VariantData, value: unknown) => void;
  onRemove: (index: number) => void;
  onMove: (index: number, direction: 'up' | 'down') => void;
  externalFontSize?: string;
  externalLineHeight?: string;
}

export function VariantCard({ variant, index, totalVariants, onUpdate, onRemove, onMove, externalFontSize, externalLineHeight }: VariantCardProps) {
  const [isExpanded, setIsExpanded] = useState(!variant.content && !variant.description);

  const getPreview = useCallback(() => {
    if (variant.description) {
      return truncateText(variant.description, 60);
    }
    return 'Пустой вариант';
  }, [variant.description]);

  const handleContentChange = useCallback((content: SerializedEditorState) => {
    onUpdate(index, 'content', content);
    const text = extractTextFromLexical(content);
    onUpdate(index, 'description', text);
  }, [index, onUpdate]);

  return (
    <Collapsible open={isExpanded} onOpenChange={setIsExpanded}>
      <div className={cn(
        "border rounded-lg transition-all duration-200",
        isExpanded ? "bg-card border-border shadow-sm" : "bg-muted/30 border-border/50 hover:border-border hover:bg-muted/50"
      )}>
        <div className="flex items-center gap-3 p-3 group">
          <CollapsibleTrigger asChild>
            <div className="flex items-center gap-3 flex-1 min-w-0 cursor-pointer select-none">
              <div className="text-muted-foreground">
                {isExpanded ? <IconChevronDown size={18} /> : <IconChevronRight size={18} />}
              </div>
              <Badge variant="secondary" className="h-7 w-7 flex items-center justify-center font-mono text-sm">
                {variant.number}
              </Badge>
              <div className="flex-1 min-w-0">
                <p className={cn("text-sm truncate", isExpanded ? "text-primary font-medium" : "text-muted-foreground")}>
                  {isExpanded ? `Вариант ${variant.number}` : getPreview()}
                </p>
              </div>
            </div>
          </CollapsibleTrigger>
          <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
            <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => onMove(index, 'up')} disabled={index === 0}>
              <IconArrowUp size={14} />
            </Button>
            <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => onMove(index, 'down')} disabled={index === totalVariants - 1}>
              <IconArrowDown size={14} />
            </Button>
            <Button variant="ghost" size="icon" className="h-7 w-7 text-destructive hover:text-destructive" onClick={() => onRemove(index)} disabled={totalVariants <= 1}>
              <IconTrash size={14} />
            </Button>
          </div>
        </div>

        <CollapsibleContent>
          <div className="px-3 pb-3">
            <LectureEditor
              initialContent={variant.content}
              onChange={handleContentChange}
              className="min-h-[120px]"
              placeholder="Опишите задание варианта..."
              preset="minimal"
              externalFontSize={externalFontSize}
              externalLineHeight={externalLineHeight}
            />
          </div>
        </CollapsibleContent>
      </div>
    </Collapsible>
  );
}
