'use client';

import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
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
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { toast } from 'sonner';
import { GroupsAPI, TransfersAPI } from '@/lib/api';
import type { GroupResponse, TransferAttestationType } from '@/lib/api/types';
import { transferSchema, transferDefaults, type TransferFormValues } from './transfer-schema';

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

  const form = useForm<TransferFormValues>({
    resolver: zodResolver(transferSchema),
    defaultValues: transferDefaults,
  });

  useEffect(() => {
    if (open) {
      loadGroups();
      form.reset(transferDefaults);
    }
  }, [open, form]);

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

  const handleSubmit = async (values: TransferFormValues) => {
    console.log('[TransferStudentDialog:handleSubmit] Starting transfer', { studentId, values });
    
    setSubmitting(true);
    try {
      await TransfersAPI.transfer(studentId, {
        to_group_id: values.toGroupId,
        to_subgroup: values.toSubgroup === 'none' ? null : parseInt(values.toSubgroup),
        transfer_date: values.transferDate,
        attestation_type: values.attestationType,
      });

      const toGroup = groups.find(g => g.id === values.toGroupId);
      toast.success(
        `Студент переведён в ${toGroup?.name || 'группу'}${
          values.toSubgroup !== 'none' ? ` (подгруппа ${values.toSubgroup})` : ''
        }`
      );
      console.log('[TransferStudentDialog:handleSubmit] Transfer successful');
      setOpen(false);
      onSuccess?.();
    } catch (e) {
      console.error('[TransferStudentDialog:handleSubmit] Transfer failed', e);
      toast.error('Ошибка при переводе');
    } finally {
      setSubmitting(false);
    }
  };

  const selectedGroup = groups.find(g => g.id === form.watch('toGroupId'));

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

        <Form {...form}>
          <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-4">
            <div className="grid gap-4 py-4">
              {/* Группа */}
              <FormField
                control={form.control}
                name="toGroupId"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Новая группа</FormLabel>
                    <Select
                      value={field.value}
                      onValueChange={field.onChange}
                      disabled={loading}
                    >
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder={loading ? 'Загрузка...' : 'Выберите группу'} />
                        </SelectTrigger>
                      </FormControl>
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
                    <FormMessage />
                  </FormItem>
                )}
              />

              {/* Подгруппа */}
              {selectedGroup?.has_subgroups && (
                <FormField
                  control={form.control}
                  name="toSubgroup"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Подгруппа</FormLabel>
                      <Select value={field.value} onValueChange={field.onChange}>
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          <SelectItem value="none">Без подгруппы</SelectItem>
                          <SelectItem value="1">Подгруппа 1</SelectItem>
                          <SelectItem value="2">Подгруппа 2</SelectItem>
                        </SelectContent>
                      </Select>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              )}

              {/* Дата перевода */}
              <FormField
                control={form.control}
                name="transferDate"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Дата перевода</FormLabel>
                    <FormControl>
                      <div className="relative">
                        <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                        <Input
                          type="date"
                          className="pl-10"
                          {...field}
                        />
                      </div>
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              {/* Тип аттестации */}
              <FormField
                control={form.control}
                name="attestationType"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Аттестация</FormLabel>
                    <Select value={field.value} onValueChange={field.onChange}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="first">1-я аттестация</SelectItem>
                        <SelectItem value="second">2-я аттестация</SelectItem>
                      </SelectContent>
                    </Select>
                    <FormDescription>
                      Снапшот данных будет сохранён для выбранной аттестации
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setOpen(false)}>
                Отмена
              </Button>
              <Button
                type="submit"
                disabled={submitting || !form.formState.isValid}
              >
                {submitting ? 'Перевод...' : 'Перевести'}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
