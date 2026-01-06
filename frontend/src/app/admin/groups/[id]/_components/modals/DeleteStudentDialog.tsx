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
} from "@/components/ui/alert-dialog";

interface DeleteStudentDialogProps {
  student: { id: string; name: string } | null;
  onOpenChange: (open: boolean) => void;
  onConfirm: () => void;
}

export function DeleteStudentDialog({
  student,
  onOpenChange,
  onConfirm,
}: DeleteStudentDialogProps) {
  return (
    <AlertDialog open={!!student} onOpenChange={(open) => !open && onOpenChange(false)}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Удалить студента?</AlertDialogTitle>
          <AlertDialogDescription>
            Вы уверены, что хотите удалить студента {`"${student?.name}"`} из группы?
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>Отмена</AlertDialogCancel>
          <AlertDialogAction 
            onClick={onConfirm} 
            className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
          >
            Удалить
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
