"use client";

import { Clock, Globe, Monitor, User, FileCode, Fingerprint } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";
import type { AuditLog } from "@/lib/api";

interface Props {
  log: AuditLog | null;
  onClose: () => void;
}

export function AuditDetailDialog({ log, onClose }: Props) {
  if (!log) return null;

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString("ru-RU");
  };

  return (
    <Dialog open={!!log} onOpenChange={() => onClose()}>
      <DialogContent className="max-w-2xl max-h-[80vh]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <FileCode className="h-5 w-5" />
            Детали записи аудита
          </DialogTitle>
        </DialogHeader>

        <ScrollArea className="max-h-[60vh] pr-4">
          <div className="space-y-6">
            {/* Основная информация */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground flex items-center gap-2">
                  <Clock className="h-4 w-4" /> Время
                </p>
                <p className="font-mono">{formatDate(log.created_at)}</p>
              </div>
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground flex items-center gap-2">
                  <User className="h-4 w-4" /> Пользователь
                </p>
                <p>{log.user_name || "Аноним"}</p>
              </div>
            </div>

            <Separator />

            {/* HTTP */}
            <div className="space-y-3">
              <h4 className="font-semibold">HTTP запрос</h4>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-muted-foreground">Метод</p>
                  <Badge variant="outline">{log.method}</Badge>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Статус</p>
                  <Badge variant={log.response_status && log.response_status >= 400 ? "destructive" : "secondary"}>
                    {log.response_status || "—"}
                  </Badge>
                </div>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Путь</p>
                <code className="text-sm bg-muted px-2 py-1 rounded block mt-1">
                  {log.path}
                </code>
              </div>
              {log.duration_ms && (
                <div>
                  <p className="text-sm text-muted-foreground">Время выполнения</p>
                  <p>{log.duration_ms} мс</p>
                </div>
              )}
            </div>

            <Separator />

            {/* Клиент */}
            <div className="space-y-3">
              <h4 className="font-semibold flex items-center gap-2">
                <Globe className="h-4 w-4" /> Клиент
              </h4>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-muted-foreground">IP адрес</p>
                  <code className="text-sm">{log.ip_address}</code>
                </div>
                {log.ip_forwarded && (
                  <div>
                    <p className="text-sm text-muted-foreground">Forwarded</p>
                    <code className="text-sm text-xs">{log.ip_forwarded}</code>
                  </div>
                )}
              </div>
              {log.user_agent && (
                <div>
                  <p className="text-sm text-muted-foreground flex items-center gap-2">
                    <Monitor className="h-4 w-4" /> User-Agent
                  </p>
                  <code className="text-xs bg-muted px-2 py-1 rounded block mt-1 break-all">
                    {log.user_agent}
                  </code>
                </div>
              )}
            </div>

            {/* Fingerprint */}
            {log.fingerprint && Object.keys(log.fingerprint).length > 0 && (
              <>
                <Separator />
                <div className="space-y-3">
                  <h4 className="font-semibold flex items-center gap-2">
                    <Fingerprint className="h-4 w-4" /> Fingerprint
                  </h4>
                  <pre className="text-xs bg-muted p-3 rounded overflow-auto max-h-40">
                    {JSON.stringify(log.fingerprint, null, 2)}
                  </pre>
                </div>
              </>
            )}

            {/* Request body */}
            {log.request_body && Object.keys(log.request_body).length > 0 && (
              <>
                <Separator />
                <div className="space-y-3">
                  <h4 className="font-semibold">Request Body</h4>
                  <pre className="text-xs bg-muted p-3 rounded overflow-auto max-h-40">
                    {JSON.stringify(log.request_body, null, 2)}
                  </pre>
                </div>
              </>
            )}
          </div>
        </ScrollArea>
      </DialogContent>
    </Dialog>
  );
}
