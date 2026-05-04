'use client';

import { useEffect, useState } from 'react';
import { BookOpenCheck, GraduationCap, Layers3 } from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { SubjectsAPI, type GroupSubjectOffering, type OfferingPolicy } from '@/lib/api';

type EditablePolicy = Omit<OfferingPolicy, 'offering_id' | 'source' | 'second_extra_required' | 'automatic_extra_required'>;

interface OfferingPolicyPanelProps {
  offerings: GroupSubjectOffering[];
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

export function OfferingPolicyPanel({ offerings }: OfferingPolicyPanelProps) {
  const [selectedOfferingId, setSelectedOfferingId] = useState('');
  const [policy, setPolicy] = useState<EditablePolicy | null>(null);
  const [source, setSource] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const selectedOffering = offerings.find((offering) => offering.id === selectedOfferingId) ?? null;

  useEffect(() => {
    if (offerings.length === 1) {
      setSelectedOfferingId(offerings[0].id);
    }
  }, [offerings]);

  useEffect(() => {
    if (!selectedOfferingId) {
      setPolicy(null);
      setSource(null);
      return;
    }
    let cancelled = false;
    setLoading(true);
    SubjectsAPI.getOfferingPolicy(selectedOfferingId)
      .then((data) => {
        if (cancelled) return;
        setPolicy(toEditable(data));
        setSource(data.source);
      })
      .catch(() => toast.error('Не удалось загрузить политику связки'))
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [selectedOfferingId]);

  async function savePolicy() {
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
  }

  return (
    <Card className="border-border/60 bg-background/80">
      <CardHeader>
        <CardTitle>Настройки предмета</CardTitle>
        <CardDescription>
          Выберите предмет в группе и задайте для него количество лабораторных, пороги аттестации, допуск и автомат.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-3 lg:grid-cols-[minmax(0,1fr)_320px] lg:items-start">
          <SubjectContextCard offering={selectedOffering} source={source} />
          <div className="space-y-1.5">
            <Label htmlFor="offering-policy-subject">Предмет</Label>
            <Select value={selectedOfferingId} onValueChange={setSelectedOfferingId}>
              <SelectTrigger id="offering-policy-subject" className="bg-background">
                <SelectValue placeholder="Выберите предмет" />
              </SelectTrigger>
              <SelectContent>
                {offerings.map((offering) => (
                  <SelectItem key={offering.id} value={offering.id}>
                    {offering.subject_name} / {offering.group_name} / {offering.semester}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        {loading ? <div className="text-sm text-muted-foreground">Загрузка политики…</div> : null}

        {policy ? (
          <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-4">
            <Field id="total_labs" label="Всего лаб по предмету" value={policy.total_labs} onChange={(value) => setPolicy(setNumberField(policy, 'total_labs', value))} />
            <Field id="labs_required_first" label="К 1-й аттестации" value={policy.labs_required_first} onChange={(value) => setPolicy(setNumberField(policy, 'labs_required_first', value))} />
            <Field id="labs_required_second_total" label="К 2-й аттестации всего" value={policy.labs_required_second_total} onChange={(value) => setPolicy(setNumberField(policy, 'labs_required_second_total', value))} />
            <Field id="exam_admission_required_labs" label="Допуск к экзамену" value={policy.exam_admission_required_labs} onChange={(value) => setPolicy(setNumberField(policy, 'exam_admission_required_labs', value))} />
            <Field id="automatic_required_labs_total" label="Порог автомата" value={policy.automatic_required_labs_total} onChange={(value) => setPolicy(setNumberField(policy, 'automatic_required_labs_total', value))} />
            <Field id="automatic_places" label="Мест на автомат" value={policy.automatic_places ?? ''} onChange={(value) => setPolicy(setNumberField(policy, 'automatic_places', value))} />
            <div className="flex items-center gap-3 rounded-lg border border-border/60 p-3">
              <Switch checked={policy.automatic_enabled} onCheckedChange={(checked) => setPolicy({ ...policy, automatic_enabled: checked })} />
              <div>
                <div className="text-sm font-medium">Автомат включён</div>
                <div className="text-xs text-muted-foreground">Работает только для экзамена</div>
              </div>
            </div>
            <div className="flex items-center justify-between gap-3 rounded-lg border border-border/60 p-3">
              <span className="text-xs text-muted-foreground">Источник: {source === 'explicit' ? 'связка' : 'legacy fallback'}</span>
              <Button onClick={savePolicy} disabled={saving || loading}>
                {saving ? 'Сохранение…' : 'Сохранить'}
              </Button>
            </div>
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}

function SubjectContextCard({
  offering,
  source,
}: {
  offering: GroupSubjectOffering | null;
  source: string | null;
}) {
  if (!offering) {
    return (
      <div className="flex items-start gap-3 rounded-lg border border-dashed border-border/70 bg-muted/30 p-3">
        <BookOpenCheck className="mt-0.5 h-5 w-5 shrink-0 text-muted-foreground" />
        <div>
          <div className="text-sm font-medium text-foreground">Предмет не выбран</div>
          <div className="text-xs text-muted-foreground">Поля количества лабораторных появятся после выбора предмета.</div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-start gap-3 rounded-lg border border-primary/25 bg-primary/5 p-3">
      <BookOpenCheck className="mt-0.5 h-5 w-5 shrink-0 text-primary" />
      <div className="min-w-0 space-y-2">
        <div className="flex flex-wrap items-center gap-2">
          <div className="truncate text-sm font-semibold text-foreground">{offering.subject_name}</div>
          {source ? (
            <Badge variant={source === 'explicit' ? 'default' : 'secondary'}>
              {source === 'explicit' ? 'настроено' : 'legacy fallback'}
            </Badge>
          ) : null}
        </div>
        <div className="flex flex-wrap gap-2 text-xs text-muted-foreground">
          <span className="inline-flex items-center gap-1">
            <GraduationCap className="h-3.5 w-3.5" />
            {offering.group_name}
          </span>
          <span className="inline-flex items-center gap-1">
            <Layers3 className="h-3.5 w-3.5" />
            {offering.semester}
          </span>
        </div>
      </div>
    </div>
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
