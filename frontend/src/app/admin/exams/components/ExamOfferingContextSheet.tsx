'use client';

import { useEffect, useState } from 'react';
import { Loader2, Link2, SquarePen } from 'lucide-react';
import { toast } from 'sonner';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from '@/components/ui/sheet';
import { ExamBanksAPI, type AdminExamOfferingContext } from '@/lib/api';

interface ExamOfferingContextSheetProps {
  open: boolean;
  offeringId: string | null;
  onOpenChange: (open: boolean) => void;
  onBankOpened: (bankId: string) => void;
  onChanged: () => void;
}

export function ExamOfferingContextSheet({
  open,
  offeringId,
  onOpenChange,
  onBankOpened,
  onChanged,
}: ExamOfferingContextSheetProps) {
  const [context, setContext] = useState<AdminExamOfferingContext | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!open || !offeringId) {
      setContext(null);
      setLoading(false);
      return;
    }

    let cancelled = false;
    const loadContext = async () => {
      setContext(null);
      setLoading(true);
      try {
        const response = await ExamBanksAPI.getOfferingContext(offeringId);
        if (!cancelled) {
          setContext(response);
        }
      } catch {
        if (!cancelled) {
          setContext(null);
          toast.error('Не удалось загрузить контекст экзамена');
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    void loadContext();
    return () => {
      cancelled = true;
    };
  }, [offeringId, open]);

  async function handleCreateBank() {
    if (!context || context.offering.offering_id !== offeringId) {
      return;
    }
    setSaving(true);
    try {
      const response = await ExamBanksAPI.createBank([context.offering.offering_id]);
      toast.success('Создан новый банк вопросов');
      onChanged();
      onBankOpened(response.bank_id);
      onOpenChange(false);
    } catch {
      toast.error('Не удалось создать банк вопросов');
    } finally {
      setSaving(false);
    }
  }

  async function handleAttachBank(bankId: string) {
    if (!context || context.offering.offering_id !== offeringId) {
      return;
    }
    setSaving(true);
    try {
      const response = await ExamBanksAPI.assignBank(bankId, [context.offering.offering_id]);
      toast.success('Группа привязана к существующему банку');
      onChanged();
      onBankOpened(response.bank_id);
      onOpenChange(false);
    } catch {
      toast.error('Не удалось привязать группу к банку');
    } finally {
      setSaving(false);
    }
  }

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-full sm:max-w-xl">
        <SheetHeader className="space-y-3">
          <SheetTitle>Банк вопросов для группы</SheetTitle>
          <SheetDescription>
            {context
              ? `${context.offering.group_name} / ${context.offering.subject_name} / ${context.offering.semester}`
              : 'Загрузка контекста…'}
          </SheetDescription>
        </SheetHeader>

        {loading ? (
          <div className="py-12 text-center text-sm text-muted-foreground">Загрузка контекста…</div>
        ) : context ? (
          <div className="space-y-4 pt-6">
            <div className="rounded-2xl border border-border/60 bg-muted/20 p-4">
              <div className="text-sm font-medium text-foreground">Текущая связка</div>
              <div className="mt-2 flex flex-wrap gap-2">
                <Badge variant="outline">{context.offering.group_name}</Badge>
                <Badge variant="outline">{context.offering.subject_name}</Badge>
                <Badge variant="outline">{context.offering.semester}</Badge>
              </div>
            </div>

            {context.bank ? (
              <div className="rounded-2xl border border-border/60 p-4">
                <div className="text-sm font-medium text-foreground">Уже привязанный банк</div>
                <div className="mt-2 text-sm text-muted-foreground">
                  В банке {context.bank.questions_count} вопросов. Его используют группы: {context.bank.offerings.map((offering) => offering.group_name).join(', ')}.
                </div>
                <Button type="button" className="mt-4" onClick={() => onBankOpened(context.bank!.bank_id)}>
                  <SquarePen className="mr-2 h-4 w-4" />
                  Открыть банк
                </Button>
              </div>
            ) : (
              <div className="rounded-2xl border border-border/60 p-4">
                <div className="text-sm font-medium text-foreground">Нового банка ещё нет</div>
                <div className="mt-2 text-sm text-muted-foreground">
                  Можно создать отдельный банк для этой группы или привязать её к одному из уже существующих банков по тому же предмету.
                </div>
                <Button type="button" className="mt-4" onClick={handleCreateBank} disabled={saving}>
                  {saving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                  Создать новый банк
                </Button>
              </div>
            )}

            {context.compatible_banks.length ? (
              <div className="space-y-3 rounded-2xl border border-border/60 p-4">
                <div className="text-sm font-medium text-foreground">Совместимые существующие банки</div>
                {context.compatible_banks.map((bank) => (
                  <div key={bank.bank_id} className="rounded-xl border border-border/50 bg-muted/20 p-3">
                    <div className="text-sm font-medium text-foreground">
                      {bank.questions_count} вопросов, групп: {bank.offerings.map((offering) => offering.group_name).join(', ')}
                    </div>
                    <Button
                      type="button"
                      variant="outline"
                      className="mt-3"
                      onClick={() => handleAttachBank(bank.bank_id)}
                      disabled={saving}
                    >
                      <Link2 className="mr-2 h-4 w-4" />
                      Привязать к этому банку
                    </Button>
                  </div>
                ))}
              </div>
            ) : null}
          </div>
        ) : null}
      </SheetContent>
    </Sheet>
  );
}
