'use client';

import { Skeleton } from '@/components/ui/skeleton';
import { BackupHealthCard } from './BackupHealthCard';
import { BackupListCard } from './BackupListCard';
import { BackupSettingsCard } from './BackupSettingsCard';
import { useBackupTab } from './useBackupTab';

export function BackupTab() {
  const {
    latestPortableBackup,
    setLatestPortableBackup,
    isLoading,
    isSaving,
    isCreating,
    settings,
    backups,
    health,
    handleCopyRecoveryCode,
    loadData,
    handleSaveSettings,
    handleCreateBackup,
    handleVerify,
    handleRestore,
    handleDelete,
    handleUpload,
  } = useBackupTab();

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-[180px] rounded-xl" />
        <Skeleton className="h-[300px] rounded-xl" />
        <Skeleton className="h-[400px] rounded-xl" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <BackupHealthCard
        health={health}
        latestPortableBackup={latestPortableBackup}
        onCopyRecoveryCode={handleCopyRecoveryCode}
        onHideRecoveryCode={() => setLatestPortableBackup(null)}
      />
      <BackupSettingsCard settings={settings} isSaving={isSaving} onSave={handleSaveSettings} />
      <BackupListCard
        backups={backups}
        isLoading={isLoading}
        isCreating={isCreating}
        onRefresh={loadData}
        onCreate={handleCreateBackup}
        onVerify={handleVerify}
        onRestore={handleRestore}
        onDelete={handleDelete}
        onUpload={handleUpload}
      />
    </div>
  );
}
