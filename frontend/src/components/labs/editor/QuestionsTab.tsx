'use client';

import { useState, useCallback } from 'react';
import { SerializedEditorState } from 'lexical';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { IconQuestionMark, IconPlus, IconTrash, IconChevronDown, IconChevronRight, IconArrowUp, IconArrowDown } from '@tabler/icons-react';
import { LectureEditor } from '@/components/lectures';
import { LabQuestion } from './types';
import { cn } from '@/lib/utils';

interface QuestionsTabProps {
  questions: (LabQuestion | string)[];
  onAdd: () => void;
  onUpdate: (index: number, value: LabQuestion) => void;
  onRemove: (index: number) => void;
  onMove?: (index: number, direction: 'up' | 'down') => void;
  externalFontSize?: string;
  externalLineHeight?: string;
}

// Конвертация legacy string в LabQuestion
function normalizeQuestion(q: LabQuestion | string): LabQuestion {
  if (typeof q === 'string') {
    return { text: q };
  }
  return q;
}

// Извлечение текста из Lexical state для превью
function extractTextFromLexical(state?: SerializedEditorState): string {
  try {
    const root = state?.root;
    if (!root?.children) return '';
    let text = '';
    const extractFromNode = (node: Record<string, unknown>) => {
      if (node.text && typeof node.text === 'string') text += node.text;
      if (node.children && Array.isArray(node.children)) node.children.forEach(extractFromNode);
    };
    root.children.forEach(extractFromNode);
    return text.trim();
  } catch {
    return '';
  }
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
      return text.length > 80 ? text.substring(0, 80) + '...' : text || 'Пустой вопрос';
    }
    if (question.text) {
      return question.text.length > 80 ? question.text.substring(0, 80) + '...' : question.text;
    }
    return 'Пустой вопрос';
  }, [question]);

  const handleContentChange = useCallback((content: SerializedEditorState) => {
    const text = extractTextFromLexical(content);
    onUpdate(index, { content, text });
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
        {questions.map((question, index) => (
          <QuestionCard
            key={index}
            question={normalizeQuestion(question)}
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
