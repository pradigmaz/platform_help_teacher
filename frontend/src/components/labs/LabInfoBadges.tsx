'use client';

import { Lab } from '@/lib/api';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Target, Calendar } from 'lucide-react';

interface LabInfoBadgesProps {
  lab: Lab;
}

export function LabInfoBadges({ lab }: LabInfoBadgesProps) {
  return (
    <>
      {/* Info badges */}
      <div className="flex flex-wrap gap-2">
        <Badge variant="secondary" className="gap-1">
          <Target className="h-3 w-3" />
          Макс. оценка: {lab.max_grade}
        </Badge>
        {lab.deadline && (
          <Badge variant="outline" className="gap-1">
            <Calendar className="h-3 w-3" />
            Дедлайн: {new Date(lab.deadline).toLocaleDateString('ru-RU')}
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
