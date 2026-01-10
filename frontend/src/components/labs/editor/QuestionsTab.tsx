'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { IconQuestionMark, IconPlus, IconTrash } from '@tabler/icons-react';

interface QuestionsTabProps {
  questions: string[];
  onAdd: () => void;
  onUpdate: (index: number, value: string) => void;
  onRemove: (index: number) => void;
}

export function QuestionsTab({ questions, onAdd, onUpdate, onRemove }: QuestionsTabProps) {
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
          <div key={index} className="flex gap-3 items-start">
            <Badge variant="outline" className="mt-2">{index + 1}</Badge>
            <Textarea
              value={question}
              onChange={(e) => onUpdate(index, e.target.value)}
              placeholder="Введите вопрос..."
              rows={2}
              className="flex-1"
            />
            <Button
              variant="ghost"
              size="icon"
              onClick={() => onRemove(index)}
              disabled={questions.length <= 1}
            >
              <IconTrash className="h-4 w-4 text-destructive" />
            </Button>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
