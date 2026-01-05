'use client';

import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Slider } from '@/components/ui/slider';
import { Badge } from '@/components/ui/badge';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { LabsComponentConfig } from '@/types/attestation';

interface LabsSettingsProps {
  config: LabsComponentConfig;
  onChange: (config: LabsComponentConfig) => void;
}

export function LabsSettings({ config, onChange }: LabsSettingsProps) {
  const update = <K extends keyof LabsComponentConfig>(key: K, value: LabsComponentConfig[K]) => {
    onChange({ ...config, [key]: value });
  };

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label>Режим оценки</Label>
          <RadioGroup
            value={config.grading_mode}
            onValueChange={(v) => update('grading_mode', v as 'binary' | 'graded')}
          >
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="binary" id="binary" />
              <Label htmlFor="binary" className="font-normal">Факт сдачи</Label>
            </div>
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="graded" id="graded" />
              <Label htmlFor="graded" className="font-normal">Учёт оценок</Label>
            </div>
          </RadioGroup>
        </div>

        {config.grading_mode === 'graded' && (
          <div className="space-y-2">
            <Label>Шкала оценок</Label>
            <Select
              value={String(config.grading_scale)}
              onValueChange={(v) => update('grading_scale', Number(v) as 5 | 10 | 100)}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="5">5-балльная</SelectItem>
                <SelectItem value="10">10-балльная</SelectItem>
                <SelectItem value="100">100-балльная</SelectItem>
              </SelectContent>
            </Select>
          </div>
        )}
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label>Минимум лабораторных</Label>
          <Input
            type="number"
            min={1}
            max={20}
            value={config.required_count}
            onChange={(e) => update('required_count', parseInt(e.target.value) || 1)}
          />
        </div>
        <div className="space-y-2">
          <Label>Бонус за доп. лабу</Label>
          <Input
            type="number"
            step={0.1}
            min={0}
            max={5}
            value={config.bonus_per_extra}
            onChange={(e) => update('bonus_per_extra', parseFloat(e.target.value) || 0)}
          />
        </div>
      </div>

      <div className="pt-4 border-t space-y-4">
        <Label className="text-sm font-medium">Дедлайны</Label>
        <div className="grid grid-cols-3 gap-4">
          <div className="space-y-2">
            <Label className="text-xs">Мягкий (дней)</Label>
            <Input
              type="number"
              min={1}
              max={30}
              value={config.soft_deadline_days}
              onChange={(e) => update('soft_deadline_days', parseInt(e.target.value) || 7)}
            />
          </div>
          <div className="space-y-2">
            <Label className="text-xs">Коэфф. мягкого</Label>
            <div className="flex items-center gap-2">
              <Slider
                value={[config.soft_deadline_penalty * 100]}
                onValueChange={([v]) => update('soft_deadline_penalty', v / 100)}
                min={0}
                max={100}
                step={5}
              />
              <Badge variant="outline" className="w-14 justify-center">
                {(config.soft_deadline_penalty * 100).toFixed(0)}%
              </Badge>
            </div>
          </div>
          <div className="space-y-2">
            <Label className="text-xs">Коэфф. жёсткого</Label>
            <div className="flex items-center gap-2">
              <Slider
                value={[config.hard_deadline_penalty * 100]}
                onValueChange={([v]) => update('hard_deadline_penalty', v / 100)}
                min={0}
                max={100}
                step={5}
              />
              <Badge variant="outline" className="w-14 justify-center">
                {(config.hard_deadline_penalty * 100).toFixed(0)}%
              </Badge>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
