'use client';

import { useState, useEffect } from 'react';
import { ArrowRight, Calendar, Users } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { toast } from 'sonner';
import { GroupsAPI, TransfersAPI } from '@/lib/api';
import type { GroupResponse, TransferAttestationType } from '@/lib/api/types';

interface TransferStudentDialogProps {
  studentId: string;
  studentName: string;
  currentGroupId?: string;
  currentGroupName?: string;
  currentSubgroup?: number | null;
  onSuccess?: () => void;
}

export function TransferStudentDialog({
  studentId,
  studentName,
  currentGroupId,
  currentGroupName,
  currentSubgroup,
  onSuccess,
}: TransferStudentDialogProps) {
  const [open, setOpen] = useState(false);
  const [groups, setGroups] = useState<GroupResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const [toGroupId, setToGroupId] = useState<string>('');
  const [toSubgroup, setToSubgroup] = useState<string>('none');
  const [transferDate, setTransferDate] = useState<string>(
    new Date().toISOString().split('T')[0]
  );
  const [attestationType, setAttestationType] = useState<TransferAttestationType>('first');

  useEffect(() => {
    if (open) {
      loadGroups();
    }
  }, [open]);

  const loadGroups = async () => {
    setLoading(true);
    try {
      const data = await GroupsAPI.list();
      setGroups(data);
    } catch {
      toast.error('Ошибка загрузки групп');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    if (!toGroupId) {
      toast.error('Выберите группу');
      return;
    }

    setSubmitting(true);
    try {
      await TransfersAPI.transfer(studentId, {
        to_group_id: toGroupId,
        to_subgroup: toSubgroup === 'none' ? null : parseInt(toSubgroup),
        transfer_date: transferDate,
        attestation_type: attestationType,
      });

      const toGroup = groups.find(g => g.id === toGroupId);
      toast.success(
        `Студент переведён в ${toGroup?.name || 'группу'}${
          toSubgroup !== 'none' ? ` (подгруппа ${toSubgroup})` : ''
        }`
      );
      setOpen(false);
      onSuccess?.();
    } catch (e) {
      toast.error('Ошибка при переводе');
    } finally {
      setSubmitting(false);
    }
  };

  const selectedGroup = groups.find(g => g.id === toGroupId);

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm" className="gap-2">
          <ArrowRight className="w-4 h-4" />
          Перевести
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Перевод студента</DialogTitle>
          <DialogDescription>
            {studentName}
            {currentGroupName && (
              <span className="block text-xs mt-1">
                Текущая группа: {currentGroupName}
                {currentSubgroup && ` (подгруппа ${currentSubgroup})`}
              </span>
            )}
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-4 py-4">
          {/* Группа */}
          <div className="grid gap-2">
            <Label htmlFor="group">Новая группа</Label>
            <Select value={toGroupId} onValueChange={setToGroupId} disabled={loading}>
              <SelectTrigger>
                <SelectValue placeholder={loading ? 'Загрузка...' : 'Выберите группу'} />
              </SelectTrigger>
              <SelectContent>
                {groups
                  .filter(g => g.id !== currentGroupId)
                  .map(group => (
                    <SelectItem key={group.id} value={group.id}>
                      <div className="flex items-center gap-2">
                        <Users className="w-4 h-4 text-muted-foreground" />
                        {group.name}
                        <span className="text-muted-foreground text-xs">
                          ({group.students_count} чел.)
                        </span>
                      </div>
                    </SelectItem>
                  ))}
              </SelectContent>
            </Select>
          </div>

          {/* Подгруппа */}
          {selectedGroup?.has_subgroups && (
            <div className="grid gap-2">
              <Label htmlFor="subgroup">Подгруппа</Label>
              <Select value={toSubgroup} onValueChange={setToSubgroup}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">Без подгруппы</SelectItem>
                  <SelectItem value="1">Подгруппа 1</SelectItem>
                  <SelectItem value="2">Подгруппа 2</SelectItem>
                </SelectContent>
              </Select>
            </div>
          )}

          {/* Дата перевода */}
          <div className="grid gap-2">
            <Label htmlFor="date">Дата перевода</Label>
            <div className="relative">
              <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input
                id="date"
                type="date"
                value={transferDate}
                onChange={e => setTransferDate(e.target.value)}
                className="pl-10"
              />
            </div>
          </div>

          {/* Тип аттестации */}
          <div className="grid gap-2">
            <Label htmlFor="attestation">Аттестация</Label>
            <Select
              value={attestationType}
              onValueChange={v => setAttestationType(v as TransferAttestationType)}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="first">1-я аттестация</SelectItem>
                <SelectItem value="second">2-я аттестация</SelectItem>
              </SelectContent>
            </Select>
            <p className="text-xs text-muted-foreground">
              Снапшот данных будет сохранён для выбранной аттестации
            </p>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)}>
            Отмена
          </Button>
          <Button onClick={handleSubmit} disabled={submitting || !toGroupId}>
            {submitting ? 'Перевод...' : 'Перевести'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
