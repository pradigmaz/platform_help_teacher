'use client';

import { Loader2 } from 'lucide-react';
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

interface RestoreBackupDialogProps {
  open: boolean;
  restoring: boolean;
  restoreConfirmed: boolean;
  recoveryCode: string;
  onRestoreConfirmedChange: (value: boolean) => void;
  onRecoveryCodeChange: (value: string) => void;
  onClose: () => void;
  onConfirm: () => Promise<void>;
}

export function RestoreBackupDialog({
  open,
  restoring,
  restoreConfirmed,
  recoveryCode,
  onRestoreConfirmedChange,
  onRecoveryCodeChange,
  onClose,
  onConfirm,
}: RestoreBackupDialogProps) {
  return (
    <AlertDialog open={open} onOpenChange={onClose}>
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
                  value={recoveryCode}
                  onChange={(event) => onRecoveryCodeChange(event.target.value)}
                  placeholder="Например: abcd-1234-ef56-7890"
                  autoComplete="off"
                  spellCheck={false}
                />
                <p className="text-xs text-muted-foreground">
                  Оставьте поле пустым, если backup создан на этой же машине и с тем же master key.
                </p>
              </div>
              <div className="flex items-center space-x-2 pt-2">
                <Checkbox
                  id="confirm"
                  checked={restoreConfirmed}
                  onCheckedChange={(checked) => onRestoreConfirmedChange(Boolean(checked))}
                />
                <label htmlFor="confirm" className="text-sm font-medium">
                  Я понимаю, что данные будут перезаписаны
                </label>
              </div>
            </div>
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>Отмена</AlertDialogCancel>
          <AlertDialogAction
            onClick={(event) => {
              event.preventDefault();
              void onConfirm();
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
  );
}
