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
  totalLabsCount: number;
  secondTotalLabsCount: number;
  automaticExtraLabsCount: number;
  onUpdate: <K extends keyof AttestationFormState>(key: K, value: AttestationFormState[K]) => void;
}

export function LabsSettingsCard({
  form,
  attestationType,
  totalLabsCount,
  secondTotalLabsCount,
  automaticExtraLabsCount,
  onUpdate,
}: LabsSettingsCardProps) {
  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-lg">
          <FlaskConical className="w-5 h-5 text-blue-500" />
          Лабораторные работы
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <Label>Вес (%)</Label>
            <div className="flex items-center gap-2">
              <Slider value={[form.labs_weight]} onValueChange={([v]) => onUpdate('labs_weight', v)} max={100} step={1} />
              <span className="w-12 text-right font-mono">{form.labs_weight}%</span>
            </div>
          </div>
          <div>
            <Label>Всего лаб в семестре</Label>
            <Input type="number" value={totalLabsCount} readOnly className="bg-muted" />
            <p className="mt-1 text-xs text-muted-foreground">
              Значение приходит из глобальных настроек лабораторных.
            </p>
          </div>
        </div>
        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <Label>Кол-во для 1-й атт.</Label>
            <Input
              type="number"
              value={form.labs_count_first}
              onChange={e => onUpdate('labs_count_first', +e.target.value)}
              min={1}
              max={totalLabsCount}
              readOnly={attestationType === 'second'}
              className={attestationType === 'second' ? 'bg-muted' : undefined}
            />
            {attestationType === 'second' && (
              <p className="mt-1 text-xs text-muted-foreground">
                Порог 1-й аттестации редактируется на вкладке «1-я аттестация».
              </p>
            )}
          </div>
          <div>
            <Label>Доп. лаб ко 2-й атт.</Label>
            <Input
              type="number"
              value={form.labs_count_second}
              onChange={e => onUpdate('labs_count_second', +e.target.value)}
              min={0}
              max={Math.max(totalLabsCount - form.labs_count_first, 0)}
              readOnly={attestationType === 'first'}
              className={attestationType === 'first' ? 'bg-muted' : undefined}
            />
            {attestationType === 'first' && (
              <p className="mt-1 text-xs text-muted-foreground">
                Доп. лабы ко 2-й аттестации редактируются на вкладке «2-я аттестация».
              </p>
            )}
          </div>
        </div>
        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <Label>Суммарно ко 2-й атт.</Label>
            <Input type="number" value={secondTotalLabsCount} readOnly className="bg-muted" />
          </div>
          <div>
            <Label>Ещё для автомата</Label>
            <Input type="number" value={automaticExtraLabsCount} readOnly className="bg-muted" />
          </div>
        </div>
        <p className="text-xs text-muted-foreground">
          Сейчас логика такая: {form.labs_count_first} к 1-й аттестации, ещё {form.labs_count_second} ко 2-й,
          суммарно {secondTotalLabsCount}. Для автомата нужно добрать ещё {automaticExtraLabsCount} из общего total {totalLabsCount}.
        </p>
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
