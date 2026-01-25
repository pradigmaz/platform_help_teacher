'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Clock, Plus, Trash2, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import { LabsAPI, type DeadlineExtension, type DeadlineExtensionCreate } from '@/lib/api/labs';
import { GroupsAPI } from '@/lib/api/groups';
import type { Lab } from '@/lib/api/types/labs';
import type { GroupResponse } from '@/lib/api/types';

interface DeadlineExtensionsDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  labs: Lab[];
}

export function DeadlineExtensionsDialog({ open, onOpenChange, labs }: DeadlineExtensionsDialogProps) {
  const [extensions, setExtensions] = useState<DeadlineExtension[]>([]);
  const [groups, setGroups] = useState<GroupResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);

  // Форма создания
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<DeadlineExtensionCreate>({
    lab_id: '',
    group_id: '',
    bonus_lessons: 1,
    reason: '',
  });

  useEffect(() => {
    if (open) {
      fetchExtensions();
      fetchGroups();
    }
  }, [open]);

  const fetchExtensions = async () => {
    setLoading(true);
    try {
      const data = await LabsAPI.getExtensions();
      setExtensions(data.items);
    } catch {
      toast.error('Ошибка загрузки продлений');
    } finally {
      setLoading(false);
    }
  };

  const fetchGroups = async () => {
    try {
      const data = await GroupsAPI.list();
      setGroups(data);
    } catch {
      console.error('Ошибка загрузки групп');
    }
  };

  const handleCreate = async () => {
    if (!form.lab_id || !form.group_id) {
      toast.error('Выберите лабу и группу');
      return;
    }
    setCreating(true);
    try {
      await LabsAPI.createExtension(form);
      toast.success('Продление создано');
      setShowForm(false);
      setForm({ lab_id: '', group_id: '', bonus_lessons: 1, reason: '' });
      fetchExtensions();
    } catch (e: unknown) {
      const error = e as { response?: { data?: { detail?: string } } };
      toast.error(error.response?.data?.detail || 'Ошибка создания');
    } finally {
      setCreating(false);
    }
  };

  const handleToggle = async (ext: DeadlineExtension) => {
    try {
      await LabsAPI.updateExtension(ext.id, { is_active: !ext.is_active });
      toast.success(ext.is_active ? 'Продление отключено' : 'Продление включено');
      fetchExtensions();
    } catch {
      toast.error('Ошибка обновления');
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Удалить продление?')) return;
    try {
      await LabsAPI.deleteExtension(id);
      toast.success('Удалено');
      fetchExtensions();
    } catch {
      toast.error('Ошибка удаления');
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px] max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Clock className="w-5 h-5" />
            Продления дедлайнов
          </DialogTitle>
          <DialogDescription>
            Временное продление дедлайна для конкретной группы. Студенты получат дополнительные пары для сдачи на максимальный балл.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Кнопка добавления */}
          {!showForm && (
            <Button variant="outline" onClick={() => setShowForm(true)} className="w-full">
              <Plus className="mr-2 h-4 w-4" /> Добавить продление
            </Button>
          )}

          {/* Форма создания */}
          {showForm && (
            <div className="border rounded-lg p-4 space-y-4 bg-muted/50">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Лабораторная</Label>
                  <Select value={form.lab_id} onValueChange={(v) => setForm({ ...form, lab_id: v })}>
                    <SelectTrigger>
                      <SelectValue placeholder="Выберите лабу" />
                    </SelectTrigger>
                    <SelectContent>
                      {labs.map((lab) => (
                        <SelectItem key={lab.id} value={lab.id}>
                          №{lab.number} — {lab.title}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Группа</Label>
                  <Select value={form.group_id} onValueChange={(v) => setForm({ ...form, group_id: v })}>
                    <SelectTrigger>
                      <SelectValue placeholder="Выберите группу" />
                    </SelectTrigger>
                    <SelectContent>
                      {groups.map((group) => (
                        <SelectItem key={group.id} value={group.id}>
                          {group.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="space-y-2">
                <Label>Доп. пары</Label>
                <Input
                  type="number"
                  min={1}
                  max={10}
                  value={form.bonus_lessons}
                  onChange={(e) => setForm({ ...form, bonus_lessons: parseInt(e.target.value) || 1 })}
                />
                <p className="text-xs text-muted-foreground">
                  Сколько дополнительных пар даётся для сдачи на максимальный балл
                </p>
              </div>
              <div className="space-y-2">
                <Label>Причина (опционально)</Label>
                <Textarea
                  value={form.reason || ''}
                  onChange={(e) => setForm({ ...form, reason: e.target.value })}
                  placeholder="Например: технические проблемы на занятии"
                  rows={2}
                />
              </div>
              <div className="flex gap-2 justify-end">
                <Button variant="outline" onClick={() => setShowForm(false)}>Отмена</Button>
                <Button onClick={handleCreate} disabled={creating}>
                  {creating && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  Создать
                </Button>
              </div>
            </div>
          )}

          {/* Список продлений */}
          {loading ? (
            <div className="flex justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : extensions.length === 0 ? (
            <p className="text-center text-muted-foreground py-8">Нет активных продлений</p>
          ) : (
            <div className="space-y-2">
              {extensions.map((ext) => (
                <div
                  key={ext.id}
                  className={`border rounded-lg p-3 flex items-center justify-between ${
                    ext.is_active ? 'bg-green-50 dark:bg-green-950/20 border-green-200 dark:border-green-800' : 'bg-muted/50'
                  }`}
                >
                  <div className="space-y-1">
                    <div className="font-medium">
                      Лаба №{ext.lab_number} — {ext.group_name}
                    </div>
                    <div className="text-sm text-muted-foreground">
                      +{ext.bonus_lessons} {ext.bonus_lessons === 1 ? 'пара' : ext.bonus_lessons < 5 ? 'пары' : 'пар'}
                      {ext.reason && <span className="ml-2">• {ext.reason}</span>}
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <Switch checked={ext.is_active} onCheckedChange={() => handleToggle(ext)} />
                    <Button variant="ghost" size="icon" onClick={() => handleDelete(ext.id)}>
                      <Trash2 className="h-4 w-4 text-destructive" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>Закрыть</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
