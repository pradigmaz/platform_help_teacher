'use client';

import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Slider } from '@/components/ui/slider';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { TestsComponentConfig } from '@/types/attestation';

interface TestsSettingsProps {
  config: TestsComponentConfig;
  onChange: (config: TestsComponentConfig) => void;
}

export function TestsSettings({ config, onChange }: TestsSettingsProps) {
  const update = <K extends keyof TestsComponentConfig>(key: K, value: TestsComponentConfig[K]) => {
    onChange({ ...config, [key]: value });
  };

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
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
        <div className="space-y-2">
          <Label>Минимум тестов</Label>
          <Input
            type="number"
            min={1}
            max={20}
            value={config.required_count}
            onChange={(e) => update('required_count', parseInt(e.target.value) || 1)}
          />
        </div>
      </div>

      <div className="pt-4 border-t space-y-4">
        <div className="flex items-center justify-between">
          <Label>Разрешить пересдачи</Label>
          <Switch
            checked={config.allow_retakes}
            onCheckedChange={(v) => update('allow_retakes', v)}
          />
        </div>

        {config.allow_retakes && (
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label className="text-xs">Макс. пересдач</Label>
              <Input
                type="number"
                min={1}
                max={5}
                value={config.max_retakes}
                onChange={(e) => update('max_retakes', parseInt(e.target.value) || 1)}
              />
            </div>
            <div className="space-y-2">
              <Label className="text-xs">Штраф за пересдачу</Label>
              <div className="flex items-center gap-2">
                <Slider
                  value={[config.retake_penalty * 100]}
                  onValueChange={([v]) => update('retake_penalty', v / 100)}
                  min={0}
                  max={50}
                  step={5}
                />
                <Badge variant="outline" className="w-14 justify-center">
                  {(config.retake_penalty * 100).toFixed(0)}%
                </Badge>
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="pt-4 border-t space-y-2">
        <Label>Учитывать лучшие N тестов</Label>
        <div className="flex items-center gap-2">
          <Switch
            checked={config.best_n_count !== null}
            onCheckedChange={(v) => update('best_n_count', v ? 3 : null)}
          />
          {config.best_n_count !== null && (
            <Input
              type="number"
              min={1}
              max={10}
              value={config.best_n_count}
              onChange={(e) => update('best_n_count', parseInt(e.target.value) || 1)}
              className="w-20"
            />
          )}
        </div>
      </div>
    </div>
  );
}
