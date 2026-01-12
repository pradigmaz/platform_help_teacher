'use client';

import { Lab } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { HelpCircle } from 'lucide-react';
import { getQuestionText } from '@/lib/utils/question-utils';

interface LabQuestionsProps {
  lab: Lab;
}

export function LabQuestions({ lab }: LabQuestionsProps) {
  if (!lab.questions || lab.questions.length === 0) return null;

  return (
    <Card>
      <CardHeader className="py-3">
        <CardTitle className="text-base flex items-center gap-2">
          <HelpCircle className="h-4 w-4" />
          Контрольные вопросы
          <Badge variant="secondary" className="ml-1">{lab.questions.length}</Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="py-3">
        <div className="space-y-3">
          {lab.questions.map((q, i) => (
            <div 
              key={i} 
              className="flex gap-3 p-3 rounded-lg bg-muted/50 hover:bg-muted/70 transition-colors"
            >
              <Badge variant="outline" className="h-6 w-6 shrink-0 flex items-center justify-center text-xs font-mono">
                {i + 1}
              </Badge>
              <p className="text-sm leading-relaxed">{getQuestionText(q)}</p>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
