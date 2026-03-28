"use client";

import { Bot, Camera, Cpu, Fingerprint, Monitor, Wifi } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { getFingerprintViewModel, type FingerprintEntry } from "./auditFingerprintModel";

interface AuditFingerprintSectionProps {
  fingerprint: unknown;
}

const KIND_LABELS = {
  missing: "Отсутствует",
  opaque_hash: "Только хеш",
  normalized_replacement: "Нормализовано",
} as const;

function FingerprintEntryCard({ title, entries }: { title: string; entries: FingerprintEntry[] }) {
  if (!entries.length) return null;
  return (
    <div className="bg-muted/50 p-3 rounded-lg space-y-2">
      <p className="text-sm font-medium">{title}</p>
      <div className="grid gap-3 sm:grid-cols-2">
        {entries.map((entry) => (
          <div key={`${entry.label}-${entry.value}`} className="min-w-0">
            <p className="text-[11px] uppercase tracking-wide text-muted-foreground">{entry.label}</p>
            <p className="text-xs break-all">{entry.value}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

export function AuditFingerprintSection({ fingerprint }: AuditFingerprintSectionProps) {
  const viewModel = getFingerprintViewModel(fingerprint);
  const fp = viewModel.structured;

  if (viewModel.kind === "absent") return null;

  return (
    <>
      <Separator />
      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <h4 className="font-semibold flex items-center gap-2">
            <Fingerprint className="h-4 w-4" /> Устройство
          </h4>
          {viewModel.kind !== "legacy_structured" && <Badge variant="outline">{KIND_LABELS[viewModel.kind]}</Badge>}
        </div>

        {viewModel.note && <div className="bg-muted/40 p-3 rounded-lg text-sm text-muted-foreground">{viewModel.note}</div>}

        {viewModel.opaqueHash && (
          <div className="bg-muted/50 p-3 rounded-lg space-y-1">
            <p className="text-sm font-medium">Opaque fingerprint hash</p>
            <code className="text-xs break-all block">{viewModel.opaqueHash}</code>
          </div>
        )}

        <FingerprintEntryCard title="Нормализованная сводка" entries={viewModel.summaryEntries} />
        <FingerprintEntryCard title="Признаки совпадения" entries={viewModel.matchingEntries} />

        {fp && (
          <>
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

            <div className="grid grid-cols-3 gap-4">
              <div className="bg-muted/50 p-3 rounded-lg">
                <p className="text-sm font-medium">Платформа</p>
                <p className="text-xs mt-1">{fp.platform || "—"}</p>
                {fp.oscpu && <p className="text-xs text-muted-foreground">{fp.oscpu}</p>}
              </div>
              <div className="bg-muted/50 p-3 rounded-lg">
                <p className="text-sm font-medium">CPU</p>
                <p className="text-xs mt-1">{fp.hardwareConcurrency || "?"} ядер</p>
                {fp.deviceMemory && <p className="text-xs text-muted-foreground">{fp.deviceMemory} GB RAM</p>}
              </div>
              <div className="bg-muted/50 p-3 rounded-lg">
                <p className="text-sm font-medium">Локаль</p>
                <p className="text-xs mt-1">{fp.language || "—"}</p>
                <p className="text-xs text-muted-foreground">{fp.timezone || "—"}</p>
              </div>
            </div>

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

            <div className="flex flex-wrap gap-2">
              {fp.touchSupport && <Badge variant="secondary">Touch</Badge>}
              {(fp.maxTouchPoints ?? 0) > 0 && <Badge variant="secondary">{fp.maxTouchPoints} touch points</Badge>}
              {fp.cookieEnabled && <Badge variant="secondary">Cookies</Badge>}
              {fp.pdfViewer && <Badge variant="secondary">PDF Viewer</Badge>}
              {fp.webdriver && <Badge variant="destructive" className="flex items-center gap-1"><Bot className="h-3 w-3" />WebDriver</Badge>}
              {fp.doNotTrack === "1" && <Badge variant="outline">DNT</Badge>}
            </div>

            {fp.plugins && fp.plugins.length > 0 && (
              <div>
                <p className="text-sm text-muted-foreground mb-1">Плагины</p>
                <div className="flex flex-wrap gap-1">
                  {fp.plugins.map((plugin) => (
                    <Badge key={plugin} variant="outline" className="text-xs">{plugin}</Badge>
                  ))}
                </div>
              </div>
            )}

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
          </>
        )}

        <FingerprintEntryCard title="Качество данных" entries={viewModel.qualityEntries} />
      </div>
    </>
  );
}
