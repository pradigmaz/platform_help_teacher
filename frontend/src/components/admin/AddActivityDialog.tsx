'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { ActivitiesAPI, AttestationType } from '@/lib/api';
import { toast } from 'sonner';
import { Loader2 } from 'lucide-react';
import { activitySchema, activityDefaults, type ActivityFormValues } from './activity-schema';

interface AddActivityDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  targetId: string;
  targetName: string;
  mode: 'group' | 'student';
  onSuccess: () => void;
}

export function AddActivityDialog({
  open,
  onOpenChange,
  targetId,
  targetName,
  mode,
  onSuccess,
}: AddActivityDialogProps) {
  const [loading, setLoading] = useState(false);

  const form = useForm<ActivityFormValues>({
    resolver: zodResolver(activitySchema),
    mode: 'onChange',
    defaultValues: activityDefaults,
  });

  const handleSubmit = form.handleSubmit(async (values) => {
    setLoading(true);

    try {
      await ActivitiesAPI.create({
        [mode === 'group' ? 'group_id' : 'student_id']: targetId,
        points: values.points,
        description: values.description,
        attestation_type: values.attestationType,
        is_active: true,
      });

      toast.success(
        mode === 'group' 
          ? 'Активность начислена группе' 
          : 'Активность начислена студенту'
      );
      
      onSuccess();
      onOpenChange(false);
      
      // Reset form
      form.reset(activityDefaults);
    } catch (error) {
      toast.error('Ошибка при начислении активности');
      console.error('[AddActivityDialog] Error:', error);
    } finally {
      setLoading(false);
    }
  });

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Начисление активности</DialogTitle>
          <DialogDescription>
            {mode === 'group' 
              ? `Добавить баллы всем студентам группы ${targetName}`
              : `Добавить баллы студенту ${targetName}`
            }
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit}>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="attestation">Аттестация</Label>
              <Select 
                value={form.watch('attestationType')} 
                onValueChange={(v) => form.setValue('attestationType', v as AttestationType)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Выберите аттестацию" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="first">Первая (до 7 недели)</SelectItem>
                  <SelectItem value="second">Вторая (до 13 недели)</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div className="grid gap-2">
              <Label htmlFor="points">Баллы</Label>
              <div className="relative">
                <Input
                  id="points"
                  type="number"
                  step="0.1"
                  {...form.register('points', { valueAsNumber: true })}
                  placeholder="0.5"
                  className="pl-8"
                />
                <span className="absolute left-3 top-2.5 text-muted-foreground font-bold text-sm">
                  {form.watch('points') > 0 ? '+' : ''}
                </span>
              </div>
              {form.formState.errors.points && (
                <p className="text-xs text-destructive">
                  {form.formState.errors.points.message}
                </p>
              )}
              <p className="text-xs text-muted-foreground">
                Используйте отрицательные значения для штрафов (например, -0.5)
              </p>
            </div>
            
            <div className="grid gap-2">
              <Label htmlFor="description">Описание / Причина</Label>
              <Textarea
                id="description"
                {...form.register('description')}
                placeholder="За активное участие в..."
              />
              {form.formState.errors.description && (
                <p className="text-xs text-destructive">
                  {form.formState.errors.description.message}
                </p>
              )}
            </div>
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Отмена
            </Button>
            <Button type="submit" disabled={loading || !form.formState.isValid}>
              {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Начислить
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

