'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import { toast } from 'sonner';
import { Save, Settings } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { SubjectsAPI, type OfferingPolicy } from '@/lib/api';
import type { AdminLabSubjectOption } from './subjectOptions';

type EditablePolicy = Omit<OfferingPolicy, 'offering_id' | 'source' | 'second_extra_required' | 'automatic_extra_required'>;

interface SubjectPolicyDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  subjects: AdminLabSubjectOption[];
  selectedSubjectId: string | null;
  onSubjectChange: (subjectId: string) => void;
}

function toEditable(policy: OfferingPolicy): EditablePolicy {
  return {
    total_labs: policy.total_labs,
    labs_required_first: policy.labs_required_first,
    labs_required_second_total: policy.labs_required_second_total,
    exam_admission_required_labs: policy.exam_admission_required_labs,
    automatic_enabled: policy.automatic_enabled,
    automatic_places: policy.automatic_places,
    automatic_required_labs_total: policy.automatic_required_labs_total,
  };
}

function setNumberField<K extends keyof EditablePolicy>(
  policy: EditablePolicy,
  key: K,
  value: string,
): EditablePolicy {
  const nextValue = value === '' ? (key === 'automatic_places' ? null : 0) : Number(value);
  return { ...policy, [key]: nextValue } as EditablePolicy;
}

export function SubjectPolicyDialog({
  open,
  onOpenChange,
  subjects,
  selectedSubjectId,
  onSubjectChange,
}: SubjectPolicyDialogProps) {
  const selectedSubject = useMemo(
    () => subjects.find((subject) => subject.id === selectedSubjectId) ?? null,
    [selectedSubjectId, subjects],
  );
  const [policy, setPolicy] = useState<EditablePolicy | null>(null);
  const [source, setSource] = useState<string | null>(null);
  const [selectedOfferingId, setSelectedOfferingId] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const offeringOptions = useMemo(() => selectedSubject?.offerings ?? [], [selectedSubject]);

  useEffect(() => {
    let cancelled = false;
    if (!open || !selectedOfferingId) {
      setPolicy(null);
      setSource(null);
      return () => {
        cancelled = true;
      };
    }

    setLoading(true);
    SubjectsAPI.getOfferingPolicy(selectedOfferingId)
      .then((data) => {
        if (cancelled) return;
        setPolicy(toEditable(data));
        setSource(data.source);
      })
      .catch(() => {
        if (!cancelled) toast.error('Не удалось загрузить настройки связки');
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [open, selectedOfferingId]);

  useEffect(() => {
    if (!open || subjects.length === 0 || selectedSubjectId) return;
    onSubjectChange(subjects[0].id);
  }, [onSubjectChange, open, selectedSubjectId, subjects]);

  useEffect(() => {
    if (!open) return;
    const hasCurrent = offeringOptions.some((offering) => offering.id === selectedOfferingId);
    if (!hasCurrent) {
      setSelectedOfferingId(offeringOptions[0]?.id ?? '');
    }
  }, [offeringOptions, open, selectedOfferingId]);

  const savePolicy = useCallback(async () => {
    if (!selectedOfferingId || !policy) return;

    setSaving(true);
    try {
      const updated = await SubjectsAPI.updateOfferingPolicy(selectedOfferingId, policy);
      setPolicy(toEditable(updated));
      setSource(updated.source);
      toast.success('Настройки связки сохранены');
    } catch {
      toast.error('Не удалось сохранить настройки связки');
    } finally {
      setSaving(false);
    }
  }, [policy, selectedOfferingId]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[760px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Settings className="h-5 w-5" />
            Настройки предмета
          </DialogTitle>
          <DialogDescription>Количество лабораторных, пороги аттестации, допуск и автомат.</DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="admin-labs-policy-subject">Предмет</Label>
            <Select value={selectedSubjectId ?? ''} onValueChange={onSubjectChange}>
              <SelectTrigger id="admin-labs-policy-subject" className="bg-background">
                <SelectValue placeholder="Выберите предмет" />
              </SelectTrigger>
              <SelectContent>
                {subjects.map((subject) => (
                  <SelectItem key={subject.id} value={subject.id}>
                    {subject.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="admin-labs-policy-offering">Связка</Label>
            <Select value={selectedOfferingId} onValueChange={setSelectedOfferingId} disabled={!offeringOptions.length}>
              <SelectTrigger id="admin-labs-policy-offering" className="bg-background">
                <SelectValue placeholder="Выберите группу и семестр" />
              </SelectTrigger>
              <SelectContent>
                {offeringOptions.map((offering) => (
                  <SelectItem key={offering.id} value={offering.id}>
                    {offering.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {loading ? <div className="text-sm text-muted-foreground">Загрузка настроек…</div> : null}

          {policy ? (
            <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
              <Field id="policy-total-labs" label="Всего лаб по предмету" value={policy.total_labs} onChange={(value) => setPolicy(setNumberField(policy, 'total_labs', value))} />
              <Field id="policy-first-labs" label="К 1-й аттестации" value={policy.labs_required_first} onChange={(value) => setPolicy(setNumberField(policy, 'labs_required_first', value))} />
              <Field id="policy-second-labs" label="К 2-й аттестации всего" value={policy.labs_required_second_total} onChange={(value) => setPolicy(setNumberField(policy, 'labs_required_second_total', value))} />
              <Field id="policy-exam-labs" label="Допуск к экзамену" value={policy.exam_admission_required_labs} onChange={(value) => setPolicy(setNumberField(policy, 'exam_admission_required_labs', value))} />
              <Field id="policy-auto-labs" label="Порог автомата" value={policy.automatic_required_labs_total} onChange={(value) => setPolicy(setNumberField(policy, 'automatic_required_labs_total', value))} />
              <Field id="policy-auto-places" label="Мест на автомат" value={policy.automatic_places ?? ''} onChange={(value) => setPolicy(setNumberField(policy, 'automatic_places', value))} />
              <div className="flex items-center justify-between gap-3 rounded-lg border border-border/60 p-3 md:col-span-2">
                <div>
                  <div className="text-sm font-medium">Автомат включён</div>
                  <div className="text-xs text-muted-foreground">{source === 'explicit' ? 'Настроено' : 'Legacy fallback'}</div>
                </div>
                <Switch checked={policy.automatic_enabled} onCheckedChange={(checked) => setPolicy({ ...policy, automatic_enabled: checked })} />
              </div>
            </div>
          ) : null}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>Закрыть</Button>
          <Button onClick={savePolicy} disabled={!policy || !selectedOfferingId || saving || loading}>
            <Save className="mr-2 h-4 w-4" />
            {saving ? 'Сохранение…' : 'Сохранить'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function Field({
  id,
  label,
  value,
  onChange,
}: {
  id: string;
  label: string;
  value: number | '';
  onChange: (value: string) => void;
}) {
  return (
    <div className="space-y-1.5">
      <Label htmlFor={id}>{label}</Label>
      <Input id={id} type="number" min={0} value={value} onChange={(event) => onChange(event.target.value)} />
    </div>
  );
}
