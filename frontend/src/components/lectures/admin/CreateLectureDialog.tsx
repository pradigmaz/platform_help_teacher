'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
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
import { Plus } from 'lucide-react';

interface Subject {
  id: string;
  name: string;
  code: string | null;
}

interface CreateLectureDialogProps {
  subjects: Subject[];
  onSubmit: (title: string, subjectId: string | null) => Promise<void>;
}

export function CreateLectureDialog({ subjects, onSubmit }: CreateLectureDialogProps) {
  const [open, setOpen] = useState(false);
  const [title, setTitle] = useState('');
  const [subjectId, setSubjectId] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;
    
    setCreating(true);
    try {
      await onSubmit(title.trim(), subjectId);
      setOpen(false);
      setTitle('');
      setSubjectId(null);
    } finally {
      setCreating(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button className="bg-gradient-to-r from-primary to-purple-600 hover:from-primary/90 hover:to-purple-600/90">
          <Plus className="mr-2 h-4 w-4" /> Создать лекцию
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[400px]">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>Новая лекция</DialogTitle>
            <DialogDescription>Введите название и выберите предмет</DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="title">Название</Label>
              <Input
                id="title"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Введение в алгоритмы"
                required
                autoFocus
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="subject">Предмет</Label>
              <Select value={subjectId || ''} onValueChange={(v) => setSubjectId(v || null)}>
                <SelectTrigger>
                  <SelectValue placeholder="Выберите предмет (опционально)" />
                </SelectTrigger>
                <SelectContent>
                  {subjects.map(subject => (
                    <SelectItem key={subject.id} value={subject.id}>
                      {subject.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => setOpen(false)}>
              Отмена
            </Button>
            <Button type="submit" disabled={creating || !title.trim()}>
              {creating ? 'Создание...' : 'Создать'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
