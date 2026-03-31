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
import { Input } from '@/components/ui/input';

interface VerifyBackupDialogProps {
  open: boolean;
  verifying: boolean;
  recoveryCode: string;
  onRecoveryCodeChange: (value: string) => void;
  onClose: () => void;
  onConfirm: () => Promise<void>;
}

export function VerifyBackupDialog({
  open,
  verifying,
  recoveryCode,
  onRecoveryCodeChange,
  onClose,
  onConfirm,
}: VerifyBackupDialogProps) {
  return (
    <AlertDialog open={open} onOpenChange={onClose}>
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
            disabled={verifying}
          >
            {verifying ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
            Проверить
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
