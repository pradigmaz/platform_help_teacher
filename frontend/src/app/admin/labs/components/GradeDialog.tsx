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
              {[2, 3, 4, 5].map((g) => (
                <Button
                  key={g}
                  variant={form.grade === g ? 'default' : 'outline'}
                  className="flex-1"
                  onClick={() => setForm({ ...form, grade: g })}
                >
                  {g}
                </Button>
              ))}
            </div>
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
