"use client";

import { useState, useEffect } from "react";
import { Clock, Globe, Eye, Shield } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { AuditAPI, type AuditLog } from "@/lib/api";
import { AuditDetailDialog } from "@/app/admin/audit/components/AuditDetailDialog";

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
};

interface Props {
  userId: string;
}

export function StudentAuditHistory({ userId }: Props) {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [selectedLog, setSelectedLog] = useState<AuditLog | null>(null);
  const [page, setPage] = useState(0);
  const limit = 20;

  useEffect(() => {
    const fetchLogs = async () => {
      setLoading(true);
      try {
        const data = await AuditAPI.getUserLogs(userId, page * limit, limit);
        setLogs(data.items);
        setTotal(data.total);
      } catch (error) {
        console.error("Failed to fetch audit logs:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchLogs();
  }, [userId, page]);

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
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Shield className="h-5 w-5" />
          История действий
          <Badge variant="secondary" className="ml-2">{total}</Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Время</TableHead>
              <TableHead>Действие</TableHead>
              <TableHead>Путь</TableHead>
              <TableHead>IP</TableHead>
              <TableHead></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              Array.from({ length: 5 }).map((_, i) => (
                <TableRow key={i}>
                  {Array.from({ length: 5 }).map((_, j) => (
                    <TableCell key={j}><Skeleton className="h-4 w-full" /></TableCell>
                  ))}
                </TableRow>
              ))
            ) : logs.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} className="text-center py-8 text-muted-foreground">
                  Нет записей
                </TableCell>
              </TableRow>
            ) : (
              logs.map((log) => {
                const action = ACTION_LABELS[log.action_type] || { label: log.action_type, color: "bg-gray-500/10" };
                return (
                  <TableRow key={log.id}>
                    <TableCell className="font-mono text-sm">
                      {formatDate(log.created_at)}
                    </TableCell>
                    <TableCell>
                      <Badge variant="secondary" className={action.color}>
                        {action.label}
                      </Badge>
                    </TableCell>
                    <TableCell className="font-mono text-xs max-w-[150px] truncate">
                      {log.path}
                    </TableCell>
                    <TableCell className="font-mono text-xs">
                      {log.ip_address}
                    </TableCell>
                    <TableCell>
                      <Button variant="ghost" size="sm" onClick={() => setSelectedLog(log)}>
                        <Eye className="h-4 w-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                );
              })
            )}
          </TableBody>
        </Table>

        {total > limit && (
          <div className="flex justify-center gap-2 mt-4">
            <Button
              variant="outline"
              size="sm"
              disabled={page === 0}
              onClick={() => setPage(p => p - 1)}
            >
              Назад
            </Button>
            <span className="flex items-center px-3 text-sm text-muted-foreground">
              {page * limit + 1}–{Math.min((page + 1) * limit, total)} из {total}
            </span>
            <Button
              variant="outline"
              size="sm"
              disabled={(page + 1) * limit >= total}
              onClick={() => setPage(p => p + 1)}
            >
              Вперёд
            </Button>
          </div>
        )}

        <AuditDetailDialog log={selectedLog} onClose={() => setSelectedLog(null)} />
      </CardContent>
    </Card>
  );
}
