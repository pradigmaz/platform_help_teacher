'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Info } from 'lucide-react';

interface GradeScaleCardProps {
  attestationType: 'first' | 'second';
}

const GRADE_SCALES = {
  first: {
    max: 35,
    min: 20,
    grades: {
      'отл': [31, 35],
      'хор': [26, 30],
      'уд': [20, 25],
      'неуд': [0, 19.99],
    }
  },
  second: {
    max: 70,
    min: 40,
    grades: {
      'отл': [61, 70],
      'хор': [51, 60],
      'уд': [40, 50],
      'неуд': [0, 39.99],
    }
  }
};

export function GradeScaleCard({ attestationType }: GradeScaleCardProps) {
  const scale = GRADE_SCALES[attestationType];

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base flex items-center gap-2">
          <Info className="w-4 h-4 text-blue-500" />
          Шкала оценок (фиксированная)
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex flex-wrap gap-2 mb-3">
          <Badge variant="outline" className="bg-green-500/10 border-green-500/30 text-green-600">
            5 (отл): {scale.grades['отл'][0]}–{scale.grades['отл'][1]}
          </Badge>
          <Badge variant="outline" className="bg-blue-500/10 border-blue-500/30 text-blue-600">
            4 (хор): {scale.grades['хор'][0]}–{scale.grades['хор'][1]}
          </Badge>
          <Badge variant="outline" className="bg-yellow-500/10 border-yellow-500/30 text-yellow-600">
            3 (уд): {scale.grades['уд'][0]}–{scale.grades['уд'][1]}
          </Badge>
          <Badge variant="outline" className="bg-red-500/10 border-red-500/30 text-red-600">
            2 (неуд): {scale.grades['неуд'][0]}–{scale.grades['неуд'][1]}
          </Badge>
        </div>
        <div className="text-sm text-muted-foreground">
          Макс: <span className="font-medium text-foreground">{scale.max}</span> баллов | 
          Мин для зачёта: <span className="font-medium text-foreground">{scale.min}</span> баллов
        </div>
      </CardContent>
    </Card>
  );
}
