'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { FlaskConical } from 'lucide-react';
import type { AttestationFormState } from './types';

interface LabsSettingsCardProps {
  form: AttestationFormState;
  attestationType: 'first' | 'second';
  onUpdate: <K extends keyof AttestationFormState>(key: K, value: AttestationFormState[K]) => void;
}

export function LabsSettingsCard({ form, attestationType, onUpdate }: LabsSettingsCardProps) {
  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-lg">
          <FlaskConical className="w-5 h-5 text-blue-500" />
          Лабораторные работы
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label>Вес (%)</Label>
            <div className="flex items-center gap-2">
              <Slider value={[form.labs_weight]} onValueChange={([v]) => onUpdate('labs_weight', v)} max={100} step={1} />
              <span className="w-12 text-right font-mono">{form.labs_weight}%</span>
            </div>
          </div>
          <div>
            <Label>Кол-во для 1-й атт.</Label>
            <Input type="number" value={form.labs_count_first} onChange={e => onUpdate('labs_count_first', +e.target.value)} min={1} max={20} />
          </div>
        </div>
        {attestationType === 'second' && (
          <div>
            <Label>Доп. лаб для 2-й атт.</Label>
            <Input type="number" value={form.labs_count_second} onChange={e => onUpdate('labs_count_second', +e.target.value)} min={0} max={20} />
          </div>
        )}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label>Коэф. оценки 4</Label>
            <div className="flex items-center gap-2">
              <Slider value={[form.grade_4_coef * 100]} onValueChange={([v]) => onUpdate('grade_4_coef', v / 100)} max={100} step={1} />
              <span className="w-12 text-right font-mono">{(form.grade_4_coef * 100).toFixed(0)}%</span>
            </div>
          </div>
          <div>
            <Label>Коэф. оценки 3</Label>
            <div className="flex items-center gap-2">
              <Slider value={[form.grade_3_coef * 100]} onValueChange={([v]) => onUpdate('grade_3_coef', v / 100)} max={100} step={1} />
              <span className="w-12 text-right font-mono">{(form.grade_3_coef * 100).toFixed(0)}%</span>
            </div>
          </div>
        </div>
        <p className="text-xs text-muted-foreground">Оценка 5 = 100% (фикс), Оценка 2 = 0% (работа не засчитана)</p>
      </CardContent>
    </Card>
  );
}
