'use client';

import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Slider } from '@/components/ui/slider';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { AttendanceComponentConfig } from '@/types/attestation';

interface AttendanceSettingsProps {
  config: AttendanceComponentConfig;
  onChange: (config: AttendanceComponentConfig) => void;
}

export function AttendanceSettings({ config, onChange }: AttendanceSettingsProps) {
  const update = <K extends keyof AttendanceComponentConfig>(key: K, value: AttendanceComponentConfig[K]) => {
    onChange({ ...config, [key]: value });
  };

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <Label>Режим начисления</Label>
        <RadioGroup
          value={config.mode}
          onValueChange={(v) => update('mode', v as 'per_class' | 'percentage')}
        >
          <div className="flex items-center space-x-2">
            <RadioGroupItem value="per_class" id="per_class" />
            <Label htmlFor="per_class" className="font-normal">За каждое занятие</Label>
          </div>
          <div className="flex items-center space-x-2">
            <RadioGroupItem value="percentage" id="percentage" />
            <Label htmlFor="percentage" className="font-normal">Процент посещений</Label>
          </div>
        </RadioGroup>
      </div>

      {config.mode === 'per_class' && (
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label>Баллов за занятие</Label>
            <Input
              type="number"
              step={0.1}
              min={0}
              max={5}
              value={config.points_per_class}
              onChange={(e) => update('points_per_class', parseFloat(e.target.value) || 0)}
            />
          </div>
          <div className="space-y-2">
            <Label>Макс. баллов</Label>
            <Input
              type="number"
              min={1}
              max={50}
              value={config.max_points}
              onChange={(e) => update('max_points', parseInt(e.target.value) || 1)}
            />
          </div>
        </div>
      )}

      {config.mode === 'percentage' && (
        <div className="space-y-2">
          <Label>Макс. баллов (при 100% посещений)</Label>
          <Input
            type="number"
            min={1}
            max={50}
            value={config.max_points}
            onChange={(e) => update('max_points', parseInt(e.target.value) || 1)}
          />
        </div>
      )}

      <div className="pt-4 border-t space-y-4">
        <div className="flex items-center justify-between">
          <Label>Штраф за пропуски</Label>
          <Switch
            checked={config.penalty_enabled}
            onCheckedChange={(v) => update('penalty_enabled', v)}
          />
        </div>

        {config.penalty_enabled && (
          <div className="space-y-2">
            <Label className="text-xs">Штраф за пропуск</Label>
            <div className="flex items-center gap-2">
              <Slider
                value={[config.penalty_per_absence]}
                onValueChange={([v]) => update('penalty_per_absence', v)}
                min={0}
                max={5}
                step={0.5}
              />
              <Badge variant="outline" className="w-14 justify-center">
                {config.penalty_per_absence}
              </Badge>
            </div>
          </div>
        )}
      </div>

      <div className="pt-4 border-t">
        <div className="flex items-center justify-between">
          <Label>Уважительные пропуски учитываются</Label>
          <Switch
            checked={config.excused_absence_counts}
            onCheckedChange={(v) => update('excused_absence_counts', v)}
          />
        </div>
      </div>
    </div>
  );
}
