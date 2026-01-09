'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Users, Info } from 'lucide-react';

interface AttendanceConfig {
  attendance_weight: number;
  present_points: number;
  late_points: number;
  absent_points: number;
}

interface Props {
  config: AttendanceConfig;
  onChange: <K extends keyof AttendanceConfig>(key: K, value: AttendanceConfig[K]) => void;
}

export function AttendanceSettingsNew({ config, onChange }: Props) {
  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-lg">
          <Users className="w-5 h-5 text-blue-500" />
          Посещаемость
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <Label>Вес (%)</Label>
          <Input type="number" value={config.attendance_weight}
            onChange={e => onChange('attendance_weight', Number(e.target.value))} />
        </div>
        
        <div className="border-t pt-4">
          <p className="text-sm font-medium mb-2">Баллы за статусы</p>
          <div className="grid grid-cols-3 gap-2">
            <div>
              <Label className="text-xs">Присутствие</Label>
              <Input type="number" step="0.1" value={config.present_points}
                onChange={e => onChange('present_points', Number(e.target.value))} />
            </div>
            <div>
              <Label className="text-xs">Опоздание</Label>
              <Input type="number" step="0.1" value={config.late_points}
                onChange={e => onChange('late_points', Number(e.target.value))} />
            </div>
            <div>
              <Label className="text-xs">Отсутствие</Label>
              <Input type="number" step="0.1" value={config.absent_points}
                onChange={e => onChange('absent_points', Number(e.target.value))} />
            </div>
          </div>
        </div>

        <div className="flex items-start gap-2 p-3 bg-blue-500/10 rounded-md">
          <Info className="w-4 h-4 text-blue-500 mt-0.5" />
          <p className="text-xs text-muted-foreground">
            <strong>Уважительная причина (EXCUSED)</strong> не учитывается — занятие как будто не было.
            Это справедливо для студентов с уважительными пропусками.
          </p>
        </div>
      </CardContent>
    </Card>
  );
}