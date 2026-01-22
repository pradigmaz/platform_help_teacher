"use client";

import { useState } from "react";
import { Trash2, AlertTriangle, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { AuditAPI } from "@/lib/api";
import { ACTION_LABELS } from "../lib/audit-constants";

const STATUS_CODES = [
  { value: 200, label: "200 OK" },
  { value: 401, label: "401 Unauthorized" },
  { value: 403, label: "403 Forbidden" },
  { value: 404, label: "404 Not Found" },
  { value: 500, label: "500 Server Error" },
];

interface Props {
  onCleared: () => void;
}

export function ClearLogsDialog({ onCleared }: Props) {
  const [open, setOpen] = useState(false);
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [selectedCodes, setSelectedCodes] = useState<number[]>([]);
  const [actionType, setActionType] = useState("");
  const [preview, setPreview] = useState<{ count: number; by_status: Record<string, number> } | null>(null);
  const [loading, setLoading] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState("");

  const toggleCode = (code: number) => {
    setSelectedCodes(prev => 
      prev.includes(code) ? prev.filter(c => c !== code) : [...prev, code]
    );
    setPreview(null);
  };

  const handlePreview = async () => {
    if (!dateFrom && !dateTo && selectedCodes.length === 0 && !actionType) {
      setError("Выберите хотя бы один фильтр");
      return;
    }
    
    setLoading(true);
    setError("");
    try {
      const filters: { date_from?: string; date_to?: string; status_codes?: number[]; action_type?: string } = {};
      if (dateFrom) filters.date_from = `${dateFrom}T00:00:00`;
      if (dateTo) filters.date_to = `${dateTo}T23:59:59`;
      if (selectedCodes.length > 0) filters.status_codes = selectedCodes;
      if (actionType && actionType !== "all") filters.action_type = actionType;
      
      const result = await AuditAPI.previewClearLogs(filters);
      setPreview(result);
    } catch (err) {
      setError("Ошибка при получении предпросмотра");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleClear = async () => {
    if (!preview || preview.count === 0) return;
    
    setDeleting(true);
    setError("");
    try {
      const filters: { date_from?: string; date_to?: string; status_codes?: number[]; action_type?: string } = {};
      if (dateFrom) filters.date_from = `${dateFrom}T00:00:00`;
      if (dateTo) filters.date_to = `${dateTo}T23:59:59`;
      if (selectedCodes.length > 0) filters.status_codes = selectedCodes;
      if (actionType && actionType !== "all") filters.action_type = actionType;
      
      await AuditAPI.clearLogs(filters);
      setOpen(false);
      resetForm();
      onCleared();
    } catch (err) {
      setError("Ошибка при удалении логов");
      console.error(err);
    } finally {
      setDeleting(false);
    }
  };

  const resetForm = () => {
    setDateFrom("");
    setDateTo("");
    setSelectedCodes([]);
    setActionType("");
    setPreview(null);
    setError("");
  };

  return (
    <Dialog open={open} onOpenChange={(v) => { setOpen(v); if (!v) resetForm(); }}>
      <DialogTrigger asChild>
        <Button variant="outline" className="gap-2 text-red-500 hover:text-red-600 hover:bg-red-50">
          <Trash2 className="h-4 w-4" />
          Очистить логи
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Trash2 className="h-5 w-5 text-red-500" />
            Очистка логов аудита
          </DialogTitle>
          <DialogDescription>
            Выберите фильтры для удаления записей. Это действие необратимо.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Период */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Дата от</Label>
              <Input type="date" value={dateFrom} onChange={(e) => { setDateFrom(e.target.value); setPreview(null); }} />
            </div>
            <div className="space-y-2">
              <Label>Дата до</Label>
              <Input type="date" value={dateTo} onChange={(e) => { setDateTo(e.target.value); setPreview(null); }} />
            </div>
          </div>

          {/* Статус коды */}
          <div className="space-y-2">
            <Label>Статус коды</Label>
            <div className="flex flex-wrap gap-3">
              {STATUS_CODES.map(({ value, label }) => (
                <label key={value} className="flex items-center gap-2 cursor-pointer">
                  <Checkbox
                    checked={selectedCodes.includes(value)}
                    onCheckedChange={() => toggleCode(value)}
                  />
                  <span className="text-sm">{label}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Тип действия */}
          <div className="space-y-2">
            <Label>Тип действия</Label>
            <Select value={actionType} onValueChange={(v) => { setActionType(v); setPreview(null); }}>
              <SelectTrigger>
                <SelectValue placeholder="Все типы" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Все типы</SelectItem>
                {Object.entries(ACTION_LABELS).map(([key, { label }]) => (
                  <SelectItem key={key} value={key}>{label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {error && (
            <p className="text-sm text-red-500">{error}</p>
          )}

          {/* Предпросмотр */}
          {preview && (
            <div className="bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-900 rounded-lg p-4 space-y-2">
              <div className="flex items-center gap-2 text-red-600 dark:text-red-400">
                <AlertTriangle className="h-5 w-5" />
                <span className="font-semibold">Будет удалено: {preview.count.toLocaleString()} записей</span>
              </div>
              {Object.keys(preview.by_status).length > 0 && (
                <div className="text-sm text-muted-foreground">
                  По статусам: {Object.entries(preview.by_status).map(([status, count]) => (
                    <span key={status} className="mr-2">{status}: {count}</span>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        <DialogFooter className="gap-2">
          <Button variant="outline" onClick={() => setOpen(false)}>Отмена</Button>
          {!preview ? (
            <Button onClick={handlePreview} disabled={loading}>
              {loading && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              Предпросмотр
            </Button>
          ) : (
            <Button variant="destructive" onClick={handleClear} disabled={deleting || preview.count === 0}>
              {deleting && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              Удалить {preview.count.toLocaleString()} записей
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
