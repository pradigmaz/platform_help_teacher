"use client";

import { useState } from "react";
import { Shield, RefreshCw, Download, Ban } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { AuditAPI } from "@/lib/api";
import { LogsTab, BansTab } from "./components";

export default function AuditPage() {
  const [activeTab, setActiveTab] = useState("logs");
  const [exporting, setExporting] = useState(false);

  const handleExport = async () => {
    setExporting(true);
    try {
      await AuditAPI.exportLogs({ days: 30, limit: 50000 });
    } catch (error) {
      console.error("Failed to export audit logs:", error);
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
        <div className="flex gap-2">
          <Button onClick={handleExport} variant="outline" size="sm" disabled={exporting}>
            <Download className="h-4 w-4 mr-2" />
            {exporting ? "Экспорт..." : "Экспорт JSONL"}
          </Button>
        </div>
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
