'use client';

import Link from 'next/link';
import { AlertTriangle, FlaskConical } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import type { AttestationFormState } from './types';

interface LabsSettingsCardProps {
  form: AttestationFormState;
  totalLabsCount: number;
  secondTotalLabsCount: number;
  automaticExtraLabsCount: number;
  onUpdate: <K extends keyof AttestationFormState>(key: K, value: AttestationFormState[K]) => void;
}

export function LabsSettingsCard({
  form,
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
        <div className="flex flex-col gap-3 rounded-lg border border-amber-500/30 bg-amber-500/10 p-3 text-sm text-amber-700 dark:text-amber-300 md:flex-row md:items-center md:justify-between">
          <div className="flex gap-3">
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
            <div>
              <div className="font-medium">Пороги лабораторных теперь настраиваются по связке</div>
              <div className="text-xs opacity-90">
                Здесь остаются вес лабораторного блока и коэффициенты оценок. Количество лаб, допуск и автомат правятся в группе / предмете / семестре.
              </div>
            </div>
          </div>
          <Button asChild size="sm" variant="outline" className="shrink-0 bg-background/70">
            <Link href="/admin/labs">Открыть раздел лабораторных</Link>
          </Button>
        </div>
        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <Label>Вес (%)</Label>
            <div className="flex items-center gap-2">
              <Slider value={[form.labs_weight]} onValueChange={([v]) => onUpdate('labs_weight', v)} max={100} step={1} />
              <span className="w-12 text-right font-mono">{form.labs_weight}%</span>
            </div>
          </div>
          <div>
            <Label htmlFor="legacy_total_labs">Всего лаб в семестре</Label>
            <Input id="legacy_total_labs" type="number" value={totalLabsCount} readOnly className="bg-muted" />
            <p className="mt-1 text-xs text-muted-foreground">
              Legacy fallback. Активное значение берётся из policy выбранной связки.
            </p>
          </div>
        </div>
        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <Label htmlFor="legacy_labs_count_first">Кол-во для 1-й атт.</Label>
            <Input
              id="legacy_labs_count_first"
              type="number"
              value={form.labs_count_first}
              min={1}
              max={totalLabsCount}
              readOnly
              className="bg-muted"
            />
            <p className="mt-1 text-xs text-muted-foreground">
              Legacy-порог. Для активного изменения откройте настройки связок.
            </p>
          </div>
          <div>
            <Label htmlFor="legacy_labs_count_second">Доп. лаб ко 2-й атт.</Label>
            <Input
              id="legacy_labs_count_second"
              type="number"
              value={form.labs_count_second}
              min={0}
              max={Math.max(totalLabsCount - form.labs_count_first, 0)}
              readOnly
              className="bg-muted"
            />
            <p className="mt-1 text-xs text-muted-foreground">
              Legacy-порог. Новая policy хранит суммарный порог 2-й аттестации по связке.
            </p>
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
          Legacy fallback: {form.labs_count_first} к 1-й аттестации, ещё {form.labs_count_second} ко 2-й,
          суммарно {secondTotalLabsCount}. Для активных предметных требований используйте policy связки.
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
