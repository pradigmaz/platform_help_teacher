"use client";

import { Eye, Globe, Fingerprint, Clock, AlertTriangle, KeyRound } from "lucide-react";
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

const AUTH_ERROR_SHORT: Record<string, string> = {
  no_token: "Нет токена",
  token_expired: "Истёк",
  invalid_token: "Невалидный",
  invalid_token_no_sub: "Нет sub",
  user_not_found: "Юзер удалён",
  user_inactive: "Заблокирован",
};

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
        <div className="flex items-center gap-1">
          <Badge variant={log.response_status && log.response_status >= 400 ? "destructive" : "outline"}>
            {log.response_status || "—"}
          </Badge>
          {log.response_status === 401 && Boolean(log.extra_data?.auth_error_reason) && (
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger>
                  <Badge variant="outline" className="gap-1 bg-red-500/10 text-red-500 border-red-500/30 cursor-help">
                    <KeyRound className="h-3 w-3" />
                    {AUTH_ERROR_SHORT[String(log.extra_data?.auth_error_reason)] || "Auth"}
                  </Badge>
                </TooltipTrigger>
                <TooltipContent>
                  <p className="text-sm">{String(log.extra_data?.auth_error_reason)}</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          )}
        </div>
      </TableCell>
      <TableCell><SuspicionBadges suspicion={log.suspicion} /></TableCell>
      <TableCell>
        <Button variant="ghost" size="sm"><Eye className="h-4 w-4" /></Button>
      </TableCell>
    </TableRow>
  );
}

function SuspicionBadges({ suspicion }: { suspicion?: AuditLog["suspicion"] }) {
  if (!suspicion?.has_suspicion && !suspicion?.score) return <span className="text-muted-foreground">—</span>;
  
  const getConfidenceColor = (confidence?: string) => {
    switch (confidence) {
      case "high": return "bg-red-500/20 text-red-500 border-red-500/30";
      case "probable": return "bg-orange-500/20 text-orange-500 border-orange-500/30";
      case "low": return "bg-yellow-500/20 text-yellow-500 border-yellow-500/30";
      default: return "bg-gray-500/10 text-gray-500";
    }
  };
  
  return (
    <TooltipProvider>
      <div className="flex gap-1 items-center">
        {/* Score badge */}
        {suspicion.score && suspicion.score > 0 && (
          <Tooltip>
            <TooltipTrigger>
              <Badge variant="outline" className={`gap-1 cursor-help ${getConfidenceColor(suspicion.confidence)}`}>
                {suspicion.score}
              </Badge>
            </TooltipTrigger>
            <TooltipContent>
              <p className="font-medium">Score: {suspicion.score}</p>
              <p className="text-sm">Уверенность: {suspicion.confidence}</p>
              {suspicion.matched_components && (
                <p className="text-xs text-muted-foreground">
                  Совпадения: {suspicion.matched_components.join(", ")}
                </p>
              )}
            </TooltipContent>
          </Tooltip>
        )}
        
        {/* Timing match - очень важный сигнал */}
        {suspicion.timing_match && (
          <Tooltip>
            <TooltipTrigger>
              <Badge variant="destructive" className="gap-1 cursor-help bg-red-500/20 text-red-500">
                <Clock className="h-3 w-3" />
              </Badge>
            </TooltipTrigger>
            <TooltipContent>
              <p className="font-medium">Timing correlation!</p>
              <p className="text-sm">Возможно: {suspicion.timing_match.user_name}</p>
              <p className="text-xs">Разница: {suspicion.timing_match.time_diff_seconds}с</p>
              <p className="text-xs text-muted-foreground">Путь: {suspicion.timing_match.auth_path}</p>
            </TooltipContent>
          </Tooltip>
        )}
        
        {/* Fingerprint match */}
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
              {suspicion.fingerprint_match.score && (
                <p className="text-xs">Score: {suspicion.fingerprint_match.score}</p>
              )}
              {suspicion.fingerprint_match.matched_components && (
                <p className="text-xs text-muted-foreground">
                  {suspicion.fingerprint_match.matched_components.join(", ")}
                </p>
              )}
            </TooltipContent>
          </Tooltip>
        )}
        
        {/* IP match */}
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
        
        {/* Inconsistencies - антидетект */}
        {suspicion.inconsistencies && suspicion.inconsistencies.length > 0 && (
          <Tooltip>
            <TooltipTrigger>
              <Badge variant="outline" className="gap-1 cursor-help bg-purple-500/10 text-purple-500 border-purple-500/30">
                <AlertTriangle className="h-3 w-3" />
              </Badge>
            </TooltipTrigger>
            <TooltipContent>
              <p className="font-medium">Подозрительный fingerprint</p>
              <p className="text-xs text-muted-foreground">
                {suspicion.inconsistencies.join(", ")}
              </p>
            </TooltipContent>
          </Tooltip>
        )}
      </div>
    </TooltipProvider>
  );
}
