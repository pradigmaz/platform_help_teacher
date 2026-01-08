"use client";

import { Eye, Globe, Fingerprint, Shield } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
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
import type { AuditLog } from "@/lib/api";
import { ACTION_LABELS, formatAuditDate } from "../lib/audit-constants";

interface AuditLogsTableProps {
  logs: AuditLog[];
  loading: boolean;
  onLogClick: (log: AuditLog) => void;
}

export function AuditLogsTable({ logs, loading, onLogClick }: AuditLogsTableProps) {
  return (
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
              logs.map((log) => (
                <AuditLogRow key={log.id} log={log} onClick={() => onLogClick(log)} />
              ))
            )}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}

function AuditLogRow({ log, onClick }: { log: AuditLog; onClick: () => void }) {
  const action = ACTION_LABELS[log.action_type] || { label: log.action_type, color: "bg-gray-500/10" };
  
  return (
    <TableRow className="cursor-pointer hover:bg-muted/50" onClick={onClick}>
      <TableCell className="font-mono text-sm">{formatAuditDate(log.created_at)}</TableCell>
      <TableCell>{log.user_name || <span className="text-muted-foreground">—</span>}</TableCell>
      <TableCell>
        <Badge variant="secondary" className={action.color}>{action.label}</Badge>
      </TableCell>
      <TableCell className="font-mono text-xs max-w-[200px] truncate">{log.path}</TableCell>
      <TableCell className="font-mono text-xs">{log.ip_address}</TableCell>
      <TableCell>
        <Badge variant={log.response_status && log.response_status >= 400 ? "destructive" : "outline"}>
          {log.response_status || "—"}
        </Badge>
      </TableCell>
      <TableCell><SuspicionBadges suspicion={log.suspicion} /></TableCell>
      <TableCell>
        <Button variant="ghost" size="sm"><Eye className="h-4 w-4" /></Button>
      </TableCell>
    </TableRow>
  );
}

function SuspicionBadges({ suspicion }: { suspicion?: AuditLog["suspicion"] }) {
  if (!suspicion?.has_suspicion) return <span className="text-muted-foreground">—</span>;
  
  return (
    <TooltipProvider>
      <div className="flex gap-1">
        {suspicion.vpn_detected && (
          <Tooltip>
            <TooltipTrigger>
              <Badge variant="destructive" className="gap-1 cursor-help bg-purple-500/10 text-purple-500">
                <Shield className="h-3 w-3" />VPN
              </Badge>
            </TooltipTrigger>
            <TooltipContent>
              <p className="font-medium">Вероятно VPN</p>
              <p className="text-sm">Timezone: {suspicion.vpn_detected.timezone}</p>
              <p className="text-sm">Язык: {suspicion.vpn_detected.language}</p>
              <p className="text-xs text-muted-foreground">
                Ожидаемые страны: {suspicion.vpn_detected.expected_countries?.join(", ")}
              </p>
            </TooltipContent>
          </Tooltip>
        )}
        {suspicion.fingerprint_match && (
          <Tooltip>
            <TooltipTrigger>
              <Badge variant="destructive" className="gap-1 cursor-help">
                <Fingerprint className="h-3 w-3" />
              </Badge>
            </TooltipTrigger>
            <TooltipContent>
              <p className="font-medium">Совпадение fingerprint</p>
              <p className="text-sm">Возможно: {suspicion.fingerprint_match.user_name}</p>
              <p className="text-xs text-muted-foreground">{suspicion.fingerprint_match.match_count} совпадений</p>
            </TooltipContent>
          </Tooltip>
        )}
        {suspicion.ip_match && (
          <Tooltip>
            <TooltipTrigger>
              <Badge variant="secondary" className="gap-1 cursor-help bg-orange-500/10 text-orange-500">
                <Globe className="h-3 w-3" />
              </Badge>
            </TooltipTrigger>
            <TooltipContent>
              <p className="font-medium">Совпадение IP</p>
              <p className="text-sm">Возможно: {suspicion.ip_match.user_name}</p>
              <p className="text-xs text-muted-foreground">{suspicion.ip_match.match_count} совпадений</p>
            </TooltipContent>
          </Tooltip>
        )}
      </div>
    </TooltipProvider>
  );
}
