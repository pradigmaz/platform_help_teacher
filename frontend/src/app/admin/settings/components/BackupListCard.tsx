'use client';

import { useRef, useState } from 'react';
import { Plus, Loader2, RefreshCw, Shield, Upload } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import type { BackupInfo, VerifyResponse } from '@/lib/api';
import { BackupListItem } from './BackupListItem';
import { DeleteBackupDialog } from './DeleteBackupDialog';
import { RestoreBackupDialog } from './RestoreBackupDialog';
import { VerifyBackupDialog } from './VerifyBackupDialog';

export interface BackupListCardProps {
  backups: BackupInfo[];
  isLoading: boolean;
  isCreating: boolean;
  onRefresh: () => void;
  onCreate: () => void;
  onVerify: (key: string, recoveryCode?: string) => Promise<VerifyResponse | null>;
  onRestore: (key: string, dropExisting: boolean, recoveryCode?: string) => Promise<boolean>;
  onDelete: (key: string) => void;
  onUpload: (file: File) => Promise<boolean>;
}

export function BackupListCard({ backups, isLoading, isCreating, onRefresh, onCreate, onVerify, onRestore, onDelete, onUpload }: BackupListCardProps) {
  const [verificationResults, setVerificationResults] = useState<Record<string, VerifyResponse>>({});
  const [verifying, setVerifying] = useState<string | null>(null);
  const [verifyDialog, setVerifyDialog] = useState<string | null>(null);
  const [verifyRecoveryCode, setVerifyRecoveryCode] = useState('');
  const [restoreDialog, setRestoreDialog] = useState<string | null>(null);
  const [restoreConfirmed, setRestoreConfirmed] = useState(false);
  const [restoreRecoveryCode, setRestoreRecoveryCode] = useState('');
  const [restoring, setRestoring] = useState(false);
  const [deleteDialog, setDeleteDialog] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleVerify = async () => {
    if (!verifyDialog) {
      return;
    }
    setVerifying(verifyDialog);
    const result = await onVerify(verifyDialog, verifyRecoveryCode.trim() || undefined);
    if (result) {
      setVerificationResults((current) => ({ ...current, [verifyDialog]: result }));
    }
    setVerifying(null);
    setVerifyDialog(null);
    setVerifyRecoveryCode('');
  };

  const handleRestore = async () => {
    if (!restoreDialog) {
      return;
    }
    setRestoring(true);
    const restored = await onRestore(restoreDialog, true, restoreRecoveryCode.trim() || undefined);
    setRestoring(false);
    if (restored) {
      setRestoreDialog(null);
      setRestoreConfirmed(false);
      setRestoreRecoveryCode('');
    }
  };

  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }
    if (!file.name.endsWith('.enc')) {
      return;
    }
    setUploading(true);
    await onUpload(file);
    setUploading(false);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <>
      <Card className="border-border/50">
        <CardHeader className="pb-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-blue-500/10 p-2">
                <Shield className="h-5 w-5 text-blue-500" />
              </div>
              <div>
                <CardTitle className="text-lg">Резервные копии</CardTitle>
                <CardDescription>Список зашифрованных бэкапов базы данных</CardDescription>
              </div>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" onClick={onRefresh} disabled={isLoading}>
                <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
              </Button>
              <input ref={fileInputRef} type="file" accept=".enc" onChange={handleFileSelect} className="hidden" />
              <Button variant="outline" size="sm" onClick={() => fileInputRef.current?.click()} disabled={uploading}>
                {uploading ? <Loader2 className="h-4 w-4 animate-spin" /> : <><Upload className="mr-1 h-4 w-4" />Загрузить</>}
              </Button>
              <Button size="sm" onClick={onCreate} disabled={isCreating}>
                {isCreating ? <Loader2 className="h-4 w-4 animate-spin" /> : <><Plus className="mr-1 h-4 w-4" />Создать</>}
              </Button>
            </div>
          </div>
        </CardHeader>

        <CardContent>
          {!backups.length ? (
            <div className="py-8 text-center text-muted-foreground">
              <Shield className="mx-auto mb-3 h-12 w-12 opacity-20" />
              <p>Нет резервных копий</p>
              <p className="text-sm">Создайте первый бэкап</p>
            </div>
        ) : (
          <div className="space-y-3">
            {backups.map((backup) => {
              return (
                <BackupListItem
                  key={backup.key}
                  backup={backup}
                  verificationResult={verificationResults[backup.key]}
                  verifying={verifying === backup.key}
                  onVerify={() => {
                    setVerifyDialog(backup.key);
                    setVerifyRecoveryCode('');
                  }}
                  onRestore={() => {
                    setRestoreDialog(backup.key);
                    setRestoreConfirmed(false);
                    setRestoreRecoveryCode('');
                  }}
                  onDelete={() => setDeleteDialog(backup.key)}
                />
              );
            })}
          </div>
        )}
        </CardContent>
      </Card>

      <VerifyBackupDialog
        open={!!verifyDialog}
        verifying={Boolean(verifyDialog && verifying === verifyDialog)}
        recoveryCode={verifyRecoveryCode}
        onRecoveryCodeChange={setVerifyRecoveryCode}
        onClose={() => {
          setVerifyDialog(null);
          setVerifyRecoveryCode('');
        }}
        onConfirm={handleVerify}
      />
      <RestoreBackupDialog
        open={!!restoreDialog}
        restoring={restoring}
        restoreConfirmed={restoreConfirmed}
        recoveryCode={restoreRecoveryCode}
        onRestoreConfirmedChange={setRestoreConfirmed}
        onRecoveryCodeChange={setRestoreRecoveryCode}
        onClose={() => {
          setRestoreDialog(null);
          setRestoreConfirmed(false);
          setRestoreRecoveryCode('');
        }}
        onConfirm={handleRestore}
      />
      <DeleteBackupDialog
        backupKey={deleteDialog}
        onClose={() => setDeleteDialog(null)}
        onDelete={onDelete}
      />
    </>
  );
}
