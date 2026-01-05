'use client';

import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Slider } from '@/components/ui/slider';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { ActivityComponentConfig } from '@/types/attestation';

interface ActivitySettingsProps {
  config: ActivityComponentConfig;
  onChange: (config: ActivityComponentConfig) => void;
}

export function ActivitySettings({ config, onChange }: ActivitySettingsProps) {
  const update = <K extends keyof ActivityComponentConfig>(key: K, value: ActivityComponentConfig[K]) => {
    onChange({ ...config, [key]: value });
  };

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
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
        <div className="space-y-2">
          <Label>Баллов за активность</Label>
          <Input
            type="number"
            step={0.5}
            min={0.5}
            max={10}
            value={config.points_per_activity}
            onChange={(e) => update('points_per_activity', parseFloat(e.target.value) || 1)}
          />
        </div>
      </div>

      <div className="pt-4 border-t space-y-4">
        <div className="flex items-center justify-between">
          <Label>Разрешить отрицательные баллы</Label>
          <Switch
            checked={config.allow_negative}
            onCheckedChange={(v) => update('allow_negative', v)}
          />
        </div>

        {config.allow_negative && (
          <div className="space-y-2">
            <Label className="text-xs">Лимит отрицательных</Label>
            <div className="flex items-center gap-2">
              <Slider
                value={[config.negative_limit]}
                onValueChange={([v]) => update('negative_limit', v)}
                min={1}
                max={20}
                step={1}
              />
              <Badge variant="outline" className="w-14 justify-center">
                -{config.negative_limit}
              </Badge>
            </div>
          </div>
        )}
      </div>

      <div className="pt-4 border-t">
        <div className="flex items-center justify-between">
          <Label>Категории активностей</Label>
          <Switch
            checked={config.categories_enabled}
            onCheckedChange={(v) => update('categories_enabled', v)}
          />
        </div>
        {config.categories_enabled && (
          <p className="text-xs text-muted-foreground mt-2">
            Категории настраиваются в разделе «Типы активностей»
          </p>
        )}
      </div>
    </div>
  );
}
