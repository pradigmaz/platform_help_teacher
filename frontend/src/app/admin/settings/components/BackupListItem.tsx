'use client';

import { AlertCircle, CheckCircle, Download, Loader2, Trash2 } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { ru } from 'date-fns/locale';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import type { BackupInfo, VerifyResponse } from '@/lib/api';

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

function formatSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

interface BackupListItemProps {
  backup: BackupInfo;
  verificationResult?: VerifyResponse;
  verifying: boolean;
  onVerify: () => void;
  onRestore: () => void;
  onDelete: () => void;
}

export function BackupListItem({
  backup,
  verificationResult,
  verifying,
  onVerify,
  onRestore,
  onDelete,
}: BackupListItemProps) {
  const verificationBadge = getVerificationBadge(verificationResult);

  return (
    <div className="flex items-center justify-between rounded-lg border bg-card p-4 transition-colors hover:bg-accent/50">
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
        <Button variant="ghost" size="sm" onClick={onVerify} disabled={verifying}>
          {verifying ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Проверить'}
        </Button>
        <Button variant="outline" size="sm" onClick={onRestore}>
          <Download className="mr-1 h-4 w-4" />
          Восстановить
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={onDelete}
          className="text-destructive hover:text-destructive"
        >
          <Trash2 className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
