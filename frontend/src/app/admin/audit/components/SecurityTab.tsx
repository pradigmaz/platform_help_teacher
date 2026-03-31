"use client";

import { Skeleton } from "@/components/ui/skeleton";
import { SecurityBansTable } from "./SecurityBansTable";
import { SecurityClearDialog } from "./SecurityClearDialog";
import { SecurityStatsCards } from "./SecurityStatsCards";
import { useSecurityTabData } from "./useSecurityTabData";

export function SecurityTab() {
  const {
    bans,
    stats,
    userInfoMap,
    loading,
    fetchData,
    clearDialog,
    setClearDialog,
    clearReason,
    setClearReason,
    clearing,
    handleClearStrikes,
  } = useSecurityTabData();

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="grid grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
        <Skeleton className="h-64" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {stats && <SecurityStatsCards stats={stats} />}
      <SecurityBansTable
        bans={bans}
        userInfoMap={userInfoMap}
        onClear={setClearDialog}
        onRefresh={fetchData}
      />
      <SecurityClearDialog
        clearDialog={clearDialog}
        clearReason={clearReason}
        clearing={clearing}
        onReasonChange={setClearReason}
        onClose={() => setClearDialog(null)}
        onConfirm={handleClearStrikes}
      />
    </div>
  );
}
