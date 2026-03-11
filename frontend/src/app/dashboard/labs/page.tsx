'use client';

import { useEffect, useState, useMemo } from 'react';
import { toast } from 'sonner';
import { StudentAPI, StudentLab } from '@/lib/api';
import { CardSpotlight } from '@/components/ui/card-spotlight';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Button } from '@/components/ui/button';
import { IconCheck, IconClock, IconX, IconLock, IconFlask, IconCalendar, IconHandStop, IconPlayerPlay } from '@tabler/icons-react';
import { motion, AnimatePresence } from 'motion/react';
import { cn } from '@/lib/utils';
import Link from 'next/link';
import {
  getResolvedAcceptanceLabel,
  getResolvedLabGrade,
  getResolvedLabStatus,
  getResolvedLabStatusLabel,
  isLabAccepted,
} from '@/lib/labs/progress';

type FilterStatus = 'all' | 'not_submitted' | 'in_queue' | 'accepted' | 'rejected';

export default function LabsPage() {
  const [loading, setLoading] = useState(true);
  const [labs, setLabs] = useState<StudentLab[]>([]);
  const [filter, setFilter] = useState<FilterStatus>('all');
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const loadLabs = async () => {
    try {
      const data = await StudentAPI.getLabs();
      setLabs(data);
    } catch {
      toast.error('Ошибка загрузки лабораторных');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadLabs();
  }, []);

  const handleMarkReady = async (labId: string) => {
    setActionLoading(labId);
    try {
      await StudentAPI.markLabReady(labId);
      toast.success('Вы в очереди! Подойдите к преподавателю с тетрадью.');
      await loadLabs();
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      toast.error(err.response?.data?.detail || 'Ошибка');
    } finally {
      setActionLoading(null);
    }
  };

  const handleCancelReady = async (labId: string) => {
    setActionLoading(labId);
    try {
      await StudentAPI.cancelLabReady(labId);
      toast.success('Вы вышли из очереди');
      await loadLabs();
    } catch {
      toast.error('Ошибка');
    } finally {
      setActionLoading(null);
    }
  };

  // Counts for filters
  const counts = useMemo(() => {
    const getStatus = (lab: StudentLab) => getResolvedLabStatus(lab);
    const accepted = labs.filter(isLabAccepted).length;
    const inQueue = labs.filter((l) => getStatus(l) === 'pending').length;
    const rejected = labs.filter((l) => getStatus(l) === 'rejected').length;
    const notSubmitted = labs.filter((l) => l.is_available && getStatus(l) === 'not_submitted').length;
    return { all: labs.length, accepted, in_queue: inQueue, rejected, not_submitted: notSubmitted };
  }, [labs]);

  // Filtered labs
  const filteredLabs = useMemo(() => {
    const getStatus = (lab: StudentLab) => getResolvedLabStatus(lab);
    if (filter === 'all') return labs;
    if (filter === 'accepted') return labs.filter(isLabAccepted);
    if (filter === 'in_queue') return labs.filter((l) => getStatus(l) === 'pending');
    if (filter === 'rejected') return labs.filter((l) => getStatus(l) === 'rejected');
    if (filter === 'not_submitted') return labs.filter((l) => l.is_available && getStatus(l) === 'not_submitted');
    return labs;
  }, [labs, filter]);

  const progress = labs.length > 0 ? Math.round((counts.accepted / labs.length) * 100) : 0;

  if (loading) return <LabsSkeleton />;

  const getStatusConfig = (lab: StudentLab) => {
    if (!lab.is_available) return { icon: IconLock, color: 'text-neutral-400', bg: 'bg-neutral-400/10', label: 'Заблокировано', border: 'border-neutral-500/20' };
    const status = getResolvedLabStatus(lab);
    switch (status) {
      case 'accepted': return { icon: IconCheck, color: 'text-green-500', bg: 'bg-green-500/10', label: getResolvedAcceptanceLabel(lab), border: 'border-green-500/30' };
      case 'pending': return { icon: IconClock, color: 'text-yellow-500', bg: 'bg-yellow-500/10', label: 'В очереди', border: 'border-yellow-500/30' };
      case 'rejected': return { icon: IconX, color: 'text-red-500', bg: 'bg-red-500/10', label: getResolvedLabStatusLabel(lab), border: 'border-red-500/30' };
      default: return { icon: IconFlask, color: 'text-blue-500', bg: 'bg-blue-500/10', label: 'Доступно', border: 'border-blue-500/20' };
    }
  };

  const filters: { value: FilterStatus; label: string }[] = [
    { value: 'all', label: 'Все' },
    { value: 'not_submitted', label: 'Не сдано' },
    { value: 'in_queue', label: 'В очереди' },
    { value: 'accepted', label: 'Принято' },
    { value: 'rejected', label: 'Отклонено' },
  ];

  return (
    <div className="p-6 space-y-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="space-y-2">
        <h1 className="text-2xl font-bold text-foreground">Лабораторные работы</h1>
        <p className="text-muted-foreground">Выполняй в тетради, сдавай преподавателю</p>
      </div>

      {/* Progress Card */}
      <CardSpotlight className="p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-lg font-semibold text-foreground">Общий прогресс</h3>
            <p className="text-sm text-muted-foreground">Сдано {counts.accepted} из {labs.length} работ</p>
          </div>
          <div className="text-3xl font-bold text-green-500">{progress}%</div>
        </div>
        <div className="relative h-3 bg-muted/50 rounded-full overflow-hidden">
          <div 
            className="h-full rounded-full bg-gradient-to-r from-green-500 to-emerald-400 transition-all duration-500"
            style={{ width: `${progress}%` }}
          />
        </div>
      </CardSpotlight>

      {/* Filter Buttons */}
      <div className="flex flex-wrap gap-2">
        {filters.map((f) => (
          <Button
            key={f.value}
            variant={filter === f.value ? 'default' : 'secondary'}
            size="sm"
            onClick={() => setFilter(f.value)}
            className={cn("gap-2", filter !== f.value && "bg-card hover:bg-card/80")}
          >
            {f.label}
            <span className={cn(
              "rounded-full px-1.5 py-0.5 text-xs",
              filter === f.value ? "bg-background/20" : "bg-muted"
            )}>
              {counts[f.value]}
            </span>
          </Button>
        ))}
      </div>

      {/* Labs Grid */}
      {filteredLabs.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredLabs.map((lab, idx) => {
            const status = getStatusConfig(lab);
            const StatusIcon = status.icon;
            const isLoading = actionLoading === lab.id;
            const resolvedGrade = getResolvedLabGrade(lab);
            const resolvedStatus = getResolvedLabStatus(lab);

            
            return (
              <motion.div key={lab.id} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: idx * 0.03 }} className="relative group"
                onMouseEnter={() => setHoveredIndex(idx)} onMouseLeave={() => setHoveredIndex(null)}>
                <AnimatePresence>
                  {hoveredIndex === idx && (
                    <motion.span className="absolute inset-0 h-full w-full bg-neutral-200/50 dark:bg-neutral-800/50 block rounded-xl" layoutId="hoverBackground"
                      initial={{ opacity: 0 }} animate={{ opacity: 1, transition: { duration: 0.15 } }} exit={{ opacity: 0, transition: { duration: 0.15, delay: 0.2 } }} />
                  )}
                </AnimatePresence>
                <div className={cn("relative z-10 p-4 rounded-xl border bg-card transition-all",
                  !lab.is_available && "opacity-60",
                  status.border)}>
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <div className={cn("p-2 rounded-lg", status.bg)}><StatusIcon className={cn("h-5 w-5", status.color)} /></div>
                      <span className="text-sm font-medium text-muted-foreground">№{lab.number}</span>
                    </div>
                    <Badge variant={lab.is_accepted ? 'default' : resolvedStatus === 'rejected' ? 'destructive' : 'secondary'}
                      className={cn(
                        lab.current_max_grade && lab.current_max_grade < lab.max_grade && resolvedGrade === undefined && "bg-orange-500/10 text-orange-500 border-orange-500/30"
                      )}>
                      {resolvedGrade !== undefined
                        ? `${resolvedGrade}/${lab.max_grade}` 
                        : lab.current_max_grade && lab.current_max_grade < lab.max_grade
                          ? `макс. ${lab.current_max_grade}`
                          : `—/${lab.max_grade}`}
                    </Badge>
                  </div>
                  <h4 className="font-semibold text-foreground mb-1 line-clamp-2">{lab.title}</h4>
                  {lab.topic && <p className="text-xs text-muted-foreground mb-2 line-clamp-1">{lab.topic}</p>}
                  <p className={cn("text-sm mb-3", status.color)}>{status.label}</p>
                  

                  
                  {lab.variant_number && (
                    <div className="text-xs text-muted-foreground mb-3">
                      Ваш вариант: <span className="font-semibold text-foreground">{lab.variant_number}</span>
                    </div>
                  )}

                  <div className="flex items-center justify-between text-xs text-muted-foreground pt-3 border-t border-border">
                    <div className="flex items-center gap-1">
                      <IconCalendar className="h-3 w-3" />
                      <span className={cn(
                        lab.deadline_5_status === 'expired' && !lab.has_extension && "text-red-500 font-medium",
                        lab.has_extension && "text-green-500 font-medium",
                        lab.lessons_until_deadline_5 !== undefined && lab.lessons_until_deadline_5 !== null && lab.lessons_until_deadline_5 <= 1 && lab.deadline_5_status !== 'expired' && !lab.has_extension && "text-orange-500 font-medium"
                      )}>
                        {lab.has_extension
                          ? `+${lab.extension_bonus} пар (продление)`
                          : lab.deadline_5_status === 'expired'
                            ? 'На 5 уже нельзя'
                            : lab.lessons_until_deadline_5 !== undefined && lab.lessons_until_deadline_5 !== null
                              ? lab.lessons_until_deadline_5 === 0
                                ? 'Последняя пара на 5'
                                : `Ещё ${lab.lessons_until_deadline_5} пар на 5`
                              : lab.deadline_5_lessons
                                ? 'Дедлайн не активен'
                                : 'Без дедлайна'
                        }
                      </span>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="mt-3 flex gap-2">
                    {lab.is_available && (
                      <>
                        <Link href={`/dashboard/labs/${lab.id}`} className="flex-1">
                          <Button variant="outline" size="sm" className="w-full">Открыть</Button>
                        </Link>
                        {!lab.is_accepted && (resolvedStatus === 'not_submitted') && (
                          <Button size="sm" onClick={() => handleMarkReady(lab.id)} disabled={isLoading}>
                            {isLoading ? '...' : <><IconPlayerPlay className="h-4 w-4 mr-1" />Сдать</>}
                          </Button>
                        )}
                        {!lab.is_accepted && lab.submission?.status === 'READY' && (
                          <Button size="sm" variant="destructive" onClick={() => handleCancelReady(lab.id)} disabled={isLoading}>
                            {isLoading ? '...' : <><IconHandStop className="h-4 w-4 mr-1" />Отмена</>}
                          </Button>
                        )}
                        {!lab.is_accepted && resolvedStatus === 'rejected' && (
                          <Button size="sm" onClick={() => handleMarkReady(lab.id)} disabled={isLoading}>
                            {isLoading ? '...' : 'Пересдать'}
                          </Button>
                        )}
                      </>
                    )}
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>
      ) : (
        <CardSpotlight className="p-12 text-center">
          <IconFlask className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-foreground mb-2">
            {filter === 'all' ? 'Нет лабораторных работ' : 'Нет работ с таким статусом'}
          </h3>
          <p className="text-muted-foreground">
            {filter === 'all' ? 'Лабораторные работы появятся здесь, когда преподаватель их добавит' : 'Попробуйте выбрать другой фильтр'}
          </p>
        </CardSpotlight>
      )}
    </div>
  );
}

function LabsSkeleton() {
  return (
    <div className="p-6 space-y-6 max-w-6xl mx-auto">
      <div className="space-y-2"><Skeleton className="h-8 w-64" /><Skeleton className="h-4 w-48" /></div>
      <Skeleton className="h-24 rounded-xl" />
      <div className="flex gap-2">{[1, 2, 3, 4, 5].map((i) => <Skeleton key={i} className="h-9 w-24 rounded-md" />)}</div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">{[1, 2, 3, 4, 5, 6].map((i) => <Skeleton key={i} className="h-48 rounded-xl" />)}</div>
    </div>
  );
}
