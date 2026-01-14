"use client";

import { useState, useEffect } from "react";
import { 
  ShieldAlert, 
  Clock, 
  Globe, 
  User, 
  Unlock, 
  AlertTriangle,
  Skull,
  Bug,
  FileWarning,
  Link2Off,
  RefreshCw
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { SecurityAPI, type SecurityStrikesResponse, type SecurityStatsResponse } from "@/lib/api";
import { toast } from "sonner";

const ATTACK_TYPE_INFO: Record<string, { icon: typeof Bug; label: string; color: string }> = {
  sql_injection: { icon: Bug, label: "SQL Injection", color: "text-red-500" },
  path_traversal: { icon: FileWarning, label: "Path Traversal", color: "text-orange-500" },
  xss: { icon: Skull, label: "XSS", color: "text-purple-500" },
  idor: { icon: Link2Off, label: "IDOR", color: "text-yellow-500" },
  unknown: { icon: AlertTriangle, label: "Неизвестно", color: "text-gray-500" },
};

const STRIKE_LEVEL_BADGES: Record<string, { label: string; variant: "default" | "secondary" | "destructive" | "outline" }> = {
  warning: { label: "⚠️ Предупреждение", variant: "secondary" },
  recorded: { label: "📝 Записано", variant: "outline" },
  banned: { label: "🚫 Забанен", variant: "destructive" },
};

export function SecurityTab() {
  const [bans, setBans] = useState<SecurityStrikesResponse[]>([]);
  const [stats, setStats] = useState<SecurityStatsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [clearDialog, setClearDialog] = useState<SecurityStrikesResponse | null>(null);
  const [clearReason, setClearReason] = useState("");
  const [clearing, setClearing] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [bansData, statsData] = await Promise.all([
        SecurityAPI.getActiveBans(),
        SecurityAPI.getStats(),
      ]);
      setBans(bansData);
      setStats(statsData);
    } catch (error) {
      console.error("Failed to fetch security data:", error);
      toast.error("Не удалось загрузить данные безопасности");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleClearStrikes = async () => {
    if (!clearDialog) return;
    
    setClearing(true);
    try {
      await SecurityAPI.clearStrikes(clearDialog.identifier, clearReason);
      toast.success("Страйки очищены");
      setClearDialog(null);
      setClearReason("");
      fetchData();
    } catch (error) {
      console.error("Failed to clear strikes:", error);
      toast.error("Не удалось очистить страйки");
    } finally {
      setClearing(false);
    }
  };

  const formatTimeLeft = (ttl: number | null) => {
    if (!ttl || ttl <= 0) return "Истёк";
    const minutes = Math.floor(ttl / 60);
    if (minutes < 60) return `${minutes} мин`;
    const hours = Math.floor(minutes / 60);
    return `${hours} ч ${minutes % 60} мин`;
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="grid grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
        <Skeleton className="h-64" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Stats Cards */}
      {stats && (
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
                {Object.keys(stats.top_attack_types).length === 0 && (
                  <span className="text-muted-foreground text-sm">Нет данных</span>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Active Bans Table */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <ShieldAlert className="h-5 w-5 text-red-500" />
              Активные баны за атаки
            </CardTitle>
            <CardDescription>
              Пользователи, заблокированные за подозрительную активность
            </CardDescription>
          </div>
          <Button variant="outline" size="sm" onClick={fetchData}>
            <RefreshCw className="h-4 w-4" />
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
                {bans.map((ban) => (
                  <TableRow key={ban.identifier}>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        {ban.identifier.startsWith("user:") ? (
                          <User className="h-4 w-4 text-muted-foreground" />
                        ) : (
                          <Globe className="h-4 w-4 text-muted-foreground" />
                        )}
                        <code className="text-xs bg-muted px-2 py-1 rounded">
                          {ban.identifier}
                        </code>
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
                          {ban.strikes.slice(0, 3).map((strike, i) => {
                            const info = ATTACK_TYPE_INFO[strike.attack_type] || ATTACK_TYPE_INFO.unknown;
                            const Icon = info.icon;
                            return (
                              <Tooltip key={i}>
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
                        {formatTimeLeft(ban.ban_ttl ?? null)}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setClearDialog(ban)}
                      >
                        <Unlock className="h-4 w-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Clear Dialog */}
      <Dialog open={!!clearDialog} onOpenChange={() => setClearDialog(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Снять бан и очистить страйки</DialogTitle>
            <DialogDescription>
              {clearDialog?.identifier}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            {clearDialog && clearDialog.strikes.length > 0 && (
              <div className="bg-muted p-3 rounded-lg space-y-2">
                <p className="text-sm font-medium">История атак:</p>
                {clearDialog.strikes.map((strike, i) => {
                  const info = ATTACK_TYPE_INFO[strike.attack_type] || ATTACK_TYPE_INFO.unknown;
                  return (
                    <div key={i} className="text-xs text-muted-foreground">
                      • {info.label}: {strike.description}
                    </div>
                  );
                })}
              </div>
            )}
            <div className="space-y-2">
              <Label>Причина (опционально)</Label>
              <Input
                value={clearReason}
                onChange={(e) => setClearReason(e.target.value)}
                placeholder="Например: ложное срабатывание"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setClearDialog(null)}>
              Отмена
            </Button>
            <Button onClick={handleClearStrikes} disabled={clearing}>
              {clearing ? "Очистка..." : "Очистить страйки"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
