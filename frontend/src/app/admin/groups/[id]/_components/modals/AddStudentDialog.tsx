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

interface AddStudentDialogProps {
  open: boolean;
  name: string;
  isAdding: boolean;
  onOpenChange: (open: boolean) => void;
  onNameChange: (name: string) => void;
  onSubmit: () => void;
}

export function AddStudentDialog({
  open,
  name,
  isAdding,
  onOpenChange,
  onNameChange,
  onSubmit,
}: AddStudentDialogProps) {
  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Добавить студента</AlertDialogTitle>
          <AlertDialogDescription>
            Введите ФИО студента для добавления в группу
          </AlertDialogDescription>
        </AlertDialogHeader>
        <div className="py-4">
          <input
            type="text"
            value={name}
            onChange={(e) => onNameChange(e.target.value)}
            placeholder="Иванов Иван Иванович"
            className="w-full px-3 py-2 border rounded-md bg-background"
            onKeyDown={(e) => e.key === 'Enter' && onSubmit()}
          />
        </div>
        <AlertDialogFooter>
          <AlertDialogCancel onClick={() => onNameChange('')}>Отмена</AlertDialogCancel>
          <AlertDialogAction onClick={onSubmit} disabled={isAdding || !name.trim()}>
            {isAdding ? 'Добавление...' : 'Добавить'}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
