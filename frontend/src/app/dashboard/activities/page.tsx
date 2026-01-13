'use client';

import { useEffect, useState } from 'react';
import { StudentAPI } from '@/lib/api';
import type { StudentActivities } from '@/lib/api/types';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { IconTrendingUp, IconTrendingDown, IconEqual } from '@tabler/icons-react';
import { cn } from '@/lib/utils';

export default function ActivitiesPage() {
  const [data, setData] = useState<StudentActivities | null>(null);
  const [loading, setLoading] = useState(true);
  const [attestationType, setAttestationType] = useState<'first' | 'second'>('first');

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const result = await StudentAPI.getActivities(attestationType);
        setData(result);
      } catch {
        setData(null);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [attestationType]);

  const formatDate = (iso: string) => {
    return new Date(iso).toLocaleDateString('ru-RU', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold">История баллов</h1>
        <p className="text-muted-foreground">Бонусы и штрафы за активность</p>
      </div>

      <Tabs value={attestationType} onValueChange={(v) => setAttestationType(v as 'first' | 'second')}>
        <TabsList>
          <TabsTrigger value="first">1 аттестация</TabsTrigger>
          <TabsTrigger value="second">2 аттестация</TabsTrigger>
        </TabsList>

        <TabsContent value={attestationType} className="mt-4 space-y-4">
          {loading ? (
            <div className="space-y-3">
              <Skeleton className="h-24 w-full" />
              <Skeleton className="h-16 w-full" />
              <Skeleton className="h-16 w-full" />
            </div>
          ) : data ? (
            <>
              {/* Stats */}
              <div className="grid grid-cols-3 gap-4">
                <Card>
                  <CardContent className="pt-4 text-center">
                    <IconTrendingUp className="h-6 w-6 mx-auto text-green-500 mb-1" />
                    <div className="text-2xl font-bold text-green-600">+{data.stats.total_bonus}</div>
                    <div className="text-xs text-muted-foreground">Бонусы</div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-4 text-center">
                    <IconTrendingDown className="h-6 w-6 mx-auto text-red-500 mb-1" />
                    <div className="text-2xl font-bold text-red-600">{data.stats.total_penalty}</div>
                    <div className="text-xs text-muted-foreground">Штрафы</div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-4 text-center">
                    <IconEqual className="h-6 w-6 mx-auto text-blue-500 mb-1" />
                    <div className={cn(
                      "text-2xl font-bold",
                      data.stats.net_total >= 0 ? "text-green-600" : "text-red-600"
                    )}>
                      {data.stats.net_total >= 0 ? '+' : ''}{data.stats.net_total}
                    </div>
                    <div className="text-xs text-muted-foreground">Итого</div>
                  </CardContent>
                </Card>
              </div>

              {/* Activities list */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Записи ({data.stats.count})</CardTitle>
                </CardHeader>
                <CardContent>
                  {data.activities.length === 0 ? (
                    <p className="text-muted-foreground text-center py-8">Нет записей</p>
                  ) : (
                    <div className="space-y-3">
                      {data.activities.map((a) => (
                        <div key={a.id} className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
                          <div className="flex-1">
                            <p className="font-medium">{a.description}</p>
                            <p className="text-xs text-muted-foreground">{formatDate(a.created_at)}</p>
                          </div>
                          <Badge variant={a.points >= 0 ? 'default' : 'destructive'} className="ml-2">
                            {a.points >= 0 ? '+' : ''}{a.points}
                          </Badge>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </>
          ) : (
            <p className="text-muted-foreground text-center py-8">Ошибка загрузки</p>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
