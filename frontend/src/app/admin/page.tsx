'use client';

import { useCallback, useEffect, useState } from 'react';
import { 
  Users, 
  BookOpen,
  FlaskConical,
  NotebookTabs,
  GraduationCap,
  Clock,
  RefreshCw
} from 'lucide-react';
import { BentoCard, BentoGrid } from '@/components/ui/bento-grid';
import { MetricCard } from '@/components/ui/metric-card';

import { NumberTicker } from '@/components/ui/number-ticker';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { toast } from '@/components/ui/sonner';
import { useAdminSession } from '@/components/admin/AdminSessionProvider';
import { AdminAPI, type AdminStats as DashboardStats } from '@/lib/api/admin';

export default function AdminPanel() {
  const { user, isLoading: sessionLoading } = useAdminSession();
  const [isLoading, setIsLoading] = useState(true);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const fetchStats = useCallback(async (options?: { force?: boolean }) => {
    setIsRefreshing(true);
    try {
      const data = await AdminAPI.getStats(options);
      setStats(data);
    } catch {
      toast.error('Ошибка при загрузке статистики');
      setStats({
        total_users: 0,
        total_students: 0,
        total_groups: 0,
        active_labs: 0
      });
    } finally {
      setIsRefreshing(false);
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (sessionLoading) {
      return;
    }

    if (!user || (user.role !== 'admin' && user.role !== 'teacher')) {
      setIsLoading(false);
      return;
    }

    void fetchStats();
  }, [fetchStats, sessionLoading, user]);

  if (sessionLoading || isLoading) {
    return (
      <div className="flex h-[50vh] items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="h-12 w-12 animate-spin rounded-full border-4 border-primary border-t-transparent"></div>
          <div className="text-xl font-medium text-muted-foreground">Проверка доступа...</div>
        </div>
      </div>
    );
  }

  if (!user || (user.role !== 'admin' && user.role !== 'teacher')) {
    return null;
  }

  const statCards = [
    {
      name: "Групп",
      value: stats?.total_groups ?? 0,
      icon: GraduationCap,
      tint: "cyan" as const,
      color: "text-cyan-500",
      description: "Учебных групп"
    },
    {
      name: "Студентов",
      value: stats?.total_students ?? 0,
      icon: Users,
      tint: "blue" as const,
      color: "text-blue-500",
      description: "Всего в системе"
    },
    {
      name: "Лекций",
      value: stats?.total_lectures ?? 0,
      icon: BookOpen,
      tint: "green" as const,
      color: "text-green-500",
      description: "Учебных материалов"
    },
    {
      name: "Лабораторных",
      value: stats?.active_labs ?? 0,
      icon: FlaskConical,
      tint: "purple" as const,
      color: "text-purple-500",
      description: "Заданий создано"
    }
  ];

  const features = [
    {
      Icon: BookOpen,
      name: "Лекции",
      description: "Создание и публикация учебных материалов.",
      href: "/admin/lectures",
      cta: "Редактировать",
      background: null,
      className: "col-span-1",
    },
    {
      Icon: FlaskConical,
      name: "Лабораторные",
      description: "Управление заданиями и дедлайнами.",
      href: "/admin/labs",
      cta: "Настроить",
      background: null,
      className: "col-span-1",
    },
    {
      Icon: NotebookTabs,
      name: "Предметы групп",
      description: "Форма контроля и очередь автомата по предметам.",
      href: "/admin/subjects",
      cta: "Открыть",
      background: null,
      className: "col-span-1",
    },
  ];

  return (
    <div className="space-y-10">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-4xl font-bold tracking-tight mb-2 text-foreground">
            Панель управления
          </h1>
          <p className="text-muted-foreground">
            Добро пожаловать, <span className="text-foreground font-medium">{user?.full_name || user?.username || 'Администратор'}</span>
          </p>
        </div>
        <Button 
          onClick={() => void fetchStats({ force: true })}
          disabled={isRefreshing}
          className="rounded-xl"
        >
          <RefreshCw className={cn("mr-2 h-4 w-4", isRefreshing && "animate-spin")} />
          Обновить
        </Button>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((stat, idx) => (
          <MetricCard
            key={idx}
            tint={stat.tint}
            className="p-6 flex flex-col justify-between"
          >
            <div>
              <div className="flex justify-between items-start mb-4">
                <div className={cn("p-3 rounded-2xl bg-accent/50 backdrop-blur-md", stat.color)}>
                  <stat.icon size={24} />
                </div>
              </div>
              <p className="text-muted-foreground text-sm font-medium tracking-wide">{stat.name}</p>
              <div className="text-4xl font-bold mt-2 text-foreground tracking-tight">
                <NumberTicker value={stat.value} />
              </div>
            </div>
            <p className="text-muted-foreground text-xs mt-4 flex items-center gap-1.5">
              <span className="h-1 w-1 rounded-full bg-primary/50" />
              {stat.description}
            </p>
          </MetricCard>
        ))}
      </div>

      {/* Bento Grid */}
      <div>
        <h2 className="text-xl font-semibold mb-4 flex items-center gap-2 text-foreground">
          <Clock className="text-primary" size={20} />
          Быстрый доступ
        </h2>
        <BentoGrid className="grid-cols-1 md:grid-cols-2 gap-4">
          {features.map((feature, idx) => (
            <BentoCard 
              key={idx}
              name={feature.name}
              description={feature.description}
              Icon={feature.Icon}
              href={feature.href}
              cta={feature.cta}
              className={feature.className}
              background={feature.background}
            />
          ))}
        </BentoGrid>
      </div>
    </div>
  );
}
