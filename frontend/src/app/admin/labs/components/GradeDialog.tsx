'use client';

import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { AlertCircle } from 'lucide-react';
import type { SubmissionDetail } from '@/lib/api/types/lab-queue';

interface GradeForm {
  grade: number;
  comment: string;
}

interface GradeDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  submission: SubmissionDetail | null;
  form: GradeForm;
  setForm: (form: GradeForm) => void;
  onAccept: () => void;
}

export function GradeDialog({ open, onOpenChange, submission, form, setForm, onAccept }: GradeDialogProps) {
  const maxGrade = submission?.max_allowed_grade ?? 5;
  const hasDeadlineLimit = maxGrade < 5;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[400px]">
        <DialogHeader>
          <DialogTitle>Принять работу</DialogTitle>
          <DialogDescription>
            {submission?.student_name} — Лаба #{submission?.lab_number}
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid gap-2">
            <Label>Оценка</Label>
            <div className="flex gap-2">
              {[2, 3, 4, 5].map((g) => {
                const isDisabled = g > maxGrade;
                return (
                  <Button
                    key={g}
                    variant={form.grade === g ? 'default' : 'outline'}
                    className={`flex-1 ${isDisabled ? 'opacity-50 cursor-not-allowed' : ''}`}
                    onClick={() => !isDisabled && setForm({ ...form, grade: g })}
                    disabled={isDisabled}
                    title={isDisabled ? `Недоступно: просрочен дедлайн (макс. ${maxGrade})` : undefined}
                  >
                    {g}
                  </Button>
                );
              })}
            </div>
            {hasDeadlineLimit && (
              <div className="flex items-center gap-2 text-sm text-amber-600 dark:text-amber-500 mt-1">
                <AlertCircle className="w-4 h-4" />
                <span>Просрочен дедлайн — максимум {maxGrade}</span>
              </div>
            )}
          </div>
          <div className="grid gap-2">
            <Label>Комментарий (необязательно)</Label>
            <Textarea
              value={form.comment}
              onChange={(e) => setForm({ ...form, comment: e.target.value })}
              placeholder="Комментарий к оценке..."
              rows={2}
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>Отмена</Button>
          <Button onClick={onAccept}>Принять</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
