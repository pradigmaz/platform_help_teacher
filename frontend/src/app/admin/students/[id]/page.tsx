'use client';

import { useParams, useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { ArrowLeft, User, Users, Calendar, CheckCircle, Clock, XCircle, AlertCircle, TrendingUp, Award, AlertTriangle, Trophy, Target, Flame, Unlink } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog';
import { toast } from 'sonner';
import { NumberTicker } from '@/components/ui/number-ticker';
import { BlurFade } from '@/components/ui/blur-fade';
import { MagicCard } from '@/components/ui/magic-card';
import { BorderBeam } from '@/components/ui/border-beam';
import { Sparkles } from '@/components/ui/sparkles';
import { AnimatedCircularProgress } from '@/components/ui/animated-circular-progress';
import dynamic from 'next/dynamic';
import api from '@/lib/api';
import { StudentActivitiesList } from '@/components/admin/StudentActivitiesList';

interface LabSubmission {
  lab_id: string;
  lab_title: string;
  status: string | null;
  grade: number | null;
  max_grade: number;
  deadline: string | null;
  submitted_at: string | null;
  feedback: string | null;
  is_overdue: boolean;
}

interface StudentStats {
  labs_total: number;
  labs_submitted: number;
  labs_accepted: number;
  labs_rejected: number;
  labs_pending: number;
  labs_overdue: number;
  points_earned: number;
  points_max: number;
  points_percent: number;
  group_rank: number | null;
  group_total: number | null;
  group_percentile: number | null;
}

interface StudentProfile {
  id: string;
  full_name: string;
  username: string | null;
  telegram_id: string | null;
  group_name: string | null;
  group_id: string | null;
  is_active: boolean;
  created_at: string;
  labs: LabSubmission[];
  stats: StudentStats;
}

const STATUS_CONFIG: Record<string, { color: string; icon: React.ReactNode; label: string }> = {
  NEW: { color: 'bg-blue-500', icon: <Clock className="w-3 h-3" />, label: 'Новая' },
  IN_REVIEW: { color: 'bg-yellow-500', icon: <Clock className="w-3 h-3" />, label: 'На проверке' },
  REQ_CHANGES: { color: 'bg-orange-500', icon: <AlertCircle className="w-3 h-3" />, label: 'Доработка' },
  ACCEPTED: { color: 'bg-green-500', icon: <CheckCircle className="w-3 h-3" />, label: 'Принято' },
  REJECTED: { color: 'bg-red-500', icon: <XCircle className="w-3 h-3" />, label: 'Отклонено' },
};

const COLORS = {
  accepted: '#22c55e',
  pending: '#eab308',
  rejected: '#ef4444',
  notSubmitted: '#94a3b8',
  overdue: '#f97316',
};

const StudentLabsChart = dynamic(() => import('@/components/admin/StudentLabsChart'), {
  ssr: false,
  loading: () => <Skeleton className="h-[350px] w-full" />,
});

export default function StudentProfilePage() {
  const params = useParams();
  const router = useRouter();
  const studentId = params.id as string;
  
  const [student, setStudent] = useState<StudentProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [resettingTelegram, setResettingTelegram] = useState(false);

  const handleResetTelegram = async () => {
    try {
      setResettingTelegram(true);
      await api.post(`/admin/students/${studentId}/reset-telegram`);
      toast.success('Telegram отвязан');
      // Обновляем данные
      const { data } = await api.get<StudentProfile>(`/admin/students/${studentId}`);
      setStudent(data);
    } catch {
      toast.error('Ошибка при сбросе Telegram');
    } finally {
      setResettingTelegram(false);
    }
  };

  useEffect(() => {
    const fetchStudent = async () => {
      try {
        const { data } = await api.get<StudentProfile>(`/admin/students/${studentId}`);
        setStudent(data);
      } catch (e) {
        setError('Не удалось загрузить данные студента');
      } finally {
        setLoading(false);
      }
    };
    fetchStudent();
  }, [studentId]);

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto p-8 space-y-6">
        <Skeleton className="h-10 w-48" />
        <Skeleton className="h-32 w-full" />
        <div className="grid grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => <Skeleton key={i} className="h-32" />)}
        </div>
      </div>
    );
  }

  if (error || !student) {
    return (
      <div className="max-w-6xl mx-auto p-8">
        <Button variant="ghost" onClick={() => router.back()}>
          <ArrowLeft className="w-4 h-4 mr-2" /> Назад
        </Button>
        <p className="text-center text-red-500 mt-8">{error || 'Студент не найден'}</p>
      </div>
    );
  }

  const { stats } = student;
  const notSubmitted = stats.labs_total - stats.labs_submitted;

  const labsStatusData = [
    { name: 'Принято', value: stats.labs_accepted, color: COLORS.accepted },
    { name: 'На проверке', value: stats.labs_pending, color: COLORS.pending },
    { name: 'Отклонено', value: stats.labs_rejected, color: COLORS.rejected },
    { name: 'Не сдано', value: notSubmitted - stats.labs_overdue, color: COLORS.notSubmitted },
    { name: 'Долги', value: stats.labs_overdue, color: COLORS.overdue },
  ].filter(d => d.value > 0);

  return (
    <div className="max-w-6xl mx-auto p-8 space-y-6">
      {/* Header */}
      <BlurFade delay={0.1}>
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => router.back()}>
            <ArrowLeft className="w-5 h-5" />
          </Button>
          <h1 className="text-2xl font-bold">Профиль студента</h1>
        </div>
      </BlurFade>

      {/* Profile Card */}
      <BlurFade delay={0.2}>
        <Card className="relative overflow-hidden bg-gradient-to-br from-background via-background to-primary/5">
          <BorderBeam size={250} duration={12} delay={9} />
          <CardContent className="pt-6">
            <div className="flex items-start gap-6">
              <div className="relative">
                <div className="w-20 h-20 rounded-full bg-gradient-to-br from-primary via-purple-500 to-pink-500 p-[3px]">
                  <div className="w-full h-full rounded-full bg-background flex items-center justify-center">
                    <User className="w-10 h-10 text-primary" />
                  </div>
                </div>
                {stats.group_rank === 1 && (
                  <div className="absolute -top-1 -right-1">
                    <Sparkles color="#FFD700">
                      <Trophy className="w-6 h-6 text-yellow-500" />
                    </Sparkles>
                  </div>
                )}
              </div>
              <div className="flex-1 min-w-0">
                <h2 className="text-2xl font-bold truncate">{student.full_name}</h2>
                {student.username && (
                  <p className="text-muted-foreground">@{student.username}</p>
                )}
                <div className="flex flex-wrap gap-2 mt-3">
                  {student.group_name && (
                    <Badge variant="secondary" className="gap-1 px-3 py-1">
                      <Users className="w-3 h-3" /> {student.group_name}
                    </Badge>
                  )}
                  <Badge 
                    variant={student.is_active ? 'default' : 'destructive'}
                    className={student.is_active ? 'bg-gradient-to-r from-green-500 to-emerald-500 dark:from-green-600 dark:to-emerald-600 text-white' : ''}
                  >
                    {student.is_active ? '● Активен' : '○ Неактивен'}
                  </Badge>
                  {stats.group_rank && stats.group_total && (
                    <Badge variant="outline" className="gap-1 bg-gradient-to-r from-yellow-500/10 to-orange-500/10 border-yellow-500/30">
                      <Award className="w-3 h-3 text-yellow-500" />
                      <span className="font-bold">{stats.group_rank}</span> из {stats.group_total}
                    </Badge>
                  )}
                </div>
                
                {/* Кнопка сброса Telegram */}
                {student.telegram_id && (
                  <div className="mt-4 pt-4 border-t">
                    <AlertDialog>
                      <AlertDialogTrigger asChild>
                        <Button variant="outline" size="sm" className="text-orange-600 border-orange-300 hover:bg-orange-50 dark:text-orange-400 dark:border-orange-700 dark:hover:bg-orange-900/20">
                          <Unlink className="w-4 h-4 mr-2" />
                          Отвязать Telegram
                        </Button>
                      </AlertDialogTrigger>
                      <AlertDialogContent>
                        <AlertDialogHeader>
                          <AlertDialogTitle>Отвязать Telegram?</AlertDialogTitle>
                          <AlertDialogDescription>
                            Студент <strong>{student.full_name}</strong> потеряет доступ к системе через текущий Telegram-аккаунт. 
                            Ему нужно будет заново ввести инвайт-код в боте.
                          </AlertDialogDescription>
                        </AlertDialogHeader>
                        <AlertDialogFooter>
                          <AlertDialogCancel>Отмена</AlertDialogCancel>
                          <AlertDialogAction 
                            onClick={handleResetTelegram}
                            disabled={resettingTelegram}
                            className="bg-orange-600 hover:bg-orange-700"
                          >
                            {resettingTelegram ? 'Отвязываю...' : 'Да, отвязать'}
                          </AlertDialogAction>
                        </AlertDialogFooter>
                      </AlertDialogContent>
                    </AlertDialog>
                  </div>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      </BlurFade>

      {/* Stats Cards with NumberTicker */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <BlurFade delay={0.3}>
          <MagicCard className="cursor-pointer group" gradientColor="#22c55e20">
            <div className="p-6 text-center relative overflow-hidden">
              <div className="absolute top-2 right-2 opacity-10 group-hover:opacity-20 transition-opacity">
                <CheckCircle className="w-12 h-12 text-green-500 dark:text-green-400" />
              </div>
              <div className="text-4xl font-bold text-green-600 dark:text-green-400">
                <NumberTicker value={stats.labs_accepted} />
              </div>
              <div className="text-sm text-muted-foreground mt-1 font-medium">Сдано</div>
            </div>
          </MagicCard>
        </BlurFade>
        
        <BlurFade delay={0.35}>
          <MagicCard className="cursor-pointer group" gradientColor="#eab30820">
            <div className="p-6 text-center relative overflow-hidden">
              <div className="absolute top-2 right-2 opacity-10 group-hover:opacity-20 transition-opacity">
                <Clock className="w-12 h-12 text-yellow-500 dark:text-yellow-400" />
              </div>
              <div className="text-4xl font-bold text-yellow-600 dark:text-yellow-400">
                <NumberTicker value={stats.labs_pending} />
              </div>
              <div className="text-sm text-muted-foreground mt-1 font-medium">На проверке</div>
            </div>
          </MagicCard>
        </BlurFade>
        
        <BlurFade delay={0.4}>
          <MagicCard className="cursor-pointer group" gradientColor="#f9731620">
            <div className="p-6 text-center relative overflow-hidden">
              <div className="absolute top-2 right-2 opacity-10 group-hover:opacity-20 transition-opacity">
                <Flame className="w-12 h-12 text-orange-500 dark:text-orange-400" />
              </div>
              <div className="text-4xl font-bold text-orange-600 dark:text-orange-400">
                <NumberTicker value={stats.labs_overdue} />
              </div>
              <div className="text-sm text-muted-foreground mt-1 font-medium">Долги</div>
            </div>
          </MagicCard>
        </BlurFade>
        
        <BlurFade delay={0.45}>
          <MagicCard className="cursor-pointer group" gradientColor="#3b82f620">
            <div className="p-6 text-center relative overflow-hidden">
              <div className="absolute top-2 right-2 opacity-10 group-hover:opacity-20 transition-opacity">
                <Target className="w-12 h-12 text-blue-500 dark:text-blue-400" />
              </div>
              <div className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-cyan-500 dark:from-blue-400 dark:to-cyan-400 bg-clip-text text-transparent">
                <NumberTicker value={stats.points_percent} decimalPlaces={0} />%
              </div>
              <div className="text-sm text-muted-foreground mt-1 font-medium">Успеваемость</div>
            </div>
          </MagicCard>
        </BlurFade>
      </div>

      {/* Activity List */}
      <BlurFade delay={0.48}>
        <StudentActivitiesList 
          studentId={student.id} 
          studentName={student.full_name} 
        />
      </BlurFade>

      {/* Charts Row */}
      <div className="grid md:grid-cols-2 gap-6">
        <BlurFade delay={0.5}>
          <StudentLabsChart data={labsStatusData} />
        </BlurFade>

        <BlurFade delay={0.55}>
          <Card className="overflow-hidden">
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-base">
                <TrendingUp className="w-5 h-5" />
                Прогресс
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-3 gap-4 py-4">
                <div className="flex flex-col items-center">
                  <AnimatedCircularProgress
                    value={stats.points_percent}
                    size={100}
                    strokeWidth={8}
                    gradientFrom="#22c55e"
                    gradientTo="#10b981"
                    label="Баллы"
                  />
                  <div className="mt-2 text-center">
                    <span className="text-xs text-muted-foreground">
                      {stats.points_earned} / {stats.points_max}
                    </span>
                  </div>
                </div>
                
                <div className="flex flex-col items-center">
                  <AnimatedCircularProgress
                    value={stats.labs_total > 0 ? (stats.labs_accepted / stats.labs_total) * 100 : 0}
                    size={100}
                    strokeWidth={8}
                    gradientFrom="#3b82f6"
                    gradientTo="#06b6d4"
                    label="Лабы"
                  />
                  <div className="mt-2 text-center">
                    <span className="text-xs text-muted-foreground">
                      {stats.labs_accepted} / {stats.labs_total}
                    </span>
                  </div>
                </div>
                
                <div className="flex flex-col items-center">
                  <AnimatedCircularProgress
                    value={stats.group_percentile ?? 0}
                    size={100}
                    strokeWidth={8}
                    gradientFrom="#a855f7"
                    gradientTo="#ec4899"
                    label="Рейтинг"
                  />
                  <div className="mt-2 text-center">
                    <span className="text-xs text-muted-foreground">
                      {stats.group_rank ?? '—'} из {stats.group_total ?? '—'}
                    </span>
                  </div>
                </div>
              </div>

              {stats.labs_overdue > 0 && (
                <div className="flex items-center gap-2 p-3 mt-4 bg-gradient-to-r from-orange-100 to-red-100 dark:from-orange-900/20 dark:to-red-900/20 rounded-lg text-orange-700 dark:text-orange-400 border border-orange-200 dark:border-orange-800">
                  <AlertTriangle className="w-5 h-5 shrink-0" />
                  <span className="text-sm font-medium">
                    {stats.labs_overdue} {stats.labs_overdue === 1 ? 'долг' : stats.labs_overdue < 5 ? 'долга' : 'долгов'} по лабораторным
                  </span>
                </div>
              )}
            </CardContent>
          </Card>
        </BlurFade>
      </div>

      {/* Labs List */}
      <BlurFade delay={0.6}>
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Calendar className="w-5 h-5" />
              Лабораторные работы
            </CardTitle>
          </CardHeader>
          <CardContent>
            {student.labs.length === 0 ? (
              <p className="text-center text-muted-foreground py-8">Нет лабораторных работ</p>
            ) : (
              <div className="space-y-3">
                {student.labs.map((lab, index) => {
                  const statusConfig = lab.status ? STATUS_CONFIG[lab.status] : null;
                  return (
                    <BlurFade key={lab.lab_id} delay={0.65 + index * 0.05}>
                      <div
                        className={`flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 transition-all duration-200 hover:shadow-md ${
                          lab.is_overdue ? 'border-orange-500 bg-gradient-to-r from-orange-50 to-red-50 dark:from-orange-900/10 dark:to-red-900/10' : ''
                        }`}
                      >
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="font-medium truncate">{lab.lab_title}</span>
                            {lab.is_overdue && (
                              <Badge variant="destructive" className="text-xs animate-pulse">Долг</Badge>
                            )}
                          </div>
                          <div className="flex gap-4 text-sm text-muted-foreground mt-1">
                            {lab.deadline && (
                              <span>Дедлайн: {new Date(lab.deadline).toLocaleDateString('ru-RU')}</span>
                            )}
                            {lab.submitted_at && (
                              <span>Сдано: {new Date(lab.submitted_at).toLocaleDateString('ru-RU')}</span>
                            )}
                          </div>
                          {lab.feedback && (
                            <div className="text-sm text-yellow-600 dark:text-yellow-400 mt-1">
                              💬 {lab.feedback}
                            </div>
                          )}
                        </div>
                        <div className="flex items-center gap-3 shrink-0">
                          {lab.grade !== null ? (
                            <span className="font-bold text-green-600 dark:text-green-400">
                              {lab.grade}/{lab.max_grade}
                            </span>
                          ) : (
                            <span className="text-muted-foreground">—/{lab.max_grade}</span>
                          )}
                          {statusConfig ? (
                            <Badge className={`${statusConfig.color} text-white gap-1`}>
                              {statusConfig.icon}
                              {statusConfig.label}
                            </Badge>
                          ) : (
                            <Badge variant="outline">Не сдано</Badge>
                          )}
                        </div>
                      </div>
                    </BlurFade>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>
      </BlurFade>
    </div>
  );
}
