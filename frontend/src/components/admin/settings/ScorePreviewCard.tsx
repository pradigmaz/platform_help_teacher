'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Calculator } from 'lucide-react';

interface ScorePreviewCardProps {
  maxPoints: number;
  labsWeight: number;
  labsCount: number;
  attendanceWeight: number;
  activityReserve: number;
  grade4Coef: number;
  grade3Coef: number;
  lateCoef: number;
  totalWeight: number;
  exampleLessonsCount?: number; // Примерное кол-во занятий для расчёта
}

export function ScorePreviewCard({
  maxPoints,
  labsWeight,
  labsCount,
  attendanceWeight,
  activityReserve,
  grade4Coef,
  grade3Coef,
  lateCoef,
  totalWeight,
  exampleLessonsCount = 10,
}: ScorePreviewCardProps) {
  const labsMax = maxPoints * (labsWeight / 100);
  const labsPerWork = labsCount > 0 ? labsMax / labsCount : 0;
  const attendanceMax = maxPoints * (attendanceWeight / 100);
  const reserveMax = maxPoints * (activityReserve / 100);
  
  // Расчёт штрафов за посещаемость (на примере N занятий)
  const pointsPerLesson = exampleLessonsCount > 0 ? attendanceMax / exampleLessonsCount : 0;
  const absentPenalty = pointsPerLesson; // За прогул теряется весь балл за занятие
  const latePenalty = pointsPerLesson * (1 - lateCoef); // За опоздание теряется часть

  const rows = [
    {
      component: `Лабораторные (${labsCount})`,
      weight: `${labsWeight}%`,
      max: labsMax.toFixed(2),
      perUnit: `${labsPerWork.toFixed(2)} за 5`,
    },
    {
      component: 'Посещаемость',
      weight: `${attendanceWeight}%`,
      max: attendanceMax.toFixed(2),
      perUnit: `−${absentPenalty.toFixed(2)} за прогул, −${latePenalty.toFixed(2)} за опозд.`,
    },
    {
      component: 'Резерв (активность)',
      weight: `${activityReserve}%`,
      max: reserveMax.toFixed(2),
      perUnit: 'бонусы/штрафы',
    },
  ];

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-lg">
          <Calculator className="w-5 h-5 text-purple-500" />
          Превью баллов
        </CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Компонент</TableHead>
              <TableHead className="text-right">Вес</TableHead>
              <TableHead className="text-right">Макс</TableHead>
              <TableHead className="text-right">За единицу</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.map((row) => (
              <TableRow key={row.component}>
                <TableCell className="font-medium">{row.component}</TableCell>
                <TableCell className="text-right">{row.weight}</TableCell>
                <TableCell className="text-right font-mono">{row.max}</TableCell>
                <TableCell className="text-right text-muted-foreground">{row.perUnit}</TableCell>
              </TableRow>
            ))}
            <TableRow className="font-bold">
              <TableCell>ИТОГО</TableCell>
              <TableCell className={`text-right ${Math.abs(totalWeight - 100) < 0.01 ? '' : 'text-red-500'}`}>
                {totalWeight.toFixed(0)}%
              </TableCell>
              <TableCell className="text-right font-mono">{maxPoints.toFixed(2)}</TableCell>
              <TableCell></TableCell>
            </TableRow>
          </TableBody>
        </Table>

        <div className="mt-4 p-3 bg-muted/50 rounded-lg text-sm space-y-1">
          <p className="font-medium">Баллы за оценки (за одну лабу):</p>
          <div className="grid grid-cols-4 gap-2 text-center">
            <div className="p-2 bg-green-500/10 rounded">
              <div className="font-bold text-green-600">5</div>
              <div className="text-xs">{labsPerWork.toFixed(2)} б.</div>
            </div>
            <div className="p-2 bg-blue-500/10 rounded">
              <div className="font-bold text-blue-600">4</div>
              <div className="text-xs">{(labsPerWork * grade4Coef).toFixed(2)} б.</div>
            </div>
            <div className="p-2 bg-yellow-500/10 rounded">
              <div className="font-bold text-yellow-600">3</div>
              <div className="text-xs">{(labsPerWork * grade3Coef).toFixed(2)} б.</div>
            </div>
            <div className="p-2 bg-red-500/10 rounded">
              <div className="font-bold text-red-600">2</div>
              <div className="text-xs">0 б.</div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
