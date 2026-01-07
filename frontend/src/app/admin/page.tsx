'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { 
  Users, 
  BookOpen,
  FlaskConical,
  GraduationCap,
  Clock,
  RefreshCw
} from 'lucide-react';
import { BentoCard, BentoGrid } from '@/components/ui/bento-grid';
import { MagicCard } from '@/components/ui/magic-card';

import { NumberTicker } from '@/components/ui/number-ticker';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { useTheme } from 'next-themes';
import { toast } from '@/components/ui/sonner';

interface User {
  username?: string;
  telegram_id?: string;
  full_name?: string;
  role: string;
}

interface DashboardStats {
  total_users: number;
  total_students: number;
  total_groups: number;
  active_labs: number;
}

export default function AdminPanel() {
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthorized, setIsAuthorized] = useState(false);
  const [user, setUser] = useState<User | null>(null);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const router = useRouter();
  const { theme } = useTheme();

  useEffect(() => {
    const checkAuth = async () => {
      try {
        const response = await fetch('/api/v1/users/me', {
          credentials: 'include'
        });
        
        if (response.ok) {
          const userData = await response.json();
          if (userData.role === 'admin' || userData.role === 'teacher') {
            setIsAuthorized(true);
            setUser(userData);
            fetchStats();
          } else {
            router.push('/');
          }
        } else {
          router.push('/auth/login?redirect=/admin');
        }
      } catch (error) {
        toast.error('Ошибка проверки авторизации');
        console.error('Auth check failed:', error);
        router.push('/auth/login?redirect=/admin');
      } finally {
        setIsLoading(false);
      }
    };
    checkAuth();
  }, [router]);

  const fetchStats = async () => {
    setIsRefreshing(true);
    try {
      const response = await fetch('/api/v1/admin/stats', {
        credentials: 'include'
      });
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      } else {
        toast.error('Ошибка при загрузке статистики');
      }
    } catch (error) {
      toast.error('Ошибка при загрузке статистики');
      console.error('Failed to fetch stats:', error);
      setStats({
        total_users: 0,
        total_students: 0,
        total_groups: 0,
        active_labs: 0
      });
    } finally {
      setIsRefreshing(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex h-[50vh] items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="h-12 w-12 animate-spin rounded-full border-4 border-primary border-t-transparent"></div>
          <div className="text-xl font-medium text-muted-foreground">Проверка доступа...</div>
        </div>
      </div>
    );
  }

  if (!isAuthorized) {
    return null;
  }

  const statCards = [
    {
      name: "Групп",
      value: stats?.total_groups ?? 0,
      icon: GraduationCap,
      color: "text-cyan-500",
      description: "Учебных групп"
    },
    {
      name: "Студентов",
      value: stats?.total_students ?? 0,
      icon: Users,
      color: "text-blue-500",
      description: "Всего в системе"
    },
    {
      name: "Лабораторных",
      value: stats?.active_labs ?? 0,
      icon: FlaskConical,
      color: "text-purple-500",
      description: "Заданий создано"
    }
  ];

  const features = [
    {
      Icon: GraduationCap,
      name: "Группы",
      description: "Создание и редактирование учебных групп.",
      href: "/admin/groups",
      cta: "Открыть",
      background: null,
      className: "col-span-1",
    },
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
          onClick={fetchStats}
          disabled={isRefreshing}
          className="rounded-xl"
        >
          <RefreshCw className={cn("mr-2 h-4 w-4", isRefreshing && "animate-spin")} />
          Обновить
        </Button>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {statCards.map((stat, idx) => (
          <MagicCard
            key={idx}
            className="p-6 flex flex-col justify-between"
            gradientColor={theme === 'dark' ? "rgba(158, 122, 255, 0.15)" : "rgba(158, 122, 255, 0.08)"}
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
          </MagicCard>
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
