'use client';

import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { BookOpenCheck, GraduationCap, Layers3, NotebookTabs } from 'lucide-react';
import { toast } from 'sonner';
import { BlurFade } from '@/components/ui/blur-fade';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { SubjectsAPI, type AutomaticQueueResponse, type FinalControlType, type GroupSubjectOffering } from '@/lib/api';
import { OfferingsFilters, type OfferingControlFilter } from './components/OfferingsFilters';
import { OfferingsTable, type OfferingsViewMode } from './components/OfferingsTable';
import { AutomaticQueueDialog } from './components/AutomaticQueueDialog';
import { OfferingPolicyPanel } from './components/OfferingPolicyPanel';
import { notifyAdminOfferingsChanged } from '@/components/admin/useAdminExamOfferings';

export default function AdminSubjectsPage() {
  const router = useRouter();
  const [offerings, setOfferings] = useState<GroupSubjectOffering[]>([]);
  const [loading, setLoading] = useState(true);
  const [savingOfferingId, setSavingOfferingId] = useState<string | null>(null);
  const [queueOffering, setQueueOffering] = useState<GroupSubjectOffering | null>(null);
  const [queue, setQueue] = useState<AutomaticQueueResponse | null>(null);
  const [queueLoading, setQueueLoading] = useState(false);
  const [search, setSearch] = useState('');
  const [selectedSubject, setSelectedSubject] = useState('all');
  const [controlFilter, setControlFilter] = useState<OfferingControlFilter>('all');
  const [viewMode, setViewMode] = useState<OfferingsViewMode>('by_subject');

  useEffect(() => {
    void loadOfferings();
  }, []);

  async function loadOfferings() {
    setLoading(true);
    try {
      setOfferings(await SubjectsAPI.listOfferings());
    } catch {
      toast.error('Ошибка загрузки предметов групп');
    } finally {
      setLoading(false);
    }
  }

  async function handleControlTypeChange(offering: GroupSubjectOffering, value: FinalControlType | null) {
    setSavingOfferingId(offering.id);
    try {
      const updated = await SubjectsAPI.updateOffering(offering.id, value);
      setOfferings((current) => current.map((item) => (item.id === updated.id ? updated : item)));
      notifyAdminOfferingsChanged();
      toast.success('Форма контроля обновлена');
      if (queueOffering?.id === updated.id) {
        setQueueOffering(updated);
      }
    } catch {
      toast.error('Не удалось обновить форму контроля');
    } finally {
      setSavingOfferingId(null);
    }
  }

  async function openQueue(offering: GroupSubjectOffering) {
    setQueueOffering(offering);
    setQueue(null);
    setQueueLoading(true);
    try {
      setQueue(await SubjectsAPI.getAutomaticQueue(offering.id));
    } catch {
      toast.error('Ошибка загрузки очереди автомата');
    } finally {
      setQueueLoading(false);
    }
  }

  function openExamPrep(offering: GroupSubjectOffering) {
    router.push(`/admin/exams?offering=${offering.id}`);
  }

  async function handleDecline(studentId: string) {
    if (!queueOffering) {
      return;
    }
    const reason = window.prompt('Причина отказа от автомата', '') ?? '';
    try {
      setQueue(await SubjectsAPI.declineAutomatic(queueOffering.id, studentId, reason));
      toast.success('Отказ зафиксирован');
    } catch {
      toast.error('Не удалось зафиксировать отказ');
    }
  }

  async function handleRestore(studentId: string) {
    if (!queueOffering) {
      return;
    }
    try {
      setQueue(await SubjectsAPI.clearAutomaticDecline(queueOffering.id, studentId));
      toast.success('Отказ снят');
    } catch {
      toast.error('Не удалось снять отказ');
    }
  }

  const examOfferingsCount = useMemo(
    () => offerings.filter((offering) => offering.final_control_type === 'exam').length,
    [offerings],
  );
  const subjectOptions = useMemo(
    () => Array.from(new Set(offerings.map((offering) => offering.subject_name))).sort((left, right) => left.localeCompare(right, 'ru')),
    [offerings],
  );
  const filteredOfferings = useMemo(() => {
    const normalizedSearch = search.trim().toLowerCase();

    return offerings.filter((offering) => {
      if (selectedSubject !== 'all' && offering.subject_name !== selectedSubject) {
        return false;
      }
      if (controlFilter === 'unset' && offering.final_control_type !== null) {
        return false;
      }
      if (controlFilter !== 'all' && controlFilter !== 'unset' && offering.final_control_type !== controlFilter) {
        return false;
      }
      if (!normalizedSearch) {
        return true;
      }
      const haystack = `${offering.subject_name} ${offering.group_name} ${offering.semester}`.toLowerCase();
      return haystack.includes(normalizedSearch);
    });
  }, [controlFilter, offerings, search, selectedSubject]);

  const filteredGroupsCount = useMemo(
    () => new Set(filteredOfferings.map((offering) => offering.group_name)).size,
    [filteredOfferings],
  );
  const filteredSubjectsCount = useMemo(
    () => new Set(filteredOfferings.map((offering) => offering.subject_name)).size,
    [filteredOfferings],
  );

  return (
    <div className="space-y-6">
      <BlurFade delay={0.1}>
        <div>
          <h1 className="flex items-center gap-3 text-3xl font-bold tracking-tight">
            <BookOpenCheck className="h-8 w-8 text-primary" />
            Предметы групп
          </h1>
          <p className="mt-1 text-muted-foreground">
            Здесь задаётся форма итогового контроля по связке группа / предмет / семестр.
          </p>
        </div>
      </BlurFade>

      <BlurFade delay={0.15}>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
          <div className="rounded-xl border border-border/60 bg-background/80 p-4">
            <div className="text-sm text-muted-foreground">Активных связок</div>
            <div className="mt-2 text-3xl font-bold">{offerings.length}</div>
          </div>
          <div className="rounded-xl border border-border/60 bg-background/80 p-4">
            <div className="text-sm text-muted-foreground">Экзаменов</div>
            <div className="mt-2 text-3xl font-bold">{examOfferingsCount}</div>
          </div>
          <div className="rounded-xl border border-border/60 bg-background/80 p-4">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <NotebookTabs className="h-4 w-4" />
              Предметов
            </div>
            <div className="mt-2 text-3xl font-bold">{subjectOptions.length}</div>
            <div className="mt-1 text-xs text-muted-foreground">В фильтре сейчас: {filteredSubjectsCount}</div>
          </div>
          <div className="rounded-xl border border-border/60 bg-background/80 p-4">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <GraduationCap className="h-4 w-4" />
              Групп в выборке
            </div>
            <div className="mt-2 text-3xl font-bold">{filteredGroupsCount}</div>
            <div className="mt-1 text-xs text-muted-foreground">Отказ от автомата сразу освобождает место следующему</div>
          </div>
        </div>
      </BlurFade>

      <BlurFade delay={0.18}>
        <div className="space-y-3 rounded-2xl border border-border/60 bg-background/80 p-4">
          <div className="flex flex-col gap-3 xl:flex-row xl:items-center xl:justify-between">
            <div>
              <div className="text-sm font-medium text-foreground">Как смотреть связи</div>
              <div className="text-xs text-muted-foreground">
                По предметам удобно задавать экзамен сразу всем группам. По группам удобно видеть, какие предметы реально есть у каждой группы.
              </div>
            </div>
            <Tabs value={viewMode} onValueChange={(value) => setViewMode(value as OfferingsViewMode)}>
              <TabsList className="grid w-full grid-cols-2 xl:w-[340px]">
                <TabsTrigger value="by_subject">По предметам</TabsTrigger>
                <TabsTrigger value="by_group">По группам</TabsTrigger>
              </TabsList>
            </Tabs>
          </div>
          <OfferingsFilters
            search={search}
            controlFilter={controlFilter}
            subjectOptions={subjectOptions}
            selectedSubject={selectedSubject}
            onSearchChange={setSearch}
            onControlFilterChange={setControlFilter}
            onSubjectChange={setSelectedSubject}
          />
        </div>
      </BlurFade>

      <BlurFade delay={0.19}>
        <OfferingPolicyPanel offerings={offerings} />
      </BlurFade>

      <BlurFade delay={0.2}>
        {loading ? (
          <div className="rounded-xl border border-border/60 bg-background/80 p-10 text-center text-sm text-muted-foreground">
            Загрузка предметов групп…
          </div>
        ) : !filteredOfferings.length ? (
          <div className="rounded-xl border border-dashed border-border/60 bg-background/80 p-10 text-center text-sm text-muted-foreground">
            <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-muted/60">
              <Layers3 className="h-5 w-5" />
            </div>
            По текущим фильтрам связки не найдены.
          </div>
        ) : (
          <OfferingsTable
            offerings={filteredOfferings}
            savingOfferingId={savingOfferingId}
            viewMode={viewMode}
            onControlTypeChange={handleControlTypeChange}
            onOpenQueue={openQueue}
            onOpenExamPrep={openExamPrep}
          />
        )}
      </BlurFade>

      <AutomaticQueueDialog
        open={Boolean(queueOffering)}
        onOpenChange={(open) => !open && setQueueOffering(null)}
        offering={queueOffering}
        queue={queue}
        loading={queueLoading}
        onDecline={handleDecline}
        onRestore={handleRestore}
      />
    </div>
  );
}
