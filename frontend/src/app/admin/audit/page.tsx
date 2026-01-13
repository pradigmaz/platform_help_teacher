"use client";

import { useState } from "react";
import { Shield, Download, Ban, Calendar } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { AuditAPI } from "@/lib/api";
import { LogsTab, BansTab } from "./components";

export default function AuditPage() {
  const [activeTab, setActiveTab] = useState("logs");
  const [exporting, setExporting] = useState(false);
  const [exportOpen, setExportOpen] = useState(false);
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [timeFrom, setTimeFrom] = useState("");
  const [timeTo, setTimeTo] = useState("");

  const handleExport = async () => {
    setExporting(true);
    try {
      const filters: { date_from?: string; date_to?: string; days?: number; limit: number } = { limit: 50000 };
      
      if (dateFrom) {
        const from = timeFrom ? `${dateFrom}T${timeFrom}:00` : `${dateFrom}T00:00:00`;
        filters.date_from = from;
      }
      if (dateTo) {
        const to = timeTo ? `${dateTo}T${timeTo}:59` : `${dateTo}T23:59:59`;
        filters.date_to = to;
      }
      if (!dateFrom && !dateTo) {
        filters.days = 30;
      }
      
      await AuditAPI.exportLogs(filters);
      setExportOpen(false);
    } catch (error) {
      console.error("Failed to export audit logs:", error);
    } finally {
      setExporting(false);
    }
  };

  const handleQuickExport = async (days: number) => {
    setExporting(true);
    try {
      await AuditAPI.exportLogs({ days, limit: 50000 });
      setExportOpen(false);
    } catch (error) {
      console.error("Failed to export:", error);
    } finally {
      setExporting(false);
    }
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
        <Dialog open={exportOpen} onOpenChange={setExportOpen}>
          <DialogTrigger asChild>
            <Button variant="outline" size="sm">
              <Download className="h-4 w-4 mr-2" />
              Экспорт JSONL
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Экспорт логов аудита</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div className="flex gap-2">
                <Button variant="outline" size="sm" onClick={() => handleQuickExport(1)} disabled={exporting}>
                  Сегодня
                </Button>
                <Button variant="outline" size="sm" onClick={() => handleQuickExport(7)} disabled={exporting}>
                  7 дней
                </Button>
                <Button variant="outline" size="sm" onClick={() => handleQuickExport(30)} disabled={exporting}>
                  30 дней
                </Button>
              </div>
              
              <div className="border-t pt-4">
                <p className="text-sm text-muted-foreground mb-3">Или выберите период:</p>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Дата от</Label>
                    <Input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />
                  </div>
                  <div className="space-y-2">
                    <Label>Время от</Label>
                    <Input type="time" value={timeFrom} onChange={(e) => setTimeFrom(e.target.value)} placeholder="00:00" />
                  </div>
                  <div className="space-y-2">
                    <Label>Дата до</Label>
                    <Input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} />
                  </div>
                  <div className="space-y-2">
                    <Label>Время до</Label>
                    <Input type="time" value={timeTo} onChange={(e) => setTimeTo(e.target.value)} placeholder="23:59" />
                  </div>
                </div>
              </div>
              
              <Button onClick={handleExport} disabled={exporting || (!dateFrom && !dateTo)} className="w-full">
                <Calendar className="h-4 w-4 mr-2" />
                {exporting ? "Экспорт..." : "Скачать за период"}
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="logs" className="gap-2">
            <Shield className="h-4 w-4" />
            Логи
          </TabsTrigger>
          <TabsTrigger value="bans" className="gap-2">
            <Ban className="h-4 w-4" />
            Баны
          </TabsTrigger>
        </TabsList>

        <TabsContent value="logs" className="mt-6">
          <LogsTab />
        </TabsContent>

        <TabsContent value="bans" className="mt-6">
          <BansTab />
        </TabsContent>
      </Tabs>
    </div>
  );
}
