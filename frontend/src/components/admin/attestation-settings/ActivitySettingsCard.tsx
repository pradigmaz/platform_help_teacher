'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { Switch } from '@/components/ui/switch';
import { Zap } from 'lucide-react';
import type { AttestationFormState } from './types';

interface ActivitySettingsCardProps {
  form: AttestationFormState;
  onUpdate: <K extends keyof AttestationFormState>(key: K, value: AttestationFormState[K]) => void;
}

export function ActivitySettingsCard({ form, onUpdate }: ActivitySettingsCardProps) {
  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-lg">
          <Zap className="w-5 h-5 text-yellow-500" />
          Резерв для активности
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <Label>Резерв (%)</Label>
          <div className="flex items-center gap-2">
            <Slider value={[form.activity_reserve]} onValueChange={([v]) => onUpdate('activity_reserve', v)} max={30} step={1} />
            <span className="w-12 text-right font-mono">{form.activity_reserve}%</span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Switch checked={form.activity_enabled} onCheckedChange={v => onUpdate('activity_enabled', v)} />
          <Label>Включить активность</Label>
        </div>
        <div className="text-xs text-muted-foreground space-y-1">
          <p>• Бонусы ограничены резервом и макс баллами</p>
          <p>• Штрафы без ограничений</p>
          <p>• Если студент набрал макс — бонусы заблокированы</p>
        </div>
      </CardContent>
    </Card>
  );
}
