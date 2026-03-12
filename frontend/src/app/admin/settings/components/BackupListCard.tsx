'use client';

import { useRef, useState } from 'react';
import { Plus, Loader2, Download, Trash2, CheckCircle, AlertCircle, RefreshCw, Shield, Upload } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { ru } from 'date-fns/locale';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { Checkbox } from '@/components/ui/checkbox';
import { Input } from '@/components/ui/input';
import type { BackupInfo, VerifyResponse } from '@/lib/api';

interface BackupListCardProps {
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

function getVerificationBadge(result?: VerifyResponse) {
  if (!result) {
    return null;
  }
  if (result.valid) {
    return { label: 'OK', variant: 'default' as const, icon: CheckCircle };
  }
  if (result.status === 'recovery_code_required') {
    return { label: 'Нужен код', variant: 'secondary' as const, icon: AlertCircle };
  }
  return { label: 'Ошибка', variant: 'destructive' as const, icon: AlertCircle };
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

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
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
                const verificationBadge = getVerificationBadge(verificationResults[backup.key]);
                return (
                  <div key={backup.key} className="flex items-center justify-between rounded-lg border bg-card p-4 transition-colors hover:bg-accent/50">
                    <div className="space-y-2">
                      <div className="flex flex-wrap items-center gap-2">
                        <code className="text-sm font-medium">{backup.name}</code>
                        {verificationBadge && (
                          <Badge variant={verificationBadge.variant} className="text-xs">
                            <verificationBadge.icon className="mr-1 h-3 w-3" />
                            {verificationBadge.label}
                          </Badge>
                        )}
                        {typeof backup.format_version === 'number' && <Badge variant="outline">v{backup.format_version}</Badge>}
                        {backup.portable && <Badge variant="secondary">Portable</Badge>}
                        {backup.offsite_present === true && <Badge variant="outline">Offsite</Badge>}
                        {backup.offsite_present === false && <Badge variant="destructive">Только local</Badge>}
                        {backup.created_with_current_key === false && <Badge variant="destructive">Другой key</Badge>}
                      </div>
                      <p className="text-xs text-muted-foreground">
                        {formatSize(backup.size)} • {formatDistanceToNow(new Date(backup.created_at), { addSuffix: true, locale: ru })}
                      </p>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          setVerifyDialog(backup.key);
                          setVerifyRecoveryCode('');
                        }}
                        disabled={verifying === backup.key}
                      >
                        {verifying === backup.key ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Проверить'}
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          setRestoreDialog(backup.key);
                          setRestoreConfirmed(false);
                          setRestoreRecoveryCode('');
                        }}
                      >
                        <Download className="mr-1 h-4 w-4" />
                        Восстановить
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setDeleteDialog(backup.key)}
                        className="text-destructive hover:text-destructive"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      <AlertDialog open={!!verifyDialog} onOpenChange={() => { setVerifyDialog(null); setVerifyRecoveryCode(''); }}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Проверка бэкапа</AlertDialogTitle>
            <AlertDialogDescription asChild>
              <div className="space-y-3">
                <p>Проверка попытается расшифровать архив, распаковать dump и прочитать его через pg_restore.</p>
                <div className="space-y-2 rounded-lg border border-border/60 bg-muted/30 p-3">
                  <label htmlFor="verify-recovery-code" className="text-sm font-medium text-foreground">
                    Recovery code для бэкапа с другой машины
                  </label>
                  <Input
                    id="verify-recovery-code"
                    value={verifyRecoveryCode}
                    onChange={(event) => setVerifyRecoveryCode(event.target.value)}
                    placeholder="Например: abcd-1234-ef56-7890"
                    autoComplete="off"
                    spellCheck={false}
                  />
                  <p className="text-xs text-muted-foreground">
                    Оставьте поле пустым, если backup создан на этой же машине и с тем же master key.
                  </p>
                </div>
              </div>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Отмена</AlertDialogCancel>
            <AlertDialogAction
              onClick={(event) => {
                event.preventDefault();
                void handleVerify();
              }}
              disabled={!verifyDialog || verifying === verifyDialog}
            >
              {verifying === verifyDialog ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
              Проверить
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <AlertDialog
        open={!!restoreDialog}
        onOpenChange={() => {
          setRestoreDialog(null);
          setRestoreConfirmed(false);
          setRestoreRecoveryCode('');
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>⚠️ Восстановление из бэкапа</AlertDialogTitle>
            <AlertDialogDescription asChild>
              <div className="space-y-3">
                <p>Это действие <strong>перезапишет все текущие данные</strong> в базе данных.</p>
                <p className="text-destructive">Все изменения, сделанные после создания бэкапа, будут потеряны.</p>
                <div className="space-y-2 rounded-lg border border-border/60 bg-muted/30 p-3">
                  <label htmlFor="restore-recovery-code" className="text-sm font-medium text-foreground">
                    Recovery code для бэкапа с другой машины
                  </label>
                  <Input
                    id="restore-recovery-code"
                    value={restoreRecoveryCode}
                    onChange={(event) => setRestoreRecoveryCode(event.target.value)}
                    placeholder="Например: abcd-1234-ef56-7890"
                    autoComplete="off"
                    spellCheck={false}
                  />
                  <p className="text-xs text-muted-foreground">
                    Оставьте поле пустым, если backup создан на этой же машине и с тем же master key.
                  </p>
                </div>
                <div className="flex items-center space-x-2 pt-2">
                  <Checkbox id="confirm" checked={restoreConfirmed} onCheckedChange={(checked) => setRestoreConfirmed(checked as boolean)} />
                  <label htmlFor="confirm" className="text-sm font-medium">Я понимаю, что данные будут перезаписаны</label>
                </div>
              </div>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Отмена</AlertDialogCancel>
            <AlertDialogAction
              onClick={(event) => {
                event.preventDefault();
                void handleRestore();
              }}
              disabled={!restoreConfirmed || restoring}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {restoring ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
              Восстановить
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <AlertDialog open={!!deleteDialog} onOpenChange={() => setDeleteDialog(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Удалить бэкап?</AlertDialogTitle>
            <AlertDialogDescription>Бэкап будет удалён безвозвратно.</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Отмена</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                onDelete(deleteDialog!);
                setDeleteDialog(null);
              }}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Удалить
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
