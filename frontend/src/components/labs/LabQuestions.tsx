'use client';

import { Lab } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { HelpCircle } from 'lucide-react';

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
          Контрольные вопросы ({lab.questions.length})
        </CardTitle>
      </CardHeader>
      <CardContent className="py-3">
        <ol className="space-y-2 list-decimal list-inside">
          {lab.questions.map((q: string, i: number) => (
            <li key={i} className="text-sm">{q}</li>
          ))}
        </ol>
      </CardContent>
    </Card>
  );
}
