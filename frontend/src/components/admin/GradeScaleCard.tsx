'use client';

import { Card, CardContent } from '@/components/ui/card';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';

interface GradeScaleCardProps {
  attestationType: 'first' | 'second';
}

const GRADE_SCALES = {
  first: {
    max: 35,
    min: 20,
    grades: [
      { name: 'неуд', label: '2', range: [0, 19], color: 'bg-red-500' },
      { name: 'уд', label: '3', range: [20, 25], color: 'bg-yellow-500' },
      { name: 'хор', label: '4', range: [26, 30], color: 'bg-blue-500' },
      { name: 'отл', label: '5', range: [31, 35], color: 'bg-green-500' },
    ]
  },
  second: {
    max: 70,
    min: 40,
    grades: [
      { name: 'неуд', label: '2', range: [0, 39], color: 'bg-red-500' },
      { name: 'уд', label: '3', range: [40, 50], color: 'bg-yellow-500' },
      { name: 'хор', label: '4', range: [51, 60], color: 'bg-blue-500' },
      { name: 'отл', label: '5', range: [61, 70], color: 'bg-green-500' },
    ]
  }
};

export function GradeScaleCard({ attestationType }: GradeScaleCardProps) {
  const scale = GRADE_SCALES[attestationType];

  return (
    <Card className="bg-muted/30">
      <CardContent className="pt-4 pb-3">
        {/* Compact bar with labels below */}
        <div className="space-y-2">
          <div className="flex h-3 rounded-full overflow-hidden">
            {scale.grades.map((grade) => {
              const width = ((grade.range[1] - grade.range[0] + 1) / scale.max) * 100;
              return (
                <Tooltip key={grade.name}>
                  <TooltipTrigger asChild>
                    <div
                      className={`${grade.color} cursor-default transition-all hover:brightness-110`}
                      style={{ width: `${width}%` }}
                    />
                  </TooltipTrigger>
                  <TooltipContent side="bottom">
                    <span className="font-medium">{grade.label} ({grade.name})</span>: {grade.range[0]}–{grade.range[1]} б.
                  </TooltipContent>
                </Tooltip>
              );
            })}
          </div>
          
          {/* Labels under bar */}
          <div className="flex text-xs">
            {scale.grades.map((grade) => {
              const width = ((grade.range[1] - grade.range[0] + 1) / scale.max) * 100;
              return (
                <div key={grade.name} className="text-center text-muted-foreground" style={{ width: `${width}%` }}>
                  <span className="font-medium text-foreground">{grade.label}</span>
                  <span className="ml-1">({grade.range[0]}–{grade.range[1]})</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Summary line */}
        <div className="flex justify-between text-xs text-muted-foreground mt-3 pt-2 border-t border-border/50">
          <span>Зачёт от <span className="font-medium text-foreground">{scale.min}</span> б.</span>
          <span>Макс <span className="font-medium text-foreground">{scale.max}</span> б.</span>
        </div>
      </CardContent>
    </Card>
  );
}
