"use client";

import { Users, Globe, Activity, TrendingUp } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import type { AuditStats } from "@/lib/api";

interface Props {
  stats: AuditStats;
}

export function AuditStatsCards({ stats }: Props) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-full bg-blue-500/10">
              <Activity className="h-6 w-6 text-blue-500" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Всего действий</p>
              <p className="text-2xl font-bold">{stats.total_logs.toLocaleString()}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-full bg-green-500/10">
              <Users className="h-6 w-6 text-green-500" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Уникальных юзеров</p>
              <p className="text-2xl font-bold">{stats.unique_users}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-full bg-purple-500/10">
              <Globe className="h-6 w-6 text-purple-500" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Уникальных IP</p>
              <p className="text-2xl font-bold">{stats.unique_ips}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-full bg-orange-500/10">
              <TrendingUp className="h-6 w-6 text-orange-500" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">За {stats.period_days} дней</p>
              <p className="text-2xl font-bold">
                {Math.round(stats.total_logs / stats.period_days)}/день
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
