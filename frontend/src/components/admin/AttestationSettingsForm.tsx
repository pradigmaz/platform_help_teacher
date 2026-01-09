'use client';

import { useState, useEffect, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { BlurFade } from '@/components/ui/blur-fade';
import { Sparkles } from '@/components/ui/sparkles';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { Switch } from '@/components/ui/switch';
import { Save, RotateCcw, Award, Calendar, AlertCircle, FlaskConical, Clock, Zap } from 'lucide-react';
import { toast } from 'sonner';
import { AttestationAPI, AttestationType } from '@/lib/api';
import { BorderBeam } from '@/components/ui/border-beam';
import { cn } from '@/lib/utils';
import { TooltipProvider } from "@/components/ui/tooltip";
import { GradeScaleCard } from './GradeScaleCard';
import { ScorePreviewCard } from './settings';

// Helper для расчёта периодов аттестации
function formatPeriod(startDate: string, weekStart: number, weekEnd: number): string {
  const start = new Date(startDate);
  const periodStart = new Date(start);
  periodStart.setDate(start.getDate() + (weekStart - 1) * 7);
  const periodEnd = new Date(start);
  periodEnd.setDate(start.getDate() + weekEnd * 7 - 1);
  
  const formatDate = (d: Date) => d.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit' });
  return `${formatDate(periodStart)} — ${formatDate(periodEnd)}`;
}

interface FormState {
  labs_weight: number;
  attendance_weight: number;
  activity_reserve: number;
  labs_count_first: number;
  labs_count_second: number;
  grade_4_coef: number;
  grade_3_coef: number;
  late_coef: number;
  late_max_grade: number;
  very_late_max_grade: number;
  late_threshold_days: number;
  self_works_enabled: boolean;
  self_works_weight: number;
  self_works_count: number;
  colloquium_enabled: boolean;
  colloquium_weight: number;
  colloquium_count: number;
  activity_enabled: boolean;
  semester_start_date: string;
}

const DEFAULT_STATE: FormState = {
  labs_weight: 70, attendance_weight: 20, activity_reserve: 10,
  labs_count_first: 8, labs_count_second: 10,
  grade_4_coef: 0.7, grade_3_coef: 0.4,
  late_coef: 0.5,
  late_max_grade: 4, very_late_max_grade: 3, late_threshold_days: 7,
  self_works_enabled: false, self_works_weight: 0, self_works_count: 2,
  colloquium_enabled: false, colloquium_weight: 0, colloquium_count: 1,
  activity_enabled: true,
  semester_start_date: '',
};

export function AttestationSettingsForm() {
  const [attestationType, setAttestationType] = useState<AttestationType>('first');
  const [form, setForm] = useState<FormState>(DEFAULT_STATE);
  const [saving, setSaving] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);

  const maxPoints = attestationType === 'first' ? 35 : 70;
  const minPassing = attestationType === 'first' ? 20 : 40;

  const totalWeight = useMemo(() => {
    let total = form.labs_weight + form.attendance_weight + form.activity_reserve;
    if (form.self_works_enabled) total += form.self_works_weight;
    if (form.colloquium_enabled) total += form.colloquium_weight;
    return total;
  }, [form]);

  const isWeightValid = Math.abs(totalWeight - 100) < 0.01;

  const update = <K extends keyof FormState>(key: K, value: FormState[K]) => {
    setForm(prev => ({ ...prev, [key]: value }));
    setHasChanges(true);
  };

  useEffect(() => {
    const load = async () => {
      try {
        const s = await AttestationAPI.getSettings(attestationType);
        setForm({
          labs_weight: s.labs_weight ?? 70,
          attendance_weight: s.attendance_weight ?? 20,
          activity_reserve: s.activity_reserve ?? 10,
          labs_count_first: s.labs_count_first ?? 8,
          labs_count_second: s.labs_count_second ?? 10,
          grade_4_coef: s.grade_4_coef ?? 0.7,
          grade_3_coef: s.grade_3_coef ?? 0.4,
          late_coef: s.late_coef ?? 0.5,
          late_max_grade: s.late_max_grade ?? 4,
          very_late_max_grade: s.very_late_max_grade ?? 3,
          late_threshold_days: s.late_threshold_days ?? 7,
          self_works_enabled: s.self_works_enabled ?? false,
          self_works_weight: s.self_works_weight ?? 0,
          self_works_count: s.self_works_count ?? 2,
          colloquium_enabled: s.colloquium_enabled ?? false,
          colloquium_weight: s.colloquium_weight ?? 0,
          colloquium_count: s.colloquium_count ?? 1,
          activity_enabled: s.activity_enabled ?? true,
          semester_start_date: s.semester_start_date ?? '',
        });
        setHasChanges(false);
      } catch { /* not created yet */ }
    };
    load();
  }, [attestationType]);

  const handleSave = async () => {
    if (!isWeightValid) {
      toast.error(`Сумма весов должна быть 100%. Текущая: ${totalWeight.toFixed(1)}%`);
      return;
    }
    setSaving(true);
    try {
      await AttestationAPI.updateSettings({
        attestation_type: attestationType,
        ...form,
        semester_start_date: form.semester_start_date || null,
      });
      setHasChanges(false);
      toast.success('Настройки сохранены');
    } catch (e: unknown) {
      toast.error(e instanceof Error ? e.message : 'Ошибка сохранения');
    } finally {
      setSaving(false);
    }
  };

  const labsCount = attestationType === 'first' 
    ? form.labs_count_first 
    : form.labs_count_first + form.labs_count_second;

  return (
    <TooltipProvider>
      <div className="space-y-6">
        {/* Header */}
        <BlurFade delay={0.1}>
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div>
              <h2 className="text-2xl font-bold flex items-center gap-2">
                <Sparkles color="#8b5cf6"><Award className="w-6 h-6 text-primary" /></Sparkles>
                Настройки аттестации
              </h2>
              <p className="text-muted-foreground">Автобалансировка баллов</p>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => { setForm(DEFAULT_STATE); setHasChanges(false); }} disabled={!hasChanges || saving}>
                <RotateCcw className="w-4 h-4 mr-2" />Сбросить
              </Button>
              <Button onClick={handleSave} disabled={!hasChanges || saving || !isWeightValid}>
                <Save className="w-4 h-4 mr-2" />{saving ? 'Сохранение...' : 'Сохранить'}
              </Button>
            </div>
          </div>
        </BlurFade>

        {/* Semester Date & Periods */}
        <BlurFade delay={0.12}>
          <Card>
            <CardContent className="pt-4">
              <div className="flex flex-col sm:flex-row gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <Calendar className="w-4 h-4 text-blue-500" />
                    <Label>Дата начала семестра</Label>
                  </div>
                  <Input 
                    type="date" 
                    value={form.semester_start_date} 
                    onChange={e => update('semester_start_date', e.target.value)} 
                    disabled={attestationType === 'second'}
                  />
                </div>
                {form.semester_start_date && (
                  <div className="flex-1 text-sm space-y-1">
                    <p className="text-muted-foreground">Периоды аттестаций:</p>
                    <p><span className="font-medium">1-я:</span> {formatPeriod(form.semester_start_date, 1, 7)}</p>
                    <p className={attestationType === 'second' ? '' : 'text-muted-foreground'}>
                      <span className="font-medium">2-я:</span> {formatPeriod(form.semester_start_date, 8, 14)}
                    </p>
                  </div>
                )}
              </div>
              {!form.semester_start_date && (
                <p className="text-xs text-muted-foreground mt-2 flex items-center gap-1">
                  <AlertCircle className="w-3 h-3" />Укажите для автовычисления периодов
                </p>
              )}
            </CardContent>
          </Card>
        </BlurFade>

        {/* Tabs */}
        <BlurFade delay={0.15}>
          <Tabs value={attestationType} onValueChange={(v) => setAttestationType(v as AttestationType)}>
            <TabsList className="grid w-full max-w-md grid-cols-2">
              <TabsTrigger value="first">1-я аттестация (35 б.)</TabsTrigger>
              <TabsTrigger value="second">2-я аттестация (70 б.)</TabsTrigger>
            </TabsList>
          </Tabs>
        </BlurFade>

        <BlurFade delay={0.2}><GradeScaleCard attestationType={attestationType} /></BlurFade>

        {/* Weight Summary */}
        <BlurFade delay={0.25}>
          <Card className="relative overflow-hidden">
            <BorderBeam size={200} duration={10} />
            <CardContent className="pt-4">
              <div className="flex flex-wrap items-center gap-4 text-sm">
                <Badge variant="outline" className="bg-green-500/10">Макс: {maxPoints} б.</Badge>
                <Badge variant="outline" className="bg-yellow-500/10">Мин: {minPassing} б.</Badge>
                <Badge variant="outline" className={cn(isWeightValid ? "bg-green-500/10 text-green-600" : "bg-red-500/10 text-red-600")}>
                  Веса: {totalWeight.toFixed(0)}% {isWeightValid ? '✓' : '(нужно 100%)'}
                </Badge>
              </div>
            </CardContent>
          </Card>
        </BlurFade>

        {/* Score Preview */}
        <BlurFade delay={0.3}>
          <ScorePreviewCard
            maxPoints={maxPoints}
            labsWeight={form.labs_weight}
            labsCount={labsCount}
            attendanceWeight={form.attendance_weight}
            activityReserve={form.activity_reserve}
            grade4Coef={form.grade_4_coef}
            grade3Coef={form.grade_3_coef}
            lateCoef={form.late_coef}
            totalWeight={totalWeight}
          />
        </BlurFade>

        {/* Labs Settings */}
        <BlurFade delay={0.35}>
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-lg">
                <FlaskConical className="w-5 h-5 text-blue-500" />
                Лабораторные работы
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Вес (%)</Label>
                  <div className="flex items-center gap-2">
                    <Slider value={[form.labs_weight]} onValueChange={([v]) => update('labs_weight', v)} max={100} step={1} />
                    <span className="w-12 text-right font-mono">{form.labs_weight}%</span>
                  </div>
                </div>
                <div>
                  <Label>Кол-во для 1-й атт.</Label>
                  <Input type="number" value={form.labs_count_first} onChange={e => update('labs_count_first', +e.target.value)} min={1} max={20} />
                </div>
              </div>
              {attestationType === 'second' && (
                <div>
                  <Label>Доп. лаб для 2-й атт.</Label>
                  <Input type="number" value={form.labs_count_second} onChange={e => update('labs_count_second', +e.target.value)} min={0} max={20} />
                </div>
              )}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Коэф. оценки 4</Label>
                  <div className="flex items-center gap-2">
                    <Slider value={[form.grade_4_coef * 100]} onValueChange={([v]) => update('grade_4_coef', v / 100)} max={100} step={1} />
                    <span className="w-12 text-right font-mono">{(form.grade_4_coef * 100).toFixed(0)}%</span>
                  </div>
                </div>
                <div>
                  <Label>Коэф. оценки 3</Label>
                  <div className="flex items-center gap-2">
                    <Slider value={[form.grade_3_coef * 100]} onValueChange={([v]) => update('grade_3_coef', v / 100)} max={100} step={1} />
                    <span className="w-12 text-right font-mono">{(form.grade_3_coef * 100).toFixed(0)}%</span>
                  </div>
                </div>
              </div>
              <p className="text-xs text-muted-foreground">Оценка 5 = 100% (фикс), Оценка 2 = 0% (работа не засчитана)</p>
            </CardContent>
          </Card>
        </BlurFade>

        {/* Attendance */}
        <BlurFade delay={0.4}>
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-lg">
                <Clock className="w-5 h-5 text-green-500" />
                Посещаемость
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label>Вес (%)</Label>
                <div className="flex items-center gap-2">
                  <Slider value={[form.attendance_weight]} onValueChange={([v]) => update('attendance_weight', v)} max={100} step={1} />
                  <span className="w-12 text-right font-mono">{form.attendance_weight}%</span>
                </div>
              </div>
              <div>
                <Label>Коэф. опоздания</Label>
                <div className="flex items-center gap-2">
                  <Slider value={[form.late_coef * 100]} onValueChange={([v]) => update('late_coef', v / 100)} max={100} step={1} />
                  <span className="w-12 text-right font-mono">{(form.late_coef * 100).toFixed(0)}%</span>
                </div>
              </div>
              <p className="text-xs text-muted-foreground">Кол-во занятий определяется автоматически из расписания</p>
            </CardContent>
          </Card>
        </BlurFade>

        {/* Activity Reserve */}
        <BlurFade delay={0.45}>
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
                  <Slider value={[form.activity_reserve]} onValueChange={([v]) => update('activity_reserve', v)} max={30} step={1} />
                  <span className="w-12 text-right font-mono">{form.activity_reserve}%</span>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Switch checked={form.activity_enabled} onCheckedChange={v => update('activity_enabled', v)} />
                <Label>Включить активность</Label>
              </div>
              <div className="text-xs text-muted-foreground space-y-1">
                <p>• Бонусы ограничены резервом и макс баллами</p>
                <p>• Штрафы без ограничений</p>
                <p>• Если студент набрал макс — бонусы заблокированы</p>
              </div>
            </CardContent>
          </Card>
        </BlurFade>

        {/* Semester Date */}
        <BlurFade delay={0.5}>
          <Card>
            <CardContent className="pt-4">
              <div className="flex items-center gap-2 mb-2">
                <Calendar className="w-4 h-4 text-blue-500" />
                <Label>Дата начала семестра</Label>
              </div>
              <Input 
                type="date" 
                value={form.semester_start_date} 
                onChange={e => update('semester_start_date', e.target.value)} 
                disabled={attestationType === 'second'}
              />
              {attestationType === 'second' ? (
                <p className="text-xs text-muted-foreground mt-1">
                  Настраивается в 1-й аттестации
                </p>
              ) : !form.semester_start_date && (
                <p className="text-xs text-muted-foreground mt-1 flex items-center gap-1">
                  <AlertCircle className="w-3 h-3" />Укажите для автовычисления периодов
                </p>
              )}
            </CardContent>
          </Card>
        </BlurFade>

      </div>
    </TooltipProvider>
  );
}
