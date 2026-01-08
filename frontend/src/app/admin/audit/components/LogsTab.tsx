"use client";

import { useState, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { AuditAPI, type AuditLog, type AuditStats } from "@/lib/api";
import { AuditStatsCards } from "./AuditStatsCards";
import { AuditFilters } from "./AuditFilters";
import { AuditLogsTable } from "./AuditLogsTable";
import { AuditDetailDialog } from "./AuditDetailDialog";

const LIMIT = 50;

export function LogsTab() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [stats, setStats] = useState<AuditStats | null>(null);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [selectedLog, setSelectedLog] = useState<AuditLog | null>(null);
  
  const [actionFilter, setActionFilter] = useState<string>("");
  const [ipFilter, setIpFilter] = useState("");
  const [pathFilter, setPathFilter] = useState("");
  const [page, setPage] = useState(0);

  const fetchLogs = useCallback(async () => {
    setLoading(true);
    try {
      const [logsData, statsData] = await Promise.all([
        AuditAPI.getLogs({
          action_type: actionFilter === "all" ? undefined : actionFilter || undefined,
          ip_address: ipFilter || undefined,
          path_contains: pathFilter || undefined,
          skip: page * LIMIT,
          limit: LIMIT,
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
  }, [actionFilter, ipFilter, pathFilter, page]);

  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  const handleSearch = () => {
    setPage(0);
    fetchLogs();
  };

  return (
    <div className="space-y-6">
      {stats && <AuditStatsCards stats={stats} />}
      
      <AuditFilters
        actionFilter={actionFilter}
        ipFilter={ipFilter}
        pathFilter={pathFilter}
        onActionChange={setActionFilter}
        onIpChange={setIpFilter}
        onPathChange={setPathFilter}
        onSearch={handleSearch}
      />
      
      <AuditLogsTable
        logs={logs}
        loading={loading}
        onLogClick={setSelectedLog}
      />
      
      {total > LIMIT && (
        <div className="flex justify-center gap-2">
          <Button variant="outline" disabled={page === 0} onClick={() => setPage(p => p - 1)}>
            Назад
          </Button>
          <span className="flex items-center px-4 text-sm text-muted-foreground">
            {page * LIMIT + 1}–{Math.min((page + 1) * LIMIT, total)} из {total}
          </span>
          <Button variant="outline" disabled={(page + 1) * LIMIT >= total} onClick={() => setPage(p => p + 1)}>
            Вперёд
          </Button>
        </div>
      )}
      
      <AuditDetailDialog log={selectedLog} onClose={() => setSelectedLog(null)} />
    </div>
  );
}
