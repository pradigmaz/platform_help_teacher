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
import type { AdminLabOfferingOption } from './subjectOptions';

type EditablePolicy = Omit<OfferingPolicy, 'offering_id' | 'source' | 'second_extra_required' | 'automatic_extra_required'>;

interface SubjectPolicyDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  offerings: AdminLabOfferingOption[];
  selectedOfferingId: string | null;
  onOfferingChange: (offeringId: string) => void;
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
  offerings,
  selectedOfferingId,
  onOfferingChange,
}: SubjectPolicyDialogProps) {
  const selectedOffering = useMemo(
    () => offerings.find((offering) => offering.id === selectedOfferingId) ?? null,
    [selectedOfferingId, offerings],
  );
  const [policy, setPolicy] = useState<EditablePolicy | null>(null);
  const [source, setSource] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

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
    if (!open || offerings.length === 0) return;
    if (selectedOfferingId && offerings.some((offering) => offering.id === selectedOfferingId)) return;
    onOfferingChange(offerings[0].id);
  }, [offerings, onOfferingChange, open, selectedOfferingId]);

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
            Настройки связки
          </DialogTitle>
          <DialogDescription>Количество лабораторных, пороги аттестации, допуск и автомат.</DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="admin-labs-policy-offering">Группа / предмет / семестр</Label>
            <Select value={selectedOfferingId ?? ''} onValueChange={onOfferingChange}>
              <SelectTrigger id="admin-labs-policy-offering" className="bg-background">
                <SelectValue placeholder="Выберите связку" />
              </SelectTrigger>
              <SelectContent>
                {offerings.map((offering) => (
                  <SelectItem key={offering.id} value={offering.id}>
                    {offering.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {selectedOffering ? (
            <div className="rounded-lg border border-border/60 bg-muted/30 p-3 text-sm text-muted-foreground">
              {selectedOffering.groupName}: {selectedOffering.subjectName}, {selectedOffering.semester}
            </div>
          ) : null}

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
