'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { FlaskConical } from 'lucide-react';

interface LabsConfig {
  labs_weight: number;
  required_labs_count: number;
  grade_5_points: number;
  grade_4_points: number;
  grade_3_points: number;
  grade_2_points: number;
  late_max_grade: number;
  very_late_max_grade: number;
  late_threshold_days: number;
}

interface Props {
  config: LabsConfig;
  onChange: <K extends keyof LabsConfig>(key: K, value: LabsConfig[K]) => void;
}

export function LabsSettingsNew({ config, onChange }: Props) {
  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-lg">
          <FlaskConical className="w-5 h-5 text-purple-500" />
          Лабораторные работы
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label>Вес (%)</Label>
            <Input type="number" value={config.labs_weight} 
              onChange={e => onChange('labs_weight', Number(e.target.value))} />
          </div>
          <div>
            <Label>Мин. кол-во лаб</Label>
            <Input type="number" value={config.required_labs_count}
              onChange={e => onChange('required_labs_count', Number(e.target.value))} />
          </div>
        </div>
        
        <div className="border-t pt-4">
          <p className="text-sm font-medium mb-2">Баллы за оценки</p>
          <div className="grid grid-cols-4 gap-2">
            <div>
              <Label className="text-xs">За 5</Label>
              <Input type="number" step="0.1" value={config.grade_5_points}
                onChange={e => onChange('grade_5_points', Number(e.target.value))} />
            </div>
            <div>
              <Label className="text-xs">За 4</Label>
              <Input type="number" step="0.1" value={config.grade_4_points}
                onChange={e => onChange('grade_4_points', Number(e.target.value))} />
            </div>
            <div>
              <Label className="text-xs">За 3</Label>
              <Input type="number" step="0.1" value={config.grade_3_points}
                onChange={e => onChange('grade_3_points', Number(e.target.value))} />
            </div>
            <div>
              <Label className="text-xs">За 2</Label>
              <Input type="number" step="0.1" value={config.grade_2_points}
                onChange={e => onChange('grade_2_points', Number(e.target.value))} />
            </div>
          </div>
        </div>

        <div className="border-t pt-4">
          <p className="text-sm font-medium mb-2">Ограничение оценки при просрочке</p>
          <div className="grid grid-cols-3 gap-2">
            <div>
              <Label className="text-xs">Макс при просрочке</Label>
              <Input type="number" min={2} max={5} value={config.late_max_grade}
                onChange={e => onChange('late_max_grade', Number(e.target.value))} />
            </div>
            <div>
              <Label className="text-xs">Макс при сильной</Label>
              <Input type="number" min={2} max={5} value={config.very_late_max_grade}
                onChange={e => onChange('very_late_max_grade', Number(e.target.value))} />
            </div>
            <div>
              <Label className="text-xs">Граница (дней)</Label>
              <Input type="number" value={config.late_threshold_days}
                onChange={e => onChange('late_threshold_days', Number(e.target.value))} />
            </div>
          </div>
          <p className="text-xs text-muted-foreground mt-1">
            Просрочил ≤{config.late_threshold_days} дней → макс {config.late_max_grade}, больше → макс {config.very_late_max_grade}
          </p>
        </div>
      </CardContent>
    </Card>
  );
}