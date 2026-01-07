'use client';

import { useEffect, useState } from 'react';
import { toast } from 'sonner';
import { StudentAPI, StudentLab } from '@/lib/api';
import { CardSpotlight } from '@/components/ui/card-spotlight';
import { TextGenerateEffect } from '@/components/ui/text-generate-effect';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import { IconCheck, IconClock, IconX, IconLock, IconFlask, IconCalendar, IconStar, IconMessage, IconHandStop, IconPlayerPlay } from '@tabler/icons-react';
import { motion, AnimatePresence } from 'motion/react';
import { cn } from '@/lib/utils';
import Link from 'next/link';

export default function LabsPage() {
  const [loading, setLoading] = useState(true);
  const [labs, setLabs] = useState<StudentLab[]>([]);
  const [selectedLab, setSelectedLab] = useState<StudentLab | null>(null);
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

  if (loading) return <LabsSkeleton />;

  const accepted = labs.filter((l) => l.submission?.status === 'ACCEPTED').length;
  const ready = labs.filter((l) => l.submission?.status === 'READY').length;
  const rejected = labs.filter((l) => l.submission?.status === 'REJECTED').length;
  const available = labs.filter((l) => l.is_available && !l.submission).length;
  const locked = labs.filter((l) => !l.is_available).length;
  const progress = labs.length > 0 ? Math.round((accepted / labs.length) * 100) : 0;

  const getStatusConfig = (lab: StudentLab) => {
    if (!lab.is_available) return { icon: IconLock, color: 'text-neutral-400', bg: 'bg-neutral-400/10', label: 'Заблокировано' };
    const status = lab.submission?.status;
    switch (status) {
      case 'ACCEPTED': return { icon: IconCheck, color: 'text-green-500', bg: 'bg-green-500/10', label: 'Принято' };
      case 'READY': return { icon: IconClock, color: 'text-yellow-500', bg: 'bg-yellow-500/10', label: 'В очереди' };
      case 'REJECTED': return { icon: IconX, color: 'text-red-500', bg: 'bg-red-500/10', label: 'Отклонено' };
      default: return { icon: IconFlask, color: 'text-blue-500', bg: 'bg-blue-500/10', label: 'Доступно' };
    }
  };

  return (
    <div className="p-6 space-y-6 max-w-5xl mx-auto">
      <div className="space-y-2">
        <TextGenerateEffect words="Лабораторные работы" className="text-2xl font-bold" duration={0.3} />
        <p className="text-muted-foreground">Выполняй в тетради, сдавай преподавателю</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <StatCard icon={<IconCheck className="h-5 w-5" />} label="Сдано" value={accepted} color="green" />
        <StatCard icon={<IconClock className="h-5 w-5" />} label="В очереди" value={ready} color="yellow" />
        <StatCard icon={<IconX className="h-5 w-5" />} label="Отклонено" value={rejected} color="red" />
        <StatCard icon={<IconFlask className="h-5 w-5" />} label="Доступно" value={available} color="blue" />
        <StatCard icon={<IconLock className="h-5 w-5" />} label="Заблокировано" value={locked} color="neutral" />
      </div>

      <CardSpotlight className="p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-lg font-semibold text-foreground">Общий прогресс</h3>
            <p className="text-sm text-muted-foreground">Сдано {accepted} из {labs.length} работ</p>
          </div>
          <div className="text-3xl font-bold text-foreground">{progress}%</div>
        </div>
        <Progress value={progress} className="h-3" />
      </CardSpotlight>

      {labs.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {labs.map((lab, idx) => {
            const status = getStatusConfig(lab);
            const StatusIcon = status.icon;
            const isLoading = actionLoading === lab.id;
            return (
              <motion.div key={lab.id} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: idx * 0.05 }} className="relative group"
                onMouseEnter={() => setHoveredIndex(idx)} onMouseLeave={() => setHoveredIndex(null)}>
                <AnimatePresence>
                  {hoveredIndex === idx && (
                    <motion.span className="absolute inset-0 h-full w-full bg-neutral-200/50 dark:bg-neutral-800/50 block rounded-xl" layoutId="hoverBackground"
                      initial={{ opacity: 0 }} animate={{ opacity: 1, transition: { duration: 0.15 } }} exit={{ opacity: 0, transition: { duration: 0.15, delay: 0.2 } }} />
                  )}
                </AnimatePresence>
                <div className={cn("relative z-10 p-4 rounded-xl border bg-white dark:bg-neutral-950 transition-all",
                  !lab.is_available && "opacity-60",
                  selectedLab?.id === lab.id ? "border-primary" : "border-neutral-200 dark:border-neutral-800")}>
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <div className={cn("p-2 rounded-lg", status.bg)}><StatusIcon className={cn("h-5 w-5", status.color)} /></div>
                      <span className="text-sm font-medium text-muted-foreground">№{lab.number}</span>
                    </div>
                    <Badge variant={lab.submission?.status === 'ACCEPTED' ? 'default' : lab.submission?.status === 'REJECTED' ? 'destructive' : 'secondary'}>
                      {lab.submission?.grade !== undefined ? `${lab.submission.grade}/${lab.max_grade}` : `—/${lab.max_grade}`}
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

                  <div className="flex items-center justify-between text-xs text-muted-foreground pt-3 border-t border-neutral-200 dark:border-neutral-800">
                    <div className="flex items-center gap-1"><IconCalendar className="h-3 w-3" /><span>{lab.deadline ? new Date(lab.deadline).toLocaleDateString('ru-RU') : 'Без дедлайна'}</span></div>
                  </div>

                  {/* Actions */}
                  <div className="mt-3 flex gap-2">
                    {lab.is_available && (
                      <>
                        <Link href={`/dashboard/labs/${lab.id}`} className="flex-1">
                          <Button variant="outline" size="sm" className="w-full">Открыть</Button>
                        </Link>
                        {!lab.submission && (
                          <Button size="sm" onClick={() => handleMarkReady(lab.id)} disabled={isLoading}>
                            {isLoading ? '...' : <><IconPlayerPlay className="h-4 w-4 mr-1" />Сдать</>}
                          </Button>
                        )}
                        {lab.submission?.status === 'READY' && (
                          <Button size="sm" variant="destructive" onClick={() => handleCancelReady(lab.id)} disabled={isLoading}>
                            {isLoading ? '...' : <><IconHandStop className="h-4 w-4 mr-1" />Отмена</>}
                          </Button>
                        )}
                        {lab.submission?.status === 'REJECTED' && (
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
          <h3 className="text-lg font-semibold text-foreground mb-2">Нет лабораторных работ</h3>
          <p className="text-muted-foreground">Лабораторные работы появятся здесь, когда преподаватель их добавит</p>
        </CardSpotlight>
      )}
    </div>
  );
}

function StatCard({ icon, label, value, color }: { icon: React.ReactNode; label: string; value: number; color: 'green' | 'yellow' | 'red' | 'blue' | 'neutral' }) {
  const colorClasses = { green: 'text-green-500 bg-green-500/10', yellow: 'text-yellow-500 bg-yellow-500/10', red: 'text-red-500 bg-red-500/10', blue: 'text-blue-500 bg-blue-500/10', neutral: 'text-neutral-500 bg-neutral-500/10' };
  return (
    <motion.div initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} className="p-4 rounded-xl border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-950">
      <div className={cn("p-2 rounded-lg w-fit mb-2", colorClasses[color])}>{icon}</div>
      <p className="text-2xl font-bold text-foreground">{value}</p>
      <p className="text-xs text-muted-foreground">{label}</p>
    </motion.div>
  );
}

function LabsSkeleton() {
  return (
    <div className="p-6 space-y-6 max-w-5xl mx-auto">
      <div className="space-y-2"><Skeleton className="h-8 w-64" /><Skeleton className="h-4 w-48" /></div>
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">{[1, 2, 3, 4, 5].map((i) => <Skeleton key={i} className="h-24 rounded-xl" />)}</div>
      <Skeleton className="h-24 rounded-xl" />
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">{[1, 2, 3, 4, 5, 6].map((i) => <Skeleton key={i} className="h-48 rounded-xl" />)}</div>
    </div>
  );
}
