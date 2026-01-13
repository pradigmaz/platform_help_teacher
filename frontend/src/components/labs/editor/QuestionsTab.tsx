'use client';

import { useState, useCallback } from 'react';
import { SerializedEditorState } from 'lexical';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { IconQuestionMark, IconPlus, IconTrash, IconChevronDown, IconChevronRight, IconArrowUp, IconArrowDown } from '@tabler/icons-react';
import { LectureEditor } from '@/components/lectures';
import { LabQuestion, normalizeQuestion } from './types';
import { cn } from '@/lib/utils';
import { extractTextFromLexical, truncateText } from '@/lib/utils/lexical-utils';

interface QuestionsTabProps {
  questions: (LabQuestion | string)[];
  onAdd: () => void;
  onUpdate: (index: number, value: LabQuestion) => void;
  onRemove: (index: number) => void;
  onMove?: (index: number, direction: 'up' | 'down') => void;
  externalFontSize?: string;
  externalLineHeight?: string;
}

interface QuestionCardProps {
  question: LabQuestion;
  index: number;
  totalQuestions: number;
  onUpdate: (index: number, value: LabQuestion) => void;
  onRemove: (index: number) => void;
  onMove?: (index: number, direction: 'up' | 'down') => void;
  externalFontSize?: string;
  externalLineHeight?: string;
}


function QuestionCard({ question, index, totalQuestions, onUpdate, onRemove, onMove, externalFontSize, externalLineHeight }: QuestionCardProps) {
  const [isExpanded, setIsExpanded] = useState(!question.content && !question.text);

  const getPreview = useCallback(() => {
    if (question.content) {
      const text = extractTextFromLexical(question.content);
      return truncateText(text, 80) || 'Пустой вопрос';
    }
    if (question.text) {
      return truncateText(question.text, 80);
    }
    return 'Пустой вопрос';
  }, [question]);

  const handleContentChange = useCallback((content: SerializedEditorState) => {
    const text = extractTextFromLexical(content);
    onUpdate(index, { ...question, content, text });
  }, [index, onUpdate, question]);

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
                {index + 1}
              </Badge>
              <div className="flex-1 min-w-0">
                <p className={cn("text-sm truncate", isExpanded ? "text-primary font-medium" : "text-muted-foreground")}>
                  {isExpanded ? `Вопрос ${index + 1}` : getPreview()}
                </p>
              </div>
            </div>
          </CollapsibleTrigger>
          <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
            {onMove && (
              <>
                <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => onMove(index, 'up')} disabled={index === 0}>
                  <IconArrowUp size={14} />
                </Button>
                <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => onMove(index, 'down')} disabled={index === totalQuestions - 1}>
                  <IconArrowDown size={14} />
                </Button>
              </>
            )}
            <Button variant="ghost" size="icon" className="h-7 w-7 text-destructive hover:text-destructive" onClick={() => onRemove(index)} disabled={totalQuestions <= 1}>
              <IconTrash size={14} />
            </Button>
          </div>
        </div>

        <CollapsibleContent>
          <div className="px-3 pb-3">
            <LectureEditor
              initialContent={question.content}
              onChange={handleContentChange}
              className="min-h-[100px]"
              placeholder="Введите вопрос..."
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

export function QuestionsTab({ questions, onAdd, onUpdate, onRemove, onMove, externalFontSize, externalLineHeight }: QuestionsTabProps) {
  // Нормализуем вопросы один раз при рендере
  const normalizedQuestions = questions.map(normalizeQuestion);
  
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span className="flex items-center gap-2">
            <IconQuestionMark className="h-5 w-5" />
            Контрольные вопросы
          </span>
          <Button size="sm" onClick={onAdd}>
            <IconPlus className="h-4 w-4 mr-1" />
            Добавить вопрос
          </Button>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {normalizedQuestions.map((question, index) => (
          <QuestionCard
            key={question.id}
            question={question}
            index={index}
            totalQuestions={questions.length}
            onUpdate={onUpdate}
            onRemove={onRemove}
            onMove={onMove}
            externalFontSize={externalFontSize}
            externalLineHeight={externalLineHeight}
          />
        ))}
      </CardContent>
    </Card>
  );
}
