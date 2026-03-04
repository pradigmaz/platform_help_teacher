"use client";

import { Clock, Globe, Monitor, User, FileCode, Fingerprint, Cpu, Wifi, Camera, Bot } from "lucide-react";
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

const AUTH_ERROR_REASONS: Record<string, string> = {
  no_token: "Токен отсутствует — клиент не отправил cookie с access_token",
  token_expired: "Токен истёк — прошло более 15 минут с момента выдачи",
  invalid_token: "Токен невалиден — повреждён, подделан или неверная подпись",
  invalid_token_no_sub: "Токен без user_id — отсутствует поле 'sub' в payload",
  user_not_found: "Пользователь не найден — удалён из БД после выдачи токена",
  user_inactive: "Пользователь деактивирован — аккаунт заблокирован",
};

interface Props {
  log: AuditLog | null;
  onClose: () => void;
}

interface FingerprintData {
  canvas?: string;
  webgl?: { vendor: string; renderer: string; extensions?: string[] };
  screen?: { width: number; height: number; colorDepth: number; pixelRatio: number; orientation?: string };
  timezone?: string;
  timezoneOffset?: number;
  language?: string;
  languages?: string[];
  platform?: string;
  hardwareConcurrency?: number;
  deviceMemory?: number;
  touchSupport?: boolean;
  maxTouchPoints?: number;
  cookieEnabled?: boolean;
  doNotTrack?: string | null;
  plugins?: string[];
  audio?: string;
  connection?: { type?: string; downlink?: number; rtt?: number; saveData?: boolean };
  mediaDevices?: { cameras: number; microphones: number; speakers: number };
  storage?: { quota?: number; usage?: number };
  pdfViewer?: boolean;
  webdriver?: boolean;
  vendor?: string;
  product?: string;
  oscpu?: string;
}

export function AuditDetailDialog({ log, onClose }: Props) {
  if (!log) return null;

  const formatDate = (dateStr: string) => new Date(dateStr).toLocaleString("ru-RU");
  const fp = log.fingerprint as FingerprintData | undefined;

  return (
    <Dialog open={!!log} onOpenChange={() => onClose()}>
      <DialogContent className="max-w-4xl max-h-[90vh]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <FileCode className="h-5 w-5" />
            Детали записи аудита
          </DialogTitle>
        </DialogHeader>

        <ScrollArea className="max-h-[75vh] pr-4">
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
              <div className="grid grid-cols-3 gap-4">
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
                {log.duration_ms && (
                  <div>
                    <p className="text-sm text-muted-foreground">Время</p>
                    <p>{log.duration_ms} мс</p>
                  </div>
                )}
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Путь</p>
                <code className="text-sm bg-muted px-2 py-1 rounded block mt-1">{log.path}</code>
              </div>
            </div>

            <Separator />

            {/* Причина ошибки аутентификации */}
            {Boolean(log.extra_data?.auth_error_reason) && (
              <>
                <div className="bg-red-500/10 border border-red-500/20 p-4 rounded-lg space-y-2">
                  <h4 className="font-semibold text-red-500">Причина ошибки 401</h4>
                  <p className="text-sm">
                    {AUTH_ERROR_REASONS[String(log.extra_data?.auth_error_reason)] || String(log.extra_data?.auth_error_reason)}
                  </p>
                </div>
                <Separator />
              </>
            )}

            {/* Клиент */}
            <div className="space-y-3">
              <h4 className="font-semibold flex items-center gap-2">
                <Globe className="h-4 w-4" /> Сеть
              </h4>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-muted-foreground">IP адрес</p>
                  <code className="text-sm">{log.ip_address}</code>
                </div>
                {log.ip_forwarded && (
                  <div>
                    <p className="text-sm text-muted-foreground">Forwarded</p>
                    <code className="text-xs">{log.ip_forwarded}</code>
                  </div>
                )}
              </div>
              {log.user_agent && (
                <div>
                  <p className="text-sm text-muted-foreground flex items-center gap-2">
                    <Monitor className="h-4 w-4" /> User-Agent
                  </p>
                  <code className="text-xs bg-muted px-2 py-1 rounded block mt-1 break-all">{log.user_agent}</code>
                </div>
              )}
            </div>

            {/* Fingerprint - красивое отображение */}
            {fp && Object.keys(fp).length > 0 && (
              <>
                <Separator />
                <div className="space-y-4">
                  <h4 className="font-semibold flex items-center gap-2">
                    <Fingerprint className="h-4 w-4" /> Устройство
                  </h4>
                  
                  {/* Экран и GPU */}
                  <div className="grid grid-cols-2 gap-4">
                    {fp.screen && (
                      <div className="bg-muted/50 p-3 rounded-lg space-y-2">
                        <p className="text-sm font-medium flex items-center gap-2">
                          <Monitor className="h-4 w-4" /> Экран
                        </p>
                        <div className="text-xs space-y-1">
                          <p>Разрешение: {fp.screen.width}×{fp.screen.height}</p>
                          <p>Глубина цвета: {fp.screen.colorDepth} бит</p>
                          <p>Pixel ratio: {fp.screen.pixelRatio}</p>
                          {fp.screen.orientation && <p>Ориентация: {fp.screen.orientation}</p>}
                        </div>
                      </div>
                    )}
                    
                    {fp.webgl && (
                      <div className="bg-muted/50 p-3 rounded-lg space-y-2">
                        <p className="text-sm font-medium flex items-center gap-2">
                          <Cpu className="h-4 w-4" /> GPU
                        </p>
                        <div className="text-xs space-y-1">
                          <p>Vendor: {fp.webgl.vendor}</p>
                          <p className="break-all">Renderer: {fp.webgl.renderer}</p>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Система */}
                  <div className="grid grid-cols-3 gap-4">
                    <div className="bg-muted/50 p-3 rounded-lg">
                      <p className="text-sm font-medium">Платформа</p>
                      <p className="text-xs mt-1">{fp.platform || '—'}</p>
                      {fp.oscpu && <p className="text-xs text-muted-foreground">{fp.oscpu}</p>}
                    </div>
                    <div className="bg-muted/50 p-3 rounded-lg">
                      <p className="text-sm font-medium">CPU</p>
                      <p className="text-xs mt-1">{fp.hardwareConcurrency || '?'} ядер</p>
                      {fp.deviceMemory && <p className="text-xs text-muted-foreground">{fp.deviceMemory} GB RAM</p>}
                    </div>
                    <div className="bg-muted/50 p-3 rounded-lg">
                      <p className="text-sm font-medium">Локаль</p>
                      <p className="text-xs mt-1">{fp.language}</p>
                      <p className="text-xs text-muted-foreground">{fp.timezone}</p>
                    </div>
                  </div>

                  {/* Соединение */}
                  {fp.connection && (
                    <div className="bg-muted/50 p-3 rounded-lg">
                      <p className="text-sm font-medium flex items-center gap-2">
                        <Wifi className="h-4 w-4" /> Соединение
                      </p>
                      <div className="text-xs mt-1 flex gap-4">
                        {fp.connection.type && <span>Тип: {fp.connection.type}</span>}
                        {fp.connection.downlink && <span>Скорость: {fp.connection.downlink} Mbps</span>}
                        {fp.connection.rtt && <span>RTT: {fp.connection.rtt} ms</span>}
                        {fp.connection.saveData && <Badge variant="outline" className="text-xs">Save Data</Badge>}
                      </div>
                    </div>
                  )}

                  {/* Медиа устройства */}
                  {fp.mediaDevices && (
                    <div className="bg-muted/50 p-3 rounded-lg">
                      <p className="text-sm font-medium flex items-center gap-2">
                        <Camera className="h-4 w-4" /> Медиа устройства
                      </p>
                      <div className="text-xs mt-1 flex gap-4">
                        <span>Камеры: {fp.mediaDevices.cameras}</span>
                        <span>Микрофоны: {fp.mediaDevices.microphones}</span>
                        <span>Динамики: {fp.mediaDevices.speakers}</span>
                      </div>
                    </div>
                  )}

                  {/* Флаги */}
                  <div className="flex flex-wrap gap-2">
                    {fp.touchSupport && <Badge variant="secondary">Touch</Badge>}
                    {(fp.maxTouchPoints ?? 0) > 0 && <Badge variant="secondary">{fp.maxTouchPoints} touch points</Badge>}
                    {fp.cookieEnabled && <Badge variant="secondary">Cookies</Badge>}
                    {fp.pdfViewer && <Badge variant="secondary">PDF Viewer</Badge>}
                    {fp.webdriver && <Badge variant="destructive" className="flex items-center gap-1"><Bot className="h-3 w-3" />WebDriver</Badge>}
                    {fp.doNotTrack === "1" && <Badge variant="outline">DNT</Badge>}
                  </div>

                  {/* Плагины */}
                  {fp.plugins && fp.plugins.length > 0 && (
                    <div>
                      <p className="text-sm text-muted-foreground mb-1">Плагины</p>
                      <div className="flex flex-wrap gap-1">
                        {fp.plugins.map((p, i) => (
                          <Badge key={i} variant="outline" className="text-xs">{p}</Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Хеши */}
                  <div className="grid grid-cols-2 gap-4 text-xs">
                    {fp.canvas && (
                      <div>
                        <p className="text-muted-foreground">Canvas hash</p>
                        <code className="text-xs">{fp.canvas}</code>
                      </div>
                    )}
                    {fp.audio && (
                      <div>
                        <p className="text-muted-foreground">Audio hash</p>
                        <code className="text-xs">{fp.audio}</code>
                      </div>
                    )}
                  </div>
                </div>
              </>
            )}

            {/* Request body */}
            {log.request_body && typeof log.request_body === 'object' && Object.keys(log.request_body).length > 0 && (
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
