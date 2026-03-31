import { Badge } from '@/components/ui/badge';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import type { SecurityStatsResponse } from '@/lib/api';
import { ATTACK_TYPE_INFO, hasTopAttackTypes } from './securityTabModel';

interface SecurityStatsCardsProps {
  stats: SecurityStatsResponse;
}

export function SecurityStatsCards({ stats }: SecurityStatsCardsProps) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      <Card>
        <CardHeader className="pb-2">
          <CardDescription>Активные баны</CardDescription>
          <CardTitle className="text-3xl text-red-500">{stats.active_bans}</CardTitle>
        </CardHeader>
      </Card>
      <Card>
        <CardHeader className="pb-2">
          <CardDescription>Страйков (1ч)</CardDescription>
          <CardTitle className="text-3xl text-yellow-500">{stats.strikes_today}</CardTitle>
        </CardHeader>
      </Card>
      <Card className="col-span-2">
        <CardHeader className="pb-2">
          <CardDescription>Топ атак</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            {Object.entries(stats.top_attack_types).map(([type, count]) => {
              const info = ATTACK_TYPE_INFO[type] || ATTACK_TYPE_INFO.unknown;
              const Icon = info.icon;
              return (
                <Badge key={type} variant="outline" className="gap-1">
                  <Icon className={`h-3 w-3 ${info.color}`} />
                  {info.label}: {count as number}
                </Badge>
              );
            })}
            {!hasTopAttackTypes(stats) && (
              <span className="text-muted-foreground text-sm">Нет данных</span>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
