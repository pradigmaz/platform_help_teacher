'use client';

import { useState } from 'react';
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
  const [points, setPoints] = useState<string>('0.5');
  const [description, setDescription] = useState('');
  const [attestationType, setAttestationType] = useState<AttestationType>('first');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      await ActivitiesAPI.create({
        [mode === 'group' ? 'group_id' : 'student_id']: targetId,
        points: parseFloat(points),
        description,
        attestation_type: attestationType,
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
      setPoints('0.5');
      setDescription('');
    } catch (error) {
      toast.error('Ошибка при начислении активности');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

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
                value={attestationType} 
                onValueChange={(v) => setAttestationType(v as AttestationType)}
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
                  value={points}
                  onChange={(e) => setPoints(e.target.value)}
                  placeholder="0.5"
                  className="pl-8"
                  required
                />
                <span className="absolute left-3 top-2.5 text-muted-foreground font-bold text-sm">
                  {parseFloat(points) > 0 ? '+' : ''}
                </span>
              </div>
              <p className="text-xs text-muted-foreground">
                Используйте отрицательные значения для штрафов (например, -0.5)
              </p>
            </div>
            
            <div className="grid gap-2">
              <Label htmlFor="description">Описание / Причина</Label>
              <Textarea
                id="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="За активное участие в..."
                required
              />
            </div>
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Отмена
            </Button>
            <Button type="submit" disabled={loading}>
              {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Начислить
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

