"use client";

import { useState, useEffect } from "react";
import { Shield, Search, Filter, RefreshCw, Eye, User, Clock, Globe, Fingerprint, AlertTriangle, Download } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { AuditAPI, type AuditLog, type AuditStats } from "@/lib/api";
import { AuditDetailDialog } from "./components/AuditDetailDialog";
import { AuditStatsCards } from "./components/AuditStatsCards";

const ACTION_LABELS: Record<string, { label: string; color: string }> = {
  view: { label: "Просмотр", color: "bg-blue-500/10 text-blue-500" },
  create: { label: "Создание", color: "bg-green-500/10 text-green-500" },
  update: { label: "Изменение", color: "bg-yellow-500/10 text-yellow-500" },
  delete: { label: "Удаление", color: "bg-red-500/10 text-red-500" },
  auth_login: { label: "Вход", color: "bg-purple-500/10 text-purple-500" },
  auth_logout: { label: "Выход", color: "bg-gray-500/10 text-gray-500" },
  submit: { label: "Сдача", color: "bg-emerald-500/10 text-emerald-500" },
  cancel: { label: "Отмена", color: "bg-orange-500/10 text-orange-500" },
  error: { label: "Ошибка", color: "bg-red-500/10 text-red-500" },
  // Bot actions
  bot_start: { label: "Бот /start", color: "bg-cyan-500/10 text-cyan-500" },
  bot_auth: { label: "Бот OTP", color: "bg-indigo-500/10 text-indigo-500" },
  bot_bind: { label: "Бот привязка", color: "bg-teal-500/10 text-teal-500" },
  bot_relink: { label: "Бот перепривязка", color: "bg-amber-500/10 text-amber-500" },
  bot_message: { label: "Бот сообщение", color: "bg-slate-500/10 text-slate-500" },
};

export default function AuditPage() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [stats, setStats] = useState<AuditStats | null>(null);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);
  const [selectedLog, setSelectedLog] = useState<AuditLog | null>(null);
  
  // Filters
  const [actionFilter, setActionFilter] = useState<string>("");
  const [ipFilter, setIpFilter] = useState("");
  const [pathFilter, setPathFilter] = useState("");
  const [page, setPage] = useState(0);
  const limit = 50;

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const [logsData, statsData] = await Promise.all([
        AuditAPI.getLogs({
          action_type: actionFilter === "all" ? undefined : actionFilter || undefined,
          ip_address: ipFilter || undefined,
          path_contains: pathFilter || undefined,
          skip: page * limit,
          limit,
        }),
        AuditAPI.getStats(7),
      ]);
      setLogs(logsData.items);
      setTotal(logsData.total);
      setStats(statsData);
    } catch (error) {
      console.error("Failed to fetch audit logs:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [actionFilter, page]);

  const handleSearch = () => {
    setPage(0);
    fetchLogs();
  };

  const handleExport = async () => {
    setExporting(true);
    try {
      await AuditAPI.exportLogs({
        action_type: actionFilter === "all" ? undefined : actionFilter || undefined,
        days: 30,
        limit: 50000,
      });
    } catch (error) {
      console.error("Failed to export audit logs:", error);
    } finally {
      setExporting(false);
    }
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleString("ru-RU", {
      day: "2-digit",
      month: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Shield className="h-8 w-8 text-primary" />
          <div>
            <h1 className="text-2xl font-bold">Аудит действий</h1>
            <p className="text-muted-foreground">Мониторинг активности студентов</p>
          </div>
        </div>
        <Button onClick={fetchLogs} variant="outline" size="sm">
          <RefreshCw className="h-4 w-4 mr-2" />
          Обновить
        </Button>
        <Button onClick={handleExport} variant="outline" size="sm" disabled={exporting}>
          <Download className="h-4 w-4 mr-2" />
          {exporting ? "Экспорт..." : "Экспорт JSONL"}
        </Button>
      </div>

      {stats && <AuditStatsCards stats={stats} />}

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Filter className="h-5 w-5" />
            Фильтры
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-4">
            <Select value={actionFilter} onValueChange={setActionFilter}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Тип действия" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Все действия</SelectItem>
                {Object.entries(ACTION_LABELS).map(([key, { label }]) => (
                  <SelectItem key={key} value={key}>{label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            
            <Input
              placeholder="IP адрес"
              value={ipFilter}
              onChange={(e) => setIpFilter(e.target.value)}
              className="w-[180px]"
            />
            
            <Input
              placeholder="Путь содержит..."
              value={pathFilter}
              onChange={(e) => setPathFilter(e.target.value)}
              className="w-[200px]"
            />
            
            <Button onClick={handleSearch}>
              <Search className="h-4 w-4 mr-2" />
              Поиск
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Время</TableHead>
                <TableHead>Пользователь</TableHead>
                <TableHead>Действие</TableHead>
                <TableHead>Путь</TableHead>
                <TableHead>IP</TableHead>
                <TableHead>Статус</TableHead>
                <TableHead>Подозрение</TableHead>
                <TableHead></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                Array.from({ length: 10 }).map((_, i) => (
                  <TableRow key={i}>
                    {Array.from({ length: 8 }).map((_, j) => (
                      <TableCell key={j}><Skeleton className="h-4 w-full" /></TableCell>
                    ))}
                  </TableRow>
                ))
              ) : logs.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={8} className="text-center py-8 text-muted-foreground">
                    Нет записей
                  </TableCell>
                </TableRow>
              ) : (
                logs.map((log) => {
                  const action = ACTION_LABELS[log.action_type] || { label: log.action_type, color: "bg-gray-500/10" };
                  return (
                    <TableRow key={log.id} className="cursor-pointer hover:bg-muted/50" onClick={() => setSelectedLog(log)}>
                      <TableCell className="font-mono text-sm">
                        {formatDate(log.created_at)}
                      </TableCell>
                      <TableCell>
                        {log.user_name || <span className="text-muted-foreground">—</span>}
                      </TableCell>
                      <TableCell>
                        <Badge variant="secondary" className={action.color}>
                          {action.label}
                        </Badge>
                      </TableCell>
                      <TableCell className="font-mono text-xs max-w-[200px] truncate">
                        {log.path}
                      </TableCell>
                      <TableCell className="font-mono text-xs">
                        {log.ip_address}
                      </TableCell>
                      <TableCell>
                        <Badge variant={log.response_status && log.response_status >= 400 ? "destructive" : "outline"}>
                          {log.response_status || "—"}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {log.suspicion?.has_suspicion ? (
                          <TooltipProvider>
                            <div className="flex gap-1">
                              {log.suspicion.vpn_detected && (
                                <Tooltip>
                                  <TooltipTrigger>
                                    <Badge variant="destructive" className="gap-1 cursor-help bg-purple-500/10 text-purple-500">
                                      <Shield className="h-3 w-3" />
                                      VPN
                                    </Badge>
                                  </TooltipTrigger>
                                  <TooltipContent>
                                    <p className="font-medium">Вероятно VPN</p>
                                    <p className="text-sm">
                                      Timezone: {log.suspicion.vpn_detected.timezone}
                                    </p>
                                    <p className="text-sm">
                                      Язык: {log.suspicion.vpn_detected.language}
                                    </p>
                                    <p className="text-xs text-muted-foreground">
                                      Ожидаемые страны: {log.suspicion.vpn_detected.expected_countries?.join(", ")}
                                    </p>
                                  </TooltipContent>
                                </Tooltip>
                              )}
                              {log.suspicion.fingerprint_match && (
                                <Tooltip>
                                  <TooltipTrigger>
                                    <Badge variant="destructive" className="gap-1 cursor-help">
                                      <Fingerprint className="h-3 w-3" />
                                    </Badge>
                                  </TooltipTrigger>
                                  <TooltipContent>
                                    <p className="font-medium">Совпадение fingerprint</p>
                                    <p className="text-sm">
                                      Возможно: {log.suspicion.fingerprint_match.user_name}
                                    </p>
                                    <p className="text-xs text-muted-foreground">
                                      {log.suspicion.fingerprint_match.match_count} совпадений
                                    </p>
                                  </TooltipContent>
                                </Tooltip>
                              )}
                              {log.suspicion.ip_match && (
                                <Tooltip>
                                  <TooltipTrigger>
                                    <Badge variant="secondary" className="gap-1 cursor-help bg-orange-500/10 text-orange-500">
                                      <Globe className="h-3 w-3" />
                                    </Badge>
                                  </TooltipTrigger>
                                  <TooltipContent>
                                    <p className="font-medium">Совпадение IP</p>
                                    <p className="text-sm">
                                      Возможно: {log.suspicion.ip_match.user_name}
                                    </p>
                                    <p className="text-xs text-muted-foreground">
                                      {log.suspicion.ip_match.match_count} совпадений
                                    </p>
                                  </TooltipContent>
                                </Tooltip>
                              )}
                            </div>
                          </TooltipProvider>
                        ) : (
                          <span className="text-muted-foreground">—</span>
                        )}
                      </TableCell>
                      <TableCell>
                        <Button variant="ghost" size="sm">
                          <Eye className="h-4 w-4" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  );
                })
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {total > limit && (
        <div className="flex justify-center gap-2">
          <Button
            variant="outline"
            disabled={page === 0}
            onClick={() => setPage(p => p - 1)}
          >
            Назад
          </Button>
          <span className="flex items-center px-4 text-sm text-muted-foreground">
            {page * limit + 1}–{Math.min((page + 1) * limit, total)} из {total}
          </span>
          <Button
            variant="outline"
            disabled={(page + 1) * limit >= total}
            onClick={() => setPage(p => p + 1)}
          >
            Вперёд
          </Button>
        </div>
      )}

      <AuditDetailDialog log={selectedLog} onClose={() => setSelectedLog(null)} />
    </div>
  );
}
