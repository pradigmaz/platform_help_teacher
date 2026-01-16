'use client';

import { useEffect, useState } from 'react';
import { Plus, Loader2, FileText, Send, Eye, Pencil, Trash2 } from 'lucide-react';
import { toast } from 'sonner';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { BlurFade } from '@/components/ui/blur-fade';
import api from '@/lib/api';
import { AnnouncementDialog } from './AnnouncementDialog';

interface Announcement {
  id: string;
  title: string;
  content: string;
  is_draft: boolean;
  published_at: string | null;
  created_at: string;
  author_name: string | null;
}

export default function AnnouncementsPage() {
  const [announcements, setAnnouncements] = useState<Announcement[]>([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [sending, setSending] = useState<string | null>(null);

  const fetchAnnouncements = async () => {
    try {
      const { data } = await api.get<Announcement[]>('/admin/announcements');
      setAnnouncements(data);
    } catch {
      toast.error('Ошибка загрузки объявлений');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnnouncements();
  }, []);

  const handleCreate = () => {
    setEditingId(null);
    setDialogOpen(true);
  };

  const handleEdit = (id: string) => {
    setEditingId(id);
    setDialogOpen(true);
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Удалить объявление?')) return;
    try {
      await api.delete(`/admin/announcements/${id}`);
      toast.success('Удалено');
      fetchAnnouncements();
    } catch {
      toast.error('Ошибка удаления');
    }
  };

  const handlePublish = async (id: string) => {
    try {
      await api.post(`/admin/announcements/${id}/publish`);
      toast.success('Опубликовано');
      fetchAnnouncements();
    } catch {
      toast.error('Ошибка публикации');
    }
  };

  const handleSend = async (id: string) => {
    setSending(id);
    try {
      const { data } = await api.post(`/admin/announcements/${id}/send`);
      toast.success(`Отправлено: Telegram ${data.stats.telegram_sent}, VK ${data.stats.vk_sent}`);
    } catch {
      toast.error('Ошибка отправки');
    } finally {
      setSending(null);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  const drafts = announcements.filter(a => a.is_draft);
  const published = announcements.filter(a => !a.is_draft);

  return (
    <div className="space-y-6">
      <BlurFade delay={0.1}>
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">Объявления</h1>
          <Button onClick={handleCreate} className="gap-2">
            <Plus className="h-4 w-4" />
            Создать
          </Button>
        </div>
      </BlurFade>

      {/* Черновики */}
      {drafts.length > 0 && (
        <BlurFade delay={0.15}>
          <div className="space-y-3">
            <h2 className="text-lg font-semibold text-muted-foreground">Черновики</h2>
            {drafts.map((a, i) => (
              <AnnouncementCard
                key={a.id}
                announcement={a}
                delay={0.2 + i * 0.05}
                onEdit={() => handleEdit(a.id)}
                onDelete={() => handleDelete(a.id)}
                onPublish={() => handlePublish(a.id)}
              />
            ))}
          </div>
        </BlurFade>
      )}

      {/* Опубликованные */}
      <BlurFade delay={0.25}>
        <div className="space-y-3">
          <h2 className="text-lg font-semibold text-muted-foreground">Опубликованные</h2>
          {published.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center text-muted-foreground">
                Нет опубликованных объявлений
              </CardContent>
            </Card>
          ) : (
            published.map((a, i) => (
              <AnnouncementCard
                key={a.id}
                announcement={a}
                delay={0.3 + i * 0.05}
                onEdit={() => handleEdit(a.id)}
                onDelete={() => handleDelete(a.id)}
                onSend={() => handleSend(a.id)}
                sending={sending === a.id}
              />
            ))
          )}
        </div>
      </BlurFade>

      <AnnouncementDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        announcementId={editingId}
        onSuccess={fetchAnnouncements}
      />
    </div>
  );
}

function AnnouncementCard({ 
  announcement, 
  delay, 
  onEdit, 
  onDelete, 
  onPublish, 
  onSend,
  sending 
}: {
  announcement: Announcement;
  delay: number;
  onEdit: () => void;
  onDelete: () => void;
  onPublish?: () => void;
  onSend?: () => void;
  sending?: boolean;
}) {
  return (
    <BlurFade delay={delay}>
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between gap-4">
            <div className="flex items-center gap-2">
              <FileText className="h-5 w-5 text-purple-500" />
              <CardTitle className="text-lg">{announcement.title}</CardTitle>
            </div>
            <Badge variant={announcement.is_draft ? "secondary" : "default"}>
              {announcement.is_draft ? 'Черновик' : 'Опубликовано'}
            </Badge>
          </div>
          <p className="text-sm text-muted-foreground">
            {announcement.author_name || 'Автор неизвестен'}
            {' • '}
            {new Date(announcement.published_at || announcement.created_at).toLocaleDateString('ru', {
              day: 'numeric',
              month: 'short',
              year: 'numeric'
            })}
          </p>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-muted-foreground line-clamp-3">{announcement.content}</p>
          
          <div className="flex gap-2 pt-2 border-t">
            <Button size="sm" variant="outline" onClick={onEdit} className="gap-1">
              <Pencil className="h-3.5 w-3.5" />
              Редактировать
            </Button>
            
            {announcement.is_draft && onPublish && (
              <Button size="sm" variant="default" onClick={onPublish} className="gap-1">
                <Eye className="h-3.5 w-3.5" />
                Опубликовать
              </Button>
            )}
            
            {!announcement.is_draft && onSend && (
              <Button size="sm" variant="secondary" onClick={onSend} disabled={sending} className="gap-1">
                {sending ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Send className="h-3.5 w-3.5" />}
                Отправить
              </Button>
            )}
            
            <Button size="sm" variant="ghost" onClick={onDelete} className="gap-1 text-destructive hover:text-destructive">
              <Trash2 className="h-3.5 w-3.5" />
            </Button>
          </div>
        </CardContent>
      </Card>
    </BlurFade>
  );
}
