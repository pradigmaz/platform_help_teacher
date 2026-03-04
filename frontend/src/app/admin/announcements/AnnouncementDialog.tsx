'use client';

import { useEffect, useState } from 'react';
import { Loader2, Save } from 'lucide-react';
import { toast } from 'sonner';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import api from '@/lib/api';

interface AnnouncementDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  announcementId: string | null;
  onSuccess: () => void;
}

export function AnnouncementDialog({ open, onOpenChange, announcementId, onSuccess }: AnnouncementDialogProps) {
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  const isEdit = !!announcementId;

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => {
    if (open && announcementId) {
      loadAnnouncement();
    } else if (open) {
      setTitle('');
      setContent('');
    }
  }, [open, announcementId]);

  const loadAnnouncement = async () => {
    setLoading(true);
    try {
      const { data } = await api.get(`/admin/announcements/${announcementId}`);
      setTitle(data.title);
      setContent(data.content);
    } catch {
      toast.error('Ошибка загрузки');
      onOpenChange(false);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (title.length < 3) {
      toast.error('Заголовок слишком короткий');
      return;
    }
    if (content.length < 10) {
      toast.error('Содержимое слишком короткое');
      return;
    }

    setSaving(true);
    try {
      if (isEdit) {
        await api.put(`/admin/announcements/${announcementId}`, { title, content });
        toast.success('Сохранено');
      } else {
        await api.post('/admin/announcements', { title, content });
        toast.success('Черновик создан');
      }
      onSuccess();
      onOpenChange(false);
    } catch {
      toast.error('Ошибка сохранения');
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>{isEdit ? 'Редактировать объявление' : 'Новое объявление'}</DialogTitle>
        </DialogHeader>

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin" />
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="title">Заголовок</Label>
              <Input
                id="title"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Новая функция: уведомления"
                required
                minLength={3}
                maxLength={200}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="content">Содержимое</Label>
              <Textarea
                id="content"
                value={content}
                onChange={(e) => setContent(e.target.value)}
                placeholder="Описание обновления или объявления..."
                required
                minLength={10}
                rows={10}
                className="resize-y"
              />
              <p className="text-xs text-muted-foreground">
                Поддерживается Markdown
              </p>
            </div>

            <div className="flex justify-end gap-2 pt-4">
              <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
                Отмена
              </Button>
              <Button type="submit" disabled={saving} className="gap-2">
                {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
                {isEdit ? 'Сохранить' : 'Создать черновик'}
              </Button>
            </div>
          </form>
        )}
      </DialogContent>
    </Dialog>
  );
}
