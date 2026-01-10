'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { Clock } from 'lucide-react';
import type { AttestationFormState } from './types';

interface AttendanceSettingsCardProps {
  form: AttestationFormState;
  onUpdate: <K extends keyof AttestationFormState>(key: K, value: AttestationFormState[K]) => void;
}

export function AttendanceSettingsCard({ form, onUpdate }: AttendanceSettingsCardProps) {
  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-lg">
          <Clock className="w-5 h-5 text-green-500" />
          Посещаемость
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <Label>Вес (%)</Label>
          <div className="flex items-center gap-2">
            <Slider value={[form.attendance_weight]} onValueChange={([v]) => onUpdate('attendance_weight', v)} max={100} step={1} />
            <span className="w-12 text-right font-mono">{form.attendance_weight}%</span>
          </div>
        </div>
        <div>
          <Label>Баллы за опоздание (% от присутствия)</Label>
          <div className="flex items-center gap-2">
            <Slider value={[form.late_coef * 100]} onValueChange={([v]) => onUpdate('late_coef', v / 100)} max={100} step={5} />
            <span className="w-12 text-right font-mono">{(form.late_coef * 100).toFixed(0)}%</span>
          </div>
          <p className="text-xs text-muted-foreground mt-1">
            Опоздание = {(form.late_coef * 100).toFixed(0)}% от баллов за присутствие
          </p>
        </div>
        <div>
          <Label>Штраф за прогул (% от присутствия)</Label>
          <div className="flex items-center gap-2">
            <Slider value={[Math.abs(form.absent_coef) * 100]} onValueChange={([v]) => onUpdate('absent_coef', -v / 100)} max={100} step={5} />
            <span className="w-12 text-right font-mono text-red-500">{form.absent_coef === 0 ? '0%' : `${(form.absent_coef * 100).toFixed(0)}%`}</span>
          </div>
          <p className="text-xs text-muted-foreground mt-1">
            {form.absent_coef === 0 && 'Прогул = 0 баллов (без штрафа)'}
            {form.absent_coef < 0 && `Прогул = ${(form.absent_coef * 100).toFixed(0)}% от присутствия (штраф)`}
          </p>
        </div>
        <p className="text-xs text-muted-foreground">Кол-во занятий определяется автоматически из расписания</p>
      </CardContent>
    </Card>
  );
}
