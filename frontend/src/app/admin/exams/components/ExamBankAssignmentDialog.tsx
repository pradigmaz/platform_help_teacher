'use client';

import { useMemo, useState } from 'react';
import { Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import { Checkbox } from '@/components/ui/checkbox';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { ExamBanksAPI, type AdminExamOfferingRef } from '@/lib/api';

interface ExamBankAssignmentDialogProps {
  open: boolean;
  bankId: string | null;
  offerings: AdminExamOfferingRef[];
  onOpenChange: (open: boolean) => void;
  onAssigned: () => void;
}

export function ExamBankAssignmentDialog({
  open,
  bankId,
  offerings,
  onOpenChange,
  onAssigned,
}: ExamBankAssignmentDialogProps) {
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [saving, setSaving] = useState(false);

  const canSubmit = useMemo(() => Boolean(bankId) && selectedIds.length > 0, [bankId, selectedIds.length]);

  function toggleOffering(offeringId: string, checked: boolean) {
    setSelectedIds((current) =>
      checked ? [...current, offeringId] : current.filter((value) => value !== offeringId),
    );
  }

  async function handleAssign() {
    if (!bankId || !selectedIds.length) {
      return;
    }

    setSaving(true);
    try {
      await ExamBanksAPI.assignBank(bankId, selectedIds);
      toast.success('Группы привязаны к банку');
      setSelectedIds([]);
      onAssigned();
      onOpenChange(false);
    } catch {
      toast.error('Не удалось привязать группы к банку');
    } finally {
      setSaving(false);
    }
  }

  return (
    <Dialog
      open={open}
      onOpenChange={(nextOpen) => {
        if (!nextOpen) {
          setSelectedIds([]);
        }
        onOpenChange(nextOpen);
      }}
    >
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Привязать группы к существующему банку</DialogTitle>
          <DialogDescription>Выберите группы, которые должны использовать уже созданный общий банк.</DialogDescription>
        </DialogHeader>

        <div className="space-y-3">
          {offerings.map((offering) => {
            const checked = selectedIds.includes(offering.offering_id);
            return (
              <label
                key={offering.offering_id}
                className="flex items-center gap-3 rounded-xl border border-border/60 px-3 py-3"
              >
                <Checkbox checked={checked} onCheckedChange={(value) => toggleOffering(offering.offering_id, Boolean(value))} />
                <div className="space-y-1">
                  <Label className="cursor-pointer">{offering.group_name}</Label>
                  <div className="text-xs text-muted-foreground">{offering.subject_name}</div>
                </div>
              </label>
            );
          })}
        </div>

        <DialogFooter>
          <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
            Отмена
          </Button>
          <Button type="button" onClick={handleAssign} disabled={!canSubmit || saving}>
            {saving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
            Привязать
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
