'use client';

import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import type { SecurityStrikesResponse } from '@/lib/api';
import { ATTACK_TYPE_INFO } from './securityTabModel';

interface SecurityClearDialogProps {
  clearDialog: SecurityStrikesResponse | null;
  clearReason: string;
  clearing: boolean;
  onReasonChange: (value: string) => void;
  onClose: () => void;
  onConfirm: () => Promise<void>;
}

export function SecurityClearDialog({
  clearDialog,
  clearReason,
  clearing,
  onReasonChange,
  onClose,
  onConfirm,
}: SecurityClearDialogProps) {
  return (
    <Dialog open={!!clearDialog} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Снять бан и очистить страйки</DialogTitle>
          <DialogDescription>{clearDialog?.identifier}</DialogDescription>
        </DialogHeader>
        <div className="space-y-4 py-4">
          {clearDialog && clearDialog.strikes.length > 0 && (
            <div className="bg-muted p-3 rounded-lg space-y-2">
              <p className="text-sm font-medium">История атак:</p>
              {clearDialog.strikes.map((strike, index) => {
                const info = ATTACK_TYPE_INFO[strike.attack_type] || ATTACK_TYPE_INFO.unknown;
                return (
                  <div key={index} className="text-xs text-muted-foreground">
                    • {info.label}: {strike.description}
                  </div>
                );
              })}
            </div>
          )}
          <div className="space-y-2">
            <Label>Причина (опционально)</Label>
            <Input
              value={clearReason}
              onChange={(event) => onReasonChange(event.target.value)}
              placeholder="Например: ложное срабатывание"
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            Отмена
          </Button>
          <Button
            onClick={() => {
              void onConfirm();
            }}
            disabled={clearing}
          >
            {clearing ? 'Очистка...' : 'Очистить страйки'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
