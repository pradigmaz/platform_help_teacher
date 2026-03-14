'use client';

import { useState, useEffect, useMemo } from 'react';
import { BlurFade } from '@/components/ui/blur-fade';
import { Sparkles } from '@/components/ui/sparkles';
import { Button } from '@/components/ui/button';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Save, RotateCcw, Award } from 'lucide-react';
import { toast } from 'sonner';
import { AttestationAPI, AttestationType, LabsAPI } from '@/lib/api';
import { TooltipProvider } from "@/components/ui/tooltip";
import { GradeScaleCard } from './GradeScaleCard';
import { ScorePreviewCard } from './settings';
import {
  LabsSettingsCard,
  AttendanceSettingsCard,
  ActivitySettingsCard,
  SemesterDateCard,
  AttestationFormState,
  DEFAULT_FORM_STATE,
} from './attestation-settings';

function clampFirstLabsCount(value: number, totalLabsCount: number) {
  const normalizedTotal = Math.max(totalLabsCount, 1);
  if (!Number.isFinite(value)) {
    return 1;
  }
  return Math.min(Math.max(Math.trunc(value), 1), normalizedTotal);
}

function getDerivedSecondLabsCount(firstLabsCount: number, totalLabsCount: number) {
  return Math.max(Math.max(totalLabsCount, 1) - firstLabsCount, 0);
}

function getNormalizedFormState(form: AttestationFormState, totalLabsCount: number): AttestationFormState {
  const labsCountFirst = clampFirstLabsCount(form.labs_count_first, totalLabsCount);
  return {
    ...form,
    labs_count_first: labsCountFirst,
    labs_count_second: getDerivedSecondLabsCount(labsCountFirst, totalLabsCount),
  };
}

export function AttestationSettingsForm() {
  const [attestationType, setAttestationType] = useState<AttestationType>('first');
  const [form, setForm] = useState<AttestationFormState>(DEFAULT_FORM_STATE);
  const [totalLabsCount, setTotalLabsCount] = useState(
    DEFAULT_FORM_STATE.labs_count_first + DEFAULT_FORM_STATE.labs_count_second
  );
  const [saving, setSaving] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);

  const normalizedForm = getNormalizedFormState(form, totalLabsCount);
  const maxPoints = attestationType === 'first' ? 35 : 70;

  const totalWeight = useMemo(() => {
    let total = form.labs_weight + form.attendance_weight + form.activity_reserve;
    if (form.self_works_enabled) total += form.self_works_weight;
    if (form.colloquium_enabled) total += form.colloquium_weight;
    return total;
  }, [form]);

  const isWeightValid = Math.abs(totalWeight - 100) < 0.01;

  const update = <K extends keyof AttestationFormState>(key: K, value: AttestationFormState[K]) => {
    setForm((prev: AttestationFormState) => {
      const next = { ...prev, [key]: value } as AttestationFormState;
      if (key === 'labs_count_first') {
        return getNormalizedFormState(next, totalLabsCount);
      }
      return next;
    });
    setHasChanges(true);
  };

  useEffect(() => {
    const load = async () => {
      try {
        const [settingsResult, firstSettingsResult, labSettingsResult] = await Promise.allSettled([
          AttestationAPI.getSettings(attestationType),
          AttestationAPI.getSettings('first'),
          LabsAPI.getSettings(),
        ]);
        const settings = settingsResult.status === 'fulfilled' ? settingsResult.value : null;
        const firstSettings = firstSettingsResult.status === 'fulfilled' ? firstSettingsResult.value : null;
        const sourceFirstLabsCount =
          firstSettings?.labs_count_first ??
          settings?.labs_count_first ??
          DEFAULT_FORM_STATE.labs_count_first;
        const fallbackTotalLabs =
          sourceFirstLabsCount +
          (settings?.labs_count_second ?? DEFAULT_FORM_STATE.labs_count_second);
        const resolvedTotalLabs =
          labSettingsResult.status === 'fulfilled'
            ? Math.max(labSettingsResult.value.labs_count, 1)
            : Math.max(fallbackTotalLabs, 1);

        setTotalLabsCount(resolvedTotalLabs);
        setForm(
          getNormalizedFormState(
            {
              labs_weight: settings?.labs_weight ?? 70,
              attendance_weight: settings?.attendance_weight ?? 20,
              activity_reserve: settings?.activity_reserve ?? 10,
              labs_count_first: sourceFirstLabsCount,
              labs_count_second: settings?.labs_count_second ?? 10,
              grade_4_coef: settings?.grade_4_coef ?? 0.7,
              grade_3_coef: settings?.grade_3_coef ?? 0.4,
              late_coef: settings?.late_coef ?? 0.5,
              absent_coef: settings?.absent_coef ?? 0,
              late_max_grade: settings?.late_max_grade ?? 4,
              very_late_max_grade: settings?.very_late_max_grade ?? 3,
              late_threshold_days: settings?.late_threshold_days ?? 7,
              self_works_enabled: settings?.self_works_enabled ?? false,
              self_works_weight: settings?.self_works_weight ?? 0,
              self_works_count: settings?.self_works_count ?? 2,
              colloquium_enabled: settings?.colloquium_enabled ?? false,
              colloquium_weight: settings?.colloquium_weight ?? 0,
              colloquium_count: settings?.colloquium_count ?? 1,
              activity_enabled: settings?.activity_enabled ?? true,
              semester_start_date: settings?.semester_start_date ?? '',
            },
            resolvedTotalLabs
          )
        );
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
        ...normalizedForm,
        semester_start_date: normalizedForm.semester_start_date || null,
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
    ? normalizedForm.labs_count_first
    : totalLabsCount;

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
              <Button
                variant="outline"
                onClick={() => {
                  setForm(getNormalizedFormState(DEFAULT_FORM_STATE, totalLabsCount));
                  setHasChanges(false);
                }}
                disabled={!hasChanges || saving}
              >
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
          <SemesterDateCard form={form} attestationType={attestationType} onUpdate={update} />
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

        {/* Score Preview */}
        <BlurFade delay={0.25}>
          <ScorePreviewCard
            maxPoints={maxPoints}
            labsWeight={form.labs_weight}
            labsCount={labsCount}
            attendanceWeight={form.attendance_weight}
            activityReserve={form.activity_reserve}
            grade4Coef={form.grade_4_coef}
            grade3Coef={form.grade_3_coef}
            lateCoef={form.late_coef}
            absentCoef={form.absent_coef}
            totalWeight={totalWeight}
          />
        </BlurFade>

        {/* Labs Settings */}
        <BlurFade delay={0.35}>
          <LabsSettingsCard
            form={normalizedForm}
            attestationType={attestationType}
            totalLabsCount={totalLabsCount}
            derivedSecondLabsCount={normalizedForm.labs_count_second}
            onUpdate={update}
          />
        </BlurFade>

        {/* Attendance */}
        <BlurFade delay={0.4}>
          <AttendanceSettingsCard form={form} onUpdate={update} />
        </BlurFade>

        {/* Activity Reserve */}
        <BlurFade delay={0.45}>
          <ActivitySettingsCard form={form} onUpdate={update} />
        </BlurFade>
      </div>
    </TooltipProvider>
  );
}
