'use client';

import { useEffect, useState } from 'react';
import { toast } from 'sonner';
import { StudentAPI, StudentLab } from '@/lib/api';
import { CardSpotlight } from '@/components/ui/card-spotlight';
import { TextGenerateEffect } from '@/components/ui/text-generate-effect';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Progress } from '@/components/ui/progress';
import { IconCheck, IconClock, IconX, IconQuestionMark, IconFlask, IconCalendar, IconStar, IconMessage } from '@tabler/icons-react';
import { motion, AnimatePresence } from 'motion/react';
import { cn } from '@/lib/utils';

export default function LabsPage() {
  const [loading, setLoading] = useState(true);
  const [labs, setLabs] = useState<StudentLab[]>([]);
  const [selectedLab, setSelectedLab] = useState<StudentLab | null>(null);
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);

  useEffect(() => {
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
    loadLabs();
  }, []);

  if (loading) return <LabsSkeleton />;

  const accepted = labs.filter((l) => l.submission?.status === 'ACCEPTED').length;
  const pending = labs.filter((l) => l.submission?.status === 'PENDING').length;
  const rejected = labs.filter((l) => l.submission?.status === 'REJECTED').length;
  const notSubmitted = labs.filter((l) => !l.submission).length;
  const progress = labs.length > 0 ? Math.round((accepted / labs.length) * 100) : 0;

  const getStatusConfig = (status?: string) => {
    switch (status) {
      case 'ACCEPTED': return { icon: IconCheck, color: 'text-green-500', bg: 'bg-green-500/10', label: 'Принято' };
      case 'PENDING': return { icon: IconClock, color: 'text-yellow-500', bg: 'bg-yellow-500/10', label: 'На проверке' };
      case 'REJECTED': return { icon: IconX, color: 'text-red-500', bg: 'bg-red-500/10', label: 'Отклонено' };
      default: return { icon: IconQuestionMark, color: 'text-neutral-500', bg: 'bg-neutral-500/10', label: 'Не сдано' };
    }
  };

  return (
    <div className="p-6 space-y-6 max-w-5xl mx-auto">
      <div className="space-y-2">
        <TextGenerateEffect words="Лабораторные работы" className="text-2xl font-bold" duration={0.3} />
        <p className="text-muted-foreground">Отслеживай прогресс сдачи и оценки</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard icon={<IconCheck className="h-5 w-5" />} label="Принято" value={accepted} color="green" />
        <StatCard icon={<IconClock className="h-5 w-5" />} label="На проверке" value={pending} color="yellow" />
        <StatCard icon={<IconX className="h-5 w-5" />} label="Отклонено" value={rejected} color="red" />
        <StatCard icon={<IconQuestionMark className="h-5 w-5" />} label="Не сдано" value={notSubmitted} color="neutral" />
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
            const status = getStatusConfig(lab.submission?.status);
            const StatusIcon = status.icon;
            return (
              <motion.div key={lab.id} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: idx * 0.05 }} className="relative group"
                onMouseEnter={() => setHoveredIndex(idx)} onMouseLeave={() => setHoveredIndex(null)} onClick={() => setSelectedLab(selectedLab?.id === lab.id ? null : lab)}>
                <AnimatePresence>
                  {hoveredIndex === idx && (
                    <motion.span className="absolute inset-0 h-full w-full bg-neutral-200/50 dark:bg-neutral-800/50 block rounded-xl" layoutId="hoverBackground"
                      initial={{ opacity: 0 }} animate={{ opacity: 1, transition: { duration: 0.15 } }} exit={{ opacity: 0, transition: { duration: 0.15, delay: 0.2 } }} />
                  )}
                </AnimatePresence>
                <div className={cn("relative z-10 p-4 rounded-xl border bg-white dark:bg-neutral-950 cursor-pointer transition-all",
                  selectedLab?.id === lab.id ? "border-primary" : "border-neutral-200 dark:border-neutral-800")}>
                  <div className="flex items-start justify-between mb-3">
                    <div className={cn("p-2 rounded-lg", status.bg)}><StatusIcon className={cn("h-5 w-5", status.color)} /></div>
                    <Badge variant={lab.submission?.status === 'ACCEPTED' ? 'default' : lab.submission?.status === 'REJECTED' ? 'destructive' : 'secondary'}>
                      {lab.submission?.grade !== undefined ? `${lab.submission.grade}/${lab.max_grade}` : `—/${lab.max_grade}`}
                    </Badge>
                  </div>
                  <h4 className="font-semibold text-foreground mb-1 line-clamp-2">{lab.title}</h4>
                  <p className={cn("text-sm mb-3", status.color)}>{status.label}</p>
                  <div className="flex items-center justify-between text-xs text-muted-foreground pt-3 border-t border-neutral-200 dark:border-neutral-800">
                    <div className="flex items-center gap-1"><IconCalendar className="h-3 w-3" /><span>{lab.deadline ? new Date(lab.deadline).toLocaleDateString('ru-RU') : 'Без дедлайна'}</span></div>
                    {lab.submission?.submitted_at && <span>Сдано: {new Date(lab.submission.submitted_at).toLocaleDateString('ru-RU')}</span>}
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

      <AnimatePresence>
        {selectedLab && (
          <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }} className="overflow-hidden">
            <CardSpotlight className="p-6">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h3 className="text-xl font-semibold text-foreground">{selectedLab.title}</h3>
                  <p className={cn("text-sm", getStatusConfig(selectedLab.submission?.status).color)}>{getStatusConfig(selectedLab.submission?.status).label}</p>
                </div>
                <button onClick={() => setSelectedLab(null)} className="text-muted-foreground hover:text-foreground transition-colors"><IconX className="h-5 w-5" /></button>
              </div>
              {selectedLab.description && <div className="mb-4"><h4 className="text-sm font-medium text-foreground mb-1">Описание</h4><p className="text-sm text-muted-foreground">{selectedLab.description}</p></div>}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <DetailItem icon={<IconStar className="h-4 w-4" />} label="Максимальный балл" value={selectedLab.max_grade.toString()} />
                <DetailItem icon={<IconCalendar className="h-4 w-4" />} label="Дедлайн" value={selectedLab.deadline ? new Date(selectedLab.deadline).toLocaleDateString('ru-RU') : 'Не указан'} />
                {selectedLab.submission?.grade !== undefined && <DetailItem icon={<IconCheck className="h-4 w-4" />} label="Ваша оценка" value={`${selectedLab.submission.grade}/${selectedLab.max_grade}`} />}
                {selectedLab.submission?.submitted_at && <DetailItem icon={<IconClock className="h-4 w-4" />} label="Дата сдачи" value={new Date(selectedLab.submission.submitted_at).toLocaleString('ru-RU')} />}
              </div>
              {selectedLab.submission?.feedback && (
                <div className="mt-4 p-4 rounded-lg bg-neutral-50 dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800">
                  <div className="flex items-center gap-2 mb-2"><IconMessage className="h-4 w-4 text-primary" /><h4 className="text-sm font-medium text-foreground">Комментарий преподавателя</h4></div>
                  <p className="text-sm text-muted-foreground">{selectedLab.submission.feedback}</p>
                </div>
              )}
            </CardSpotlight>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function StatCard({ icon, label, value, color }: { icon: React.ReactNode; label: string; value: number; color: 'green' | 'yellow' | 'red' | 'neutral' }) {
  const colorClasses = { green: 'text-green-500 bg-green-500/10', yellow: 'text-yellow-500 bg-yellow-500/10', red: 'text-red-500 bg-red-500/10', neutral: 'text-neutral-500 bg-neutral-500/10' };
  return (
    <motion.div initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} className="p-4 rounded-xl border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-950">
      <div className={cn("p-2 rounded-lg w-fit mb-2", colorClasses[color])}>{icon}</div>
      <p className="text-2xl font-bold text-foreground">{value}</p>
      <p className="text-xs text-muted-foreground">{label}</p>
    </motion.div>
  );
}

function DetailItem({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <div className="p-3 rounded-lg bg-neutral-50 dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800">
      <div className="flex items-center gap-2 text-muted-foreground mb-1">{icon}<span className="text-xs">{label}</span></div>
      <p className="text-sm font-medium text-foreground">{value}</p>
    </div>
  );
}

function LabsSkeleton() {
  return (
    <div className="p-6 space-y-6 max-w-5xl mx-auto">
      <div className="space-y-2"><Skeleton className="h-8 w-64" /><Skeleton className="h-4 w-48" /></div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">{[1, 2, 3, 4].map((i) => <Skeleton key={i} className="h-24 rounded-xl" />)}</div>
      <Skeleton className="h-24 rounded-xl" />
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">{[1, 2, 3, 4, 5, 6].map((i) => <Skeleton key={i} className="h-40 rounded-xl" />)}</div>
    </div>
  );
}
