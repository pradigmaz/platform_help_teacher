'use client';

import { useState, useRef } from 'react';
import { Plus, Loader2, Download, Trash2, CheckCircle, AlertCircle, RefreshCw, Shield, Upload } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
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
import type { BackupInfo } from '@/lib/api';
import { formatDistanceToNow } from 'date-fns';
import { ru } from 'date-fns/locale';

interface BackupListCardProps {
  backups: BackupInfo[];
  isLoading: boolean;
  isCreating: boolean;
  onRefresh: () => void;
  onCreate: () => void;
  onVerify: (key: string) => Promise<boolean>;
  onRestore: (key: string, dropExisting: boolean) => Promise<boolean>;
  onDelete: (key: string) => void;
  onUpload: (file: File) => Promise<boolean>;
}

export function BackupListCard({
  backups,
  isLoading,
  isCreating,
  onRefresh,
  onCreate,
  onVerify,
  onRestore,
  onDelete,
  onUpload,
}: BackupListCardProps) {
  const [verifying, setVerifying] = useState<string | null>(null);
  const [verified, setVerified] = useState<Record<string, boolean>>({});
  const [restoreDialog, setRestoreDialog] = useState<string | null>(null);
  const [restoreConfirmed, setRestoreConfirmed] = useState(false);
  const [restoring, setRestoring] = useState(false);
  const [deleteDialog, setDeleteDialog] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleVerify = async (key: string) => {
    setVerifying(key);
    const valid = await onVerify(key);
    setVerified({ ...verified, [key]: valid });
    setVerifying(null);
  };

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    if (!file.name.endsWith('.enc')) {
      return;
    }
    
    setUploading(true);
    await onUpload(file);
    setUploading(false);
    
    // Reset input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleRestore = async () => {
    if (!restoreDialog) return;
    setRestoring(true);
    await onRestore(restoreDialog, true);
    setRestoring(false);
    setRestoreDialog(null);
    setRestoreConfirmed(false);
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
              <div className="p-2 rounded-lg bg-blue-500/10">
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
              <input
                ref={fileInputRef}
                type="file"
                accept=".enc"
                onChange={handleFileSelect}
                className="hidden"
              />
              <Button 
                variant="outline" 
                size="sm" 
                onClick={() => fileInputRef.current?.click()}
                disabled={uploading}
              >
                {uploading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <><Upload className="h-4 w-4 mr-1" />Загрузить</>
                )}
              </Button>
              <Button size="sm" onClick={onCreate} disabled={isCreating}>
                {isCreating ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <><Plus className="h-4 w-4 mr-1" />Создать</>
                )}
              </Button>
            </div>
          </div>
        </CardHeader>

        <CardContent>
          {!backups || backups.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <Shield className="h-12 w-12 mx-auto mb-3 opacity-20" />
              <p>Нет резервных копий</p>
              <p className="text-sm">Создайте первый бэкап</p>
            </div>
          ) : (
            <div className="space-y-3">
              {backups.map((backup) => (
                <div
                  key={backup.key}
                  className="flex items-center justify-between p-4 rounded-lg border bg-card hover:bg-accent/50 transition-colors"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <code className="text-sm font-medium">{backup.name}</code>
                      {verified[backup.key] !== undefined && (
                        <Badge variant={verified[backup.key] ? 'default' : 'destructive'} className="text-xs">
                          {verified[backup.key] ? (
                            <><CheckCircle className="h-3 w-3 mr-1" />OK</>
                          ) : (
                            <><AlertCircle className="h-3 w-3 mr-1" />Ошибка</>
                          )}
                        </Badge>
                      )}
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {formatSize(backup.size)} • {formatDistanceToNow(new Date(backup.created_at), { addSuffix: true, locale: ru })}
                    </p>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleVerify(backup.key)}
                      disabled={verifying === backup.key}
                    >
                      {verifying === backup.key ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        'Проверить'
                      )}
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setRestoreDialog(backup.key)}
                    >
                      <Download className="h-4 w-4 mr-1" />
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
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Restore Dialog */}
      <AlertDialog open={!!restoreDialog} onOpenChange={() => { setRestoreDialog(null); setRestoreConfirmed(false); }}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>⚠️ Восстановление из бэкапа</AlertDialogTitle>
            <AlertDialogDescription className="space-y-3">
              <p>Это действие <strong>перезапишет все текущие данные</strong> в базе данных.</p>
              <p className="text-destructive">Все изменения, сделанные после создания бэкапа, будут потеряны!</p>
              <div className="flex items-center space-x-2 pt-2">
                <Checkbox
                  id="confirm"
                  checked={restoreConfirmed}
                  onCheckedChange={(checked) => setRestoreConfirmed(checked as boolean)}
                />
                <label htmlFor="confirm" className="text-sm font-medium">
                  Я понимаю, что данные будут перезаписаны
                </label>
              </div>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Отмена</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleRestore}
              disabled={!restoreConfirmed || restoring}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {restoring ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
              Восстановить
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Delete Dialog */}
      <AlertDialog open={!!deleteDialog} onOpenChange={() => setDeleteDialog(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Удалить бэкап?</AlertDialogTitle>
            <AlertDialogDescription>
              Бэкап будет удалён безвозвратно.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Отмена</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => { onDelete(deleteDialog!); setDeleteDialog(null); }}
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
