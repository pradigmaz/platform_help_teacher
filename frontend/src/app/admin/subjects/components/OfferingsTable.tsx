'use client';

import type { ReactNode } from 'react';
import { FolderKanban, GraduationCap, LibraryBig, Users } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import type { FinalControlType, GroupSubjectOffering } from '@/lib/api';

export type OfferingsViewMode = 'by_subject' | 'by_group';

interface OfferingsTableProps {
  offerings: GroupSubjectOffering[];
  savingOfferingId: string | null;
  viewMode: OfferingsViewMode;
  onControlTypeChange: (offering: GroupSubjectOffering, value: FinalControlType | null) => void;
  onOpenQueue: (offering: GroupSubjectOffering) => void;
  onOpenExamPrep: (offering: GroupSubjectOffering) => void;
}

const FINAL_CONTROL_LABELS: Record<FinalControlType, string> = {
  exam: 'Экзамен',
  credit: 'Зачёт',
  differentiated_credit: 'Диф. зачёт',
};

function getControlBadge(offering: GroupSubjectOffering) {
  if (!offering.final_control_type) {
    return <Badge variant="outline">Не задано</Badge>;
  }
  if (offering.final_control_type === 'exam') {
    return <Badge className="bg-emerald-600 text-white hover:bg-emerald-600">Экзамен</Badge>;
  }
  return <Badge variant="secondary">{FINAL_CONTROL_LABELS[offering.final_control_type]}</Badge>;
}

function getAutomaticBadge(offering: GroupSubjectOffering) {
  if (offering.final_control_type === 'exam') {
    return <Badge variant="outline">Автомат активен</Badge>;
  }
  if (!offering.final_control_type) {
    return <Badge variant="outline">Автомат не настроен</Badge>;
  }
  return <Badge variant="outline">Автомат недоступен</Badge>;
}

function getSemesterLabel(semester: string) {
  const part = semester.split('-')[1];
  if (part === '1') {
    return 'Семестр 1';
  }
  if (part === '2') {
    return 'Семестр 2';
  }
  return semester;
}

function OfferingRow({
  offering,
  mode,
  savingOfferingId,
  onControlTypeChange,
  onOpenQueue,
  onOpenExamPrep,
}: {
  offering: GroupSubjectOffering;
  mode: OfferingsViewMode;
  savingOfferingId: string | null;
  onControlTypeChange: (offering: GroupSubjectOffering, value: FinalControlType | null) => void;
  onOpenQueue: (offering: GroupSubjectOffering) => void;
  onOpenExamPrep: (offering: GroupSubjectOffering) => void;
}) {
  const primaryLabel = mode === 'by_subject' ? offering.group_name : offering.subject_name;
  const secondaryLabel = mode === 'by_subject' ? offering.subject_name : offering.group_name;

  return (
    <div className="grid grid-cols-1 gap-3 rounded-2xl border border-border/50 bg-muted/20 p-4 xl:grid-cols-[minmax(0,1.2fr)_180px_220px_220px]">
      <div className="space-y-2">
        <div className="flex flex-wrap items-center gap-2">
          <div className="font-semibold text-foreground">{primaryLabel}</div>
          <Badge variant="outline">{getSemesterLabel(offering.semester)}</Badge>
          {getControlBadge(offering)}
          {getAutomaticBadge(offering)}
        </div>
        <p className="text-xs text-muted-foreground">
          {mode === 'by_subject' ? 'Предмет' : 'Группа'}: {secondaryLabel}. Автомат участвует только при экзамене.
        </p>
      </div>

      <div className="space-y-1 text-sm">
        <div className="text-muted-foreground">Форма контроля</div>
        <div className="font-medium text-foreground">
          {offering.final_control_type ? FINAL_CONTROL_LABELS[offering.final_control_type] : 'Не задана'}
        </div>
      </div>

      <Select
        value={offering.final_control_type ?? 'unset'}
        onValueChange={(value) =>
          onControlTypeChange(offering, value === 'unset' ? null : (value as FinalControlType))
        }
        disabled={savingOfferingId === offering.id}
      >
        <SelectTrigger className="h-11 bg-background">
          <SelectValue placeholder="Не задано" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="unset">Не задано</SelectItem>
          <SelectItem value="exam">{FINAL_CONTROL_LABELS.exam}</SelectItem>
          <SelectItem value="credit">{FINAL_CONTROL_LABELS.credit}</SelectItem>
          <SelectItem value="differentiated_credit">{FINAL_CONTROL_LABELS.differentiated_credit}</SelectItem>
        </SelectContent>
      </Select>

      <div className="flex flex-col gap-2 md:flex-row xl:flex-col">
        <Button
          variant={offering.final_control_type === 'exam' ? 'default' : 'outline'}
          size="sm"
          disabled={offering.final_control_type !== 'exam'}
          onClick={() => onOpenQueue(offering)}
          className="h-11"
        >
          Очередь
        </Button>
        <Button
          variant="outline"
          size="sm"
          disabled={offering.final_control_type !== 'exam'}
          onClick={() => onOpenExamPrep(offering)}
          className="h-11"
        >
          Вопросы ({offering.exam_prep_questions_count})
        </Button>
      </div>
    </div>
  );
}

function renderCards({
  title,
  description,
  icon,
  metricLabel,
  offerings,
  mode,
  savingOfferingId,
  onControlTypeChange,
  onOpenQueue,
  onOpenExamPrep,
}: {
  title: string;
  description: string;
  icon: ReactNode;
  metricLabel: string;
  offerings: GroupSubjectOffering[];
  mode: OfferingsViewMode;
  savingOfferingId: string | null;
  onControlTypeChange: (offering: GroupSubjectOffering, value: FinalControlType | null) => void;
  onOpenQueue: (offering: GroupSubjectOffering) => void;
  onOpenExamPrep: (offering: GroupSubjectOffering) => void;
}) {
  const examsCount = offerings.filter((offering) => offering.final_control_type === 'exam').length;
  const unsetCount = offerings.filter((offering) => offering.final_control_type === null).length;

  return (
    <Card key={title} className="overflow-hidden border-border/60 bg-background/80 shadow-sm">
      <CardHeader className="pb-4">
        <div className="flex flex-col gap-3 xl:flex-row xl:items-center xl:justify-between">
          <div className="space-y-2">
            <CardTitle className="flex items-center gap-2 text-xl">
              {icon}
              {title}
            </CardTitle>
            <CardDescription>{description}</CardDescription>
          </div>
          <div className="flex flex-wrap gap-2">
            <Badge variant="outline" className="gap-1">
              <Users className="h-3.5 w-3.5" />
              {metricLabel}: {offerings.length}
            </Badge>
            <Badge variant="outline" className="gap-1">
              <GraduationCap className="h-3.5 w-3.5" />
              Экзаменов: {examsCount}
            </Badge>
            {unsetCount > 0 ? <Badge variant="outline">Не настроено: {unsetCount}</Badge> : null}
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {offerings.map((offering) => (
          <OfferingRow
            key={offering.id}
            offering={offering}
            mode={mode}
            savingOfferingId={savingOfferingId}
            onControlTypeChange={onControlTypeChange}
            onOpenQueue={onOpenQueue}
            onOpenExamPrep={onOpenExamPrep}
          />
        ))}
      </CardContent>
    </Card>
  );
}

export function OfferingsTable({
  offerings,
  savingOfferingId,
  viewMode,
  onControlTypeChange,
  onOpenQueue,
  onOpenExamPrep,
}: OfferingsTableProps) {
  if (!offerings.length) {
    return (
      <Card className="border-border/60 bg-background/80">
        <CardContent className="py-12 text-center text-sm text-muted-foreground">
          Для выбранных фильтров связки не найдены.
        </CardContent>
      </Card>
    );
  }

  if (viewMode === 'by_group') {
    const groupedByGroup = offerings.reduce<Record<string, GroupSubjectOffering[]>>((accumulator, offering) => {
      accumulator[offering.group_name] ??= [];
      accumulator[offering.group_name].push(offering);
      return accumulator;
    }, {});

    const groups = Object.entries(groupedByGroup)
      .map(([groupName, groupOfferings]) => ({
        title: groupName,
        offerings: groupOfferings.sort((left, right) => left.subject_name.localeCompare(right.subject_name, 'ru')),
      }))
      .sort((left, right) => left.title.localeCompare(right.title, 'ru'));

    return (
      <div className="space-y-4">
        {groups.map((group) =>
          renderCards({
            title: group.title,
            description: 'Показывает все предметы этой группы и быстро подсказывает, где автомат вообще возможен.',
            icon: <LibraryBig className="h-5 w-5 text-primary" />,
            metricLabel: 'Предметов',
            offerings: group.offerings,
            mode: viewMode,
            savingOfferingId,
            onControlTypeChange,
            onOpenQueue,
            onOpenExamPrep,
          }),
        )}
      </div>
    );
  }

  const groupedBySubject = offerings.reduce<Record<string, GroupSubjectOffering[]>>((accumulator, offering) => {
    accumulator[offering.subject_name] ??= [];
    accumulator[offering.subject_name].push(offering);
    return accumulator;
  }, {});

  const subjects = Object.entries(groupedBySubject)
    .map(([subjectName, subjectOfferings]) => ({
      title: subjectName,
      offerings: subjectOfferings.sort((left, right) => left.group_name.localeCompare(right.group_name, 'ru')),
    }))
    .sort((left, right) => left.title.localeCompare(right.title, 'ru'));

  return (
    <div className="space-y-4">
      {subjects.map((subject) =>
        renderCards({
          title: subject.title,
          description: 'Один предмет, все его группы, форма контроля и быстрый доступ к очереди автомата.',
          icon: <FolderKanban className="h-5 w-5 text-primary" />,
          metricLabel: 'Групп',
          offerings: subject.offerings,
          mode: viewMode,
            savingOfferingId,
            onControlTypeChange,
            onOpenQueue,
            onOpenExamPrep,
          }),
        )}
    </div>
  );
}
