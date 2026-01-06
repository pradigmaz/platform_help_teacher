'use client';

import { useState, useMemo } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { BlurFade } from '@/components/ui/blur-fade';
import { Sparkles } from '@/components/ui/sparkles';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Save, 
  RotateCcw, 
  FlaskConical, 
  Users, 
  FileText,
  Star,
  Award,
  Info
} from 'lucide-react';
import { toast } from 'sonner';
import { AttestationType } from '@/lib/api';
import { BorderBeam } from '@/components/ui/border-beam';
import { NumberTicker } from '@/components/ui/number-ticker';
import { cn } from '@/lib/utils';
import { TooltipProvider } from "@/components/ui/tooltip";
import { ComponentToggle } from './ComponentToggle';
import { GradeScaleCard } from './GradeScaleCard';
import { 
  LabsSettings, 
  TestsSettings, 
  AttendanceSettings, 
  ActivitySettings 
} from './settings';
import { 
  ComponentsConfig, 
  DEFAULT_COMPONENTS_CONFIG,
  LabsComponentConfig,
  TestsComponentConfig,
  AttendanceComponentConfig,
  ActivityComponentConfig
} from '@/types/attestation';

export function AttestationSettingsForm() {
  const [attestationType, setAttestationType] = useState<AttestationType>('first');
  const [config, setConfig] = useState<ComponentsConfig>(DEFAULT_COMPONENTS_CONFIG);
  const [saving, setSaving] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);

  const totalWeight = useMemo(() => {
    return Object.values(config)
      .filter(c => c.enabled)
      .reduce((sum, c) => sum + c.weight, 0);
  }, [config]);

  const isWeightValid = Math.abs(totalWeight - 100) < 0.01;

  const maxPoints = attestationType === 'first' ? 35 : 70;
  const minPassing = attestationType === 'first' ? 20 : 40;

  const updateComponent = <K extends keyof ComponentsConfig>(
    key: K, 
    value: Partial<ComponentsConfig[K]>
  ) => {
    setConfig(prev => ({
      ...prev,
      [key]: { ...prev[key], ...value }
    }));
    setHasChanges(true);
  };

  const handleSave = async () => {
    if (!isWeightValid) {
      toast.error(`Сумма весов должна быть 100%. Текущая: ${totalWeight.toFixed(1)}%`);
      return;
    }

    setSaving(true);
    try {
      // TODO: API call to save config
      // await AttestationAPI.updateComponentsConfig(attestationType, config);
      setHasChanges(false);
      toast.success('Настройки сохранены');
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : 'Ошибка сохранения';
      toast.error(message);
    } finally {
      setSaving(false);
    }
  };

  const handleReset = () => {
    setConfig(DEFAULT_COMPONENTS_CONFIG);
    setHasChanges(false);
  };

  return (
    <TooltipProvider>
      <div className="space-y-6">
        {/* Header */}
        <BlurFade delay={0.1}>
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div>
              <h2 className="text-2xl font-bold flex items-center gap-2">
                <Sparkles color="#8b5cf6">
                  <Award className="w-6 h-6 text-primary" />
                </Sparkles>
                Настройки аттестации
              </h2>
              <p className="text-muted-foreground">Глобальные настройки для всех групп</p>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" onClick={handleReset} disabled={!hasChanges || saving}>
                <RotateCcw className="w-4 h-4 mr-2" />
                Сбросить
              </Button>
              <Button 
                onClick={handleSave} 
                disabled={!hasChanges || saving || !isWeightValid} 
                className="bg-gradient-to-r from-primary to-purple-600 hover:from-primary/90 hover:to-purple-600/90"
              >
                <Save className="w-4 h-4 mr-2" />
                {saving ? 'Сохранение...' : 'Сохранить'}
              </Button>
            </div>
          </div>
        </BlurFade>

        {/* Attestation Type Tabs */}
        <BlurFade delay={0.15}>
          <Tabs value={attestationType} onValueChange={(v) => setAttestationType(v as AttestationType)}>
            <TabsList className="grid w-full max-w-md grid-cols-2">
              <TabsTrigger value="first" className="flex items-center gap-2">
                <Badge variant="outline" className="bg-blue-500/10 border-blue-500/30">1</Badge>
                1-я аттестация (35 б.)
              </TabsTrigger>
              <TabsTrigger value="second" className="flex items-center gap-2">
                <Badge variant="outline" className="bg-purple-500/10 border-purple-500/30">2</Badge>
                2-я аттестация (70 б.)
              </TabsTrigger>
            </TabsList>
          </Tabs>
        </BlurFade>

        {/* Grade Scale */}
        <BlurFade delay={0.2}>
          <GradeScaleCard attestationType={attestationType} />
        </BlurFade>

        {/* Period Dates */}
        <BlurFade delay={0.22}>
          <Card>
            <CardContent className="pt-4">
              <div className="flex items-center gap-2 mb-4">
                <Info className="w-4 h-4 text-blue-500" />
                <span className="font-medium">Период аттестации</span>
                <span className="text-sm text-muted-foreground">(для фильтрации посещаемости)</span>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm text-muted-foreground">Начало периода</label>
                  <input 
                    type="date" 
                    className="w-full mt-1 px-3 py-2 border rounded-md bg-background"
                    placeholder="Начало"
                  />
                </div>
                <div>
                  <label className="text-sm text-muted-foreground">Конец периода</label>
                  <input 
                    type="date" 
                    className="w-full mt-1 px-3 py-2 border rounded-md bg-background"
                    placeholder="Конец"
                  />
                </div>
              </div>
              <p className="text-xs text-muted-foreground mt-2">
                Если не указано, учитывается вся посещаемость за семестр
              </p>
            </CardContent>
          </Card>
        </BlurFade>

        {/* Weight Summary */}
        <BlurFade delay={0.25}>
          <Card className="relative overflow-hidden bg-gradient-to-r from-background via-background to-primary/5">
            <BorderBeam size={200} duration={10} />
            <CardContent className="pt-4">
              <div className="flex flex-wrap items-center gap-4 text-sm">
                <span className="font-medium flex items-center gap-2">
                  <Info className="w-4 h-4 text-blue-500" />
                  Фиксированные значения:
                </span>
                <Badge variant="outline" className="bg-green-500/10 border-green-500/30">
                  Макс: <NumberTicker value={maxPoints} /> баллов
                </Badge>
                <Badge variant="outline" className="bg-yellow-500/10 border-yellow-500/30">
                  Мин. для зачёта: <NumberTicker value={minPassing} /> баллов
                </Badge>
                <Badge 
                  variant="outline" 
                  className={cn(
                    isWeightValid 
                      ? "bg-green-500/10 border-green-500/30 text-green-600" 
                      : "bg-red-500/10 border-red-500/30 text-red-600"
                  )}
                >
                  Сумма весов: {totalWeight.toFixed(0)}% {isWeightValid ? '✓' : '(нужно 100%)'}
                </Badge>
              </div>
            </CardContent>
          </Card>
        </BlurFade>

        {/* Components */}
        <BlurFade delay={0.3}>
          <div className="space-y-4">
            <ComponentToggle
              title="Лабораторные работы"
              icon={FlaskConical}
              enabled={config.labs.enabled}
              weight={config.labs.weight}
              onToggle={(enabled) => updateComponent('labs', { enabled })}
              onWeightChange={(weight) => updateComponent('labs', { weight })}
              color="#8b5cf6"
            >
              <LabsSettings
                config={config.labs}
                onChange={(labs: LabsComponentConfig) => setConfig(prev => ({ ...prev, labs }))}
              />
            </ComponentToggle>

            <ComponentToggle
              title="Контрольные работы"
              icon={FileText}
              enabled={config.tests.enabled}
              weight={config.tests.weight}
              onToggle={(enabled) => updateComponent('tests', { enabled })}
              onWeightChange={(weight) => updateComponent('tests', { weight })}
              color="#f59e0b"
            >
              <TestsSettings
                config={config.tests}
                onChange={(tests: TestsComponentConfig) => setConfig(prev => ({ ...prev, tests }))}
              />
            </ComponentToggle>

            <ComponentToggle
              title="Посещаемость"
              icon={Users}
              enabled={config.attendance.enabled}
              weight={config.attendance.weight}
              onToggle={(enabled) => updateComponent('attendance', { enabled })}
              onWeightChange={(weight) => updateComponent('attendance', { weight })}
              color="#3b82f6"
            >
              <AttendanceSettings
                config={config.attendance}
                onChange={(attendance: AttendanceComponentConfig) => setConfig(prev => ({ ...prev, attendance }))}
              />
            </ComponentToggle>

            <ComponentToggle
              title="Активность"
              icon={Star}
              enabled={config.activity.enabled}
              weight={config.activity.weight}
              onToggle={(enabled) => updateComponent('activity', { enabled })}
              onWeightChange={(weight) => updateComponent('activity', { weight })}
              color="#22c55e"
            >
              <ActivitySettings
                config={config.activity}
                onChange={(activity: ActivityComponentConfig) => setConfig(prev => ({ ...prev, activity }))}
              />
            </ComponentToggle>
          </div>
        </BlurFade>
      </div>
    </TooltipProvider>
  );
}
