'use client';

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

interface LabForm {
  title: string;
  description: string;
  max_grade: number;
  deadline: string;
}

interface LabDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  form: LabForm;
  setForm: (form: LabForm) => void;
  onSubmit: (e: React.FormEvent) => void;
  isEditing: boolean;
}

export function LabDialog({ open, onOpenChange, form, setForm, onSubmit, isEditing }: LabDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <form onSubmit={onSubmit}>
          <DialogHeader>
            <DialogTitle>{isEditing ? 'Редактировать' : 'Новая лабораторная'}</DialogTitle>
            <DialogDescription>
              {isEditing ? 'Измените данные лабораторной работы' : 'Заполните данные для создания'}
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="title">Название</Label>
              <Input 
                id="title" 
                value={form.title} 
                onChange={(e) => setForm({ ...form, title: e.target.value })} 
                placeholder="Лабораторная работа №1" 
                required 
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="description">Описание</Label>
              <Textarea 
                id="description" 
                value={form.description} 
                onChange={(e) => setForm({ ...form, description: e.target.value })} 
                placeholder="Описание задания..." 
                rows={3} 
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="grid gap-2">
                <Label htmlFor="max_grade">Макс. балл</Label>
                <Input 
                  id="max_grade" 
                  type="number" 
                  min={1} 
                  value={form.max_grade} 
                  onChange={(e) => setForm({ ...form, max_grade: parseInt(e.target.value) || 10 })} 
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="deadline">Дедлайн</Label>
                <Input 
                  id="deadline" 
                  type="date" 
                  value={form.deadline} 
                  onChange={(e) => setForm({ ...form, deadline: e.target.value })} 
                />
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button type="submit">{isEditing ? 'Сохранить' : 'Создать'}</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
