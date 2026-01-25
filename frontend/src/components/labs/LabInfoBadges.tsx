'use client';

import { Lab } from '@/lib/api';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Target, Calendar } from 'lucide-react';

interface LabInfoBadgesProps {
  lab: Lab;
}

export function LabInfoBadges({ lab }: LabInfoBadgesProps) {
  const formatDeadline = (lessons: number | null | undefined) => {
    if (!lessons) return null;
    return `${lessons} ${lessons === 1 ? 'пара' : lessons < 5 ? 'пары' : 'пар'}`;
  };

  const deadline5 = lab.deadline_5_lessons;
  const deadline4 = lab.deadline_4_lessons;

  return (
    <>
      {/* Info badges */}
      <div className="flex flex-wrap gap-2">
        {deadline5 && (
          <Badge variant="outline" className="gap-1">
            <Calendar className="h-3 w-3" />
            На 5: {formatDeadline(deadline5)}
          </Badge>
        )}
        {deadline4 && (
          <Badge variant="outline" className="gap-1">
            <Calendar className="h-3 w-3" />
            На 4: {formatDeadline(deadline4)}
          </Badge>
        )}
        {lab.is_sequential && (
          <Badge variant="outline">Последовательная сдача</Badge>
        )}
        <Badge variant="outline">{lab.variants?.length || 0} вариантов</Badge>
        <Badge variant="outline">{lab.questions?.length || 0} вопросов</Badge>
      </div>

      {/* Goal */}
      {lab.goal && (
        <Card>
          <CardHeader className="py-3">
            <CardTitle className="text-base flex items-center gap-2">
              <Target className="h-4 w-4" />
              Цель работы
            </CardTitle>
          </CardHeader>
          <CardContent className="py-3">
            <p className="text-sm">{lab.goal}</p>
          </CardContent>
        </Card>
      )}

      {/* Formatting guide */}
      {lab.formatting_guide && (
        <Card>
          <CardHeader className="py-3">
            <CardTitle className="text-base">Что записать в тетрадь</CardTitle>
          </CardHeader>
          <CardContent className="py-3">
            <pre className="text-sm whitespace-pre-wrap font-sans">{lab.formatting_guide}</pre>
          </CardContent>
        </Card>
      )}
    </>
  );
}
