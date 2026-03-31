'use client';

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

interface DeleteBackupDialogProps {
  backupKey: string | null;
  onClose: () => void;
  onDelete: (key: string) => void;
}

export function DeleteBackupDialog({
  backupKey,
  onClose,
  onDelete,
}: DeleteBackupDialogProps) {
  return (
    <AlertDialog open={!!backupKey} onOpenChange={onClose}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Удалить бэкап?</AlertDialogTitle>
          <AlertDialogDescription>Бэкап будет удалён безвозвратно.</AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>Отмена</AlertDialogCancel>
          <AlertDialogAction
            onClick={() => {
              if (backupKey) {
                onDelete(backupKey);
              }
              onClose();
            }}
            className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
          >
            Удалить
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
