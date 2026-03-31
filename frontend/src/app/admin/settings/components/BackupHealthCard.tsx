'use client';

import { Copy, ShieldCheck, TriangleAlert } from 'lucide-react';
import type { BackupHealthResponse } from '@/lib/api';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';

interface BackupHealthCardProps {
  health: BackupHealthResponse | null;
  latestPortableBackup: { backupKey: string; recoveryCode: string } | null;
  onCopyRecoveryCode: () => Promise<void>;
  onHideRecoveryCode: () => void;
}

export function BackupHealthCard({
  health,
  latestPortableBackup,
  onCopyRecoveryCode,
  onHideRecoveryCode,
}: BackupHealthCardProps) {
  return (
    <>
      {health && (
        <Card className="border-border/50">
          <CardContent className="flex flex-col gap-4 p-4 md:flex-row md:items-center md:justify-between">
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                {health.status === 'healthy' ? <ShieldCheck className="h-4 w-4 text-green-500" /> : <TriangleAlert className="h-4 w-4 text-amber-500" />}
                <p className="text-sm font-semibold text-foreground">Состояние backup/recovery</p>
              </div>
              <p className="text-sm text-muted-foreground">
                {health.checks?.backups?.latest ? `Последний бэкап: ${health.checks.backups.latest}` : 'Последний бэкап ещё не найден'}
              </p>
              {typeof health.checks?.backups?.age_hours === 'number' && (
                <p className="text-xs text-muted-foreground">
                  Возраст: {health.checks.backups.age_hours.toFixed(2)} ч
                  {typeof health.expected_max_age_hours === 'number' ? ` • лимит ${health.expected_max_age_hours.toFixed(0)} ч` : ''}
                </p>
              )}
            </div>
            <div className="flex flex-wrap gap-2">
              <Badge variant={health.freshness_status === 'fresh' || health.freshness_status === 'disabled' ? 'default' : 'destructive'}>
                {health.freshness_status}
              </Badge>
              <Badge variant={health.offsite_configured ? 'outline' : 'secondary'}>
                {health.offsite_configured ? 'Offsite configured' : 'Offsite off'}
              </Badge>
            </div>
          </CardContent>
        </Card>
      )}

      {latestPortableBackup && (
        <Card className="border-amber-500/40 bg-amber-500/5">
          <CardContent className="flex flex-col gap-4 p-4 md:flex-row md:items-start md:justify-between">
            <div className="space-y-2">
              <p className="text-sm font-semibold text-foreground">Recovery code для {latestPortableBackup.backupKey}</p>
              <p className="text-sm text-muted-foreground">
                Сохраните его отдельно от файла. Сервер больше не покажет этот код и не хранит его для повторной выдачи.
              </p>
              <code className="block w-fit rounded-md bg-background px-3 py-2 text-sm font-medium">
                {latestPortableBackup.recoveryCode}
              </code>
            </div>
            <div className="flex gap-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => {
                  void onCopyRecoveryCode();
                }}
              >
                <Copy className="mr-2 h-4 w-4" />
                Скопировать
              </Button>
              <Button type="button" variant="ghost" size="sm" onClick={onHideRecoveryCode}>
                Скрыть
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </>
  );
}
