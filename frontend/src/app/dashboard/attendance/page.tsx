'use client';

import { useEffect, useState } from 'react';
import { toast } from 'sonner';
import { StudentAPI, StudentAttendance } from '@/lib/api';
import { CardSpotlight } from '@/components/ui/card-spotlight';
import { TextGenerateEffect } from '@/components/ui/text-generate-effect';
import { NumberTicker } from '@/components/ui/number-ticker';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Progress } from '@/components/ui/progress';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { IconCheck, IconClock, IconX, IconAlertCircle } from '@tabler/icons-react';
import { motion, AnimatePresence } from 'motion/react';
import { cn } from '@/lib/utils';

export default function AttendancePage() {
  const [loading, setLoading] = useState(true);
  const [attendance, setAttendance] = useState<StudentAttendance | null>(null);

  useEffect(() => {
    const loadAttendance = async () => {
      try {
        const data = await StudentAPI.getAttendance();
        setAttendance(data);
      } catch {
        toast.error('Ошибка загрузки посещаемости');
      } finally {
        setLoading(false);
      }
    };
    loadAttendance();
  }, []);

  if (loading) return <AttendanceSkeleton />;

  if (!attendance) {
    return (
      <div className="p-6 max-w-5xl mx-auto">
        <CardSpotlight className="p-12 text-center">
          <IconAlertCircle className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-foreground mb-2">Нет данных</h3>
          <p className="text-muted-foreground">Данные о посещаемости появятся здесь после первого занятия</p>
        </CardSpotlight>
      </div>
    );
  }

  const { stats, records } = attendance;

  const getStatusConfig = (status: string) => {
    switch (status.toLowerCase()) {
      case 'present': return { icon: IconCheck, color: 'text-green-500', label: 'Присутствовал' };
      case 'late': return { icon: IconClock, color: 'text-yellow-500', label: 'Опоздал' };
      case 'excused': return { icon: IconAlertCircle, color: 'text-blue-500', label: 'Уважительная' };
      case 'absent': return { icon: IconX, color: 'text-red-500', label: 'Отсутствовал' };
      default: return { icon: IconAlertCircle, color: 'text-neutral-500', label: status };
    }
  };

  const getStatusVariant = (status: string): 'default' | 'secondary' | 'destructive' | 'outline' => {
    switch (status.toLowerCase()) {
      case 'present': return 'default';
      case 'late': return 'secondary';
      case 'excused': return 'outline';
      case 'absent': return 'destructive';
      default: return 'secondary';
    }
  };

  return (
    <div className="p-6 space-y-6 max-w-5xl mx-auto">
      <div className="space-y-2">
        <TextGenerateEffect words="Посещаемость" className="text-2xl font-bold" duration={0.3} />
        <p className="text-muted-foreground">Всего занятий: {stats.total_classes}</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard icon={<IconCheck className="h-5 w-5" />} label="Присутствовал" value={stats.present} color="green" />
        <StatCard icon={<IconClock className="h-5 w-5" />} label="Опоздал" value={stats.late} color="yellow" />
        <StatCard icon={<IconAlertCircle className="h-5 w-5" />} label="Уважительная" value={stats.excused} color="blue" />
        <StatCard icon={<IconX className="h-5 w-5" />} label="Пропустил" value={stats.absent} color="red" />
      </div>

      <CardSpotlight className="p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-lg font-semibold text-foreground">Процент посещаемости</h3>
            <p className="text-sm text-muted-foreground">{stats.present + stats.late} из {stats.total_classes} занятий</p>
          </div>
          <div className="text-3xl font-bold text-foreground"><NumberTicker value={Math.round(stats.attendance_rate)} />%</div>
        </div>
        <Progress value={stats.attendance_rate} className="h-3" />
      </CardSpotlight>

      <CardSpotlight className="p-6">
        <h3 className="text-lg font-semibold text-foreground mb-4">История посещений</h3>
        {records && records.length > 0 ? (
          <div className="rounded-lg border border-neutral-200 dark:border-neutral-800 overflow-hidden">
            <Table>
              <TableHeader>
                <TableRow className="border-neutral-200 dark:border-neutral-800 hover:bg-transparent">
                  <TableHead className="text-neutral-500 dark:text-neutral-400">Дата</TableHead>
                  <TableHead className="text-neutral-500 dark:text-neutral-400">Статус</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                <AnimatePresence>
                  {records.map((record, index) => {
                    const status = getStatusConfig(record.status);
                    const StatusIcon = status.icon;
                    return (
                      <motion.tr key={index} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.03 }} className="border-neutral-200 dark:border-neutral-800">
                        <TableCell className="text-foreground">
                          {new Date(record.date).toLocaleDateString('ru-RU', { weekday: 'short', day: 'numeric', month: 'short' })}
                        </TableCell>
                        <TableCell>
                          <Badge variant={getStatusVariant(record.status)} className="gap-1">
                            <StatusIcon className="h-3 w-3" />
                            {status.label}
                          </Badge>
                        </TableCell>
                      </motion.tr>
                    );
                  })}
                </AnimatePresence>
              </TableBody>
            </Table>
          </div>
        ) : (
          <div className="text-center py-8 text-muted-foreground">Нет записей о посещениях</div>
        )}
      </CardSpotlight>
    </div>
  );
}

function StatCard({ icon, label, value, color }: { icon: React.ReactNode; label: string; value: number; color: 'green' | 'yellow' | 'blue' | 'red' }) {
  const colorClasses = {
    green: 'text-green-500 bg-green-500/10',
    yellow: 'text-yellow-500 bg-yellow-500/10',
    blue: 'text-blue-500 bg-blue-500/10',
    red: 'text-red-500 bg-red-500/10',
  };

  return (
    <motion.div initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} className="p-4 rounded-xl border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-950">
      <div className={cn("p-2 rounded-lg w-fit mb-2", colorClasses[color])}>{icon}</div>
      <p className="text-2xl font-bold text-foreground"><NumberTicker value={value} /></p>
      <p className="text-xs text-muted-foreground">{label}</p>
    </motion.div>
  );
}

function AttendanceSkeleton() {
  return (
    <div className="p-6 space-y-6 max-w-5xl mx-auto">
      <div className="space-y-2"><Skeleton className="h-8 w-48" /><Skeleton className="h-4 w-32" /></div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">{[1, 2, 3, 4].map((i) => <Skeleton key={i} className="h-24 rounded-xl" />)}</div>
      <Skeleton className="h-24 rounded-xl" />
      <Skeleton className="h-64 rounded-xl" />
    </div>
  );
}
