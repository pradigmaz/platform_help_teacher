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

interface RejectDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  submission: SubmissionDetail | null;
  comment: string;
  setComment: (comment: string) => void;
  onReject: () => void;
}

export function RejectDialog({ open, onOpenChange, submission, comment, setComment, onReject }: RejectDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[400px]">
        <DialogHeader>
          <DialogTitle>Отклонить работу</DialogTitle>
          <DialogDescription>
            {submission?.student_name} — Лаба #{submission?.lab_number}
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid gap-2">
            <Label>Причина отклонения</Label>
            <Textarea
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              placeholder="Укажите причину..."
              rows={3}
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>Отмена</Button>
          <Button variant="destructive" onClick={onReject} disabled={!comment.trim()}>
            Отклонить
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
