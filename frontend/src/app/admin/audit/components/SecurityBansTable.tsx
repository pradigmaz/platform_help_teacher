'use client';

import {
  AlertTriangle,
  Clock,
  Globe,
  ShieldAlert,
  Unlock,
  User,
  Users,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import type { SecurityStrikesResponse, UserInfoResponse } from '@/lib/api';
import { ATTACK_TYPE_INFO, formatSecurityBanTimeLeft } from './securityTabModel';

interface SecurityBansTableProps {
  bans: SecurityStrikesResponse[];
  userInfoMap: Record<string, UserInfoResponse>;
  onClear: (ban: SecurityStrikesResponse) => void;
  onRefresh: () => void;
}

export function SecurityBansTable({
  bans,
  userInfoMap,
  onClear,
  onRefresh,
}: SecurityBansTableProps) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle className="flex items-center gap-2">
            <ShieldAlert className="h-5 w-5 text-red-500" />
            Активные баны за атаки
          </CardTitle>
          <CardDescription>Пользователи, заблокированные за подозрительную активность</CardDescription>
        </div>
        <Button variant="outline" size="sm" onClick={onRefresh}>
          Обновить
        </Button>
      </CardHeader>
      <CardContent>
        {bans.length === 0 ? (
          <div className="text-center py-12 text-muted-foreground">
            <ShieldAlert className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p>Нет активных банов за атаки</p>
            <p className="text-sm">Система работает в штатном режиме</p>
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Идентификатор</TableHead>
                <TableHead>Страйки</TableHead>
                <TableHead>Атаки</TableHead>
                <TableHead>Осталось</TableHead>
                <TableHead className="w-[100px]">Действия</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {bans.map((ban) => {
                const userId = ban.identifier.startsWith('user:') ? ban.identifier.replace('user:', '') : null;
                const userInfo = userId ? userInfoMap[userId] : null;

                return (
                  <TableRow key={ban.identifier}>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        {ban.identifier.startsWith('user:') ? (
                          <User className="h-4 w-4 text-muted-foreground" />
                        ) : (
                          <Globe className="h-4 w-4 text-muted-foreground" />
                        )}
                        <div className="flex flex-col">
                          {userInfo ? (
                            <>
                              <span className="font-medium">{userInfo.full_name}</span>
                              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                                {userInfo.group_name && (
                                  <span className="flex items-center gap-1">
                                    <Users className="h-3 w-3" />
                                    {userInfo.group_name}
                                  </span>
                                )}
                                {userInfo.username && <span>@{userInfo.username}</span>}
                              </div>
                            </>
                          ) : (
                            <code className="text-xs bg-muted px-2 py-1 rounded">{ban.identifier}</code>
                          )}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="destructive" className="gap-1">
                        <AlertTriangle className="h-3 w-3" />
                        {ban.strike_count}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <TooltipProvider>
                        <div className="flex flex-wrap gap-1">
                          {ban.strikes.slice(0, 3).map((strike, index) => {
                            const info = ATTACK_TYPE_INFO[strike.attack_type] || ATTACK_TYPE_INFO.unknown;
                            const Icon = info.icon;
                            return (
                              <Tooltip key={`${ban.identifier}-${index}`}>
                                <TooltipTrigger>
                                  <Badge variant="outline" className="gap-1">
                                    <Icon className={`h-3 w-3 ${info.color}`} />
                                    {info.label}
                                  </Badge>
                                </TooltipTrigger>
                                <TooltipContent className="max-w-xs">
                                  <p className="font-medium">{strike.description}</p>
                                  <p className="text-xs text-muted-foreground mt-1">
                                    {strike.url.slice(0, 100)}...
                                  </p>
                                  <p className="text-xs mt-1">{strike.timestamp}</p>
                                </TooltipContent>
                              </Tooltip>
                            );
                          })}
                          {ban.strikes.length > 3 && (
                            <Badge variant="secondary">+{ban.strikes.length - 3}</Badge>
                          )}
                        </div>
                      </TooltipProvider>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Clock className="h-4 w-4 text-muted-foreground" />
                        {formatSecurityBanTimeLeft(ban.ban_ttl ?? null)}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Button variant="ghost" size="sm" onClick={() => onClear(ban)}>
                        <Unlock className="h-4 w-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}
